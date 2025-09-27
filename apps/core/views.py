from django.shortcuts import render

# Create your views here.

def landing(request):
    return render(request, "core/landing.html")

def home(request):
    return render(request, "core/home.html")
