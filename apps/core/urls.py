from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index_redirect, name="index"),
    path("landing/", views.landing, name="landing"),
    path("home/", views.home, name="home"),
]
