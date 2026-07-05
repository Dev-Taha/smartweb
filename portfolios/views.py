"""
portfolios/onboarding.py

Multi-step onboarding flow for newly registered users: collect profile info,
publications, and teaching load, then let them pick a starting template.
"""
import io
import json
import logging
import threading
import traceback
import uuid
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import OperationalError
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.urls import reverse

from accounts.models import User
from services.ai_extraction import (
    extract_text_from_cv_file,
    extract_cv_data,
    save_extracted_data,
)
from .models import Profile, Publication, Teaching, Theme
from django.contrib import messages
from .forms import ProfileForm, PublicationForm, TeachingForm, EducationFormSet


def _form_has_data(form):
    """Return True when a bound form contains meaningful user input."""
    if not form.is_bound:
        return False

    for field_name in form.fields:
        if field_name in {'DELETE'}:
            continue
        value = form.cleaned_data.get(field_name)
        if value not in (None, '', []):
            return True
    return False


def _is_empty_optional_form(form):
    """Return True for new optional forms that contain no meaningful input."""
    if form.instance.pk:
        return False
    return not _form_has_data(form)

logger = logging.getLogger(__name__)

CV_TASKS: dict[str, dict] = {}
CV_TASKS_LOCK = threading.Lock()

SECTIONS = [
    'Personal Info', 'Professional Bio', 'Education', 'Research Interests',
    'Publications', 'Teaching Load', 'Contact Details',
]


def get_current_user(request):
    return User.objects.get(id=request.session['user_id'])


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'full_name': f"{user.first_name} {user.last_name}"}
    )
    return profile


def onboarding_one(request):
    return render(request, 'onboarding/onboarding1.html')


def _start_cv_task(profile, file_obj, filename):
    task_id = str(uuid.uuid4())
    with CV_TASKS_LOCK:
        CV_TASKS[task_id] = {"status": "processing", "data": None, "error": None}

    file_bytes = file_obj.read()
    mirror_file = io.BytesIO(file_bytes)
    mirror_file.name = filename

    def task():
        try:
            text = extract_text_from_cv_file(io.BytesIO(file_bytes), filename, file_size=len(file_bytes))
            extracted_json = extract_cv_data(text)
            profile.cv_file.save(filename, ContentFile(file_bytes), save=True)
            save_extracted_data(profile, extracted_json)
            with CV_TASKS_LOCK:
                CV_TASKS[task_id]["status"] = "completed"
                CV_TASKS[task_id]["data"] = extracted_json
        except Exception as exc:
            logger.error(
                "CV processing failed for task %s: %s\n%s",
                task_id,
                exc,
                traceback.format_exc(),
            )
            with CV_TASKS_LOCK:
                CV_TASKS[task_id]["status"] = "failed"
                CV_TASKS[task_id]["error"] = str(exc)

    background_thread = threading.Thread(target=task, daemon=True)
    background_thread.start()
    return task_id


