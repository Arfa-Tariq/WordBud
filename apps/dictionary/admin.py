"""
Django admin configuration for dictionary app.
Provides efficient management interface for favorites and search history.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import UserFavorite, SearchHistory, UserData


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    """Admin interface for user favorites with enhanced features."""
    
    list_display = ('word', 'user_email', 'created_at', 'has_notes', 'view_word_link')
    list_filter = ('created_at', 'user')
    search_fields = ('word', 'user__email', 'user__first_name', 'user__last_name', 'notes')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Word Information', {
            'fields': ('user', 'word', 'created_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email with link to user admin."""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def has_notes(self, obj):
        """Show if word has notes."""
        return bool(obj.notes)
    has_notes.boolean = True
    has_notes.short_description = 'Has Notes'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?q={obj.word}'
        return format_html('<a href="{}" target="_blank" class="button">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['export_favorites', 'delete_old_favorites']
    
    def export_favorites(self, request, queryset):
        """Export selected favorites (placeholder for CSV export)."""
        count = queryset.count()
        self.message_user(request, f'{count} favorites selected for export.')
    export_favorites.short_description = "Export selected favorites"
    
    def delete_old_favorites(self, request, queryset):
        """Delete favorites older than 1 year."""
        one_year_ago = timezone.now() - timedelta(days=365)
        old_favorites = queryset.filter(created_at__lt=one_year_ago)
        count = old_favorites.count()
        old_favorites.delete()
        self.message_user(request, f'{count} old favorites deleted.')
    delete_old_favorites.short_description = "Delete favorites older than 1 year"


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """Admin interface for search history with analytics."""
    
    list_display = ('word', 'user_email', 'searched_at', 'ip_address', 'is_recent', 'view_word_link')
    list_filter = ('searched_at', 'user')
    search_fields = ('word', 'user__email', 'ip_address', 'user_agent')
    readonly_fields = ('searched_at',)
    ordering = ('-searched_at',)
    list_per_page = 100
    date_hierarchy = 'searched_at'
    
    fieldsets = (
        ('Search Information', {
            'fields': ('user', 'word', 'searched_at')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email or 'Anonymous' for null users."""
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html('<span style="color: #999;">Anonymous</span>')
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def is_recent(self, obj):
        """Show if search was in last 24 hours."""
        return obj.searched_at >= timezone.now() - timedelta(hours=24)
    is_recent.boolean = True
    is_recent.short_description = 'Recent (24h)'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?q={obj.word}'
        return format_html('<a href="{}" target="_blank" class="button">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['export_searches', 'delete_old_searches', 'show_popular_words']
    
    def export_searches(self, request, queryset):
        """Export selected searches."""
        count = queryset.count()
        self.message_user(request, f'{count} searches selected for export.')
    export_searches.short_description = "Export selected searches"
    
    def delete_old_searches(self, request, queryset):
        """Delete searches older than 6 months."""
        six_months_ago = timezone.now() - timedelta(days=180)
        old_searches = queryset.filter(searched_at__lt=six_months_ago)
        count = old_searches.count()
        old_searches.delete()
        self.message_user(request, f'{count} old searches deleted.')
    delete_old_searches.short_description = "Delete searches older than 6 months"
    
    def show_popular_words(self, request, queryset):
        """Show most popular words in selection."""
        popular = (
            queryset
            .values('word')
            .annotate(count=Count('word'))
            .order_by('-count')[:10]
        )
        words_list = ', '.join([f"{item['word']} ({item['count']})" for item in popular])
        self.message_user(request, f'Top words: {words_list}')
    show_popular_words.short_description = "Show popular words in selection"


@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    """Admin interface for legacy user data (favorites)."""
    
    list_display = ('favorite_word', 'user_email', 'created_at', 'view_word_link', 'migrate_action')
    list_filter = ('user', 'created_at')
    search_fields = ('favorite_word', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    list_per_page = 50
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def user_email(self, obj):
        """Display user email with link."""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?q={obj.favorite_word}'
        return format_html('<a href="{}" target="_blank" class="button">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def migrate_action(self, obj):
        """Button to migrate to new favorites model."""
        return format_html(
            '<a class="button" href="#" onclick="alert(\'Use bulk action to migrate\'); return false;">Migrate</a>'
        )
    migrate_action.short_description = 'Migrate'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['migrate_to_favorites']
    
    def migrate_to_favorites(self, request, queryset):
        """Migrate legacy favorites to new UserFavorite model."""
        migrated_count = 0
        skipped_count = 0
        
        for legacy_item in queryset:
            favorite = legacy_item.migrate_to_favorite()
            if favorite:
                migrated_count += 1
            else:
                skipped_count += 1
        
        self.message_user(
            request,
            f'Migrated {migrated_count} favorites. Skipped {skipped_count} (already exist).'
        )
    migrate_to_favorites.short_description = "Migrate to new UserFavorite model"


# Custom admin site configuration
admin.site.site_header = "WordBud Dictionary Admin"
admin.site.site_title = "WordBud Admin"
admin.site.index_title = "Dictionary Management Dashboard"


# Admin dashboard customization
class DashboardStats:
    """Helper class for dashboard statistics."""
    
    @staticmethod
    def get_stats():
        """Get key statistics for admin dashboard."""
        today = timezone.now()
        last_24h = today - timedelta(hours=24)
        last_7d = today - timedelta(days=7)
        
        return {
            'total_favorites': UserFavorite.objects.count(),
            'total_searches': SearchHistory.objects.count(),
            'searches_24h': SearchHistory.objects.filter(searched_at__gte=last_24h).count(),
            'searches_7d': SearchHistory.objects.filter(searched_at__gte=last_7d).count(),
            'unique_users_searched': SearchHistory.objects.filter(user__isnull=False).values('user').distinct().count(),
            'popular_words': SearchHistory.get_popular_words(limit=5),
        }
