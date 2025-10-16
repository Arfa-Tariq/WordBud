"""
Django admin configuration for dictionary app.
Provides efficient management interface for favorites and search history.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import UserFavorite, SearchHistory, UserData


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    """Admin interface for user favorites."""
    
    list_display = ('user_email', 'word', 'created_at', 'view_word_link')
    list_filter = ('created_at', 'user')
    search_fields = ('word', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 50
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?word={obj.word}'
        return format_html('<a href="{}" target="_blank">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """Admin interface for search history."""
    
    list_display = ('word', 'user_email', 'searched_at', 'ip_address', 'view_word_link')
    list_filter = ('searched_at', 'user')
    search_fields = ('word', 'user__email', 'ip_address')
    readonly_fields = ('searched_at',)
    ordering = ('-searched_at',)
    list_per_page = 100
    
    def user_email(self, obj):
        """Display user email or 'Anonymous' for null users."""
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?word={obj.word}'
        return format_html('<a href="{}" target="_blank">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    """Admin interface for legacy user data (favorites)."""
    
    list_display = ('user_email', 'favorite_word', 'view_word_link')
    list_filter = ('user',)
    search_fields = ('favorite_word', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__email', 'favorite_word')
    list_per_page = 50
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        url = reverse('dictionary:dictionary') + f'?word={obj.favorite_word}'
        return format_html('<a href="{}" target="_blank">View Word</a>', url)
    view_word_link.short_description = 'Dictionary Link'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


# Custom admin actions
def export_popular_words(modeladmin, request, queryset):
    """Export most popular searched words."""
    # This could be expanded to generate CSV/Excel exports
    pass
export_popular_words.short_description = "Export popular words"


# Add custom admin site configuration
admin.site.site_header = "WordBud Dictionary Admin"
admin.site.site_title = "WordBud Admin"
admin.site.index_title = "Dictionary Management"
