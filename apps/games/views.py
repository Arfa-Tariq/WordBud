from django.shortcuts import render
import random
import requests
from django.conf import settings
import os
from dotenv import load_dotenv
# Merriam-Webster API details
API_KEY = os.getenv("MERRIAM_WEBSTER_API_KEY")
BASE_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json"

# Small pool of common words — can be replaced with DB or Random Word API later
COMMON_WORDS = [
    "python", "django", "variable", "function", "template",
    "computer", "network", "language", "education", "science"
]


def get_valid_word():
    """
    Fetch a random valid English word verified from Merriam-Webster API.
    """
    while True:
        word = random.choice(COMMON_WORDS)
        url = f"{BASE_URL}/{word}?key={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0 and "meta" in data[0]:
                    return word.lower()
        except Exception as e:
            print("API error:", e)
            break

    # fallback if API fails
    return random.choice(COMMON_WORDS)


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
        return render(request, "games/word_game.html", {
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
# GAME 2: WORD SCRAMBLE (prototype)
# -----------------------------
def word_scramble(request):
    pass

# -----------------------------
# GAME 3: SYNONYM MATCH (prototype)
# -----------------------------
def synonym_match(request):
    pass


# -----------------------------
# GAME 4: WORD MEANING QUIZ (prototype)
# -----------------------------
def meaning_quiz(request):
    pass

def game_hub(request):
    """Main hub to display all available games."""
    games = [
        {"name": "Word Guess", "url": "games:word_guess", "desc": "Guess the hidden word before you run out of attempts!"},
        {"name": "Word Scramble", "url": "games:word_scramble", "desc": "Unscramble the letters to find the correct word."},
        {"name": "Synonym Match", "url": "games:synonym_match", "desc": "Find the correct synonym for the given word."},
        {"name": "Word Meaning Quiz", "url": "games:meaning_quiz", "desc": "Choose the correct definition of a given word."},
    ]
    return render(request, "games/game_hub.html", {"games": games})
