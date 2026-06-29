
from django.shortcuts import render, redirect 
from django.contrib import messages
from .models import User
from .forms import RegisterForm, LoginForm
from django.http import JsonResponse
import bcrypt
import secrets
import requests
from urllib.parse import urlencode
from django.views import View
from django.conf import settings
from portfolios.models import Profile

def login(request):

    if 'user_id' in request.session: 
        return redirect('portfolios:onboarding_one')
    context = {'login_form': LoginForm()}

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            email_input = login_form.cleaned_data['email']
            password_input = login_form.cleaned_data['password']
            user_list = User.objects.filter(email__iexact=email_input)
            
            if user_list:
                logged_user = user_list[0]
                if bcrypt.checkpw(password_input.encode(), logged_user.password.encode()):
                    request.session['user_id'] = logged_user.id
                    return redirect('portfolios:onboarding_one')
            
            messages.error(request, "Invalid Email or Password")
            
            context['login_form'] = login_form
            
        else:
            context['login_form'] = login_form

    
    return render(request, 'accounts/login.html', context)

def register(request):

    if 'user_id' in request.session:
        return redirect('portfolios:onboarding_one')
 
    context = {'reg_form': RegisterForm()}

    if request.method == 'POST':
        reg_form = RegisterForm(request.POST) 
        if reg_form.is_valid():
            user = reg_form.save(commit=False)
            password = reg_form.cleaned_data['password']
            user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user.save()
            Profile.objects.create(
                user      = user,
                full_name = f"{user.first_name} {user.last_name}",
            )
            request.session['user_id'] = user.id 
            return redirect('portfolios:onboarding_one')
        
        context['reg_form'] = reg_form

    return render(request, 'accounts/register.html', context)

def logout(request):
    request.session.clear()
    return redirect('accounts:login') 


class GoogleLoginView(View):
    """
    Step 1: Redirect the user to Google's login page.
    """

    def get(self, request):
        # Generate a random state token to prevent CSRF attacks
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state

        # Build the Google authorization URL
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'online',
            'prompt': 'select_account',  # Always show account chooser
        }

        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return redirect(google_auth_url)


class GoogleCallbackView(View):
    """
    Step 2: Google redirects back here with a code.
    We exchange the code for user info and log them in.
    """

    def get(self, request):
        # 1. Check for errors from Google (user denied access, etc.)
        error = request.GET.get('error')
        if error:
            messages.error(request, f'Google login failed: {error}')
            return redirect('accounts:login')

        # 2. Verify state token (CSRF protection)
        state = request.GET.get('state')
        saved_state = request.session.pop('google_oauth_state', None)
        if not state or state != saved_state:
            messages.error(request, 'Invalid state token. Please try again.')
            return redirect('accounts:login')

        # 3. Get the authorization code
        code = request.GET.get('code')
        if not code:
            messages.error(request, 'No authorization code received.')
            return redirect('accounts:login')

        # 4. Exchange the code for an access token
        token_data = self._exchange_code_for_token(code)
        if not token_data:
            messages.error(request, 'Failed to get access token from Google.')
            return redirect('accounts:login')

        # 5. Get user info from Google
        user_info = self._get_user_info(token_data['access_token'])
        if not user_info:
            messages.error(request, 'Failed to fetch user info from Google.')
            return redirect('accounts:login')

        # 6. Find or create the user
        user = self._get_or_create_user(user_info)

        # 7. Log the user in (session)
        request.session['user_id'] = user.id
        request.session['user_name'] = user.first_name

        messages.success(request, f'Welcome {user.first_name}!')
        return redirect('portfolios:onboarding_one')

    def _exchange_code_for_token(self, code):
        """POST request to Google to exchange code for access token."""
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }

        try:
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Token exchange error: {e}")
            return None

    def _get_user_info(self, access_token):
        """GET user info from Google using the access token."""
        user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get(user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"User info error: {e}")
            return None

    def _get_or_create_user(self, user_info):
        """
        Find an existing user or create a new one.
        Google returns: { sub, email, given_name, family_name, picture, ... }
        """
        google_id = user_info.get('sub')  # Google's unique user ID
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        picture = user_info.get('picture', '')

        # Try to find by google_id first
        user = User.objects.filter(google_id=google_id).first()
        if user:
            return user

        # Then try by email (user might have registered locally before)
        user = User.objects.filter(email=email).first()
        if user:
            # Link the Google account to the existing user
            user.google_id = google_id
            if not user.profile_picture:
                user.profile_picture = picture
            user.save()
            return user

        # Create a brand new user
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            google_id=google_id,
            profile_picture=picture,
            password=None,  # No password for Google users
        )
        return user

