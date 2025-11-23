"""
Dictionary API services for WordBud.
Handles API calls, caching, and data parsing for Merriam-Webster APIs.
Fully optimized with robust error handling and dynamic features.
"""

import requests
from django.core.cache import cache
from django.conf import settings
from datetime import date
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import random
import time

logger = logging.getLogger(__name__)

# API Configuration
MW_DICTIONARY_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json/"
MW_THESAURUS_URL = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/"
RANDOM_WORD_API = "https://random-word-api.herokuapp.com/word?number=50"
# Cache timeouts
CACHE_TIMEOUT = 6 * 60 * 60  # 6 hours for word data
WORD_OF_DAY_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours
RANDOM_WORD_CACHE_TIMEOUT = 5 * 60  # 5 minutes for random word pool

# Fallback word lists (only used if all APIs fail)
FALLBACK_WORDS = [
    "serendipity", "ephemeral", "luminescence", "quixotic", "eloquent",
    "cogent", "benevolent", "audacious", "ubiquitous", "paradigm",
    "mellifluous", "petrichor", "ethereal", "sonorous", "ineffable",
    "ebullient", "magnanimous", "resilient", "sagacious", "tenacious"
]


def fetch_from_api(api_type: str, word: str) -> Tuple[Optional[Any], Optional[str]]:
    """
    Fetch data from Merriam-Webster API with caching and error handling.
    
    Args:
        api_type: Either 'dictionary' or 'thesaurus'
        word: The word to look up
        
    Returns:
        Tuple of (data, error_message)
    """
    cache_key = f"{api_type}_{word.lower().strip()}"
    cached = cache.get(cache_key)
    
    if cached is not None:
        logger.debug(f"Cache hit for {api_type}: {word}")
        return cached, None

    # Select appropriate API
    if api_type == "dictionary":
        api_key = settings.MW_DICTIONARY_API_KEY
        url = f"{MW_DICTIONARY_URL}{word}?key={api_key}"
    else:
        api_key = settings.MW_THESAURUS_API_KEY
        url = f"{MW_THESAURUS_URL}{word}?key={api_key}"

    try:
        logger.info(f"Fetching {api_type} data for: {word}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Cache successful responses
            cache.set(cache_key, data, CACHE_TIMEOUT)
            return data, None
        elif response.status_code == 404:
            error = f"Word '{word}' not found in {api_type}"
            cache.set(cache_key, [], 300)  # Cache 404s briefly
            return None, error
        else:
            error = f"API returned status {response.status_code}"
            logger.warning(f"{error} for {word}")
            return None, error
            
    except requests.Timeout:
        error = "Request timed out. Please try again."
        logger.error(f"Timeout fetching {api_type} for {word}")
        return None, error
    except requests.RequestException as e:
        error = f"Connection error: {str(e)}"
        logger.error(f"Request error for {word}: {str(e)}")
        return None, error
    except Exception as e:
        error = "An unexpected error occurred"
        logger.error(f"Unexpected error fetching {word}: {str(e)}")
        return None, error


def get_dictionary_data(word: str) -> Tuple[Optional[Any], Optional[str]]:
    """Get dictionary data for a word."""
    return fetch_from_api("dictionary", word)


def get_thesaurus_data(word: str) -> Tuple[Optional[Any], Optional[str]]:
    """Get thesaurus data for a word."""
    return fetch_from_api("thesaurus", word)


def parse_dictionary_response(data: Any) -> List[Dict[str, Any]]:
    """
    Parse Merriam-Webster dictionary API response comprehensively.
    Extracts all available fields including definitions, examples, etymology,
    pronunciations, audio, and more.
    
    Returns:
        List of dictionaries containing parsed word data
    """
    if not data:
        return []

    # If API returns suggestions (list of strings), return them
    if isinstance(data, list) and data and isinstance(data[0], str):
        return [{"suggestions": data}]

    results = []
    
    try:
        for entry in data:
            if isinstance(entry, str):
                continue  # Skip string suggestions in mixed responses
            
            if not isinstance(entry, dict):
                continue
                
            # Extract metadata
            meta = entry.get("meta", {})
            word_id = meta.get("id", "").split(":")[0]  # Remove homograph numbers
            
            # Basic information
            headword = entry.get("hwi", {})
            hw_text = headword.get("hw", word_id).replace("*", "·")  # Replace syllable markers
            
            # Pronunciation
            pronunciations = []
            if "prs" in headword:
                for pr in headword["prs"]:
                    pron_data = {
                        "ipa": pr.get("mw", ""),  # Merriam-Webster pronunciation
                        "sound": pr.get("sound", {}),
                    }
                    pronunciations.append(pron_data)
            
            # Audio files
            audio_files = []
            for pr in headword.get("prs", []):
                if "sound" in pr and "audio" in pr["sound"]:
                    audio_id = pr["sound"]["audio"]
                    # Determine subdirectory based on MW rules
                    if audio_id.startswith("bix"):
                        subdir = "bix"
                    elif audio_id.startswith("gg"):
                        subdir = "gg"
                    elif audio_id[0].isdigit():
                        subdir = "number"
                    else:
                        subdir = audio_id[0]
                    
                    audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{subdir}/{audio_id}.mp3"
                    audio_files.append(audio_url)
            
            # Part of speech
            part_of_speech = entry.get("fl", "")
            
            # Short definitions (simplified)
            short_definitions = entry.get("shortdef", [])
            
            # Detailed definitions with examples
            definitions = []
            examples = []
            
            for def_section in entry.get("def", []):
                for sense_sequence in def_section.get("sseq", []):
                    for sense_item in sense_sequence:
                        if len(sense_item) > 1 and isinstance(sense_item[1], dict):
                            sense_data = sense_item[1]
                            
                            # Extract definition text
                            for dt_item in sense_data.get("dt", []):
                                if dt_item[0] == "text":
                                    def_text = dt_item[1].replace("{bc}", "").replace("{it}", "").replace("{/it}", "")
                                    definitions.append(def_text.strip())
                                
                                # Extract examples (vis = verbal illustrations)
                                if dt_item[0] == "vis":
                                    for vis_item in dt_item[1]:
                                        example_text = vis_item.get("t", "")
                                        # Clean up example text
                                        example_text = example_text.replace("{it}", "<em>").replace("{/it}", "</em>")
                                        example_text = example_text.replace("{wi}", "").replace("{/wi}", "")
                                        if example_text:
                                            examples.append(example_text)
            
            # Etymology
            etymology = []
            for et_item in entry.get("et", []):
                if len(et_item) > 1:
                    et_text = et_item[1]
                    # Clean etymology text
                    et_text = et_text.replace("{it}", "<em>").replace("{/it}", "</em>")
                    et_text = et_text.replace("{ma}", "").replace("{/ma}", "")
                    etymology.append(et_text)
            
            # Date of first known use
            date_info = entry.get("date", "")
            if date_info:
                date_info = date_info.replace("{bc}", "")
            
            # Usage notes and additional information
            usage_notes = []
            for un in entry.get("uros", []):  # Undefined run-ons
                if "ure" in un:
                    usage_notes.append(un["ure"])
            
            # Compile the result
            result = {
                "word": hw_text,
                "word_id": word_id,
                "part_of_speech": part_of_speech,
                "pronunciations": pronunciations,
                "audio": audio_files,
                "short_definitions": short_definitions,
                "definitions": definitions if definitions else short_definitions,
                "examples": examples,
                "etymology": etymology,
                "date": date_info,
                "usage_notes": usage_notes,
            }
            
            results.append(result)
    except Exception as e:
        logger.error(f"Error parsing dictionary response: {str(e)}")
    
    return results


def parse_thesaurus_response(data: Any) -> Dict[str, List[str]]:
    """
    Parse Merriam-Webster Thesaurus API response.
    Extracts synonyms, antonyms, related words, and near antonyms.
    Safely handles lists of suggestions or unexpected data structures.
    """
    # Default result structure
    result = {
        "synonyms": [],
        "antonyms": [],
        "related": [],
        "near_antonyms": []
    }

    if not data:
        return result

    # Handle suggestion-only responses (list of strings)
    if isinstance(data, list) and data and all(isinstance(item, str) for item in data):
        result["suggestions"] = data
        return result

    try:
        for entry in data:
            if not isinstance(entry, dict):
                # Skip anything that is not a dict
                continue

            meta = entry.get("meta", {})

            # Synonyms
            syns = meta.get("syns", [])
            for group in syns:
                if isinstance(group, list):
                    result["synonyms"].extend(group)

            # Antonyms
            ants = meta.get("ants", [])
            for group in ants:
                if isinstance(group, list):
                    result["antonyms"].extend(group)

            # Additional thesaurus data from definitions
            for def_section in entry.get("def", []):
                sseq_list = def_section.get("sseq", [])
                if not isinstance(sseq_list, list):
                    continue

                for sense_sequence in sseq_list:
                    if not isinstance(sense_sequence, list):
                        continue

                    for sense_item in sense_sequence:
                        if len(sense_item) < 2 or not isinstance(sense_item[1], dict):
                            continue
                        sense_data = sense_item[1]

                        # Related words
                        for rel_list in sense_data.get("rel_list", []):
                            if isinstance(rel_list, dict) and "wd" in rel_list:
                                result["related"].extend(rel_list.get("wd", []))
                            elif isinstance(rel_list, list):
                                for rel in rel_list:
                                    if isinstance(rel, dict) and "wd" in rel:
                                        result["related"].extend(rel.get("wd", []))

                        # Near antonyms
                        for near_list in sense_data.get("near_list", []):
                            if isinstance(near_list, dict) and "wd" in near_list:
                                result["near_antonyms"].extend(near_list.get("wd", []))
                            elif isinstance(near_list, list):
                                for near in near_list:
                                    if isinstance(near, dict) and "wd" in near:
                                        result["near_antonyms"].extend(near.get("wd", []))

        # Deduplicate and sort, limit to top 20
        for key in ["synonyms", "antonyms", "related", "near_antonyms"]:
            result[key] = sorted(list(set(result[key])))[:20]

    except Exception as e:
        logger.error(f"Error parsing thesaurus response: {str(e)}")

    return result


def get_word_of_the_day() -> Dict[str, Any]:
    """
    Get word of the day with full caching.
    Changes daily at midnight. Fully dynamic.
    """
    today = date.today().isoformat()
    cache_key = f"word_of_day_{today}"
    
    cached_word = cache.get(cache_key)
    if cached_word:
        return cached_word
    
    # Generate deterministic word based on day of year
    day_of_year = date.today().timetuple().tm_yday
    
    # Try to get a dynamic word from Random Word API first
    try:
        response = requests.get(f"{RANDOM_WORD_API}&seed={today}", timeout=5)
        if response.status_code == 200:
            words = response.json()
            if words and isinstance(words, list):
                word = words[0]
            else:
                # Fallback to deterministic selection
                word = FALLBACK_WORDS[day_of_year % len(FALLBACK_WORDS)]
        else:
            word = FALLBACK_WORDS[day_of_year % len(FALLBACK_WORDS)]
    except Exception as e:
        logger.warning(f"Failed to fetch dynamic word of the day: {str(e)}")
        word = FALLBACK_WORDS[day_of_year % len(FALLBACK_WORDS)]
    
    # Fetch full dictionary data
    dict_data, error = get_dictionary_data(word)
    parsed_data = parse_dictionary_response(dict_data)
    
    word_data = {
        "word": word,
        "definition": "Expand your vocabulary with this word!",
        "part_of_speech": "",
        "date": today,
    }
    
    if parsed_data and len(parsed_data) > 0 and "suggestions" not in parsed_data[0]:
        first_entry = parsed_data[0]
        word_data["definition"] = first_entry.get("short_definitions", [""])[0] if first_entry.get("short_definitions") else first_entry.get("definitions", [""])[0] if first_entry.get("definitions") else "Expand your vocabulary!"
        word_data["part_of_speech"] = first_entry.get("part_of_speech", "")
    
    # Cache for 24 hours
    cache.set(cache_key, word_data, WORD_OF_DAY_CACHE_TIMEOUT)
    return word_data


def get_random_word() -> str:
    """
    Get a truly random word from external API.
    Falls back to curated list if API fails.
    """
    cache_key = "random_word_pool"
    word_pool = cache.get(cache_key)

    # Refresh pool if empty or too small
    if not word_pool or len(word_pool) < 5:
        try:
            response = requests.get(RANDOM_WORD_API, timeout=5)
            if response.status_code == 200:
                words = response.json()
                if words and isinstance(words, list):
                    word_pool = words
                    cache.set(cache_key, word_pool, RANDOM_WORD_CACHE_TIMEOUT)
        except Exception as e:
            logger.warning(f"Failed to fetch random words: {str(e)}")
            word_pool = FALLBACK_WORDS.copy()  # fallback immediately if API fails

    # Always pick randomly from pool
    if word_pool:
        chosen_word = random.choice(word_pool)
        # Remove chosen word from pool so next call gets a new one
        try:
            word_pool.remove(chosen_word)
            cache.set(cache_key, word_pool, RANDOM_WORD_CACHE_TIMEOUT)
        except ValueError:
            pass  # just in case
        return chosen_word

    # Final fallback
    return random.choice(FALLBACK_WORDS)

def get_spelling_suggestions(word: str) -> List[str]:
    """
    Get spelling suggestions when exact match not found.
    """
    dict_data, error = get_dictionary_data(word)
    
    if isinstance(dict_data, list) and dict_data and isinstance(dict_data[0], str):
        return dict_data[:10]  # Return first 10 suggestions
    
    return []


def search_word_comprehensive(word: str) -> Dict[str, Any]:
    """
    Comprehensive word search that fetches and parses all data.
    
    Returns:
        Dictionary with all word information including dictionary and thesaurus data
    """
    result = {
        "word": word,
        "found": False,
        "dictionary_results": [],
        "thesaurus": {},
        "suggestions": [],
        "error": None
    }
    
    try:
        # Fetch dictionary data
        dict_data, dict_error = get_dictionary_data(word)
        
        if dict_data:
            parsed_results = parse_dictionary_response(dict_data)
            
            # Check for suggestions
            if parsed_results and "suggestions" in parsed_results[0]:
                result["suggestions"] = parsed_results[0]["suggestions"]
                result["error"] = f"No exact match found for '{word}'. Did you mean:"
            elif parsed_results:
                result["found"] = True
                result["dictionary_results"] = parsed_results
                
                # Fetch thesaurus data
                thes_data, thes_error = get_thesaurus_data(word)
                if thes_data:
                    result["thesaurus"] = parse_thesaurus_response(thes_data)
            else:
                result["error"] = f"No results found for '{word}'."
                result["suggestions"] = get_spelling_suggestions(word)
        else:
            result["error"] = dict_error or f"No results found for '{word}'."
            result["suggestions"] = get_spelling_suggestions(word)
    
    except Exception as e:
        logger.error(f"Error in comprehensive word search for '{word}': {str(e)}")
        result["error"] = "An error occurred while processing your request."
    
    return result