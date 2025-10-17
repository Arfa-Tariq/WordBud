from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    path('', views.word_lookup, name='dictionary'),
    path('search/', views.word_lookup, name='search'),
    path('random/', views.random_word_view, name='random_word'),
    path('word-of-day/refresh/', views.word_of_day_refresh, name='word_of_day_refresh'),
]
