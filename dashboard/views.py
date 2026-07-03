from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import User
from django.urls import reverse

from portfolios.forms import PublicationForm, ProfileForm, TeachingForm, EducationForm, ContactLinkForm,PublicationFormSet, TeachingFormSet, EducationFormSet, ContactLinkFormSet

from portfolios.models import Theme, Profile, Publication, Teaching, Education, ContactLink

from .forms import AccountSettingsForm
import bcrypt



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

    # Ensure this user has a Profile row (auto-create on first visit)
    default_theme = Theme.objects.filter(slug='academic-light', is_active=True).first()
    full_name = (
            getattr(user, 'full_name', None)
            or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            or getattr(user, 'username', None)
            or getattr(user, 'email', 'User')
    )
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'full_name': full_name, 'theme': default_theme},
    )

    if request.method == 'POST':
        selected_template = request.POST.get('selected_template', profile.selected_template)
        valid_templates = {value for value, _ in profile.TEMPLATE_CHOICES}
        if selected_template in valid_templates:
            profile.selected_template = selected_template
            profile.save()
            messages.success(request, 'Template selection saved successfully.')
            return redirect('dashboard:templates_dashboard')

    # All active themes for the gallery
    themes = Theme.objects.filter(is_active=True).order_by('name')

    # Which theme is shown in the preview pane right now
    preview_slug = request.GET.get('preview')
    active_theme = None
    if preview_slug:
        active_theme = Theme.objects.filter(slug=preview_slug, is_active=True).first()
    active_theme = active_theme or profile.theme or themes.first()

    preview_url = None
    if active_theme:
        preview_url = reverse('portfolios:preview', args=[active_theme.slug])

    return render(request, 'dashboard/templates_dashboard.html', {
        'user': user,
        'profile': profile,
        'themes': themes,
        'active_theme': active_theme,
        'preview_url': preview_url,
    })


def settings_view(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user = get_current_user(request)
    profile = get_profile(user)

    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, request.FILES, current_user=user)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name'].strip()
            user.last_name = form.cleaned_data['last_name'].strip()
            # email is read-only in the form; only update if different and allowed
            user.email = form.cleaned_data['email'].strip()
            if form.cleaned_data.get('new_password'):
                user.password = bcrypt.hashpw(
                    form.cleaned_data['new_password'].encode(),
                    bcrypt.gensalt()
                ).decode()
            user.save()

            profile.full_name = form.cleaned_data['full_name'].strip()
            profile.academic_title = form.cleaned_data['academic_title'].strip()
            profile.institution = form.cleaned_data['institution'].strip()
            profile.field_of_study = form.cleaned_data['field_of_study'].strip()
            profile.bio = form.cleaned_data['bio'].strip()

            if request.FILES.get('profile_image'):
                profile.profile_image = request.FILES['profile_image']

            profile.save()
            messages.success(request, 'Your settings were updated successfully.')
            return redirect('dashboard:setting_dashboard')
    else:
        form = AccountSettingsForm(initial={
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email or '',
            'full_name': profile.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'academic_title': profile.academic_title or '',
            'institution': profile.institution or '',
            'field_of_study': profile.field_of_study or '',
            'bio': profile.bio or '',
        }, current_user=user)

    return render(request, 'dashboard/setting_dashboard.html', {
        'user': user,
        'profile': profile,
        'form': form,
    })


def set_theme_view(request):
    """Save & Publish — sets the selected theme as the user's active theme."""
    if 'user_id' not in request.session:
        return redirect('accounts:login')
    if request.method != 'POST':
        return redirect('dashboard:templates_dashboard')

    user = get_current_user(request)
    profile = get_profile(user)

    slug = request.POST.get('theme_slug')
    theme = get_object_or_404(Theme, slug=slug, is_active=True)
    profile.theme = theme
    profile.save()

    return redirect('dashboard:templates_dashboard')


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
    next_url = request.GET.get('next', '')
    if next_url.startswith('/'):
        return redirect(next_url)
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
    next_url = request.GET.get('next', '')
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('dashboard:main_dashboard')



# def edit_profile(request):
#     if 'user_id' not in request.session:
#         return redirect('accounts:login')

#     user, profile = get_user_and_profile(request)

#     form = ProfileForm(
#         request.POST  or None,
#         request.FILES or None,
#         instance=profile
#     )

#     if form.is_valid():
#         form.save()

