#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.test import Client
from accounts.models import User
from portfolios.models import Profile

# Clean up if exists
User.objects.filter(email='testuser_preview@test.com').delete()

# Create a test user with incomplete onboarding
user = User.objects.create(
    email='testuser_preview@test.com',
    first_name='Test',
    last_name='User',
    password='testpass123'
)

# Create profile with incomplete onboarding
import uuid
profile = Profile.objects.create(
    user=user,
    full_name='Test User',
    slug=f'test-user-{uuid.uuid4().hex[:8]}',
    onboarding_completed=False
)

client = Client()

# Simulate an authenticated session by setting the user_id in session
# (since this custom User model doesn't use Django's auth system)
session = client.session
session['user_id'] = user.id
session.save()

# Make the request to preview endpoint
response = client.get('/portfolios/preview/academic-dark/')
print(f"Status Code: {response.status_code}")
print(f"\nResponse Body (first 500 chars):\n{response.content.decode('utf-8', errors='ignore')[:500]}")
print(f"\nHeaders:\n")
for header, value in response.items():
    if header not in ['Content-Type']:  # Skip lengthy headers
        print(f"  {header}: {value}")

# Clean up
User.objects.filter(email='testuser_preview@test.com').delete()
