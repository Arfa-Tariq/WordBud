"""
Dictionary views for WordBud.
Handles web requests and API endpoints.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db.models import Count
from datetime import date
import logging

from . import services
from .models import UserFavorite, SearchHistory

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def word_lookup(request):
    """
    Main word lookup view with comprehensive data display.
    Handles search queries and displays all available word information.
    """
    word = request.GET.get("q", "").strip()
    results = []
    thesaurus = {}
    error = None
    suggestions = []
    is_favorite = False
    
    if word:
        try:
            # Fetch dictionary data
            dict_data = services.get_dictionary_data(word)
            results = services.parse_dictionary_response(dict_data)
            
            # Check for spelling suggestions
            if results and "suggestions" in results[0]:
                suggestions = results[0]["suggestions"]
                results = []
                error = f"No exact match found for '{word}'. Did you mean:"
            elif not results:
                # Try to get suggestions
                suggestions = services.get_spelling_suggestions(word)
                if suggestions:
                    error = f"No exact match found for '{word}'. Did you mean:"
                else:
                    error = f"No results found for '{word}'."
            
            # Fetch thesaurus data if we have results
            if results and "suggestions" not in results[0]:
                thesaurus_data = services.get_thesaurus_data(word)
                thesaurus = services.parse_thesaurus_response(thesaurus_data)
                
                # Record search history
                if request.user.is_authenticated:
                    SearchHistory.objects.create(
                        user=request.user,
                        word=word.lower(),
                        ip_address=get_client_ip(request)
                    )
                else:
                    SearchHistory.objects.create(
                        word=word.lower(),
                        ip_address=get_client_ip(request)
                    )
                
                # Check if word is in favorites
                if request.user.is_authenticated:
                    is_favorite = UserFavorite.objects.filter(
                        user=request.user,
                        word=word.lower()
                    ).exists()
        
        except Exception as e:
            logger.error(f"Error processing word lookup for '{word}': {str(e)}")
            error = "An error occurred while processing your request."
    
    # Get word of the day
    word_of_day = services.get_word_of_the_day()
    
    context = {
        "word": word,
        "results": results,
        "thesaurus": thesaurus,
        "error": error,
        "suggestions": suggestions,
        "word_of_day": word_of_day,
        "is_favorite": is_favorite,
    }
    
    return render(request, "dictionary/searchword.html", context)


def random_word_view(request):
    """Redirect to a random word search."""
    word = services.get_random_word()
    return redirect(f"{request.path.replace('random/', '')}?q={word}")


def word_of_day_refresh(request):
    """Force refresh the word of the day cache."""
    today = date.today().isoformat()
    cache.delete(f"word_of_day_{today}")
    return redirect("dictionary:dictionary")


@login_required
@require_http_methods(["POST"])
def add_to_favorites(request):
    """Add a word to user's favorites."""
    word = request.POST.get("word", "").strip().lower()
    
    if not word:
        return JsonResponse({"success": False, "error": "No word provided"}, status=400)
    
    try:
        favorite, created = UserFavorite.objects.get_or_create(
            user=request.user,
            word=word
        )
        
        if created:
            return JsonResponse({
                "success": True,
                "message": f"'{word}' added to favorites",
                "action": "added"
            })
        else:
            return JsonResponse({
                "success": True,
                "message": f"'{word}' is already in favorites",
                "action": "exists"
            })
    
    except Exception as e:
        logger.error(f"Error adding favorite for user {request.user.id}: {str(e)}")
        return JsonResponse({"success": False, "error": "Failed to add favorite"}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_from_favorites(request):
    """Remove a word from user's favorites."""
    word = request.POST.get("word", "").strip().lower()
    
    if not word:
        return JsonResponse({"success": False, "error": "No word provided"}, status=400)
    
    try:
        deleted_count = UserFavorite.objects.filter(
            user=request.user,
            word=word
        ).delete()[0]
        
        if deleted_count > 0:
            return JsonResponse({
                "success": True,
                "message": f"'{word}' removed from favorites",
                "action": "removed"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": f"'{word}' not found in favorites"
            }, status=404)
    
    except Exception as e:
        logger.error(f"Error removing favorite for user {request.user.id}: {str(e)}")
        return JsonResponse({"success": False, "error": "Failed to remove favorite"}, status=500)


@login_required
def favorites_list(request):
    """Display user's favorite words."""
    favorites = UserFavorite.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        "favorites": favorites,
    }
    
    return render(request, "dictionary/favorites.html", context)


@login_required
def search_history(request):
    """Display user's search history."""
    history = SearchHistory.objects.filter(user=request.user).order_by('-searched_at')[:50]
    
    # Get popular searches
    popular_words = (
        SearchHistory.objects
        .filter(user=request.user)
        .values('word')
        .annotate(count=Count('word'))
        .order_by('-count')[:10]
    )
    
    context = {
        "history": history,
        "popular_words": popular_words,
    }
    
    return render(request, "dictionary/history.html", context)


# API Endpoints (keep existing endpoints unchanged)
@require_http_methods(["GET"])
def api_word_lookup(request):
    """
    API endpoint for word lookup.
    Returns JSON with dictionary and thesaurus data.
    """
    word = request.GET.get("word", "").strip()
    
    if not word:
        return JsonResponse({"error": "No word provided"}, status=400)
    
    try:
        # Fetch dictionary data
        dict_data = services.get_dictionary_data(word)
        results = services.parse_dictionary_response(dict_data)
        
        # Fetch thesaurus data
        thesaurus_data = services.get_thesaurus_data(word)
        thesaurus = services.parse_thesaurus_response(thesaurus_data)
        
        # Check for suggestions
        suggestions = []
        if results and "suggestions" in results[0]:
            suggestions = results[0]["suggestions"]
            results = []
        
        response_data = {
            "word": word,
            "results": results,
            "thesaurus": thesaurus,
            "suggestions": suggestions,
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"API error for word '{word}': {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def api_word_of_day(request):
    """
    API endpoint for word of the day.
    Returns JSON with word of the day data.
    """
    try:
        word_data = services.get_word_of_the_day()
        return JsonResponse(word_data)
    except Exception as e:
        logger.error(f"API error for word of day: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)