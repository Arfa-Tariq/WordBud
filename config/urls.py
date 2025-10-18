"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from apps.core.admin_dashboard import admin_dashboard, clear_cache, export_analytics

urlpatterns = [
        # Custom Admin Dashboard (staff-only)
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/clear-cache/", clear_cache, name="clear_cache"),
    path("admin/export-analytics/", export_analytics, name="export_analytics"),
    # Admin
    path("admin/", admin.site.urls),
        
    # Apps
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("dictionary/", include(("apps.dictionary.urls", "dictionary"), namespace="dictionary")),
    path("", include(("apps.core.urls", "core"), namespace="core")),
    path("translator/", include("apps.translator.urls", namespace="translator")),
    path('games/', include('apps.games.urls')),
]

