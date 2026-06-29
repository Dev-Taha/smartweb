from django import forms
from .models import Profile, Publication, Teaching, Media, Content, Page


# ── 1. Personal Info ─────────────────────────────────────────────────────
class ProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = [
            'full_name', 'academic_title', 'institution',
            'field_of_study', 'bio', 'profile_picture',
            'google_scholar', 'research_gate'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Dr. Sarah Johnson',
                'required': True,
            }),
            'academic_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Associate Professor',
                'required': True,
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. MIT',
                'required': True,
            }),
            'field_of_study': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Machine Learning, NLP',
                'required': True,
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a short academic biography...',
                'required': True,
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'd-none',
                'required': False,
            }),
            'google_scholar': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://scholar.google.com/...',
                'required': False,
            }),
            'research_gate': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.researchgate.net/...',
                'required': False,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['full_name', 'academic_title', 'institution', 'field_of_study', 'bio']:
            if field_name in self.fields:
                self.fields[field_name].required = True


# ── 2. Publication ───────────────────────────────────────────────────────
class PublicationForm(forms.ModelForm):
    class Meta:
        model  = Publication
        fields = [
            'title', 'description',
            'pdf_link', 'github_link', 'publication_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control pub-required',
                'placeholder': 'Publication title',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Abstract or short description...'
            }),
            'pdf_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'github_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/...'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type' : 'date'
            }),
        }


# ── 3. Teaching ──────────────────────────────────────────────────────────
class TeachingForm(forms.ModelForm):
    class Meta:
        model  = Teaching
        fields = ['course_name', 'description', 'syllabus_link', 'teachingscol']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control teach-required',
                'placeholder': 'e.g. Machine Learning 101',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Course description...'
            }),
            'syllabus_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'teachingscol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Fall 2024'
            }),
        }


# ── 4. Media ─────────────────────────────────────────────────────────────
class MediaForm(forms.ModelForm):
    class Meta:
        model  = Media
        fields = ['file_path', 'caption']
        widgets = {
            'file_path': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image caption...'
            }),
        }


# ── 5. Page ──────────────────────────────────────────────────────────────
class PageForm(forms.ModelForm):
    class Meta:
        model  = Page
        fields = ['title', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Publications'
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }