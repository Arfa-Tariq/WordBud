from django.shortcuts import render
import requests
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import UserData
# Create your views here.

def search_word(request):
    return render(request, "dictionary/search.html")

def safe_request(url, params=None):
    """Safely makes an API request with timeout and handles errors."""
    try:
        resp = requests.get(url, params=params, timeout=6)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_dictionary_data(word):
    """Main dictionary info: meanings, phonetics, origin"""
    data = {}
    response = safe_request(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if not response:
        return None

    try:
        entry = response[0]
        data["word"] = entry.get("word")
        data["phonetic"] = entry.get("phonetic")
        data["phonetics"] = entry.get("phonetics", [])
        data["meanings"] = entry.get("meanings", [])
        data["origin"] = entry.get("origin")
        return data
    except Exception:
        return None


def fetch_synonyms_antonyms(word):
    """Fetch synonyms and antonyms from Datamuse API"""
    synonyms = []
    antonyms = []

    syn_data = safe_request(f"https://api.datamuse.com/words?rel_syn={word}")
    ant_data = safe_request(f"https://api.datamuse.com/words?rel_ant={word}")

    if syn_data:
        synonyms = [s["word"] for s in syn_data]
    if ant_data:
        antonyms = [a["word"] for a in ant_data]

    return {"synonyms": synonyms, "antonyms": antonyms}


def fetch_wikipedia_fact(word):
    """Fetch 'Did you know' fact or etymology hint from Wikipedia"""
    result = {"fun_fact": None, "origin_hint": None}
    wiki_data = safe_request(f"https://en.wikipedia.org/api/rest_v1/page/summary/{word.capitalize()}")

    if wiki_data:
        extract = wiki_data.get("extract")
        if extract:
            result["fun_fact"] = extract
        text = extract or ""
        for part in text.split("."):
            if any(k in part.lower() for k in ["latin", "greek", "french", "old english", "derived from"]):
                result["origin_hint"] = part.strip() + "."
                break

    return result


def fetch_word_of_day():
    """Fetch random word and meaning"""
    result = {"random_word": None, "random_definition": None}
    rand_data = safe_request("https://random-word-api.herokuapp.com/word")

    if rand_data:
        random_word = rand_data[0]
        dict_data = safe_request(f"https://api.dictionaryapi.dev/api/v2/entries/en/{random_word}")
        if dict_data:
            try:
                defs = dict_data[0].get("meanings", [])
                if defs and defs[0]["definitions"]:
                    result["random_word"] = random_word
                    result["random_definition"] = defs[0]["definitions"][0]["definition"]
            except Exception:
                pass
    return result


def dictionary_view(request):
    """Main view combining all fetchers"""
    word = request.GET.get("word")
    data = {}
    error = None

    if word:
        dict_data = fetch_dictionary_data(word)
        syn_ant_data = fetch_synonyms_antonyms(word)
        wiki_data = fetch_wikipedia_fact(word)

        if not dict_data:
            error = "Could not fetch word details."
        else:
            data.update(dict_data)
            data.update(syn_ant_data)
            data.update(wiki_data)

            if not data.get("origin") and data.get("origin_hint"):
                data["origin"] = data["origin_hint"]

    # Word of the day
    data.update(fetch_word_of_day())

    return render(request, "searchword.html", {"data": data, "word": word, "error": error})


# ---------- add favorite (POST) ----------
@login_required
def add_favorite(request, word):
    user = request.user

    # Add the word if it doesn't exist
    if not UserData.objects.filter(user=user, favorite_word=word).exists():
        UserData.objects.create(user=user, favorite_word=word)
        messages.success(request, f'"{word}" added to your favorites!')
    else:
        messages.info(request, f'"{word}" is already in your favorites.')

    # Stay on the same page with query parameters
    referer = request.META.get('HTTP_REFERER')  # URL of the previous page
    if referer:
        return redirect(referer)
    else:
        return redirect('dictionary:dictionary')  # fallback

@login_required
def favorites_list(request):
    favorites = UserData.objects.filter(user=request.user)
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required
def remove_favorite(request, word):
    user = request.user
    # Delete the favorite if it exists
    favorite = UserData.objects.filter(user=user, favorite_word=word)
    if favorite.exists():
        favorite.delete()
        messages.success(request, f'"{word}" has been removed from your favorites.')
    else:
        messages.info(request, f'"{word}" was not found in your favorites.')

    # Redirect back to the favorites page
    return redirect('dictionary:favorites_list')