"""
Django admin configuration for Core app - Analytics and Logging
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import SearchLog, TranslationLog, APIHealthLog


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    """Admin interface for search logs with analytics features."""
    
    list_display = (
        'word', 
        'user_display', 
        'searched_at', 
        'found_status',
        'response_time_display',
        'view_word_link'
    )
    list_filter = (
        'found',
        'searched_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('word', 'user__email', 'ip_address')
    readonly_fields = ('searched_at',)
    date_hierarchy = 'searched_at'
    list_per_page = 50
    ordering = ('-searched_at',)
    
    fieldsets = (
        ('Search Details', {
            'fields': ('word', 'user', 'searched_at', 'found')
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'user_agent', 'response_time_ms'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        """Display user email with link or 'Anonymous'."""
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html('<span style="color: #999;">Anonymous ({})</span>', obj.ip_address)
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__email'
    
    def found_status(self, obj):
        """Visual indicator for found/not found."""
        if obj.found:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Found</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Not Found</span>'
        )
    found_status.short_description = 'Status'
    found_status.admin_order_field = 'found'
    
    def response_time_display(self, obj):
        """Display response time with color coding."""
        if obj.response_time_ms is None:
            return '-'
        
        time_ms = obj.response_time_ms
        if time_ms < 500:
            color = 'green'
        elif time_ms < 1500:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} ms</span>',
            color, time_ms
        )
    response_time_display.short_description = 'Response Time'
    response_time_display.admin_order_field = 'response_time_ms'
    
    def view_word_link(self, obj):
        """Link to view word in dictionary."""
        from django.urls import reverse
        url = reverse('dictionary:dictionary') + f'?q={obj.word}'
        return format_html(
            '<a href="{}" target="_blank" class="button">View Word</a>',
            url
        )
    view_word_link.short_description = 'Dictionary'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['export_searches', 'delete_old_logs']
    
    def export_searches(self, request, queryset):
        """Export selected searches (placeholder for CSV export)."""
        count = queryset.count()
        self.message_user(request, f'{count} search logs selected for export.')
    export_searches.short_description = "Export selected searches"
    
    def delete_old_logs(self, request, queryset):
        """Delete logs older than 90 days."""
        ninety_days_ago = timezone.now() - timedelta(days=90)
        old_logs = queryset.filter(searched_at__lt=ninety_days_ago)
        count = old_logs.count()
        old_logs.delete()
        self.message_user(request, f'{count} old search logs deleted.')
    delete_old_logs.short_description = "Delete logs older than 90 days"


@admin.register(TranslationLog)
class TranslationLogAdmin(admin.ModelAdmin):
    """Admin interface for translation logs with language analytics."""
    
    list_display = (
        'language_pair_display',
        'user_display',
        'translated_at',
        'success_status',
        'char_count_display',
        'response_time_display'
    )
    list_filter = (
        'success',
        'source_language',
        'target_language',
        'translated_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'source_text',
        'translated_text',
        'user__email',
        'ip_address'
    )
    readonly_fields = ('translated_at', 'char_count')
    date_hierarchy = 'translated_at'
    list_per_page = 50
    ordering = ('-translated_at',)
    
    fieldsets = (
        ('Translation Details', {
            'fields': (
                'user',
                'source_language',
                'target_language',
                'translated_at',
                'success'
            )
        }),
        ('Content', {
            'fields': ('source_text', 'translated_text', 'char_count'),
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'response_time_ms', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def language_pair_display(self, obj):
        """Display language pair with flags."""
        return format_html(
            '<strong>{}</strong> → <strong>{}</strong>',
            obj.source_language.upper(),
            obj.target_language.upper()
        )
    language_pair_display.short_description = 'Language Pair'
    language_pair_display.admin_order_field = 'source_language'
    
    def user_display(self, obj):
        """Display user email with link or 'Anonymous'."""
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html(
            '<span style="color: #999;">Anonymous ({})</span>',
            obj.ip_address
        )
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__email'
    
    def success_status(self, obj):
        """Visual indicator for success/failure."""
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Success</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Failed</span>'
        )
    success_status.short_description = 'Status'
    success_status.admin_order_field = 'success'
    
    def char_count_display(self, obj):
        """Display character count with formatting."""
        return format_html(
            '<span style="color: #666;">{} chars</span>',
            obj.char_count
        )
    char_count_display.short_description = 'Characters'
    char_count_display.admin_order_field = 'char_count'
    
    def response_time_display(self, obj):
        """Display response time with color coding."""
        if obj.response_time_ms is None:
            return '-'
        
        time_ms = obj.response_time_ms
        if time_ms < 1000:
            color = 'green'
        elif time_ms < 3000:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} ms</span>',
            color, time_ms
        )
    response_time_display.short_description = 'Response Time'
    response_time_display.admin_order_field = 'response_time_ms'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['export_translations', 'delete_old_logs']
    
    def export_translations(self, request, queryset):
        """Export selected translations."""
        count = queryset.count()
        self.message_user(request, f'{count} translation logs selected for export.')
    export_translations.short_description = "Export selected translations"
    
    def delete_old_logs(self, request, queryset):
        """Delete logs older than 90 days."""
        ninety_days_ago = timezone.now() - timedelta(days=90)
        old_logs = queryset.filter(translated_at__lt=ninety_days_ago)
        count = old_logs.count()
        old_logs.delete()
        self.message_user(request, f'{count} old translation logs deleted.')
    delete_old_logs.short_description = "Delete logs older than 90 days"


@admin.register(APIHealthLog)
class APIHealthLogAdmin(admin.ModelAdmin):
    """Admin interface for API health monitoring."""
    
    list_display = (
        'api_type_display',
        'checked_at',
        'status_display',
        'status_code_display',
        'response_time_display'
    )
    list_filter = (
        'api_type',
        'success',
        'checked_at',
    )
    search_fields = ('endpoint', 'error_message')
    readonly_fields = ('checked_at',)
    date_hierarchy = 'checked_at'
    list_per_page = 100
    ordering = ('-checked_at',)
    
    fieldsets = (
        ('API Details', {
            'fields': ('api_type', 'endpoint', 'checked_at')
        }),
        ('Response Info', {
            'fields': ('success', 'status_code', 'response_time_ms')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def api_type_display(self, obj):
        """Display API type with icon."""
        icons = {
            'dictionary': '📖',
            'thesaurus': '📚',
            'translator': '🌐',
            'random_word': '🎲'
        }
        icon = icons.get(obj.api_type, '🔧')
        return format_html(
            '{} <strong>{}</strong>',
            icon,
            obj.get_api_type_display()
        )
    api_type_display.short_description = 'API Type'
    api_type_display.admin_order_field = 'api_type'
    
    def status_display(self, obj):
        """Visual indicator for API status."""
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Healthy</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Failed</span>'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'success'
    
    def status_code_display(self, obj):
        """Display HTTP status code with color."""
        if obj.status_code is None:
            return '-'
        
        code = obj.status_code
        if 200 <= code < 300:
            color = 'green'
        elif 300 <= code < 400:
            color = 'blue'
        elif 400 <= code < 500:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, code
        )
    status_code_display.short_description = 'HTTP Status'
    status_code_display.admin_order_field = 'status_code'
    
    def response_time_display(self, obj):
        """Display response time with color coding."""
        if obj.response_time_ms is None:
            return '-'
        
        time_ms = obj.response_time_ms
        if time_ms < 1000:
            color = 'green'
        elif time_ms < 3000:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} ms</span>',
            color, time_ms
        )
    response_time_display.short_description = 'Response Time'
    response_time_display.admin_order_field = 'response_time_ms'
    
    actions = ['delete_old_logs']
    
    def delete_old_logs(self, request, queryset):
        """Delete logs older than 7 days."""
        seven_days_ago = timezone.now() - timedelta(days=7)
        old_logs = queryset.filter(checked_at__lt=seven_days_ago)
        count = old_logs.count()
        old_logs.delete()
        self.message_user(request, f'{count} old API health logs deleted.')
    delete_old_logs.short_description = "Delete logs older than 7 days"


# Customize admin site headers
admin.site.site_header = "WordBud Administration"
admin.site.site_title = "WordBud Admin Portal"
admin.site.index_title = "Welcome to WordBud Admin Dashboard"