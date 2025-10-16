"""
Dictionary services for API calls, caching, and data processing.
Handles all external API interactions and caching logic for optimal performance.
"""

import requests
import random
from django.core.cache import cache
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# API Configuration
API_TIMEOUT = getattr(settings, 'DICTIONARY_API_TIMEOUT', 5)
WORD_OF_DAY_TIMEOUT = getattr(settings, 'WORD_OF_DAY_CACHE_TIMEOUT', 86400)
DICT_CACHE_TIMEOUT = getattr(settings, 'DICTIONARY_CACHE_TIMEOUT', 3600)

# Fallback words for when APIs fail
FALLBACK_WORDS = [
    'serendipity', 'ephemeral', 'petrichor', 'wanderlust', 'mellifluous',
    'eloquent', 'ethereal', 'luminous', 'resilient', 'magnificent',
    'tranquil', 'vibrant', 'harmony', 'wisdom', 'courage'
]


def safe_api_request(url: str, params: Optional[Dict] = None, timeout: int = API_TIMEOUT) -> Optional[Dict]:
    """
    Safely make an API request with proper error handling and timeout.
    
    Args:
        url: The API endpoint URL
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        JSON response data or None if request fails
    """
    headers = {
        "User-Agent": "WordBud/1.0 (Django Dictionary App)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"API request failed for {url}: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Invalid JSON response from {url}: {e}")
        return None


class DictionaryService:
    """Main service class for dictionary operations."""
    
    @staticmethod
    def get_word_definition(word: str) -> Dict[str, Any]:
        """
        Get comprehensive word definition with caching.
        
        Args:
            word: The word to look up
            
        Returns:
            Dictionary containing word data with safe defaults
        """
        cache_key = f"dict_word_{word.lower()}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Initialize default data structure
        word_data = {
            "word": word,
            "phonetic": "Not available",
            "phonetics": [],
            "meanings": [],
            "origin": "Not available",
            "synonyms": [],
            "antonyms": [],
            "fun_fact": ""
        }
        
        # Use parallel requests for better performance
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all API calls concurrently
            future_dict = executor.submit(DictionaryService._fetch_dictionary_api, word)
            future_synonyms = executor.submit(DictionaryService._fetch_synonyms_antonyms, word)
            future_wiki = executor.submit(DictionaryService._fetch_wikipedia_info, word)
            
            # Collect results with timeout handling
            try:
                dict_result = future_dict.result(timeout=6)
                if dict_result:
                    word_data.update(dict_result)
            except Exception as e:
                logger.warning(f"Dictionary API failed for '{word}': {e}")
            
            try:
                syn_ant_result = future_synonyms.result(timeout=6)
                if syn_ant_result:
                    word_data["synonyms"] = syn_ant_result.get("synonyms", [])
                    word_data["antonyms"] = syn_ant_result.get("antonyms", [])
            except Exception as e:
                logger.warning(f"Synonyms/Antonyms API failed for '{word}': {e}")
            
            try:
                wiki_result = future_wiki.result(timeout=6)
                if wiki_result:
                    if wiki_result.get("fun_fact"):
                        word_data["fun_fact"] = wiki_result["fun_fact"]
                    if word_data["origin"] == "Not available" and wiki_result.get("origin_hint"):
                        word_data["origin"] = wiki_result["origin_hint"]
            except Exception as e:
                logger.warning(f"Wikipedia API failed for '{word}': {e}")
        
        # Ensure we have at least one definition
        if not word_data["meanings"]:
            word_data["meanings"] = [{
                "partOfSpeech": "N/A",
                "definitions": [{"definition": "Definition not available", "example": ""}]
            }]
        
        # Cache the result
        cache.set(cache_key, word_data, DICT_CACHE_TIMEOUT)
        return word_data
    
    @staticmethod
    def _fetch_dictionary_api(word: str) -> Optional[Dict]:
        """Fetch data from Free Dictionary API."""
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        data = safe_api_request(url)
        
        if not data or not isinstance(data, list) or not data:
            return None
        
        try:
            entry = data[0]
            result = {
                "phonetic": entry.get("phonetic", "Not available"),
                "phonetics": entry.get("phonetics", []),
                "origin": entry.get("origin", "Not available"),
                "meanings": []
            }
            
            # Process meanings
            for meaning in entry.get("meanings", []):
                processed_meaning = {
                    "partOfSpeech": meaning.get("partOfSpeech", "N/A"),
                    "definitions": []
                }
                
                for definition in meaning.get("definitions", []):
                    processed_meaning["definitions"].append({
                        "definition": definition.get("definition", ""),
                        "example": definition.get("example", "")
                    })
                
                if processed_meaning["definitions"]:
                    result["meanings"].append(processed_meaning)
            
            return result
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"Error processing dictionary API response for '{word}': {e}")
            return None
    
    @staticmethod
    def _fetch_synonyms_antonyms(word: str) -> Optional[Dict]:
        """Fetch synonyms and antonyms from multiple sources."""
        synonyms = set()
        antonyms = set()
        
        # Try Datamuse API for synonyms
        syn_data = safe_api_request(f"https://api.datamuse.com/words?rel_syn={word}&max=10")
        if syn_data:
            synonyms.update(item.get("word", "") for item in syn_data if item.get("word"))
        
        # Try Datamuse API for antonyms
        ant_data = safe_api_request(f"https://api.datamuse.com/words?rel_ant={word}&max=10")
        if ant_data:
            antonyms.update(item.get("word", "") for item in ant_data if item.get("word"))
        
        return {
            "synonyms": list(synonyms)[:10],
            "antonyms": list(antonyms)[:10]
        }
    
    @staticmethod
    def _fetch_wikipedia_info(word: str) -> Optional[Dict]:
        """Fetch additional information from Wikipedia."""
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{word.title()}"
        data = safe_api_request(url)
        
        if not data:
            return None
        
        result = {}
        extract = data.get("extract", "")
        
        if extract:
            # Use first 200 characters as fun fact
            result["fun_fact"] = extract[:200] + "..." if len(extract) > 200 else extract
            
            # Look for etymology hints
            for sentence in extract.split("."):
                if any(keyword in sentence.lower() for keyword in 
                      ["latin", "greek", "french", "old english", "derived from", "etymology"]):
                    result["origin_hint"] = sentence.strip() + "."
                    break
        
        return result


