from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index_redirect(request):
    """
    Redirect root URL ('/') depending on authentication state.
    - If logged in → send to home
    - If guest → send to landing page
    """
    if request.user.is_authenticated:
        return redirect("core:home")
    return redirect("core:landing")


def landing(request):
    """
    Public landing page.
    Homepage for guests where they can explore and search.
    """
    return render(request, "core/landing.html")


@login_required
def home(request):
    """
    User dashboard/homepage — requires login.
    Shows personalized features and tools.
    """
    return render(request, "core/home.html")
