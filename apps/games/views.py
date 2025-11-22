from django.shortcuts import render
import random
import requests
from django.conf import settings
import os
from dotenv import load_dotenv
# Merriam-Webster API details
load_dotenv()
API_KEY = (
    os.getenv("MW_DICTIONARY_API_KEY")
    or os.getenv("MW_THESAURUS_API_KEY")   
    or os.getenv("MERRIAM_WEBSTER_API_KEY")
    or getattr(settings, "MW_DICTIONARY_API_KEY", None)
    or getattr(settings, "MERRIAM_WEBSTER_API_KEY", None)
)
BASE_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json"

def get_valid_word():
    """
    Fetch a random valid English word verified from Merriam-Webster API.
    Retries multiple times until a valid word is found.
    """
    attempts = 0
    while attempts < 5:
        attempts += 1
        # Fetch a random word from API
        try:
            r = requests.get(RANDOM_WORD_API, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    word = data[0].lower()
                else:
                    continue
            else:
                continue
        except Exception as e:
            print("Random word API error:", e)
            continue

        # Verify the word with Merriam-Webster
        try:
            url = f"{BASE_URL}/{word}?key={API_KEY}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                mw_data = res.json()
                if isinstance(mw_data, list) and len(mw_data) > 0 and "meta" in mw_data[0]:
                    return word
        except Exception as e:
            print("Merriam-Webster API error:", e)
            continue

    # fallback if API fails repeatedly
    print("Falling back to a local word")
    return random.choice(["python", "django", "variable", "function", "computer"])


def word_guess(request):
    """
    Word Guess Game (like Hangman) — uses Merriam-Webster API validated words.
    """
    if 'game' not in request.session:
        word = get_valid_word()
        request.session['game'] = {
            'word': word,
            'guessed': [],
            'attempts': 6
        }

    game = request.session['game']
    word = game['word']
    guessed = game['guessed']
    attempts = game['attempts']
    message = ""

    if request.method == "POST":
        guess = request.POST.get('guess', '').lower()

        if guess and guess not in guessed:
            guessed.append(guess)
            if guess not in word:
                attempts -= 1
                message = f"'{guess}' is not in the word."
            else:
                message = f"✅ Good job! '{guess}' is in the word."

            # update session
            request.session['game'] = {
                'word': word,
                'guessed': guessed,
                'attempts': attempts
            }

    display_word = " ".join([c if c in guessed else "_" for c in word])

    won = "_" not in display_word
    lost = attempts <= 0

    if won or lost:
        final_message = "🎉 You won!" if won else f"❌ You lost! The word was '{word}'."
        request.session.pop('game', None)
        return render(request, "games/word_guess.html", {
            'display_word': display_word,
            'attempts': attempts,
            'message': final_message,
            'game_over': True
        })

    return render(request, "games/word_guess.html", {
        'display_word': display_word,
        'attempts': attempts,
        'message': message,
        'game_over': False
    })
# -----------------------------
# GAME 2: WORD SCRAMBLE
# -----------------------------
def word_scramble(request):
    """Unscramble the given scrambled word (uses Merriam-Webster API words)."""
    if 'scramble' not in request.session:
        word = get_valid_word()
        scrambled = ''.join(random.sample(word, len(word)))
        request.session['scramble'] = {'word': word, 'scrambled': scrambled, 'attempts': 3}

    game = request.session['scramble']
    word = game['word']
    scrambled = game['scrambled']
    attempts = game['attempts']
    message = ""

    if request.method == "POST":
        guess = request.POST.get("guess", "").lower()
        if guess == word:
            message = f"🎉 Correct! The word was '{word}'."
            request.session.pop('scramble', None)
            return render(request, "games/word_scramble.html", {"scrambled": scrambled, "message": message, "game_over": True})
        else:
            attempts -= 1
            if attempts <= 0:
                message = f"❌ Game over! The correct word was '{word}'."
                request.session.pop('scramble', None)
                return render(request, "games/word_scramble.html", {"scrambled": scrambled, "message": message, "game_over": True})
            else:
                message = f"'{guess}' is not correct. Attempts left: {attempts}"
                request.session['scramble'] = {'word': word, 'scrambled': scrambled, 'attempts': attempts}

    return render(request, "games/word_scramble.html", {"scrambled": scrambled, "message": message, "game_over": False})


# -----------------------------
# GAME 3: SYNONYM MATCH (API-only version)
# -----------------------------
THESAURUS_API_KEY = os.getenv("MW_THESAURUS_API_KEY")
THESAURUS_URL = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json"
RANDOM_WORD_API = "https://random-word-api.herokuapp.com/word?lang=en"

def get_random_word():
    """Get a random English word."""
    try:
        r = requests.get(RANDOM_WORD_API, timeout=2)
        if r.status_code == 200:
            j = r.json()
            if isinstance(j, list) and j:
                return j[0].lower()
    except:
        pass
    return random.choice(["happy", "bright", "strong", "clear", "fast"])

def get_synonyms(word):
    """Fetch synonyms for a given word from Merriam-Webster API."""
    try:
        res = requests.get(f"{THESAURUS_URL}/{word}", params={"key": THESAURUS_API_KEY}, timeout=2)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and data and isinstance(data[0], dict):
                syn_groups = data[0].get("meta", {}).get("syns", [])
                synonyms = [s for g in syn_groups for s in g if " " not in s]
                return list(set(synonyms))
    except Exception as e:
        print("API error:", e)
    return []
def synonym_match(request):
    """
    Synonym Match Game — API-only version using session-stored round like meaning_quiz.
    """
    def fetch_random_word():
        try:
            r = requests.get(RANDOM_WORD_API, timeout=2)
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, list) and j:
                    return j[0].lower()
        except:
            pass
        return random.choice(["happy", "bright", "strong", "clear", "fast"])

    def fetch_synonyms(word):
        try:
            res = requests.get(f"{THESAURUS_URL}/{word}", params={"key": THESAURUS_API_KEY}, timeout=2)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    syn_groups = data[0].get("meta", {}).get("syns", [])
                    synonyms = [s for g in syn_groups for s in g if " " not in s]
                    return list(set(synonyms))
        except Exception as e:
            print("API error:", e)
        return []

    # --- Create a new round if session empty ---
    if "synonym_match" not in request.session:
        attempts = 0
        while attempts < 5:
            attempts += 1
            word = fetch_random_word()
            synonyms = fetch_synonyms(word)
            if len(synonyms) >= 2:
                correct = random.choice(synonyms)
                break
        else:
            return render(request, "games/synonym_match.html", {
                "word": None,
                "options": [],
                "message": "❌ Could not fetch synonyms. Try again later.",
                "game_over": True
            })

        # Generate distractors (words that are not synonyms)
        distractors = []
        while len(distractors) < 3:
            w = fetch_random_word()
            if w not in synonyms and w != word and w != correct and w not in distractors:
                distractors.append(w)

        options = [correct] + distractors
        random.shuffle(options)

        # Store round in session
        request.session["synonym_match"] = {
            "word": word,
            "correct": correct,
            "options": options
        }

    # --- Evaluate POST or render question ---
    state = request.session["synonym_match"]
    word, correct, options = state["word"], state["correct"], state["options"]
    message = ""
    game_over = False

    if request.method == "POST":
        choice = (request.POST.get("choice") or "").strip()
        if choice.lower() == correct.lower():
            message = f"✅ Correct! '{choice.title()}' is a synonym of '{word.title()}'."
        else:
            message = f"❌ Wrong! The correct synonym was '{correct.title()}'."
        game_over = True
        request.session.pop("synonym_match", None)

    return render(request, "games/synonym_match.html", {
        "word": word.title(),
        "options": [o.title() for o in options],
        "message": message,
        "game_over": game_over
    })


