"""
Translator views for WordBud with comprehensive logging.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from deep_translator import GoogleTranslator
from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES
import logging
import time

from apps.core.models import TranslationLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def translate_view(request):
    """
    Main translation page view.
    Displays translation interface with language selection.
    """
    # Get all supported languages and sort them alphabetically
    languages = sorted(
        [(code, name.title()) for name, code in GOOGLE_LANGUAGES_TO_CODES.items()],
        key=lambda x: x[1]
    )
    
    context = {
        'languages': languages,
        'total_languages': len(languages),
    }
    
    return render(request, 'translator/translate.html', context)


@require_http_methods(["POST"])
def translate_ajax(request):
    """
    AJAX endpoint for translation with comprehensive logging.
    """
    start_time = time.time()
    
    try:
        text = request.POST.get('text', '').strip()
        target_lang = request.POST.get('target_lang', 'en').strip()
        source_lang = request.POST.get('source_lang', 'auto').strip()
        
        # Validation
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'Please enter text to translate'
            }, status=400)
        
        if len(text) > 5000:
            return JsonResponse({
                'success': False,
                'error': 'Text is too long. Maximum 5000 characters allowed.'
            }, status=400)
        
        # Get language codes dict
        lang_codes = GOOGLE_LANGUAGES_TO_CODES
        valid_codes = list(lang_codes.values())
        
        if target_lang not in valid_codes:
            return JsonResponse({
                'success': False,
                'error': 'Invalid target language selected'
            }, status=400)
        
        # Perform translation
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(text)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Get language names
            source_lang_name = get_language_name(source_lang if source_lang != 'auto' else 'en')
            target_lang_name = get_language_name(target_lang)
            
            # If source was auto, try to detect it
            detected_source = source_lang
            if source_lang == 'auto':
                try:
                    from deep_translator import single_detection
                    detected = single_detection(text, api_key='free')
                    detected_source = detected
                    source_lang_name = get_language_name(detected)
                except:
                    detected_source = 'auto'
                    source_lang_name = 'Auto-detected'
            
            # Log the translation
            try:
                TranslationLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    source_text=text[:1000],  # Limit stored text length
                    translated_text=translated_text[:1000],
                    source_language=detected_source,
                    target_language=target_lang,
                    translated_at=timezone.now(),
                    ip_address=get_client_ip(request),
                    success=True,
                    response_time_ms=response_time_ms,
                    char_count=len(text)
                )
            except Exception as e:
                logger.warning(f"Failed to log translation: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'translated_text': translated_text,
                'source_lang': detected_source,
                'source_lang_name': source_lang_name,
                'target_lang': target_lang,
                'target_lang_name': target_lang_name,
                'original_text': text,
            })
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            
            # Log failed translation
            try:
                TranslationLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    source_text=text[:1000],
                    translated_text='',
                    source_language=source_lang,
                    target_language=target_lang,
                    translated_at=timezone.now(),
                    ip_address=get_client_ip(request),
                    success=False,
                    error_message=str(e),
                    response_time_ms=None,
                    char_count=len(text)
                )
            except Exception as log_error:
                logger.warning(f"Failed to log failed translation: {str(log_error)}")
            
            return JsonResponse({
                'success': False,
                'error': 'Translation service is temporarily unavailable. Please try again.'
            }, status=503)
    
    except Exception as e:
        logger.error(f"Unexpected error in translation: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)


@require_http_methods(["POST"])
def detect_language(request):
    """
    AJAX endpoint for language detection.
    Detects the language of provided text.
    """
    try:
        text = request.POST.get('text', '').strip()
        
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'Please enter text to detect language'
            }, status=400)
        
        # Detect language using deep-translator
        try:
            from deep_translator import single_detection
            detected_lang = single_detection(text, api_key='free')
            language_name = get_language_name(detected_lang)
            
            return JsonResponse({
                'success': True,
                'detected_lang': detected_lang,
                'language_name': language_name,
                'confidence': 1.0,  # deep-translator doesn't provide confidence
            })
        
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Could not detect language. Please try again.'
            }, status=503)
    
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred.'
        }, status=500)


def get_language_name(lang_code):
    """
    Get language name from language code.
    """
    # Reverse lookup in GOOGLE_LANGUAGES_TO_CODES
    for name, code in GOOGLE_LANGUAGES_TO_CODES.items():
        if code == lang_code:
            return name.title()
    return lang_code.upper()