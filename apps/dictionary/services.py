"""
Dictionary API services for WordBud.
Handles API calls, caching, and data parsing for Merriam-Webster APIs.
"""

import requests
from django.core.cache import cache
from django.conf import settings
from datetime import date
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# API Configuration
MW_DICTIONARY_URL = "https://www.dictionaryapi.com/api/v3/references/collegiate/json/"
MW_THESAURUS_URL = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/"
CACHE_TIMEOUT = 6 * 60 * 60  # 6 hours
WORD_OF_DAY_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours

# Curated word lists for Word of the Day and Random Word
CURATED_WORDS = [
    "serendipity", "ephemeral", "luminescence", "quixotic", "eloquent",
    "cogent", "benevolent", "audacious", "ubiquitous", "paradigm",
    "mellifluous", "petrichor", "ethereal", "sonorous", "ineffable",
    "ebullient", "magnanimous", "resilient", "sagacious", "tenacious",
    "verbose", "zealous", "ameliorate", "cacophony", "delineate",
    "esoteric", "fastidious", "gregarious", "halcyon", "iconoclast",
    "juxtapose", "kerfuffle", "languid", "meticulous", "nefarious",
    "obfuscate", "panacea", "quintessential", "reticent", "soliloquy",
    "tangential", "ubiquity", "vicarious", "wistful", "xenophobia",
    "yielding", "zenith", "aberration", "brevity", "conundrum"
]


def fetch_from_api(api_type: str, word: str) -> Dict[str, Any]:
    """
    Fetch data from Merriam-Webster API with caching.
    
    Args:
        api_type: Either 'dictionary' or 'thesaurus'
        word: The word to look up
        
    Returns:
        Dictionary containing API response or error information
    """
    cache_key = f"{api_type}_{word.lower().strip()}"
    cached = cache.get(cache_key)
    
    if cached:
        logger.debug(f"Cache hit for {api_type}: {word}")
        return cached

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
            cache.set(cache_key, data, CACHE_TIMEOUT)
            return data
        else:
            logger.warning(f"API returned status {response.status_code} for {word}")
            return {"error": f"API returned status {response.status_code}"}
            
    except requests.Timeout:
        logger.error(f"Timeout fetching {api_type} for {word}")
        return {"error": "Request timed out. Please try again."}
    except requests.RequestException as e:
        logger.error(f"Request error for {word}: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error fetching {word}: {str(e)}")
        return {"error": "An unexpected error occurred"}


def get_dictionary_data(word: str) -> Dict[str, Any]:
    """Get dictionary data for a word."""
    return fetch_from_api("dictionary", word)


def get_thesaurus_data(word: str) -> Dict[str, Any]:
    """Get thesaurus data for a word."""
    return fetch_from_api("thesaurus", word)


def parse_dictionary_response(data: Any) -> List[Dict[str, Any]]:
    """
    Parse Merriam-Webster dictionary API response.
    Extracts all available fields comprehensively.
    
    Returns:
        List of dictionaries containing parsed word data
    """
    if not data or (isinstance(data, dict) and "error" in data):
        return []

    # If API returns suggestions (list of strings), return them
    if isinstance(data, list) and data and isinstance(data[0], str):
        return [{"suggestions": data}]

    results = []
    
    for entry in data:
        if isinstance(entry, str):
            continue  # Skip string suggestions in mixed responses
            
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
        
        # Usage notes
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
    
    return results


def parse_thesaurus_response(data: Any) -> Dict[str, Any]:
    """
    Parse Merriam-Webster thesaurus API response.
    Extracts synonyms, antonyms, and related words.
    """
    if not data or (isinstance(data, dict) and "error" in data):
        return {"synonyms": [], "antonyms": [], "related": [], "near_antonyms": []}
    
    # If suggestions returned
    if isinstance(data, list) and data and isinstance(data[0], str):
        return {"suggestions": data, "synonyms": [], "antonyms": []}
    
    result = {
        "synonyms": [],
        "antonyms": [],
        "related": [],
        "near_antonyms": []
    }
    
    for entry in data:
        if isinstance(entry, str):
            continue
        
        meta = entry.get("meta", {})
        
        # Synonyms
        syns = meta.get("syns", [])
        result["synonyms"].extend([word for group in syns for word in group])
        
        # Antonyms
        ants = meta.get("ants", [])
        result["antonyms"].extend([word for group in ants for word in group])
        
        # Additional thesaurus data from definitions
        for def_section in entry.get("def", []):
            for sense_sequence in def_section.get("sseq", []):
                for sense_item in sense_sequence:
                    if len(sense_item) > 1 and isinstance(sense_item[1], dict):
                        sense_data = sense_item[1]
                        
                        # Related words
                        if "rel_list" in sense_data:
                            for rel in sense_data["rel_list"]:
                                result["related"].extend(rel.get("wd", []))
                        
                        # Near antonyms
                        if "near_list" in sense_data:
                            for near in sense_data["near_list"]:
                                result["near_antonyms"].extend(near.get("wd", []))
    
    # Remove duplicates and sort
    result["synonyms"] = sorted(list(set(result["synonyms"])))
    result["antonyms"] = sorted(list(set(result["antonyms"])))
    result["related"] = sorted(list(set(result["related"])))
    result["near_antonyms"] = sorted(list(set(result["near_antonyms"])))
    
    return result


def get_word_of_the_day() -> Dict[str, Any]:
    """
    Get word of the day with full caching.
    Changes daily at midnight.
    """
    today = date.today().isoformat()
    cache_key = f"word_of_day_{today}"
    
    cached_word = cache.get(cache_key)
    if cached_word:
        return cached_word
    
    # Select word based on day of year for consistency
    day_of_year = date.today().timetuple().tm_yday
    word = CURATED_WORDS[day_of_year % len(CURATED_WORDS)]
    
    # Fetch full dictionary data
    dict_data = parse_dictionary_response(get_dictionary_data(word))
    
    word_data = {
        "word": word,
        "definition": "",
        "part_of_speech": "",
        "date": today,
    }
    
    if dict_data and len(dict_data) > 0:
        first_entry = dict_data[0]
        word_data["definition"] = first_entry.get("short_definitions", [""])[0] if first_entry.get("short_definitions") else ""
        word_data["part_of_speech"] = first_entry.get("part_of_speech", "")
    
    # Cache for 24 hours
    cache.set(cache_key, word_data, WORD_OF_DAY_CACHE_TIMEOUT)
    return word_data


def get_random_word() -> str:
    """
    Get a random word from curated list.
    Uses timestamp-based selection for variety.
    """
    import random
    import time
    
    # Seed with current timestamp for dynamic selection
    random.seed(int(time.time()))
    return random.choice(CURATED_WORDS)


def get_spelling_suggestions(word: str) -> List[str]:
    """
    Get spelling suggestions when exact match not found.
    """
    dict_data = get_dictionary_data(word)
    
    if isinstance(dict_data, list) and dict_data and isinstance(dict_data[0], str):
        return dict_data  # API returned suggestions
    
    return []