def meaning_quiz(request):
    """
    API-only Word Meaning Quiz with session-persisted round.
    - On GET: build a round (4 API-fetched words + definitions), store in session.
    - On POST: evaluate user's choice against the stored round, show feedback.
    """

    # helper: fetch a random word (external Random Word API)
    def fetch_random_word():
        try:
            r = requests.get("https://random-word-api.herokuapp.com/word?lang=en", timeout=2)
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, list) and j:
                    return j[0]
        except Exception:
            pass
        # last-resort fallback (rare, only if random API fails); still short list to recover
        return random.choice(["language", "computer", "network", "education", "function"])

    # helper: get a short clean definition from Merriam-Webster
    def fetch_definition(word):
        try:
            r = requests.get(f"{BASE_URL}/{word}?key={API_KEY}", timeout=2)
            if r.status_code == 200:
                data = r.json()
                # If API returns suggestion list (strings) skip
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    # find first entry with a shortdef
                    for entry in data:
                        if isinstance(entry, dict):
                            defs = entry.get("shortdef", [])
                            if defs:
                                # prefer short, readable first def
                                d = defs[0].strip()
                                if len(d) > 180:
                                    # shorten long defs a bit (split on semicolon)
                                    d = d.split(";")[0].strip()
                                return d
        except Exception as e:
            print("meaning_quiz: definition fetch error for", word, ":", e)
        return None

    # --- If no round in session, create and store one ---
    if "meaning_quiz" not in request.session:
        word_defs = {}  # word -> definition
        attempts = 0
        # collect 4 distinct words that have definitions from the MW API
        while len(word_defs) < 4 and attempts < 20:
            attempts += 1
            w = fetch_random_word().lower()
            if w in word_defs:
                continue
            d = fetch_definition(w)
            if d:
                word_defs[w] = d

        if len(word_defs) < 4:
            # API issues: inform user instead of providing broken round
            return render(request, "games/meaning_quiz.html", {
                "definition": "❌ Sorry — could not fetch enough words from the API. Try again in a moment.",
                "options": [],
                "message": "API limit or network issue.",
                "game_over": True
            })

        # choose correct_word from the set and prepare options (words only)
        correct_word = random.choice(list(word_defs.keys()))
        definition = word_defs[correct_word]

        options = list(word_defs.keys())
        random.shuffle(options)

        # store exactly what we will display & check in session
        request.session["meaning_quiz"] = {
            "correct_word": correct_word,
            "definition": definition,
            "options": options
        }

    # --- Evaluate POST using the stored round (do NOT regenerate) ---
    state = request.session.get("meaning_quiz", {})
    correct_word = state.get("correct_word")
    definition = state.get("definition")
    options = state.get("options", [])

    message = ""
    game_over = False

    if request.method == "POST":
        # read the user's choice (exact value must match stored word)
        choice = (request.POST.get("choice") or "").strip()
        if not state:
            # session expired or missing
            message = "❌ Session expired; please try again."
            game_over = True
        else:
            # compare normalized (case-insensitive)
            if choice.lower() == correct_word.lower():
                message = f"✅ Correct! '{choice.title()}' matches the definition."
            else:
                message = f"❌ Wrong! The correct word was: {correct_word.title()}."
            game_over = True
            # clear the round so Play Again gets a fresh round
            try:
                del request.session["meaning_quiz"]
            except KeyError:
                pass

    # render the template using the same question/options the user saw
    return render(request, "games/meaning_quiz.html", {
        "definition": definition,
        "options": options,
        "message": message,
        "game_over": game_over
    })



def game_hub(request):
    """Main hub to display all available games."""
    games = [
        {"name": "Word Guess", "url": "games:word_guess", "desc": "Guess the hidden word before you run out of attempts!"},
        {"name": "Word Scramble", "url": "games:word_scramble", "desc": "Unscramble the letters to find the correct word."},
        {"name": "Synonym Match", "url": "games:synonym_match", "desc": "Find the correct synonym for the given word."},
        {"name": "Word Meaning Quiz", "url": "games:meaning_quiz", "desc": "Choose the correct definition of a given word."},
    ]
    return render(request, "games/game_hub.html", {"games": games})
