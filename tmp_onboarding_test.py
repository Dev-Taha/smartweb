from django.test import Client
from accounts.models import User
from portfolios.models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile
import os

user = User.objects.first()
print('user id', user.id)
profile = Profile.objects.filter(user=user).first()
print('profile id', profile.id, 'initial', repr(str(profile.profile_image)))

client = Client()
session = client.session
session['user_id'] = user.id
session.save()

img_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'
img = SimpleUploadedFile('onboarding_test.png', img_data, content_type='image/png')

post_data = {
    'full_name': 'Test User',
    'academic_title': 'Dr.',
    'institution': 'Test University',
    'field_of_study': 'Physics',
    'bio': 'Test bio',
    'google_scholar': '',
    'research_gate': '',
    'research_interests': '',
    'education_set-TOTAL_FORMS': '0',
    'education_set-INITIAL_FORMS': '0',
    'education_set-MIN_NUM_FORMS': '0',
    'education_set-MAX_NUM_FORMS': '1000',
}

response = client.post('/portfolios/onboarding-two/', data={**post_data, 'profile_image': img}, follow=True)
print('status_code', response.status_code)
print('redirect_chain', response.redirect_chain)
print('response_url', response.request.get('PATH_INFO'))

profile.refresh_from_db()
print('after image', repr(str(profile.profile_image)))
print('exists on disk', bool(profile.profile_image) and os.path.exists(profile.profile_image.path))
