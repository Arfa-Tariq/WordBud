from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.game_hub, name='game_hub'),
    path('word-guess/', views.word_guess, name='word_guess'),
    path('word-scramble/', views.word_scramble, name='word_scramble'),
    path('synonym-match/', views.synonym_match, name='synonym_match'),
    path('meaning-quiz/', views.meaning_quiz, name='meaning_quiz'),
]
