from django.shortcuts import redirect

from .models import Profile

ONBOARDING_PATHS = {
    '/portfolios/onboarding-one/',
    '/portfolios/onboarding-two/',
    '/portfolios/onboarding-three/',
}

# Paths that should NOT be blocked even if onboarding is incomplete
ONBOARDING_EXEMPTIONS = {
    '/portfolios/preview/',  # Allow preview iframe to load during onboarding
}

class OnboardingMiddleware:
    """Ensure onboarding is completed before allowing access to the main app.

    - If authenticated and onboarding is incomplete, redirect to onboarding1.
    - If authenticated and onboarding completed, block access to onboarding paths.
    - Do not interfere with login/logout, static files, or anonymous pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not request.session.get('user_id'):
            return self.get_response(request)

        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        if path.startswith('/api/'):
            return self.get_response(request)

        if path.startswith('/accounts/login') or path.startswith('/accounts/register') or path.startswith('/accounts/logout'):
            return self.get_response(request)

        try:
            profile = Profile.objects.get(user_id=request.session['user_id'])
        except Profile.DoesNotExist:
            profile = None

        onboarding_completed = bool(getattr(profile, 'onboarding_completed', False))

        # Allow exempted paths even if onboarding is incomplete
        is_exempted_path = any(path.startswith(exemption) for exemption in ONBOARDING_EXEMPTIONS)

        if not onboarding_completed and path not in ONBOARDING_PATHS and not is_exempted_path:
            return redirect('portfolios:onboarding_one')

        if onboarding_completed and path in ONBOARDING_PATHS:
            return redirect('dashboard:main_dashboard')

        return self.get_response(request)
