"""
Dictionary models for WordBud.
Lightweight models focusing only on essential user data.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class UserFavorite(models.Model):
    """
    Stores user's favorite words.
    Lightweight model for fast queries and minimal database load.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_words'
    )
    word = models.CharField(
        max_length=100,
        db_index=True,  # Index for fast lookups
        help_text="The favorite word (stored in lowercase)"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True  # Index for ordering
    )
    
    class Meta:
        unique_together = ('user', 'word')  # Prevent duplicates
        ordering = ['-created_at']  # Most recent first
        indexes = [
            models.Index(fields=['user', '-created_at']),  # Composite index for user favorites
        ]
    
    def save(self, *args, **kwargs):
        # Always store words in lowercase for consistency
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.word}"


class SearchHistory(models.Model):
    """
    Optional model to track user search history.
    Can be used for analytics and personalization.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_history',
        null=True,
        blank=True  # Allow anonymous searches
    )
    word = models.CharField(
        max_length=100,
        db_index=True
    )
    searched_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="For anonymous user tracking"
    )
    
    class Meta:
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', '-searched_at']),
            models.Index(fields=['word', '-searched_at']),
        ]
    
    def save(self, *args, **kwargs):
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        user_str = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_str} searched '{self.word}'"


# Legacy model for backward compatibility
class UserData(models.Model):
    """
    Legacy model - kept for backward compatibility.
    New code should use UserFavorite instead.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    favorite_word = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.user.email} - {self.favorite_word}"