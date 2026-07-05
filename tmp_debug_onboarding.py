import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
import django
django.setup()

from django.test import Client
from accounts.models import User
from portfolios.views import get_profile
from portfolios.forms import ProfileForm, PublicationForm, TeachingForm, EducationFormSet

user = User.objects.create(first_name='Test', last_name='User', email='debug4@example.com')
client = Client()
session = client.session
session['user_id'] = user.id
session.save()

payload = {
    'full_name': 'Test User',
    'academic_title': 'Dr.',
    'institution': 'Test University',
    'field_of_study': 'Computer Science',
    'tagline': '',
    'bio': 'A short bio',
    'google_scholar': '',
    'research_gate': '',
    'research_interests': '',
    'title': '',
    'description': '',
    'pdf_link': '',
    'github_link': '',
    'publication_date': '',
    'course_name': '',
    'semester': '',
    'syllabus_link': '',
    'education_entries-TOTAL_FORMS': '1',
    'education_entries-INITIAL_FORMS': '0',
    'education_entries-MAX_NUM_FORMS': '1000',
    'education_entries-0-degree': '',
    'education_entries-0-field_of_study': '',
    'education_entries-0-institution': '',
    'education_entries-0-start_year': '',
    'education_entries-0-end_year': '',
    'education_entries-0-description': '',
    'education_entries-0-honor': '',
    'education_entries-0-DELETE': '',
}

response = client.post('/portfolios/onboarding-two/', payload)
print('status', response.status_code)
print('redirect_chain', response.redirect_chain)

profile = get_profile(user)
profile_form = ProfileForm(data=payload, files={}, instance=profile)
publication_form = PublicationForm(data=payload)
teaching_form = TeachingForm(data=payload)
education_formset = EducationFormSet(data=payload, instance=profile)

print('profile_form.is_valid()', profile_form.is_valid())
print('profile_form.errors', profile_form.errors)
print('publication_form.is_valid()', publication_form.is_valid())
print('publication_form.errors', publication_form.errors)
print('teaching_form.is_valid()', teaching_form.is_valid())
print('teaching_form.errors', teaching_form.errors)
print('education_formset.is_valid()', education_formset.is_valid())
print('education_formset.errors', education_formset.errors)
print('education_formset.non_form_errors()', education_formset.non_form_errors())
