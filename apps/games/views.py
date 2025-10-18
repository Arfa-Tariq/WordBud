import os
import random
import requests
from django.shortcuts import render
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔑 Merriam-Webster API setup
API_KEY = os.getenv("MERRIAM_WEBSTER_API_KEY")
BASE_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json"

# A small pool of fallback words
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
                # Merriam-Webster returns a list with entries for valid words
                if isinstance(data, list) and len(data) > 0 and "meta" in data[0]:
                    return word.lower()
        except Exception as e:
            print("API error:", e)
            break

    # fallback in case API or env fails
    return random.choice(COMMON_WORDS)


def word_game(request):
    """
    Word Guess Game using Merriam-Webster API verified words.
    """

    # Start new game if none exists
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

    # Handle POST (user guess)
    if request.method == "POST":
        guess = request.POST.get('guess', '').lower()

        if guess and guess not in guessed:
            guessed.append(guess)
            if guess not in word:
                attempts -= 1
                message = f"'{guess}' is not in the word."
            else:
                message = f"✅ Good job! '{guess}' is in the word."

            # Update session
            request.session['game'] = {
                'word': word,
                'guessed': guessed,
                'attempts': attempts
            }

    display_word = " ".join([c if c in guessed else "_" for c in word])
    won = "_" not in display_word
    lost = attempts <= 0

    # End of game
    if won or lost:
        final_message = "🎉 You won!" if won else f"❌ You lost! The word was '{word}'."
        request.session.pop('game', None)
        return render(request, "games/word_game.html", {
            'display_word': display_word,
            'attempts': attempts,
            'message': final_message,
            'game_over': True
        })

    # Render game in progress
    return render(request, "games/word_game.html", {
        'display_word': display_word,
        'attempts': attempts,
        'message': message,
        'game_over': False
    })
