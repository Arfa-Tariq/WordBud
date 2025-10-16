from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor

from .models import UserData
from .services import (
    fetch_dictionary_data,
    fetch_synonyms_antonyms,
    fetch_wikipedia_fact,
    fetch_word_of_day,
    get_random_word,
)


def search_word(request):
    # Provide WOTD on the landing search page for engagement
    wotd = fetch_word_of_day()
    return render(request, "dictionary/search.html", {"wotd": wotd})


def dictionary_view(request):
    word = request.GET.get("word")
    data = {}
    error = None

    if word:
        # Run dictionary, synonyms, and Wikipedia fetches in parallel
        with ThreadPoolExecutor() as executor:
            future_dict = executor.submit(fetch_dictionary_data, word)
            future_syn_ant = executor.submit(fetch_synonyms_antonyms, word)
            future_wiki = executor.submit(fetch_wikipedia_fact, word)

            # Use try/except for each future to prevent a single failure from blocking others
            try:
                dict_data = future_dict.result(timeout=6)
            except Exception:
                dict_data = {
                    "word": word,
                    "phonetic": "Not available",
                    "phonetics": [],
                    "meanings": [{"partOfSpeech": "N/A", "definitions": ["Not available"]}],
                    "origin": "Not available",
                }

            try:
                syn_ant_data = future_syn_ant.result(timeout=6)
            except Exception:
                syn_ant_data = {"synonyms": [], "antonyms": []}

            try:
                wiki_data = future_wiki.result(timeout=6)
            except Exception:
                wiki_data = {"fun_fact": None, "origin_hint": None}

        # Merge results
        data.update(dict_data)
        data.update(syn_ant_data)
        data.update(wiki_data)

        # Fill origin if missing
        if not data.get("origin") or data.get("origin") == "Not available":
            if data.get("origin_hint"):
                data["origin"] = data["origin_hint"]
            else:
                data["origin"] = "Not available"

    # Word of the day
    data.update(fetch_word_of_day())

    return render(request, "dictionary/searchword.html", {"data": data, "word": word, "error": error})


# ------------------ favorites ------------------
@login_required
def add_favorite(request, word):
    user = request.user
    if not UserData.objects.filter(user=user, favorite_word=word).exists():
        UserData.objects.create(user=user, favorite_word=word)
        messages.success(request, f'"{word}" added to your favorites!')
    else:
        messages.info(request, f'"{word}" is already in your favorites.')
    return redirect(request.META.get('HTTP_REFERER', reverse('dictionary:dictionary')))

@login_required
def favorites_list(request):
    favorites = UserData.objects.filter(user=request.user)
    return render(request, 'dictionary/favorites.html', {'favorites': favorites})

@login_required
def remove_favorite(request, word):
    favorite = UserData.objects.filter(user=request.user, favorite_word=word)
    if favorite.exists():
        favorite.delete()
        messages.success(request, f'"{word}" has been removed from your favorites.')
    else:
        messages.info(request, f'"{word}" was not found in your favorites.')
    return redirect('dictionary:favorites_list')


# ------------------ random & WOTD refresh ------------------
def random_word_view(request):
    word = get_random_word()
    return redirect(f"{reverse('dictionary:dictionary')}?word={word}")


@login_required
def refresh_wotd(request):
    if not request.user.is_staff:
        messages.info(request, "Only staff can refresh Word of the Day.")
        return redirect('dictionary:dictionary')
    cache.delete("word_of_day")
    fetch_word_of_day()
    messages.success(request, "Word of the Day refreshed.")
    return redirect('dictionary:dictionary')
