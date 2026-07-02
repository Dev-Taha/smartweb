from django import forms
from .models import Profile, Publication, Teaching, Media, Page,ContactLink,Education


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
                'placeholder': 'e.g. Dr. Sarah Johnson'
            }),
            'academic_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Associate Professor'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. MIT'
            }),
            'field_of_study': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Machine Learning, NLP'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a short academic biography...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'google_scholar': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://scholar.google.com/...'
            }),
            'research_gate': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.researchgate.net/...'
            }),
        }


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
                'class': 'form-control',
                'placeholder': 'Publication title'
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
        fields = ['course_name', 'description', 'syllabus_link', 'semester']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Machine Learning 101'
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
            'semester': forms.TextInput(attrs={
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


# ── 4. Education ─────────────────────────────────────────────────────────
class EducationForm(forms.ModelForm):
    class Meta:
        model  = Education
        fields = ['degree', 'field_of_study', 'institution', 'start_year', 'end_year', 'description', 'honor']
        widgets = {
            'degree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Ph.D."}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Computer Science"}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. MIT"}),
            'start_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "e.g. 2018"}),
            'end_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "e.g. 2022 (leave blank if ongoing)"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': "Dissertation title, advisor..."}),
            'honor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Summa Cum Laude (optional)"}),
        }


# ── 5. ContactLink ────────────────────────────────────────────────────────
class ContactLinkForm(forms.ModelForm):
    class Meta:
        model  = ContactLink
        fields = ['label', 'value', 'url', 'link_type']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Office Email"}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. sarah@mit.edu"}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': "https://... (optional)"}),
            'link_type': forms.Select(attrs={'class': 'form-select'}),
        }