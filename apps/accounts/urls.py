from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Profile Management
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("profile/preferences/", views.preferences_view, name="preferences"),
    
    # Account Settings
    path("email/change/", views.email_change_view, name="email_change"),
    path("password/change/", views.password_change_view, name="password_change"),
    
    # AJAX Endpoints
    path("api/profile-image/delete/", views.delete_profile_image, name="delete_profile_image"),
    path("api/preference/update/", views.update_preference, name="update_preference"),
    path("api/stats/", views.profile_stats_api, name="profile_stats"),
    
    # Optional: Account Deletion
    path("account/delete/", views.account_delete_view, name="account_delete"),
]