from django import forms
from django.forms import inlineformset_factory
from .models import Profile, Publication, Teaching,ContactLink,Education
from accounts.models import User


# ── 1. Personal Info ─────────────────────────────────────────────────────
class ProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = [
            'full_name', 'academic_title', 'institution',
            'field_of_study', 'bio', 'profile_image',
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
           'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
           
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


# EducationFormSet = inlineformset_factory(
#     Profile, Education, fields=('degree', 'field_of_study', 'institution', 'start_year', 'end_year'),
#     extra=1, can_delete=True
# )

# ContactLinkFormSet = inlineformset_factory(
#     Profile, ContactLink, fields=('label', 'value', 'url', 'link_type'),
#     extra=1, can_delete=True
# )

class AccountSettingsForm(forms.Form):

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    academic_title = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    institution = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    field_of_study = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    profile_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank to keep current password'
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat new password'
        })
    )

    def __init__(self, *args, **kwargs):
        # بناخذ اليوزر الحالي عشان نتحقق من الإيميل
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        qs = User.objects.filter(email=email)
        if self.current_user:
            qs = qs.exclude(id=self.current_user.id)
        if qs.exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean(self):
        cleaned_data    = super().clean()
        new_password    = cleaned_data.get('new_password')
        confirm_password= cleaned_data.get('confirm_password')

        if new_password and new_password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data