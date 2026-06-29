from django.urls import path
from . import views

app_name = 'portfolios'

urlpatterns = [
    path('onboarding-one/', views.onboarding_one, name='onboarding_one'),
    path('onboarding-two/', views.onboarding_two, name='onboarding_two'),
    path('onboarding-three/', views.onboarding_three, name='onboarding_three'),
    path('preview/dark-1/', views.dark_template1_preview, name='preview_dark_1'),
    path('preview/dark-2/', views.dark_template2_preview, name='preview_dark_2'),
    path('preview/light-1/', views.light_template1_preview, name='preview_light_1'),
    path('preview/light-2/', views.light_template2_preview, name='preview_light_2'),
    
]
