from django.shortcuts import render
from googletrans import LANGUAGES
from .services import translate_text, get_language_code

def translate_view(request):
    translated_text = None
    user_language_input = ""
    
    if request.method == "POST":
        text = request.POST.get("text", "")
        user_language_input = request.POST.get("language", "")
        lang_code = get_language_code(user_language_input)
        translated_text = translate_text(text, lang_code)

    language_names = sorted([name.title() for name in LANGUAGES.values()])

    return render(request, "translator/translate.html", {
        "translated_text": translated_text,
        "user_language_input": user_language_input,
        "language_names": language_names
    })
