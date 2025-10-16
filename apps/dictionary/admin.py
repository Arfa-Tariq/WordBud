from django.contrib import admin

from .models import UserData


@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ("user", "favorite_word")
    search_fields = ("user__email", "favorite_word")