class WordOfTheDayService:
    """Service for managing Word of the Day functionality."""
    
    @staticmethod
    def get_word_of_the_day() -> Dict[str, Any]:
        """
        Get the current word of the day with 24-hour caching.
        
        Returns:
            Dictionary with word and definition, or fallback data
        """
        cache_key = "word_of_the_day"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Try to get a new word of the day
        word_data = WordOfTheDayService._fetch_new_word_of_day()
        
        # Cache for 24 hours
        cache.set(cache_key, word_data, WORD_OF_DAY_TIMEOUT)
        return word_data
    
    @staticmethod
    def _fetch_new_word_of_day() -> Dict[str, Any]:
        """Fetch a new word of the day from various sources."""
        # Try multiple APIs for word of the day
        sources = [
            "https://api.wordnik.com/v4/words.json/wordOfTheDay",
            "https://random-word-api.herokuapp.com/word"
        ]
        
        for source_url in sources:
            try:
                if "wordnik" in source_url:
                    # Wordnik API (requires API key, so skip for now)
                    continue
                elif "random-word-api" in source_url:
                    data = safe_api_request(source_url)
                    if data and isinstance(data, list) and data:
                        word = data[0]
                        definition_data = DictionaryService.get_word_definition(word)
                        
                        if definition_data and definition_data.get("meanings"):
                            first_def = definition_data["meanings"][0]["definitions"][0]["definition"]
                            return {
                                "word": word,
                                "definition": first_def,
                                "full_data": definition_data
                            }
            except Exception as e:
                logger.warning(f"Word of the day source failed {source_url}: {e}")
                continue
        
        # Fallback to a curated word
        fallback_word = random.choice(FALLBACK_WORDS)
        definition_data = DictionaryService.get_word_definition(fallback_word)
        
        return {
            "word": fallback_word,
            "definition": definition_data["meanings"][0]["definitions"][0]["definition"] if definition_data.get("meanings") else "A beautiful word",
            "full_data": definition_data
        }


