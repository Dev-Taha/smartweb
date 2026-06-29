from django.db import models
from accounts.models import User


# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio_profile')
    full_name      = models.CharField(max_length=255, blank=True)
    academic_title = models.CharField(max_length=255, blank=True)
    bio            = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    institution    = models.CharField(max_length=255, blank=True, null=True)
    field_of_study = models.CharField(max_length=255, blank=True, null=True)

    TEMPLATE_CLASSIC   = 'classic-scholar'
    TEMPLATE_MODERN    = 'modern-dark'
    TEMPLATE_MINIMAL   = 'minimalist-lab'
    TEMPLATE_EXECUTIVE = 'executive-academic'

    TEMPLATE_CHOICES = [
        (TEMPLATE_CLASSIC, 'Classic Scholar'),
        (TEMPLATE_MODERN, 'Modern Dark'),
        (TEMPLATE_MINIMAL, 'Minimalist Lab'),
        (TEMPLATE_EXECUTIVE, 'Executive Academic'),
    ]

    selected_template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        blank=True,
        null=True,
        default=TEMPLATE_CLASSIC,
    )

    google_scholar = models.URLField(blank=True, null=True)
    research_gate  = models.URLField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.email


class Page(models.Model):
    profile     = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='pages')
    title       = models.CharField(max_length=255)
    order_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return self.title


class Content(models.Model):
    page        = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='contents')
    block_type  = models.CharField(max_length=50)  # 'text', 'image', 'carousel'
    title       = models.CharField(max_length=255, blank=True)
    order_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.block_type} - {self.page.title}"


class Publication(models.Model):
    profile          = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='publications')
    title            = models.CharField(max_length=255)
    description      = models.TextField(blank=True)
    pdf_link         = models.TextField(blank=True)
    github_link      = models.CharField(max_length=500, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publication_date']

    def __str__(self):
        return self.title


class Teaching(models.Model):
    profile       = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='teachings')
    course_name   = models.CharField(max_length=45)
    description   = models.TextField(blank=True)
    syllabus_link = models.URLField(blank=True, null=True)
    teachingscol  = models.CharField(max_length=45, blank=True)

    def __str__(self):
        return self.course_name


class Media(models.Model):
    profile   = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='medias')
    file_path = models.URLField(blank=True, null=True)
    caption   = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.caption or self.file_path