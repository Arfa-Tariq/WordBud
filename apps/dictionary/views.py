from django.shortcuts import render

# Create your views here.

def search_word(request):
    return render(request, "dictionary/search.html")
