"""
Enhanced Django admin for user management with activity tracking.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import CustomUser
# apps/accounts/admin.py
from django.utils.html import format_html

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Enhanced user admin with activity summary and management tools."""
    
    model = CustomUser
    
    list_display = (
        'email',
        'username',
        'activity_summary',
        'is_active_status',
        'is_staff',
        'is_superuser',
        'last_login_display'
    )
    
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'last_login',
    )
    
    search_fields = ('email', 'username')
    
    ordering = ('-last_login',)
    
    fieldsets = (
        ('Account Info', {
            'fields': ('email', 'username', 'password')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        ('Important Dates', {
            'fields': ('last_login',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login',)
    list_display = ('email', 'get_full_name', 'profile_image_thumbnail', 'is_active', 'date_joined')
    
    def profile_image_thumbnail(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />', obj.profile_image.url)
        return '—'
    profile_image_thumbnail.short_description = 'Profile Picture'

    def activity_summary(self, obj):
        """Display user activity summary with links."""
        
        # Count favorites
        favorites_count = obj.favorite_words.count()
        
        # Count search logs
        search_logs_count = obj.search_logs.count() if hasattr(obj, 'search_logs') else 0
        
        # Count translation logs
        translation_logs_count = obj.translation_logs.count() if hasattr(obj, 'translation_logs') else 0
        
        # Build summary HTML
        summary_parts = []
        
        if favorites_count > 0:
            fav_url = reverse('admin:dictionary_userfavorite_changelist') + f'?user__id__exact={obj.id}'
            summary_parts.append(
                format_html(
                    '⭐ <a href="{}">{} favorites</a>',
                    fav_url, favorites_count
                )
            )
        
        if search_logs_count > 0:
            search_url = reverse('admin:core_searchlog_changelist') + f'?user__id__exact={obj.id}'
            summary_parts.append(
                format_html(
                    '🔍 <a href="{}">{} searches</a>',
                    search_url, search_logs_count
                )
            )
        
        if translation_logs_count > 0:
            trans_url = reverse('admin:core_translationlog_changelist') + f'?user__id__exact={obj.id}'
            summary_parts.append(
                format_html(
                    '🌐 <a href="{}">{} translations</a>',
                    trans_url, translation_logs_count
                )
            )
        
        if not summary_parts:
            return format_html('<span style="color: #999;">No activity yet</span>')
        
        return format_html(' | '.join(summary_parts))
    
    activity_summary.short_description = 'User Activity'
    
    def is_active_status(self, obj):
        """Visual indicator for active/inactive status."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
        )
    is_active_status.short_description = 'Status'
    is_active_status.admin_order_field = 'is_active'
    
    def last_login_display(self, obj):
        """Display last login with relative time."""
        if obj.last_login:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            diff = now - obj.last_login
            
            if diff < timedelta(hours=1):
                time_str = 'Just now'
                color = 'green'
            elif diff < timedelta(days=1):
                hours = int(diff.total_seconds() / 3600)
                time_str = f'{hours}h ago'
                color = 'green'
            elif diff < timedelta(days=7):
                days = diff.days
                time_str = f'{days}d ago'
                color = 'orange'
            elif diff < timedelta(days=30):
                weeks = diff.days // 7
                time_str = f'{weeks}w ago'
                color = 'orange'
            else:
                months = diff.days // 30
                time_str = f'{months}mo ago'
                color = 'red'

