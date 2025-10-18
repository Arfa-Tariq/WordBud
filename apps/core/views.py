from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def landing(request):
    """
    Landing page - accessible to everyone.
    This is the main homepage where users can search words without logging in.
    """
    return render(request, "core/landing.html")

@login_required
def home(request):
    """
    User dashboard - requires authentication.
    Shows personalized content for logged-in users.
    """
    return render(request, "core/home.html")