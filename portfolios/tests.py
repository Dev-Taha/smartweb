from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Education
from .views import resolve_preview_theme


class PortfolioPreviewTests(TestCase):
    def test_legacy_preview_alias_maps_to_existing_theme(self):
        theme = resolve_preview_theme("light-1")

        self.assertEqual(theme.slug, "academic-light")
        self.assertEqual(theme.template_path, "themes/academic-light/index.html")


class OnboardingTwoTemplateTests(TestCase):
    def test_onboarding_two_uses_a_real_submit_button(self):
        user = User.objects.create(first_name="Test", last_name="User", email="test@example.com")
        session = self.client.session
        session["user_id"] = user.id
        session.save()

        response = self.client.get(reverse("portfolios:onboarding_two"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="go-step3-btn"')
        self.assertContains(response, '<button type="submit"')

    def test_blank_education_rows_are_ignored_on_submit(self):
        user = User.objects.create(first_name="Test", last_name="User", email="test2@example.com")
        session = self.client.session
        session["user_id"] = user.id
        session.save()

        response = self.client.post(
            reverse("portfolios:onboarding_two"),
            {
                "full_name": "Test User",
                "academic_title": "Dr.",
                "institution": "Test University",
                "field_of_study": "Computer Science",
                "bio": "A short bio",
                "tagline": "",
                "google_scholar": "",
                "research_gate": "",
                "research_interests": "",
                "title": "",
                "description": "",
                "pdf_link": "",
                "github_link": "",
                "publication_date": "",
                "course_name": "",
                "semester": "",
                "syllabus_link": "",
                "education_entries-TOTAL_FORMS": "1",
                "education_entries-INITIAL_FORMS": "0",
                "education_entries-MAX_NUM_FORMS": "1000",
                "education_entries-0-degree": "",
                "education_entries-0-field_of_study": "",
                "education_entries-0-institution": "",
                "education_entries-0-start_year": "",
                "education_entries-0-end_year": "",
                "education_entries-0-description": "",
                "education_entries-0-honor": "",
                "education_entries-0-DELETE": "",
            },
        )

        self.assertRedirects(response, reverse("portfolios:onboarding_three"))
        self.assertFalse(Education.objects.exists())
