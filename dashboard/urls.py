from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard pages
    path('home/',       views.dashboard_view,  name='main_dashboard'),
    path('templates/',  views.templates_view,  name='templates_dashboard'),
    path('settings/',   views.settings_view,   name='setting_dashboard'),
    path('profile/edit/', views.edit_profile,  name='edit_profile'), 

    # Publications
    path('publication/add/',                    views.add_publication,    name='add_publication'),
    path('publication/edit/<int:pub_id>/',      views.edit_publication,   name='edit_publication'),
    path('publication/delete/<int:pub_id>/',    views.delete_publication, name='delete_publication'),

    # Teachings
    path('teaching/add/',                       views.add_teaching,       name='add_teaching'),
    path('teaching/edit/<int:teach_id>/',       views.edit_teaching,      name='edit_teaching'),
    path('teaching/delete/<int:teach_id>/',     views.delete_teaching,    name='delete_teaching'),
]