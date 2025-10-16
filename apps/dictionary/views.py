"""
Dictionary views for WordBud.
High-performance, API-driven dictionary functionality with caching and error handling.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
import logging

from .services import (
    DictionaryService, 
    WordOfTheDayService, 
    RandomWordService, 
    FavoritesService
)
from .models import UserFavorite, SearchHistory, UserData

logger = logging.getLogger(__name__)


def search_word(request):
    """
    Render the main search page.
    Shows search form and word of the day.
    """
    # Get word of the day for the search page
    word_of_day = WordOfTheDayService.get_word_of_the_day()
    
    context = {
        'word_of_day': word_of_day,
        'page_title': 'Dictionary Search'
    }
    
    return render(request, "dictionary/search.html", context)


def dictionary_view(request):
    """
    Main dictionary lookup view.
    Handles word searches and displays comprehensive word information.
    """
    word = request.GET.get("word", "").strip()
    context = {
        'word': word,
        'page_title': f'Dictionary - {word.title()}' if word else 'Dictionary'
    }
    
    if word:
        try:
            # Get comprehensive word data
            word_data = DictionaryService.get_word_definition(word)
            context['data'] = word_data
            
            # Track search history (optional)
            if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    SearchHistory.objects.create(
                        user=request.user,
                        word=word,
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                except Exception:
                    pass  # Silently fail if search history can't be saved
            
            # Check if word is in user's favorites
            if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    context['is_favorite'] = FavoritesService.is_favorite(request.user, word)
                except Exception:
                    context['is_favorite'] = False
            
        except Exception as e:
            logger.error(f"Error fetching word data for '{word}': {e}")
            try:
                messages.error(request, f"Sorry, we couldn't find information for '{word}'. Please try another word.")
            except Exception:
                pass  # Silently fail if messages can't be added
            context['error'] = True
    
    # Always include word of the day
    try:
        word_of_day = WordOfTheDayService.get_word_of_the_day()
        context['word_of_day'] = word_of_day
    except Exception as e:
        logger.error(f"Error fetching word of the day: {e}")
        context['word_of_day'] = {
            'word': 'serendipity',
            'definition': 'The occurrence and development of events by chance in a happy or beneficial way.'
        }
    
    return render(request, "dictionary/searchword.html", context)


@require_http_methods(["GET"])
def random_word_view(request):
    """
    Get a random word with definition.
    Can be called via AJAX for dynamic updates.
    """
    try:
        random_data = RandomWordService.get_random_word()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - return JSON
            return JsonResponse(random_data)
        else:
            # Regular request - redirect to dictionary view
            return redirect(f"{reverse('dictionary:dictionary')}?word={random_data['word']}")
            
    except Exception as e:
        logger.error(f"Error getting random word: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Failed to get random word'}, status=500)
        else:
            try:
                messages.error(request, "Sorry, couldn't get a random word right now.")
            except Exception:
                pass
            return redirect('dictionary:search')


@login_required
@require_http_methods(["POST"])
def add_favorite(request, word):
    """
    Add a word to user's favorites.
    Handles both AJAX and regular form submissions.
    """
    try:
        with transaction.atomic():
            created = FavoritesService.add_favorite(request.user, word)
            
            if created:
                message = f'"{word.title()}" added to your favorites!'
                try:
                    messages.success(request, message)
                except Exception:
                    pass
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': message,
                        'is_favorite': True
                    })
            else:
                message = f'"{word.title()}" is already in your favorites.'
                try:
                    messages.info(request, message)
                except Exception:
                    pass
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': message,
                        'is_favorite': True
                    })
                    
    except Exception as e:
        logger.error(f"Error adding favorite '{word}' for user {request.user}: {e}")
        message = "Sorry, couldn't add to favorites right now."
        try:
            messages.error(request, message)
        except Exception:
            pass
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message}, status=500)
    
    # Redirect back to the referring page or dictionary view
    return redirect(request.META.get('HTTP_REFERER', reverse('dictionary:dictionary')))


@login_required
@require_http_methods(["POST"])
def remove_favorite(request, word):
    """
    Remove a word from user's favorites.
    """
    try:
        with transaction.atomic():
            removed = FavoritesService.remove_favorite(request.user, word)
            
            if removed:
                message = f'"{word.title()}" removed from your favorites.'
                try:
                    messages.success(request, message)
                except Exception:
                    pass
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': message,
                        'is_favorite': False
                    })
            else:
                message = f'"{word.title()}" was not in your favorites.'
                try:
                    messages.info(request, message)
                except Exception:
                    pass
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': message,
                        'is_favorite': False
                    })
                    
    except Exception as e:
        logger.error(f"Error removing favorite '{word}' for user {request.user}: {e}")
        message = "Sorry, couldn't remove from favorites right now."
        try:
            messages.error(request, message)
        except Exception:
            pass
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message}, status=500)
    
    return redirect(request.META.get('HTTP_REFERER', reverse('dictionary:favorites_list')))


@login_required
def favorites_list(request):
    """
    Display user's favorite words with pagination.
    """
    favorites_queryset = FavoritesService.get_user_favorites(request.user)
    
    # Pagination
    paginator = Paginator(favorites_queryset, 20)  # 20 favorites per page
    page_number = request.GET.get('page')
    favorites_page = paginator.get_page(page_number)
    
    context = {
        'favorites': favorites_page,
        'page_title': 'My Favorite Words'
    }
    
    return render(request, 'dictionary/favorites.html', context)


@login_required
def search_history(request):
    """
    Display user's search history with pagination.
    Optional feature for user engagement.
    """
    history_queryset = SearchHistory.objects.filter(user=request.user)
    
    # Pagination
    paginator = Paginator(history_queryset, 50)  # 50 searches per page
    page_number = request.GET.get('page')
    history_page = paginator.get_page(page_number)
    
    context = {
        'history': history_page,
        'page_title': 'Search History'
    }
    
    return render(request, 'dictionary/history.html', context)


def word_of_day_refresh(request):
    """
    Force refresh the word of the day.
    Useful for admin or testing purposes.
    """
    try:
        from django.core.cache import cache
        cache.delete("word_of_the_day")
        
        word_of_day = WordOfTheDayService.get_word_of_the_day()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(word_of_day)
        else:
            try:
                messages.success(request, "Word of the day refreshed!")
            except Exception:
                pass
            return redirect('dictionary:search')
            
    except Exception as e:
        logger.error(f"Error refreshing word of the day: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Failed to refresh word of the day'}, status=500)
        else:
            try:
                messages.error(request, "Sorry, couldn't refresh word of the day.")
            except Exception:
                pass
            return redirect('dictionary:search')


# API Views for potential future mobile app or AJAX calls
def api_word_lookup(request, word):
    """
    API endpoint for word lookup.
    Returns JSON data for the word.
    """
    try:
        word_data = DictionaryService.get_word_definition(word)
        return JsonResponse(word_data)
    except Exception as e:
        logger.error(f"API word lookup failed for '{word}': {e}")
        return JsonResponse({'error': 'Word lookup failed'}, status=500)


def api_word_of_day(request):
    """
    API endpoint for word of the day.
    """
    try:
        word_of_day = WordOfTheDayService.get_word_of_the_day()
        return JsonResponse(word_of_day)
    except Exception as e:
        logger.error(f"API word of day failed: {e}")
        return JsonResponse({'error': 'Word of day lookup failed'}, status=500)
