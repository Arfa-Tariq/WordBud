"""
Custom Admin Dashboard for WordBud Analytics
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Sum
from datetime import timedelta
from apps.core.models import SearchLog, TranslationLog, APIHealthLog
from apps.dictionary.models import UserFavorite, SearchHistory
from apps.accounts.models import CustomUser
from django.contrib import admin

@staff_member_required
def admin_dashboard(request):
    """
    Custom admin dashboard with comprehensive analytics.
    Shows user activity, API health, and system statistics.
    """
    
    # Get time range from request (default to 30 days)
    days = int(request.GET.get('days', 30))
    cutoff = timezone.now() - timedelta(days=days)
    
    # === USER STATISTICS ===
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    recent_signups = CustomUser.objects.filter(
        last_login__isnull=False,
        last_login__gte=cutoff
    ).count()
    
    # Users who logged in recently
    active_last_7d = CustomUser.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # === SEARCH STATISTICS ===
    search_stats = SearchLog.get_search_stats(days=days)
    popular_searches = SearchLog.get_popular_searches(limit=10, days=days)
    
    # Search trends (last 7 days, daily)
    search_trends = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = SearchLog.objects.filter(
            searched_at__gte=day_start,
            searched_at__lte=day_end
        ).count()
        
        search_trends.insert(0, {
            'date': day_start.strftime('%m/%d'),
            'count': count
        })
    
    # === TRANSLATION STATISTICS ===
    translation_stats = TranslationLog.get_translation_stats(days=days)
    popular_lang_pairs = TranslationLog.get_popular_language_pairs(limit=10, days=days)
    
    # Translation trends (last 7 days, daily)
    translation_trends = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = TranslationLog.objects.filter(
            translated_at__gte=day_start,
            translated_at__lte=day_end
        ).count()
        
        translation_trends.insert(0, {
            'date': day_start.strftime('%m/%d'),
            'count': count
        })
    
    # === FAVORITES STATISTICS ===
    total_favorites = UserFavorite.objects.count()
    favorites_last_30d = UserFavorite.objects.filter(
        created_at__gte=cutoff
    ).count()
    
    # Most favorited words
    most_favorited = UserFavorite.objects.values('word').annotate(
        count=Count('word')
    ).order_by('-count')[:10]
    
    # === API HEALTH ===
    api_health = APIHealthLog.get_api_health_summary(hours=24)
    
    # Recent API failures
    recent_failures = APIHealthLog.objects.filter(
        success=False,
        checked_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-checked_at')[:10]
    
    # === CACHE STATISTICS ===
    cache_stats = get_cache_stats()
    
    # === SYSTEM PERFORMANCE ===
    # Average response times
    avg_search_time = SearchLog.objects.filter(
        searched_at__gte=cutoff,
        response_time_ms__isnull=False
    ).aggregate(Avg('response_time_ms'))['response_time_ms__avg']
    
    avg_translation_time = TranslationLog.objects.filter(
        translated_at__gte=cutoff,
        response_time_ms__isnull=False
    ).aggregate(Avg('response_time_ms'))['response_time_ms__avg']
    
    # === TOP USERS BY ACTIVITY ===
    top_searchers = CustomUser.objects.annotate(
        search_count=Count('search_logs')
    ).filter(search_count__gt=0).order_by('-search_count')[:5]
    
    top_translators = CustomUser.objects.annotate(
        translation_count=Count('translation_logs')
    ).filter(translation_count__gt=0).order_by('-translation_count')[:5]
    
    # === PREPARE CONTEXT ===
    context = {
        'days': days,
        
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'recent_signups': recent_signups,
        'active_last_7d': active_last_7d,
        
        # Search stats
        'search_stats': search_stats,
        'popular_searches': popular_searches,
        'search_trends': search_trends,
        'avg_search_time': round(avg_search_time) if avg_search_time else 0,
        
        # Translation stats
        'translation_stats': translation_stats,
        'popular_lang_pairs': popular_lang_pairs,
        'translation_trends': translation_trends,
        'avg_translation_time': round(avg_translation_time) if avg_translation_time else 0,
        
        # Favorites stats
        'total_favorites': total_favorites,
        'favorites_last_30d': favorites_last_30d,
        'most_favorited': most_favorited,
        
        # API health
        'api_health': api_health,
        'recent_failures': recent_failures,
        
        # Cache stats
        'cache_stats': cache_stats,
        
        # Top users
        'top_searchers': top_searchers,
        'top_translators': top_translators,
        
        # Metadata
        'refresh_time': timezone.now(),
    }
    context.update(admin.site.each_context(request))
    return render(request, 'admin/custom_dashboard.html', context)


def get_cache_stats():
    """
    Get cache statistics.
    Note: This is a simplified version. Real cache stats depend on backend.
    """
    try:
        # Try to get some basic cache info
        # This is backend-dependent
        return {
            'status': 'operational',
            'backend': cache.__class__.__name__,
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@staff_member_required
def clear_cache(request):
    """
    Clear application cache (superuser only).
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can clear cache.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        try:
            cache.clear()
            messages.success(request, 'Cache cleared successfully!')
        except Exception as e:
            messages.error(request, f'Failed to clear cache: {str(e)}')
    
    return redirect('admin_dashboard')


@staff_member_required
def export_analytics(request):
    """
    Export analytics data to CSV.
    """
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Get date range
    days = int(request.GET.get('days', 30))
    cutoff = timezone.now() - timedelta(days=days)
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="wordbud_analytics_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['WordBud Analytics Export'])
    writer.writerow(['Date Range:', f'Last {days} days'])
    writer.writerow(['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Search statistics
    writer.writerow(['SEARCH STATISTICS'])
    writer.writerow(['Total Searches', 'Successful', 'Not Found', 'Success Rate'])
    search_stats = SearchLog.get_search_stats(days=days)
    writer.writerow([
        search_stats['total'],
        search_stats['found'],
        search_stats['not_found'],
        f"{search_stats['success_rate']:.1f}%"
    ])
    writer.writerow([])
    
    # Popular searches
    writer.writerow(['TOP SEARCHES'])
    writer.writerow(['Word', 'Count'])
    popular = SearchLog.get_popular_searches(limit=20, days=days)
    for item in popular:
        writer.writerow([item['word'], item['count']])
    writer.writerow([])
    
    # Translation statistics
    writer.writerow(['TRANSLATION STATISTICS'])
    writer.writerow(['Total Translations', 'Successful', 'Failed', 'Success Rate', 'Total Characters'])
    trans_stats = TranslationLog.get_translation_stats(days=days)
    writer.writerow([
        trans_stats['total'],
        trans_stats['successful'],
        trans_stats['failed'],
        f"{trans_stats['success_rate']:.1f}%",
        trans_stats['total_chars']
    ])
    writer.writerow([])
    
    # Popular language pairs
    writer.writerow(['TOP LANGUAGE PAIRS'])
    writer.writerow(['Source', 'Target', 'Count'])
    lang_pairs = TranslationLog.get_popular_language_pairs(limit=20, days=days)
    for item in lang_pairs:
        writer.writerow([
            item['source_language'],
            item['target_language'],
            item['count']
        ])
    
    return response