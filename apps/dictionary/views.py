"""
Dictionary views for WordBud.
Handles web requests and API endpoints with robust error handling.
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
import logging

from . import services
from .models import UserFavorite, SearchHistory

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_user_agent(request):
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')[:255]


def word_lookup(request):
    """
    Main word lookup view with comprehensive data display.
    Handles search queries and displays all available word information.
    """
    word = request.GET.get("q", "").strip()
    context = {
        "word": word,
        "results": [],
        "thesaurus": {},
        "error": None,
        "suggestions": [],
        "word_of_day": None,
        "is_favorite": False,
    }
    
    # Get word of the day for homepage
    if not word:
        try:
            context["word_of_day"] = services.get_word_of_the_day()
        except Exception as e:
            logger.error(f"Error fetching word of the day: {str(e)}")
    
    # Handle word search
    if word:
        try:
            # Use comprehensive search service
            search_result = services.search_word_comprehensive(word)
            
            context.update({
                "results": search_result.get("dictionary_results", []),
                "thesaurus": search_result.get("thesaurus", {}),
                "error": search_result.get("error"),
                "suggestions": search_result.get("suggestions", []),
            })
            
            # Record search history if results found
            if search_result.get("found"):
                try:
                    if request.user.is_authenticated:
                        SearchHistory.objects.create(
                            user=request.user,
                            word=word.lower(),
                            ip_address=get_client_ip(request),
                            user_agent=get_user_agent(request)
                        )
                    else:
                        SearchHistory.objects.create(
                            word=word.lower(),
                            ip_address=get_client_ip(request),
                            user_agent=get_user_agent(request)
                        )
                except Exception as e:
                    logger.warning(f"Failed to record search history: {str(e)}")
                
                # Check if word is in favorites
                if request.user.is_authenticated:
                    try:
                        context["is_favorite"] = UserFavorite.objects.filter(
                            user=request.user,
                            word=word.lower()
                        ).exists()
                    except Exception as e:
                        logger.warning(f"Failed to check favorite status: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error processing word lookup for '{word}': {str(e)}")
            context["error"] = "An error occurred while processing your request."
    
    return render(request, "dictionary/searchword.html", context)


def random_word_view(request):
    """Redirect to a random word search."""
    try:
        word = services.get_random_word()
        return redirect(f'/dictionary/?q={word}')
    except Exception as e:
        logger.error(f"Error generating random word: {str(e)}")
        return redirect('dictionary:dictionary')


@require_http_methods(["POST"])
def word_of_day_refresh(request):
    """Force refresh the word of the day cache."""
    from datetime import date
    from django.core.cache import cache
    
    try:
        today = date.today().isoformat()
        cache.delete(f"word_of_day_{today}")
        logger.info("Word of the day cache refreshed")
    except Exception as e:
        logger.error(f"Error refreshing word of the day: {str(e)}")
    
    return redirect("dictionary:dictionary")


@login_required
@require_http_methods(["POST"])
def add_to_favorites(request):
    """Add a word to user's favorites via AJAX."""
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
    """Remove a word from user's favorites via AJAX."""
    word = request.POST.get("word", "").strip().lower()
    
    if not word:
        return JsonResponse({"success": False, "error": "No word provided"}, status=400)
    
    try:
        deleted_count, _ = UserFavorite.objects.filter(
            user=request.user,
            word=word
        ).delete()
        
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
    """Display user's favorite words with pagination."""
    try:
        favorites_qs = UserFavorite.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(favorites_qs, 20)  # 20 favorites per page
        
        try:
            favorites = paginator.page(page)
        except PageNotAnInteger:
            favorites = paginator.page(1)
        except EmptyPage:
            favorites = paginator.page(paginator.num_pages)
        
        context = {
            "favorites": favorites,
        }
    except Exception as e:
        logger.error(f"Error fetching favorites for user {request.user.id}: {str(e)}")
        context = {
            "favorites": [],
            "error": "Failed to load favorites"
        }
    
    return render(request, "dictionary/favorites.html", context)


@login_required
def search_history(request):
    """Display user's search history with pagination."""
    try:
        history_qs = SearchHistory.objects.filter(user=request.user).order_by('-searched_at')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(history_qs, 50)  # 50 entries per page
        
        try:
            history = paginator.page(page)
        except PageNotAnInteger:
            history = paginator.page(1)
        except EmptyPage:
            history = paginator.page(paginator.num_pages)
        
        # Get popular searches (top 10)
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
    except Exception as e:
        logger.error(f"Error fetching search history for user {request.user.id}: {str(e)}")
        context = {
            "history": [],
            "popular_words": [],
            "error": "Failed to load search history"
        }
    
    return render(request, "dictionary/history.html", context)


# API Endpoints
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
        result = services.search_word_comprehensive(word)
        
        response_data = {
            "word": word,
            "found": result.get("found", False),
            "results": result.get("dictionary_results", []),
            "thesaurus": result.get("thesaurus", {}),
            "suggestions": result.get("suggestions", []),
            "error": result.get("error")
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