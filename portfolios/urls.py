"""
portfolios/urls.py
"""
from django.urls import path

from . import views

app_name = "portfolios"

urlpatterns = [
    # Public portfolio at /u/<slug>/
    path("u/<slug:slug>/", views.portfolio_detail, name="detail"),
    path("preview/<slug:theme_slug>/", views.portfolio_preview, name="preview"),
    path("u/<slug:slug>/cv/download/", views.download_cv, name="download_cv"),
    path('onboarding-one/', views.onboarding_one, name='onboarding_one'),
    path('onboarding-two/', views.onboarding_two, name='onboarding_two'),
    path('onboarding-three/', views.onboarding_three, name='onboarding_three'),
    # Theme-based preview route uses templates/themes/<slug>/index.html
]

