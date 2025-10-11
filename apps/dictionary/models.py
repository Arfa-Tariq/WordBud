# dictionary/models.py
from django.db import models
from django.conf import settings
from apps.accounts.models import CustomUser

class UserData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    favorite_word = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.email} - {self.favorite_word}"