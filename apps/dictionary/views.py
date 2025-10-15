import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import UserData
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor

def search_word(request):
    return render(request, "dictionary/search.html")

# ------------------ helper ------------------
def safe_request(url, params=None, timeout=5):
    """Safely makes an API request with timeout and handles errors."""
    headers = {
        "User-Agent": "MyDictionaryApp/1.0 (https://gmail.com; mutahirahmed001@gmail.com)"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
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
    """Fetch word details with parallel fallback and safe defaults for template"""
    cached = cache.get(f"dict_{word}")
    if cached:
        return cached

    data = {
        "word": word,
        "phonetic": "Not available",
        "phonetics": [],
        "meanings": [],
        "origin": "Not available",
        "synonyms": [],
        "antonyms": [],
        "fun_fact": ""
    }

    # --- Functions for parallel API calls ---
    def get_dict_info():
        dict_url = f"https://freedictionaryapi.com/api/v1/entries/en/{word}"
        resp = safe_request(dict_url)
        return resp

    def get_syn_ant():
        return fetch_synonyms_antonyms(word)

    def get_wiki():
        return fetch_wikipedia_fact(word)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        future_dict = executor.submit(get_dict_info)
        future_syn_ant = executor.submit(get_syn_ant)
        future_wiki = executor.submit(get_wiki)

        dict_data = future_dict.result()
        syn_ant_data = future_syn_ant.result()
        wiki_data = future_wiki.result()

    # --- Process dictionary API first ---
    if dict_data:
        try:
            entries = dict_data if isinstance(dict_data, list) else dict_data.get("entries", [])
            if entries:
                first_entry = entries[0]

                # Phonetic
                if first_entry.get("phonetic"):
                    data["phonetic"] = first_entry["phonetic"]
                if first_entry.get("pronunciations"):
                    data["phonetics"] = first_entry["pronunciations"]

                # Origin
                if first_entry.get("origin"):
                    data["origin"] = first_entry["origin"]

                # Meanings
                senses = first_entry.get("meanings") or first_entry.get("senses") or []
                temp_meanings = []
                for s in senses:
                    defs = []

                    if isinstance(s, dict):
                        # Single definition
                        if "definition" in s:
                            defs.append({
                                "definition": s.get("definition", "") or "",
                                "example": s.get("example") or ""
                            })
                        # Multiple definitions
                        elif "definitions" in s and isinstance(s["definitions"], list):
                            for d in s["definitions"]:
                                if isinstance(d, dict):
                                    defs.append({
                                        "definition": d.get("definition", "") or "",
                                        "example": d.get("example") or ""
                                    })
                                else:
                                    defs.append({
                                        "definition": str(d) or "",
                                        "example": ""
                                    })
                    elif isinstance(s, str):
                        defs.append({
                            "definition": s or "",
                            "example": ""
                        })

                    if defs:
                        temp_meanings.append({
                            "partOfSpeech": s.get("partOfSpeech") if isinstance(s, dict) else "N/A",
                            "definitions": defs
                        })

                if temp_meanings:
                    data["meanings"] = temp_meanings

        except Exception:
            pass

    # --- Wikipedia fallback if meanings empty ---
    if not data["meanings"]:
        if wiki_data and wiki_data.get("fun_fact"):
            first_sentence = wiki_data["fun_fact"].split(".")[0].strip()
            if first_sentence:
                data["meanings"] = [{
                    "partOfSpeech": "N/A",
                    "definitions": [{"definition": first_sentence + ".", "example": ""}]
                }]
        if not data["meanings"]:
            data["meanings"] = [{
                "partOfSpeech": "N/A",
                "definitions": [{"definition": "Not available", "example": ""}]
            }]

    # --- Origin fallback ---
    if data["origin"] == "Not available" and wiki_data and wiki_data.get("origin_hint"):
        data["origin"] = wiki_data["origin_hint"]

    # --- Synonyms/Antonyms ---
    if syn_ant_data:
        data["synonyms"] = syn_ant_data.get("synonyms", [])
        data["antonyms"] = syn_ant_data.get("antonyms", [])
    else:
        data["synonyms"] = []
        data["antonyms"] = []

    # --- Fun fact ---
    if wiki_data and wiki_data.get("fun_fact"):
        data["fun_fact"] = wiki_data["fun_fact"]

    # --- Cache for 1 hour ---
    cache.set(f"dict_{word}", data, 3600)
    return data



# ------------------ synonyms & antonyms ------------------
def fetch_synonyms_antonyms(word):
    cached = cache.get(f"syn_ant_{word}")
    if cached:
        return cached

    synonyms, antonyms = set(), set()
    dict_url = f"https://freedictionaryapi.com/api/v1/entries/en/{word}"
    dict_data = safe_request(dict_url)

    if dict_data:
        try:
            entries = dict_data if isinstance(dict_data, list) else dict_data.get("entries", [])
            for entry in entries:
                meanings = entry.get("meanings") or entry.get("senses") or []
                for m in meanings:
                    synonyms.update(m.get("synonyms") or [])
                    antonyms.update(m.get("antonyms") or [])
        except Exception:
            pass

    if not antonyms:
        ant_data = safe_request(f"https://api.datamuse.com/words?rel_ant={word}")
        if ant_data:
            antonyms.update(a["word"] for a in ant_data if "word" in a)
    if not synonyms:
        syn_data = safe_request(f"https://api.datamuse.com/words?rel_syn={word}")
        if syn_data:
            synonyms.update(s["word"] for s in syn_data if "word" in s)

    result = {
        "synonyms": list(synonyms)[:10],
        "antonyms": list(antonyms)[:10]
    }
    cache.set(f"syn_ant_{word}", result, 3600)
    return result

# ------------------ wikipedia fact ------------------
def fetch_wikipedia_fact(word):
    cached = cache.get(f"wiki_{word}")
    if cached:
        return cached

    result = {"fun_fact": None, "origin_hint": None}
    wiki_data = safe_request(f"https://en.wikipedia.org/api/rest_v1/page/summary/{word}")

    if wiki_data:
        extract = wiki_data.get("extract")
        if extract:
            result["fun_fact"] = extract
        for part in (extract or "").split("."):
            if any(k in part.lower() for k in ["latin", "greek", "french", "old english", "derived from"]):
                result["origin_hint"] = part.strip() + "."
                break

    cache.set(f"wiki_{word}", result, 3600)
    return result

# ------------------ word of the day ------------------
def fetch_word_of_day():
    cached = cache.get("word_of_day")
    if cached:
        return cached

    result = {"random_word": None, "random_definition": None}

    try:
        rand_data = safe_request("https://random-word-api.herokuapp.com/word")
        if not rand_data:
            cache.set("word_of_day", result, 3600)
            return result

        random_word = rand_data[0]
        dict_url = f"https://freedictionaryapi.com/api/v1/entries/en/{random_word}"
        dict_data = safe_request(dict_url)

        definition = None
        if dict_data:
            try:
                entries = dict_data if isinstance(dict_data, list) else dict_data.get("entries", [])
                for e in entries:
                    senses = e.get("senses") or e.get("meanings") or []
                    for s in senses:
                        if isinstance(s, dict):
                            defs = s.get("definition") or (s.get("definitions") and s.get("definitions")[0])
                            if defs:
                                definition = defs
                                break
                        elif isinstance(s, str):
                            definition = s
                            break
                    if definition:
                        break
            except Exception:
                definition = None

        if not definition:
            wiki = safe_request(f"https://en.wikipedia.org/api/rest_v1/page/summary/{random_word.title()}")
            if wiki:
                definition = wiki.get("extract")

        if definition:
            result["random_word"] = random_word
            result["random_definition"] = definition

    except Exception:
        pass

    cache.set("word_of_day", result, 3600)
    return result

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
