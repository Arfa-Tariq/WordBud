from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate

# Create your views here.


def signup(request):
    return render(request, "accounts/signup.html")

def login_view(request):
    return render(request, "accounts/login.html")

def profile(request):
    return render(request, "accounts/profile.html")
# def logout_view(request):
#     logout(request)
#     return redirect("accounts:login")  # Redirect to login page after logout