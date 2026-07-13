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
import mimetypes
import os

from django.http import FileResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse

from accounts.models import User
from services.ai_extraction import (
    extract_text_from_cv_file,
    extract_cv_data,
    save_extracted_data,
)
from .models import Profile, Publication, Teaching, Theme, ContactLink
from django.contrib import messages
from django.db.models import Max
from .forms import ProfileForm, PublicationForm, TeachingForm, EducationFormSet, PublicationFormSet, TeachingFormSet


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


@ensure_csrf_cookie
def onboarding_one(request):
    if 'user_id' not in request.session:
        return redirect('accounts:login')
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
        return JsonResponse({'error': 'Only POST supported.'}, status=405)
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

    try:
        user = get_current_user(request)
    except Exception:
        return JsonResponse({'error': 'Invalid session or user not found.'}, status=401)

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

    education_error_message = None
    focus_education = False

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        # detect if client posted formset management data; if not, fall back to legacy array fields
        has_pub_formset = any(k.startswith('publications-') for k in request.POST.keys()) or 'publications-TOTAL_FORMS' in request.POST
        has_teach_formset = any(k.startswith('teachings-') for k in request.POST.keys()) or 'teachings-TOTAL_FORMS' in request.POST

        if has_pub_formset:
            publication_formset = PublicationFormSet(request.POST, instance=profile)
            pub_legacy = False
        else:
            publication_formset = PublicationFormSet(instance=profile)
            pub_legacy = True

        if has_teach_formset:
            teaching_formset = TeachingFormSet(request.POST, instance=profile)
            teach_legacy = False
        else:
            teaching_formset = TeachingFormSet(instance=profile)
            teach_legacy = True

        education_formset = EducationFormSet(request.POST, instance=profile)

        # validate everything (legacy pub/teach counted as valid here)
        forms_valid = profile_form.is_valid() and (publication_formset.is_valid() if not pub_legacy else True) and (teaching_formset.is_valid() if not teach_legacy else True) and education_formset.is_valid()
        education_error_message = None

        if forms_valid:
            profile_form.save()

            email_value = profile_form.cleaned_data.get('email', '').strip()
            phone_value = profile_form.cleaned_data.get('phone_number', '').strip()

            def _upsert_contact_link(link_type, label, value):
                existing_link = profile.contact_links.filter(link_type=link_type).first()
                if not value:
                    if existing_link:
                        existing_link.delete()
                    return

                if existing_link:
                    existing_link.value = value
                    existing_link.label = label
                    existing_link.save()
                    return

                max_order = profile.contact_links.aggregate(max_order=Max('order_index'))['max_order']
                order_index = 0 if max_order is None else max_order + 1
                ContactLink.objects.create(
                    profile=profile,
                    link_type=link_type,
                    label=label,
                    value=value,
                    order_index=order_index,
                )

            _upsert_contact_link('email', 'Email', email_value)
            _upsert_contact_link('phone', 'Phone', phone_value)

            # Save inline formsets or fall back to legacy array parsing
            if not pub_legacy:
                publication_formset.save()
            else:
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

            if not teach_legacy:
                teaching_formset.save()
            else:
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

            # Ignore empty education rows so optional blank entries do not break saving.
            valid_education_forms = [
                form for form in education_formset.forms
                if not _is_empty_optional_form(form)
            ]
            if valid_education_forms:
                education_formset.forms = valid_education_forms
                education_formset.save()

            return redirect('portfolios:onboarding_three')
        else:
            education_error_message = None
            if not education_formset.is_valid():
                for form in education_formset.forms:
                    for field, field_errors in form.errors.items():
                        if field == 'start_year' or any('start year' in str(error).lower() for error in field_errors):
                            education_error_message = "Please complete the missing 'Start Year' field for the education entry you started filling in, or delete that row entirely if you do not want to add it."
                            break
                    if education_error_message:
                        break

            if education_error_message:
                messages.error(request, education_error_message)
                focus_education = True
            else:
                messages.error(request, 'There was an error saving your information. Please review the highlighted fields and try again.')
            try:
                logger.error('onboarding_two POST validation failed; profile_form.errors=%s', profile_form.errors.as_json())
            except Exception:
                logger.error('onboarding_two POST: could not serialize profile_form.errors')
            try:
                logger.error('publication_formset.errors=%s', publication_formset.errors)
            except Exception:
                logger.error('onboarding_two POST: could not serialize publication_formset.errors')
            try:
                logger.error('teaching_formset.errors=%s', teaching_formset.errors)
            except Exception:
                logger.error('onboarding_two POST: could not serialize teaching_formset.errors')
            try:
                logger.error('education_formset.errors=%s', json.dumps(education_formset.errors))
                logger.error('education_formset.non_form_errors=%s', education_formset.non_form_errors())
            except Exception:
                logger.error('onboarding_two POST: could not serialize education_formset.errors')
    else:
        profile_form = ProfileForm(instance=profile)
        publication_formset = PublicationFormSet(instance=profile)
        teaching_formset = TeachingFormSet(instance=profile)
        education_formset = EducationFormSet(instance=profile)

    context = {
        'profile_form': profile_form,
        'publication_formset': publication_formset,
        'teaching_formset': teaching_formset,
        'education_formset': education_formset,
        'sections': SECTIONS,
        'education_error_message': education_error_message,
        'focus_education': bool(education_error_message),
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
            profile.onboarding_completed = True
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
    theme = profile.theme
    if not theme:
        raise Http404('No theme assigned to this profile.')
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

    return render(request, theme.template_path, {
        'theme': theme,
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


def download_cv(request, slug):
    profile = get_object_or_404(Profile, slug=slug)
    if not profile.is_published and request.session.get('user_id') != profile.user_id:
        raise Http404('CV not found.')
    if not profile.cv_file:
        raise Http404('CV not found.')
    file_path = profile.cv_file.path
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    filename = os.path.basename(file_path)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
