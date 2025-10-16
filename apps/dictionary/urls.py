from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_word, name="search"),
    path('', views.dictionary_view, name='dictionary'),
    path('add-favorite/<str:word>/', views.add_favorite, name='add_favorite'),
    path('favorites/', views.favorites_list, name='favorites_list'), 
    path('favorites/remove/<str:word>/', views.remove_favorite, name='remove_favorite'),
    path('random/', views.random_word_view, name='random'),
    path('wotd/refresh/', views.refresh_wotd, name='refresh_wotd'),

]
