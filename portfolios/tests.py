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

    def test_partial_education_entry_shows_user_facing_error(self):
        user = User.objects.create(first_name="Test", last_name="User", email="test3@example.com")
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
                "education_entries-0-degree": "PhD",
                "education_entries-0-field_of_study": "",
                "education_entries-0-institution": "MIT",
                "education_entries-0-start_year": "",
                "education_entries-0-end_year": "",
                "education_entries-0-description": "",
                "education_entries-0-honor": "",
                "education_entries-0-DELETE": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please complete the missing")

    def test_invalid_education_post_preserves_formset_data(self):
        user = User.objects.create(first_name="Test", last_name="User", email="test4@example.com")
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
                "education_entries-TOTAL_FORMS": "2",
                "education_entries-INITIAL_FORMS": "0",
                "education_entries-MAX_NUM_FORMS": "1000",
                "education_entries-0-degree": "PhD",
                "education_entries-0-field_of_study": "Computer Science",
                "education_entries-0-institution": "MIT",
                "education_entries-0-start_year": "2020",
                "education_entries-0-end_year": "2024",
                "education_entries-0-description": "Dissertation",
                "education_entries-0-honor": "Summa Cum Laude",
                "education_entries-0-DELETE": "",
                "education_entries-1-degree": "MSc",
                "education_entries-1-field_of_study": "AI",
                "education_entries-1-institution": "Stanford",
                "education_entries-1-start_year": "",
                "education_entries-1-end_year": "2021",
                "education_entries-1-description": "Research assistant",
                "education_entries-1-honor": "",
                "education_entries-1-DELETE": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "education_entries-1-degree")
        self.assertContains(response, "value=\"MSc\"")
        self.assertContains(response, "Please complete the missing")

    def test_single_year_education_autofill_saves(self):
        user = User.objects.create(first_name="Test", last_name="User", email="test5@example.com")
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
                "education_entries-0-degree": "Certificate",
                "education_entries-0-field_of_study": "",
                "education_entries-0-institution": "Axsos Academy",
                "education_entries-0-start_year": "",
                "education_entries-0-end_year": "2026",
                "education_entries-0-description": "",
                "education_entries-0-honor": "",
                "education_entries-0-DELETE": "",
            },
        )

        # Should redirect to step 3 on successful save
        self.assertRedirects(response, reverse("portfolios:onboarding_three"))

        # Created education should have start_year == end_year
        educ = Education.objects.first()
        self.assertIsNotNone(educ)
        self.assertEqual(educ.start_year, educ.end_year)
