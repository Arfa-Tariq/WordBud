import requests
from django.core.cache import cache
from django.conf import settings
from datetime import date
import random

MW_DICTIONARY_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json/"
MW_THESAURUS_URL = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/"
CACHE_TIMEOUT = 6 * 60 * 60  # 6 hours

# ------------------------------
# API fetching with caching
# ------------------------------
def fetch_from_api(api_type, word):
    cache_key = f"{api_type}_{word}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    api_key = settings.MW_DICTIONARY_API_KEY if api_type == "dictionary" else settings.MW_THESAURUS_API_KEY
    url = f"{MW_DICTIONARY_URL if api_type=='dictionary' else MW_THESAURUS_URL}{word}?key={api_key}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            cache.set(cache_key, data, CACHE_TIMEOUT)
            return data
        return {"error": f"API returned {r.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}

def get_dictionary_data(word):
    return fetch_from_api("dictionary", word)

def get_thesaurus_data(word):
    return fetch_from_api("thesaurus", word)

# ------------------------------
# Parsing functions
# ------------------------------
def parse_dictionary_response(data):
    if not data or isinstance(data, dict) and "error" in data:
        return []

    results = []
    for entry in data:
        if isinstance(entry, str):
            continue  # skip suggestions
        word = entry.get("meta", {}).get("id", "")
        part_of_speech = entry.get("fl", "")
        shortdef = entry.get("shortdef", [])
        examples, etymology, pronunciations, audio = [], [], [], []

        for sense_block in entry.get("def", []):
            for sseq in sense_block.get("sseq", []):
                for sense in sseq:
                    sense_data = sense[1] if isinstance(sense[1], dict) else {}
                    for dt in sense_data.get("dt", []):
                        if dt[0] == "vis":
                            examples.extend([v.get("t","") for v in dt[1]])
                        if dt[0] == "sound":
                            aud = dt[1].get("audio")
                            if aud:
                                audio.append(f"https://media.merriam-webster.com/soundc11/{aud[0]}/{aud}.mp3")
        results.append({
            "word": word,
            "part_of_speech": part_of_speech,
            "definitions": shortdef,
            "examples": examples,
            "etymology": entry.get("et", []),
            "pronunciations": pronunciations,
            "audio": audio,
        })
    return results

def parse_thesaurus_response(data):
    if not data or isinstance(data, dict) and "error" in data:
        return {"synonyms": [], "antonyms": [], "usage": []}
    entry = data[0] if isinstance(data[0], dict) else {}
    syns = entry.get("meta", {}).get("syns", [])
    ants = entry.get("meta", {}).get("ants", [])
    synonyms = [w for group in syns for w in group]
    antonyms = [w for group in ants for w in group]
    usage = entry.get("def", [])
    return {"synonyms": synonyms, "antonyms": antonyms, "usage": usage}

# ------------------------------
# Word of the Day
# ------------------------------
def get_word_of_the_day():
    today = date.today().isoformat()
    cache_key = f"word_of_day_{today}"
    word_data = cache.get(cache_key)
    if word_data:
        return word_data

    # pick random word from a small curated list or your database
    words_list = ["serendipity", "ephemeral", "luminescence", "quixotic", "eloquent"]
    word = random.choice(words_list)
    dict_data = parse_dictionary_response(get_dictionary_data(word))
    word_data = {"word": word, "definition": dict_data[0]["definitions"][0] if dict_data else "", "date": today}
    cache.set(cache_key, word_data, 24*60*60)
    return word_data

def random_word():
    # for Random Word search
    words_list = ["serendipity", "ephemeral", "luminescence", "quixotic", "eloquent", "cogent", "benevolent", "audacious"]
    return random.choice(words_list)
