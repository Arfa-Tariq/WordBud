"""
Profile Views - Complete user profile management system
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    ProfileUpdateForm,
    PreferencesForm,
    EmailChangeForm,
    PasswordChangeCustomForm
)
from .models import CustomUser

logger = logging.getLogger(__name__)


# ============= Authentication Views =============

def signup_view(request):
    """User registration view."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to WordBud! Your account has been created.')
            return redirect("core:home")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    """User login view."""
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_short_name()}!')
            
            # Redirect to 'next' parameter or home
            next_url = request.GET.get('next', 'core:home')
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """User logout view."""
    if request.method == "POST":
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect("core:landing")


# ============= Profile Views =============

@login_required
def profile_view(request):
    """
    Main profile view - displays user profile with activity stats.
    This replaces the existing placeholder profile page.
    """
    user = request.user
    
    # Get user activity statistics
    activity_stats = user.get_activity_stats()
    
    # Get recent favorites
    from apps.dictionary.models import UserFavorite
    recent_favorites = UserFavorite.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get recent searches
    from apps.core.models import SearchLog
    recent_searches = SearchLog.objects.filter(user=user).order_by('-searched_at')[:10]
    
    context = {
        'user': user,
        'activity_stats': activity_stats,
        'recent_favorites': recent_favorites,
        'recent_searches': recent_searches,
    }
    
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit_view(request):
    """Profile editing view - handles profile updates."""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, "accounts/profile_edit.html", context)


@login_required
def preferences_view(request):
    """User preferences management view."""
    if request.method == 'POST':
        form = PreferencesForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Save preferences to user model
            preferences = {
                'theme': form.cleaned_data['theme'],
                'email_notifications': form.cleaned_data['email_notifications'],
                'show_search_history': form.cleaned_data['show_search_history'],
                'items_per_page': form.cleaned_data['items_per_page'],
            }
            
            request.user.preferences = preferences
            request.user.save(update_fields=['preferences'])
            
            messages.success(request, 'Your preferences have been saved!')
            return redirect('accounts:profile')
    else:
        form = PreferencesForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, "accounts/preferences.html", context)


@login_required
def email_change_view(request):
    """Email change view with password confirmation."""
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, user=request.user)
        
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            request.user.email = new_email
            request.user.save(update_fields=['email'])
            
            messages.success(request, f'Your email has been changed to {new_email}')
            return redirect('accounts:profile')
    else:
        form = EmailChangeForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, "accounts/email_change.html", context)


@login_required
def password_change_view(request):
    """Custom password change view."""
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.POST, user=request.user)
        
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            
            # Keep user logged in after password change
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeCustomForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, "accounts/password_change.html", context)


# ============= AJAX Endpoints =============

@login_required
@require_http_methods(["POST"])
def delete_profile_image(request):
    """AJAX endpoint to delete profile image."""
    try:
        user = request.user
        if user.profile_image:
            # Delete the file
            user.profile_image.delete(save=False)
            user.profile_image = None
            user.save(update_fields=['profile_image'])
            
            return JsonResponse({
                'success': True,
                'message': 'Profile image deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No profile image to delete'
            }, status=400)
    
    except Exception as e:
        logger.error(f"Error deleting profile image: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to delete profile image'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_preference(request):
    """AJAX endpoint to update a single preference."""
    try:
        key = request.POST.get('key')
        value = request.POST.get('value')
        
        if not key:
            return JsonResponse({
                'success': False,
                'error': 'Preference key is required'
            }, status=400)
        
        # Convert string boolean values
        if value in ['true', 'false']:
            value = value == 'true'
        
        # Save preference
        request.user.set_preference(key, value)
        
        return JsonResponse({
            'success': True,
            'message': f'Preference "{key}" updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating preference: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to update preference'
        }, status=500)


@login_required
def profile_stats_api(request):
    """API endpoint for profile statistics (for AJAX updates)."""
    try:
        stats = request.user.get_activity_stats()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'favorites': stats['favorites_count'],
                'searches': stats['searches_count'],
                'translations': stats['translations_count'],
                'member_since': stats['member_since'].strftime('%B %Y'),
                'last_login': stats['last_login'].strftime('%B %d, %Y %H:%M') if stats['last_login'] else 'Never',
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching profile stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch statistics'
        }, status=500)


@login_required
def account_delete_view(request):
    """Account deletion view (optional - implement with caution)."""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if request.user.check_password(password):
            # Log the user out
            user = request.user
            logout(request)
            
            # Delete the account
            user.delete()
            
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('core:landing')
        else:
            messages.error(request, 'Incorrect password. Account not deleted.')
    
    return render(request, "accounts/account_delete.html")