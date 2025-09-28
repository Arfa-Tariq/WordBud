from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def landing(request):
    if request.user.is_authenticated:
        return redirect("core:home") # Redirect authenticated users to home
    return render(request, "core/landing.html")

@login_required
def home(request):
    return render(request, "core/home.html")
