from django.urls import path
from .views import translate_view

app_name = "translator"

urlpatterns = [
    path("", translate_view, name="translate"),
]