#         pub_ids = request.POST.getlist('pub_id[]')
#         pub_titles = request.POST.getlist('pub_title[]')
#         pub_dates = request.POST.getlist('pub_date[]')
#         pub_pdfs = request.POST.getlist('pub_pdf[]')
#         pub_githubs = request.POST.getlist('pub_github[]')

#         for idx, title in enumerate(pub_titles):
#             title_text = title.strip()
#             if idx < len(pub_ids) and pub_ids[idx].strip():
#                 pub = Publication.objects.filter(id=pub_ids[idx], profile=profile).first()
#                 if pub:
#                     if not title_text:
#                         pub.delete()
#                         continue
#                     pub.title = title_text
#                     pub.publication_date = pub_dates[idx] or None
#                     pub.pdf_link = pub_pdfs[idx] if idx < len(pub_pdfs) else ''
#                     pub.github_link = pub_githubs[idx] if idx < len(pub_githubs) else ''
#                     pub.save()
#                     continue
#             if not title_text:
#                 continue
#             Publication.objects.create(
#                 profile=profile,
#                 title=title_text,
#                 publication_date=pub_dates[idx] or None,
#                 pdf_link=pub_pdfs[idx] if idx < len(pub_pdfs) else '',
#                 github_link=pub_githubs[idx] if idx < len(pub_githubs) else '',
#             )

#         teach_ids = request.POST.getlist('teach_id[]')
#         course_names = request.POST.getlist('course_name[]')
#         course_semesters = request.POST.getlist('semester[]')
#         course_descs = request.POST.getlist('course_desc[]')
#         course_links = request.POST.getlist('syllabus_link[]')

#         for idx, name in enumerate(course_names):
#             name_text = name.strip()
#             if idx < len(teach_ids) and teach_ids[idx].strip():
#                 teach = Teaching.objects.filter(id=teach_ids[idx], profile=profile).first()
#                 if teach:
#                     if not name_text:
#                         teach.delete()
#                         continue
#                     teach.course_name = name_text
#                     teach.semester = course_semesters[idx] if idx < len(course_semesters) else ''
#                     teach.description = course_descs[idx] if idx < len(course_descs) else ''
#                     teach.syllabus_link = course_links[idx] if idx < len(course_links) else ''
#                     teach.save()
#                     continue
#             if not name_text:
#                 continue
#             Teaching.objects.create(
#                 profile=profile,
#                 course_name=name_text,
#                 semester=course_semesters[idx] if idx < len(course_semesters) else '',
#                 description=course_descs[idx] if idx < len(course_descs) else '',
#                 syllabus_link=course_links[idx] if idx < len(course_links) else '',
#             )

#         return redirect('dashboard:main_dashboard')

#     publications = Publication.objects.filter(profile=profile)
#     teachings = Teaching.objects.filter(profile=profile)

#     return render(request, 'dashboard/profile.html', {
#         'form'   : form,
#         'profile': profile,
#         'publications': publications,
#         'teachings': teachings,
#     })

def edit_profile(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user, profile = get_user_and_profile(request)

    # كل formset بيعرف تلقائياً يجيب بيانات الـ profile
    profile_form  = ProfileForm(
        request.POST  or None,
        request.FILES or None,
        instance=profile,
    )
    pub_formset   = PublicationFormSet(request.POST or None, instance=profile, prefix='pub')
    teach_formset = TeachingFormSet(request.POST or None,   instance=profile, prefix='teach')
    edu_formset   = EducationFormSet(request.POST or None,  instance=profile, prefix='edu')
    cl_formset    = ContactLinkFormSet(request.POST or None, instance=profile, prefix='cl')

    if request.method == 'POST':
        all_valid = (
            profile_form.is_valid()  and
            pub_formset.is_valid()   and
            teach_formset.is_valid() and
            edu_formset.is_valid()   and
            cl_formset.is_valid()
        )
        if all_valid:
            profile_form.save()
            pub_formset.save()    # يضيف + يعدل + يحذف تلقائياً
            teach_formset.save()
            edu_formset.save()
            cl_formset.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard:main_dashboard')

    return render(request, 'dashboard/profile.html', {
        'form'         : profile_form,
        'pub_formset'  : pub_formset,
        'teach_formset': teach_formset,
        'edu_formset'  : edu_formset,
        'cl_formset'   : cl_formset,
        'profile'      : profile,
    })