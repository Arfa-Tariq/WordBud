"""
Core models for WordBud - Logging and Analytics
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class SearchLog(models.Model):
    """
    Tracks all dictionary searches for analytics.
    Records both authenticated and anonymous searches.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_logs',
        help_text="User who performed the search (null for anonymous)"
    )
    word = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Word that was searched"
    )
    searched_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the search occurred"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the searcher"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent"
    )
    found = models.BooleanField(
        default=True,
        help_text="Whether the word was found in dictionary"
    )
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="API response time in milliseconds"
    )
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name = "Search Log"
        verbose_name_plural = "Search Logs"
        indexes = [
            models.Index(fields=['user', '-searched_at']),
            models.Index(fields=['word', '-searched_at']),
            models.Index(fields=['-searched_at']),
            models.Index(fields=['found', '-searched_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_str} searched '{self.word}' at {self.searched_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_popular_searches(cls, limit=10, days=30):
        """Get most popular searches in last N days"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return (
            cls.objects
            .filter(searched_at__gte=cutoff, found=True)
            .values('word')
            .annotate(count=models.Count('word'))
            .order_by('-count')[:limit]
        )
    
    @classmethod
    def get_search_stats(cls, days=30):
        """Get search statistics for dashboard"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        
        total = cls.objects.filter(searched_at__gte=cutoff).count()
        found = cls.objects.filter(searched_at__gte=cutoff, found=True).count()
        not_found = total - found
        
        return {
            'total': total,
            'found': found,
            'not_found': not_found,
            'success_rate': (found / total * 100) if total > 0 else 0
        }


class TranslationLog(models.Model):
    """
    Tracks all translation requests for analytics.
    Records language pairs and user activity.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translation_logs',
        help_text="User who performed the translation (null for anonymous)"
    )
    source_text = models.TextField(
        help_text="Original text to translate"
    )
    translated_text = models.TextField(
        help_text="Translated result"
    )
    source_language = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Source language code (e.g., 'en', 'es')"
    )
    target_language = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Target language code"
    )
    translated_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the translation occurred"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether translation was successful"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if translation failed"
    )
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Translation API response time in milliseconds"
    )
    char_count = models.IntegerField(
        default=0,
        help_text="Number of characters translated"
    )
    
    class Meta:
        ordering = ['-translated_at']
        verbose_name = "Translation Log"
        verbose_name_plural = "Translation Logs"
        indexes = [
            models.Index(fields=['user', '-translated_at']),
            models.Index(fields=['source_language', 'target_language']),
            models.Index(fields=['-translated_at']),
            models.Index(fields=['success', '-translated_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_str} translated {self.source_language}→{self.target_language} at {self.translated_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_popular_language_pairs(cls, limit=10, days=30):
        """Get most popular language pairs"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return (
            cls.objects
            .filter(translated_at__gte=cutoff, success=True)
            .values('source_language', 'target_language')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:limit]
        )
    
    @classmethod
    def get_translation_stats(cls, days=30):
        """Get translation statistics for dashboard"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        
        total = cls.objects.filter(translated_at__gte=cutoff).count()
        successful = cls.objects.filter(translated_at__gte=cutoff, success=True).count()
        failed = total - successful
        total_chars = cls.objects.filter(
            translated_at__gte=cutoff, 
            success=True
        ).aggregate(models.Sum('char_count'))['char_count__sum'] or 0
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'total_chars': total_chars
        }


class APIHealthLog(models.Model):
    """
    Tracks API health and performance.
    Records failures, response times, and availability.
    """
    API_TYPES = [
        ('dictionary', 'Dictionary API'),
        ('thesaurus', 'Thesaurus API'),
        ('translator', 'Translation API'),
        ('random_word', 'Random Word API'),
    ]
    
    api_type = models.CharField(
        max_length=20,
        choices=API_TYPES,
        db_index=True,
        help_text="Which API this log entry is for"
    )
    endpoint = models.CharField(
        max_length=255,
        help_text="API endpoint called"
    )
    status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code returned"
    )
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the API call was successful"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if call failed"
    )
    checked_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this health check occurred"
    )
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name = "API Health Log"
        verbose_name_plural = "API Health Logs"
        indexes = [
            models.Index(fields=['api_type', '-checked_at']),
            models.Index(fields=['success', '-checked_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_api_type_display()} - {self.checked_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_api_health_summary(cls, hours=24):
        """Get API health summary for dashboard"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=hours)
        
        summary = {}
        for api_type, api_name in cls.API_TYPES:
            total = cls.objects.filter(api_type=api_type, checked_at__gte=cutoff).count()
            successful = cls.objects.filter(
                api_type=api_type, 
                checked_at__gte=cutoff, 
                success=True
            ).count()
            
            avg_response = cls.objects.filter(
                api_type=api_type,
                checked_at__gte=cutoff,
                success=True,
                response_time_ms__isnull=False
            ).aggregate(models.Avg('response_time_ms'))['response_time_ms__avg']
            
            summary[api_type] = {
                'name': api_name,
                'total': total,
                'successful': successful,
                'failed': total - successful,
                'uptime': (successful / total * 100) if total > 0 else 0,
                'avg_response_ms': round(avg_response) if avg_response else None
            }
        
        return summary