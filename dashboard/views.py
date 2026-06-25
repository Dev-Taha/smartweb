from django.shortcuts import render
from django.views import generic


class Landing(generic.TemplateView):
    template_name = 'dashboard/dashboard.html'
