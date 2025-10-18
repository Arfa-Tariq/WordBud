from googletrans import Translator, LANGUAGES
import difflib

translator = Translator()

def get_language_code(user_input: str) -> str:
    user_input_lower = user_input.strip().lower()
    for code, lang_name in LANGUAGES.items():
        if lang_name.lower() == user_input_lower:
            return code
    closest = difflib.get_close_matches(user_input_lower, [name.lower() for name in LANGUAGES.values()], n=1)
    if closest:
        for code, lang_name in LANGUAGES.items():
            if lang_name.lower() == closest[0]:
                return code
    return "en"

def translate_text(text: str, target_lang: str) -> str:
    try:
        return translator.translate(text, dest=target_lang).text
    except Exception as e:
        return f"Error translating text: {str(e)}"
