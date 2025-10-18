"""
Dictionary models for WordBud.
Lightweight models focusing only on essential user data.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator


class UserFavorite(models.Model):
    """
    Stores user's favorite words.
    Lightweight model for fast queries and minimal database load.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_words',
        db_index=True
    )
    word = models.CharField(
        max_length=100,
        db_index=True,
        validators=[MinLengthValidator(1)],
        help_text="The favorite word (stored in lowercase)"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this word"
    )
    
    class Meta:
        unique_together = ('user', 'word')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['word']),
        ]
        verbose_name = "User Favorite"
        verbose_name_plural = "User Favorites"
    
    def save(self, *args, **kwargs):
        """Normalize word to lowercase before saving."""
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.word}"


class SearchHistory(models.Model):
    """
    Track user search history for analytics and personalization.
    Supports both authenticated and anonymous users.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_history',
        null=True,
        blank=True,
        db_index=True
    )
    word = models.CharField(
        max_length=100,
        db_index=True,
        validators=[MinLengthValidator(1)]
    )
    searched_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address for anonymous tracking"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent string"
    )
    
    class Meta:
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', '-searched_at']),
            models.Index(fields=['word', '-searched_at']),
            models.Index(fields=['ip_address', '-searched_at']),
        ]
        verbose_name = "Search History"
        verbose_name_plural = "Search Histories"
    
    def save(self, *args, **kwargs):
        """Normalize word to lowercase before saving."""
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        user_str = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_str} searched '{self.word}' at {self.searched_at}"
    
    @classmethod
    def get_popular_words(cls, limit=10, user=None):
        """
        Get most searched words.
        
        Args:
            limit: Number of words to return
            user: Filter by specific user (optional)
        
        Returns:
            QuerySet with word and count
        """
        queryset = cls.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        return (
            queryset
            .values('word')
            .annotate(count=models.Count('word'))
            .order_by('-count')[:limit]
        )
    
    @classmethod
    def get_recent_searches(cls, user=None, limit=50):
        """
        Get recent search history.
        
        Args:
            user: Filter by specific user (optional)
            limit: Number of records to return
        
        Returns:
            QuerySet of recent searches
        """
        queryset = cls.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset.order_by('-searched_at')[:limit]


class UserData(models.Model):
    """
    Legacy model - kept for backward compatibility.
    New code should use UserFavorite instead.
    
    This model may be deprecated in future versions.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='legacy_data'
    )
    favorite_word = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(1)]
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this favorite was added"
    )
    
    class Meta:
        verbose_name = "User Data (Legacy)"
        verbose_name_plural = "User Data (Legacy)"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Normalize word to lowercase before saving."""
        self.favorite_word = self.favorite_word.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.favorite_word}"
    
    def migrate_to_favorite(self):
        """
        Migrate this legacy favorite to the new UserFavorite model.
        Returns the created UserFavorite instance or None if already exists.
        """
        favorite, created = UserFavorite.objects.get_or_create(
            user=self.user,
            word=self.favorite_word,
            defaults={'created_at': self.created_at}
        )
        return favorite if created else None