"""
URL configuration for translator app.
"""

from django.urls import path
from . import views

app_name = 'translator'

urlpatterns = [
    path('', views.translate_view, name='translate'),
    path('ajax/', views.translate_ajax, name='translate_ajax'),
    path('detect/', views.detect_language, name='detect_language'),
]