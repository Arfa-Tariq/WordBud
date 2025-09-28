from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "username", "password1", "password2")

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # override "username" field to be email