def upload_cv(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST supported.')
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    if 'cv_file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    file = request.FILES['cv_file']
    if file.size == 0:
        return JsonResponse({'error': 'Uploaded file is empty.'}, status=400)

    file_bytes = file.read()
    if len(file_bytes) == 0:
        return JsonResponse({'error': 'Uploaded file is empty.'}, status=400)
    if file.size is not None and len(file_bytes) != file.size:
        return JsonResponse({'error': 'File upload appears incomplete.'}, status=400)

    extension = file.name.lower().rsplit('.', 1)[-1] if '.' in file.name else ''
    extension = f".{extension}"
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            PdfReader(io.BytesIO(file_bytes))
        except Exception:
            return JsonResponse(
                {'error': 'Unable to open the PDF file. Please verify it is a valid PDF.'},
                status=400,
            )

    user = get_current_user(request)
    profile = get_profile(user)
    if profile is None:
        return JsonResponse({'error': 'User profile not found.'}, status=404)

    try:
        task_id = _start_cv_task(profile, io.BytesIO(file_bytes), file.name)
        return JsonResponse({'task_id': task_id, 'status': 'processing'})
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({'error': 'Failed to start CV processing.'}, status=500)


def cv_status(request, task_id):
    with CV_TASKS_LOCK:
        task = CV_TASKS.get(task_id)
    if task is None:
        return JsonResponse({'error': 'Task not found.'}, status=404)
    response = {'status': task['status']}
    if task['status'] == 'completed':
        response['data'] = task['data']
    elif task['status'] == 'failed':
        response['error'] = task['error']
    return JsonResponse(response)


def onboarding_two(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user = get_current_user(request)
    profile = get_profile(user)

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        publication_form = PublicationForm(request.POST)
        teaching_form = TeachingForm(request.POST)
        education_formset = EducationFormSet(request.POST, instance=profile)

        # validate everything; publications/teaching handling stays as-is
        forms_valid = profile_form.is_valid() and publication_form.is_valid() and teaching_form.is_valid() and education_formset.is_valid()

        if forms_valid:
            profile_form.save()

            if _form_has_data(publication_form):
                publication = publication_form.save(commit=False)
                publication.profile = profile
                publication.save()

            if _form_has_data(teaching_form):
                teaching = teaching_form.save(commit=False)
                teaching.profile = profile
                teaching.save()

            # Ignore empty education rows so optional blank entries do not break saving.
            valid_education_forms = [
                form for form in education_formset.forms
                if not _is_empty_optional_form(form)
            ]
            if valid_education_forms:
                education_formset.forms = valid_education_forms
                education_formset.save()

            pub_titles = request.POST.getlist('pub_title[]')
            pub_dates = request.POST.getlist('pub_date[]')
            pub_pdfs = request.POST.getlist('pub_pdf[]')
            pub_githubs = request.POST.getlist('pub_github[]')
            for idx, title in enumerate(pub_titles):
                if not title.strip():
                    continue
                extra_pub = Publication(
                    profile=profile,
                    title=title.strip(),
                    publication_date=pub_dates[idx] if idx < len(pub_dates) else None,
                    pdf_link=pub_pdfs[idx] if idx < len(pub_pdfs) else '',
                    github_link=pub_githubs[idx] if idx < len(pub_githubs) else '',
                )
                extra_pub.save()

            course_names = request.POST.getlist('course_name[]')
            course_semesters = request.POST.getlist('semester[]')
            course_descs = request.POST.getlist('course_desc[]')
            course_links = request.POST.getlist('syllabus_link[]')
            for idx, name in enumerate(course_names):
                if not name.strip():
                    continue
                extra_teaching = Teaching(
                    profile=profile,
                    course_name=name.strip(),
                    semester=course_semesters[idx] if idx < len(course_semesters) else '',
                    description=course_descs[idx] if idx < len(course_descs) else '',
                    syllabus_link=course_links[idx] if idx < len(course_links) else '',
                )
                extra_teaching.save()

            return redirect('portfolios:onboarding_three')
        else:
            # Provide a clear message when validation fails so the user isn't silently returned
            messages.error(request, 'There was an error saving your information. Please review the highlighted fields and try again.')
            try:
                logger.error('onboarding_two POST validation failed; profile_form.errors=%s', profile_form.errors.as_json())
            except Exception:
                logger.error('onboarding_two POST: could not serialize profile_form.errors')
            try:
                logger.error('publication_form.errors=%s', publication_form.errors.as_json())
            except Exception:
                logger.error('onboarding_two POST: could not serialize publication_form.errors')
            try:
                logger.error('teaching_form.errors=%s', teaching_form.errors.as_json())
            except Exception:
                logger.error('onboarding_two POST: could not serialize teaching_form.errors')
            try:
                logger.error('education_formset.errors=%s', json.dumps(education_formset.errors))
            except Exception:
                logger.error('onboarding_two POST: could not serialize education_formset.errors')
    else:
        profile_form = ProfileForm(instance=profile)
        publication_form = PublicationForm()
        teaching_form = TeachingForm()
        education_formset = EducationFormSet(instance=profile)

    context = {
        'profile_form': profile_form,
        'publication_form': publication_form,
        'teaching_form': teaching_form,
        'education_formset': education_formset,
        'sections': SECTIONS,
    }
    return render(request, 'onboarding/onboarding2.html', context)


def onboarding_three(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user = get_current_user(request)
    profile = get_profile(user)

    # All active themes for the gallery
    themes = Theme.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        theme_slug = request.POST.get('selected_template')
        theme = themes.filter(slug=theme_slug).first()
        if theme:
            profile.theme = theme
            profile.selected_template = theme_slug  # keeps existing choice field in sync
            profile.save()
            return redirect('dashboard:main_dashboard')

    preview_slug = request.GET.get('preview')
    active_theme = None
    if preview_slug:
        active_theme = themes.filter(slug=preview_slug).first()

    if active_theme is None:
        active_theme = profile.theme

    if active_theme is None:
        active_theme = themes.first()

    preview_url = None
    if active_theme:
        preview_url = reverse('portfolios:preview', args=[active_theme.slug])

    context = {
        'themes': themes,
        'active_theme': active_theme,
        'selected_template': active_theme.slug if active_theme else Profile.TEMPLATE_CLASSIC,
        'preview_url': preview_url,
    }
    return render(request, 'onboarding/onboarding3.html', context)


def portfolio_detail(request, slug):
    profile = get_object_or_404(Profile, slug=slug, is_published=True)
    publications = Publication.objects.filter(profile=profile)
    # Normalize research interests: prefer ResearchInterest entries, fall back to
    # legacy `profile.research_interests` text (one per line).
    ri_qs = profile.research_interests_entries.all() if hasattr(profile, 'research_interests_entries') else []
    if getattr(ri_qs, 'exists', None) and ri_qs.exists():
        research_items = ri_qs
    else:
        text = getattr(profile, 'research_interests', '') or ''
        # split on newlines or commas so legacy CSV-like entries become separate items
        import re
        parts = [p.strip() for p in re.split(r'[,\n]+', text) if p.strip()]
        from types import SimpleNamespace
        research_items = [SimpleNamespace(title=part, description='', tag_list=[]) for part in parts]

    return render(request, 'portfolios/portfolio_detail.html', {
        'profile': profile,
        'publications': profile.publications.all(),
        'teachings': profile.teachings.all(),
        'research_interests': research_items,
        'education': profile.education_entries.all(),
        'contact_links': profile.contact_links.all(),
    })


def resolve_preview_theme(theme_slug):
    slug_aliases = {
        'light-1': 'academic-light',
        'dark-1': 'modern-dark',
        'light-2': 'modern-light',
        'dark-2': 'academic-dark',
        'classic-scholar': 'academic-light',
        'modern-dark': 'modern-dark',
        'minimalist-lab': 'modern-light',
        'executive-academic': 'academic-dark',
    }
    resolved_slug = slug_aliases.get(theme_slug, theme_slug)

    try:
        db_theme = Theme.objects.filter(slug=resolved_slug, is_active=True).first()
    except OperationalError:
        db_theme = None

    if db_theme:
        return db_theme

    theme_dir = Path(settings.BASE_DIR) / 'templates' / 'themes' / resolved_slug
    if not theme_dir.exists():
        raise Http404('No Theme matches the given query.')

    metadata_path = theme_dir / 'theme.json'
    metadata = {}
    if metadata_path.exists():
        with metadata_path.open(encoding='utf-8') as fh:
            metadata = json.load(fh)

    return SimpleNamespace(
        slug=resolved_slug,
        name=metadata.get('name', resolved_slug.replace('-', ' ').title()),
        description=metadata.get('description', ''),
        template_path=f'themes/{resolved_slug}/index.html',
        preview_image=metadata.get('preview_image', ''),
        palette=metadata.get('palette', {}),
        is_active=True,
    )


@xframe_options_exempt
def portfolio_preview(request, theme_slug):
    if 'user_id' not in request.session:
        return redirect('accounts:login')

    user = get_current_user(request)
    profile = get_profile(user)
    theme = resolve_preview_theme(theme_slug)

    ri_qs = profile.research_interests_entries.all() if hasattr(profile, 'research_interests_entries') else []
    if getattr(ri_qs, 'exists', None) and ri_qs.exists():
        research_items = ri_qs
    else:
        text = getattr(profile, 'research_interests', '') or ''
        import re
        parts = [p.strip() for p in re.split(r'[,\n]+', text) if p.strip()]
        from types import SimpleNamespace
        research_items = [SimpleNamespace(title=part, description='', tag_list=[]) for part in parts]

    return render(request, theme.template_path, {
        'theme': theme,
        'profile': profile,
        'publications': profile.publications.all(),
        'teachings': profile.teachings.all(),
        'research_interests': research_items,
        'education': profile.education_entries.all() if hasattr(profile, 'education_entries') else [],
        'contact_links': profile.contact_links.all() if hasattr(profile, 'contact_links') else [],
    })
