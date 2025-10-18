"""
URL configuration for dictionary app.
Clean, organized routes for all dictionary features.
"""

from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Main views
    path('', views.word_lookup, name='dictionary'),
    path('search/', views.word_lookup, name='search'),
    path('random/', views.random_word_view, name='random_word'),
    path('word-of-day/refresh/', views.word_of_day_refresh, name='word_of_day_refresh'),
    
    # Favorites
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/add/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/', views.remove_from_favorites, name='remove_from_favorites'),
    
    # Search history
    path('history/', views.search_history, name='search_history'),
    
    # API endpoints (unchanged for backward compatibility)
    path('api/lookup/', views.api_word_lookup, name='api_word_lookup'),
    path('api/word-of-day/', views.api_word_of_day, name='api_word_of_day'),
]