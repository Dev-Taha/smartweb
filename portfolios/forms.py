from django import forms
from django.forms import inlineformset_factory
from .models import Profile, Publication, Teaching,ContactLink,Education


# ── 1. Personal Info ─────────────────────────────────────────────────────
class ProfileForm(forms.ModelForm):
    # profile_picture = forms.ImageField(
    #     required=False,
    #     widget=forms.FileInput(attrs={
    #         'class': 'form-control',
    #         'accept': 'image/*',
    #     })
    # )

    class Meta:
        model = Profile
        # added tagline,research_interests
        fields = [
        'full_name', 'academic_title', 'institution',
        'field_of_study', 'tagline', 'bio', 'profile_image',
        'google_scholar', 'research_gate', 'research_interests'
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
            'tagline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Associate Professor of CS',
                'required': False,
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a short academic biography...'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'id': 'profile-image-input',
                'accept': 'image/*'
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
            'research_interests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'e.g. NLP, Computer Vision, Responsible AI',
                'required': False,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['full_name', 'academic_title', 'institution', 'field_of_study', 'bio']:
            if field_name in self.fields:
                self.fields[field_name].required = True

    # def save(self, commit=True):
    #     profile = super().save(commit=False)
    #     picture = self.cleaned_data.get('profile_picture')
    #     if picture:
    #         profile.profile_image = picture
    #     if commit:
    #         profile.save()
    #     return profile


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
                'placeholder': 'Publication title',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make publication title optional so onboarding does not block
        if 'title' in self.fields:
            self.fields['title'].required = False


# ── 3. Teaching ──────────────────────────────────────────────────────────
class TeachingForm(forms.ModelForm):
    class Meta:
        model  = Teaching
        fields = ['course_name', 'description', 'syllabus_link', 'semester']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Machine Learning 101',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make teaching fields optional so onboarding does not block when none provided
        for fname in self.fields:
            self.fields[fname].required = False


# ── 4. Media ─────────────────────────────────────────────────────────────
# class MediaForm(forms.ModelForm):
#     class Meta:
#         model  = Media
#         fields = ['file_path', 'caption']
#         widgets = {
#             'file_path': forms.URLInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'https://...'
#             }),
#             'caption': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Image caption...'
#             }),
#         }


# ── 5. Page ──────────────────────────────────────────────────────────────
# class PageForm(forms.ModelForm):
#     class Meta:
#         model  = Page
#         fields = ['title', 'order_index']
#         widgets = {
#             'title': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'e.g. Publications'
#             }),
#             'order_index': forms.NumberInput(attrs={
#                 'class': 'form-control'
#             }),
#         }


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


    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_year")
        end = cleaned_data.get("end_year")

        has_any_details = any(
            cleaned_data.get(field) not in (None, "", [])
            for field in ["degree", "field_of_study", "institution", "description", "honor", "end_year"]
        )
        if has_any_details and not start:
            self.add_error("start_year", "Please enter a start year if you provide any education details.")

        if end and start and end < start:
            self.add_error("end_year", "End year cannot be before start year.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make education fields optional in the form so users can skip this step in the wizard
        for fname in self.fields:
            self.fields[fname].required = False



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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make contact link fields optional so users can skip adding any
        for fname in self.fields:
            self.fields[fname].required = False
# ── FormSets ──────────────────────────────────────────────────────────────
PublicationFormSet = inlineformset_factory(
    Profile, Publication,
    form=PublicationForm,
    extra=1,
    can_delete=True,
)
TeachingFormSet = inlineformset_factory(
    Profile, Teaching,
    form=TeachingForm,
    extra=1,
    can_delete=True,
)
EducationFormSet = inlineformset_factory(
    Profile, Education,
    form=EducationForm,
    extra=1,
    can_delete=True,
)
ContactLinkFormSet = inlineformset_factory(
    Profile, ContactLink,
    form=ContactLinkForm,
    extra=1,
    can_delete=True,
)