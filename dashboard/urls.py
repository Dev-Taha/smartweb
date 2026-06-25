from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.Landing.as_view(), name='landing'),
]