class RandomWordService:
    """Service for generating random words."""
    
    @staticmethod
    def get_random_word() -> Dict[str, Any]:
        """
        Get a random word with definition.
        Uses caching to improve performance.
        
        Returns:
            Dictionary with random word data
        """
        # Try to get from various random word APIs
        sources = [
            "https://random-word-api.herokuapp.com/word",
            "https://api.datamuse.com/words?sp=?????&max=1"  # 5-letter word
        ]
        
        for source_url in sources:
            try:
                data = safe_api_request(source_url)
                if not data:
                    continue
                
                word = None
                if "random-word-api" in source_url and isinstance(data, list) and data:
                    word = data[0]
                elif "datamuse" in source_url and isinstance(data, list) and data:
                    word = data[0].get("word")
                
                if word:
                    word_data = DictionaryService.get_word_definition(word)
                    return {
                        "word": word,
                        "definition": word_data["meanings"][0]["definitions"][0]["definition"] if word_data.get("meanings") else "Definition not available",
                        "full_data": word_data
                    }
            except Exception as e:
                logger.warning(f"Random word source failed {source_url}: {e}")
                continue
        
        # Fallback to curated list
        fallback_word = random.choice(FALLBACK_WORDS)
        word_data = DictionaryService.get_word_definition(fallback_word)
        
        return {
            "word": fallback_word,
            "definition": word_data["meanings"][0]["definitions"][0]["definition"] if word_data.get("meanings") else "A carefully selected word",
            "full_data": word_data
        }


class FavoritesService:
    """Service for managing user favorites."""
    
    @staticmethod
    def add_favorite(user, word: str) -> bool:
        """
        Add a word to user's favorites.
        
        Args:
            user: Django user instance
            word: Word to add to favorites
            
        Returns:
            True if added, False if already exists
        """
        from .models import UserFavorite, UserData
        
        # Try new model first
        try:
            favorite, created = UserFavorite.objects.get_or_create(
                user=user,
                word=word.lower()
            )
            return created
        except Exception:
            # Fallback to legacy model
            try:
                favorite, created = UserData.objects.get_or_create(
                    user=user,
                    favorite_word=word.lower()
                )
                return created
            except Exception:
                return False
    
    @staticmethod
    def remove_favorite(user, word: str) -> bool:
        """
        Remove a word from user's favorites.
        
        Args:
            user: Django user instance
            word: Word to remove from favorites
            
        Returns:
            True if removed, False if not found
        """
        from .models import UserFavorite, UserData
        
        removed = False
        
        # Try new model first
        try:
            favorite = UserFavorite.objects.get(user=user, word=word.lower())
            favorite.delete()
            removed = True
        except UserFavorite.DoesNotExist:
            pass
        except Exception:
            pass
        
        # Also try legacy model
        try:
            favorite = UserData.objects.get(user=user, favorite_word=word.lower())
            favorite.delete()
            removed = True
        except UserData.DoesNotExist:
            pass
        except Exception:
            pass
        
        return removed
    
    @staticmethod
    def get_user_favorites(user):
        """Get all favorites for a user."""
        from .models import UserFavorite, UserData
        
        # Try new model first
        try:
            favorites = UserFavorite.objects.filter(user=user).order_by('-created_at')
            if favorites.exists():
                return favorites
        except Exception:
            pass
        
        # Fallback to legacy model
        try:
            return UserData.objects.filter(user=user)
        except Exception:
            return []
    
    @staticmethod
    def is_favorite(user, word: str) -> bool:
        """Check if a word is in user's favorites."""
        from .models import UserFavorite, UserData
        
        # Check new model first
        try:
            if UserFavorite.objects.filter(user=user, word=word.lower()).exists():
                return True
        except Exception:
            pass
        
        # Check legacy model
        try:
            return UserData.objects.filter(user=user, favorite_word=word.lower()).exists()
        except Exception:
            return False