
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import User
from portfolios.models import Profile, Publication, Teaching
from portfolios.forms import PublicationForm,ProfileForm, TeachingForm



def get_current_user(request):
    return User.objects.get(id=request.session['user_id'])
def get_user_and_profile(request):
    user = User.objects.get(id=request.session['user_id'])
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(
            user      = user,
            full_name = f"{user.first_name} {user.last_name}",
        )
    return user, profile


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'full_name': f"{user.first_name} {user.last_name}"}
    )
    return profile


# ── الموجودة عندك ─────────────────────────────────────────────────────────
def dashboard_view(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    publications = Publication.objects.filter(profile=profile)
    teachings    = Teaching.objects.filter(profile=profile)
    return render(request, 'dashboard/dashboard.html', {
        'user'        : user,
        'profile'     : profile,
        'publications': publications,
        'teachings'   : teachings,
        'pub_count'   : publications.count(),
        'teach_count' : teachings.count(),
    })


def templates_view(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user = get_current_user(request)
    return render(request, 'dashboard/templates_dashboard.html', {'user': user})


def settings_view(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user = get_current_user(request)
    return render(request, 'dashboard/setting_dashboard.html', {'user': user})


# ── Publications ──────────────────────────────────────────────────────────
def add_publication(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    form    = PublicationForm()
    if request.method == 'POST':
        form = PublicationForm(request.POST)
        if form.is_valid():
            pub         = form.save(commit=False)
            pub.profile = profile
            pub.save()
            messages.success(request, 'Publication added successfully!')
            return redirect('dashboard:main_dashboard')
    return render(request, 'dashboard/publication.html', {
        'form': form, 'title': 'Add Publication'
    })


def edit_publication(request, pub_id):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    pub     = get_object_or_404(Publication, id=pub_id, profile=profile)
    form    = PublicationForm(instance=pub)
    if request.method == 'POST':
        form = PublicationForm(request.POST, instance=pub)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publication updated!')
            return redirect('dashboard:main_dashboard')
    return render(request, 'dashboard/publication.html', {
        'form': form, 'title': 'Edit Publication'
    })


def delete_publication(request, pub_id):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    pub     = get_object_or_404(Publication, id=pub_id, profile=profile)
    pub.delete()
    messages.success(request, 'Publication deleted.')
    return redirect('dashboard:main_dashboard')


# ── Teachings ─────────────────────────────────────────────────────────────
def add_teaching(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    form    = TeachingForm()
    if request.method == 'POST':
        form = TeachingForm(request.POST)
        if form.is_valid():
            teach         = form.save(commit=False)
            teach.profile = profile
            teach.save()
            messages.success(request, 'Course added successfully!')
            return redirect('dashboard:main_dashboard')
    return render(request, 'dashboard/teaching.html', {
        'form': form, 'title': 'Add Course'
    })


def edit_teaching(request, teach_id):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    teach   = get_object_or_404(Teaching, id=teach_id, profile=profile)
    form    = TeachingForm(instance=teach)
    if request.method == 'POST':
        form = TeachingForm(request.POST, instance=teach)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated!')
            return redirect('dashboard:main_dashboard')
    return render(request, 'dashboard/teaching.html', {
        'form': form, 'title': 'Edit Course'
    })


def delete_teaching(request, teach_id):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    user    = get_current_user(request)
    profile = get_profile(user)
    teach   = get_object_or_404(Teaching, id=teach_id, profile=profile)
    teach.delete()
    messages.success(request, 'Course deleted.')
    return redirect('dashboard:main_dashboard')



def edit_profile(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user, profile = get_user_and_profile(request)

    form = ProfileForm(
        request.POST  or None,
        request.FILES or None,
        instance=profile
    )

    if form.is_valid():
        form.save()
        return redirect('dashboard:main_dashboard')

    return render(request, 'dashboard/profile.html', {
        'form'   : form,
        'profile': profile,
    })