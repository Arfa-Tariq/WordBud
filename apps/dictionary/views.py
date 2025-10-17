from django.shortcuts import render, redirect
from . import services
from django.http import JsonResponse

def word_lookup(request):
    word = request.GET.get("q")
    results, thesaurus, error = [], {}, None

    if word:
        dict_data = services.parse_dictionary_response(services.get_dictionary_data(word))
        results = dict_data if isinstance(dict_data, list) else []
        thesaurus_data = services.parse_thesaurus_response(services.get_thesaurus_data(word))
        thesaurus = thesaurus_data if isinstance(thesaurus_data, dict) else {}
        if not results:
            error = "No results found."

    word_of_day = services.get_word_of_the_day()
    return render(request, "dictionary/searchword.html", {
        "word": word or "",
        "results": results,
        "thesaurus": thesaurus,
        "error": error,
        "word_of_day": word_of_day,
    })

def random_word_view(request):
    word = services.random_word()
    return redirect(f"?q={word}")

def word_of_day_refresh(request):
    from django.core.cache import cache
    today = services.date.today().isoformat()
    cache.delete(f"word_of_day_{today}")
    return redirect("/")
