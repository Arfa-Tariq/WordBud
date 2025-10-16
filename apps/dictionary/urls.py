"""
URL configuration for dictionary app.
Provides clean, RESTful URLs for all dictionary functionality.
"""

from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Main dictionary views
    path('', views.dictionary_view, name='dictionary'),
    path('search/', views.search_word, name='search'),
    
    # Random word functionality
    path('random/', views.random_word_view, name='random_word'),
    
    # Word of the day
    path('word-of-day/refresh/', views.word_of_day_refresh, name='word_of_day_refresh'),
    
    # Favorites management
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/add/<str:word>/', views.add_favorite, name='add_favorite'),
    path('favorites/remove/<str:word>/', views.remove_favorite, name='remove_favorite'),
    
    # Search history (optional feature)
    path('history/', views.search_history, name='search_history'),
    
    # API endpoints for AJAX calls or future mobile app
    path('api/word/<str:word>/', views.api_word_lookup, name='api_word_lookup'),
    path('api/word-of-day/', views.api_word_of_day, name='api_word_of_day'),
]
