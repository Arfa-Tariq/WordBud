from django.shortcuts import render

# Create your views here.

def list_favorites(request):
    return render(request, "favorites/list.html")
