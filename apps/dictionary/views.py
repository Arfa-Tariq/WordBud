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
    headers = {
        "User-Agent": "MyDictionaryApp/1.0 (https://gmail.com; mutahirahmed001@gmail.com)"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            try:
                return resp.json()
            except ValueError:
                print("⚠️ Response not JSON from:", url)
                return None
        else:
            print(f"⚠️ API returned {resp.status_code} for {url}")
            return None
    except Exception as e:
        print(f"⚠️ Request failed for {url}: {e}")
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
    """Fetch synonyms and antonyms using FreeDictionaryAPI (primary) and Datamuse (fallback)."""
    synonyms, antonyms = set(), set()

    # 1️⃣ Try FreeDictionaryAPI first
    dict_url = f"https://freedictionaryapi.com/api/v1/entries/en/{word}"
    dict_data = safe_request(dict_url)

    if dict_data:
        try:
            if isinstance(dict_data, list):
                entries = dict_data
            elif isinstance(dict_data, dict):
                entries = dict_data.get("entries", [])
            else:
                entries = []

            for entry in entries:
                meanings = entry.get("meanings") or entry.get("senses") or []
                for m in meanings:
                    # some APIs call them "synonyms"/"antonyms" lists
                    syns = m.get("synonyms") or []
                    ants = m.get("antonyms") or []
                    synonyms.update(syns)
                    antonyms.update(ants)
        except Exception:
            pass

    # 2️⃣ Fallback to Datamuse if needed
    if not antonyms:
        ant_data = safe_request(f"https://api.datamuse.com/words?rel_ant={word}")
        if ant_data and isinstance(ant_data, list):
            antonyms.update(a["word"] for a in ant_data if "word" in a)

    if not synonyms:
        syn_data = safe_request(f"https://api.datamuse.com/words?rel_syn={word}")
        if syn_data and isinstance(syn_data, list):
            synonyms.update(s["word"] for s in syn_data if "word" in s)

    # 3️⃣ Limit long lists (for display)
    synonyms = list(synonyms)[:10]
    antonyms = list(antonyms)[:10]

    return {
        "synonyms": synonyms,
        "antonyms": antonyms
    }



def fetch_wikipedia_fact(word):
    """Fetch 'Did you know' fact or etymology hint from Wikipedia"""
    result = {"fun_fact": None, "origin_hint": None}
    wiki_data = safe_request(f"https://en.wikipedia.org/api/rest_v1/page/summary/{word}")

    if wiki_data:
        extract = wiki_data.get("extract")
        if extract:
            result["fun_fact"] = extract
        text = extract or ""
        for part in text.split("."):
            if any(k in part.lower() for k in ["latin", "greek", "french", "old english", "derived from"]):
                result["origin_hint"] = part.strip() + "."
                break
    print(result)
    return result


def fetch_word_of_day():
    """Fetch random word and meaning using a more reliable free dictionary (FreeDictionaryAPI).
    Falls back to Datamuse/Wikipedia behaviour if needed and is tolerant of different response shapes.
    """
    result = {"random_word": None, "random_definition": None}

    # 1) get a random word
    rand_data = safe_request("https://random-word-api.herokuapp.com/word")
    if not rand_data:
        return result

    random_word = rand_data[0]

    # 2) try Free Dictionary API (Wiktionary-backed)
    # endpoint pattern: https://freedictionaryapi.com/api/v1/entries/{lang}/{word}
    dict_url = f"https://freedictionaryapi.com/api/v1/entries/en/{random_word}"
    dict_data = safe_request(dict_url)

    # 3) Try to extract a definition from possible response shapes:
    definition = None
    try:
        if dict_data:
            # FreeDictionaryAPI typically returns a dict with keys like "word" and "entries"
            if isinstance(dict_data, dict):
                # entries -> list -> senses -> list -> definition
                entries = dict_data.get("entries") or dict_data.get("results") or []
                if entries and isinstance(entries, list):
                    # prefer first sensible definition
                    for e in entries:
                        # e may have "senses" (list) or "senses" nested
                        senses = e.get("senses") or e.get("meanings") or []
                        if senses and isinstance(senses, list):
                            for s in senses:
                                # senses may have "definition" or "definitions" or "definition" inside subsense
                                if isinstance(s, dict):
                                    defs = s.get("definition") or (s.get("definitions") and s.get("definitions")[0])
                                    if defs:
                                        definition = defs
                                        break
                                elif isinstance(s, str):
                                    definition = s
                                    break
                        # fallback to entry-level synonyms/definitions
                        if not definition:
                            entry_defs = e.get("definition") or e.get("definitions")
                            if entry_defs:
                                if isinstance(entry_defs, list):
                                    definition = entry_defs[0]
                                else:
                                    definition = entry_defs
                        if definition:
                            break
            # Some dictionary endpoints return a list similar to dictionaryapi.dev:
            elif isinstance(dict_data, list):
                first = dict_data[0]
                defs = first.get("meanings", []) if isinstance(first, dict) else []
                if defs and defs[0].get("definitions"):
                    definition = defs[0]["definitions"][0].get("definition")
    except Exception:
        definition = None

    # 4) If we didn't get a definition, as a fallback attempt to use Wikipedia extract
    if not definition:
        wiki = safe_request(f"https://en.wikipedia.org/api/rest_v1/page/summary/{random_word.title()}")
        if wiki and isinstance(wiki, dict):
            definition = wiki.get("extract")

    # 5) Fill result
    if definition:
        result["random_word"] = random_word
        result["random_definition"] = definition

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

    return render(request, "dictionary/searchword.html", {"data": data, "word": word, "error": error})


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
    return render(request, 'dictionary/favorites.html', {'favorites': favorites})

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