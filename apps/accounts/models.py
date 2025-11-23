from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from PIL import Image
import os

# Create your models here.

'''Explanation:

AbstractBaseUser = bare minimum user model (email, password, last login).

PermissionsMixin = gives us groups, permissions, and is_superuser.

BaseUserManager = custom manager for creating users/superusers.

USERNAME_FIELD = "email" = tells Django to use email for login.

REQUIRED_FIELDS = [] = no extra fields required when creating superusers.

Extended User Profile Model for WordBud - Adds profile picture, bio, and user preferences'''
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Extended User model with profile features.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Profile Fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Tell us about yourself (max 500 characters)"
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Profile picture (JPG, PNG, GIF - max 5MB)"
    )
    
    # User Preferences (stored as JSON)
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences (theme, notifications, etc.)"
    )
    
    # Account Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return full name or email if name not set."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        return self.email.split('@')[0]
    
    def get_short_name(self):
        """Return first name or username."""
        return self.first_name or self.username or self.email.split('@')[0]
    
    def save(self, *args, **kwargs):
        """Override save to resize profile images."""
        super().save(*args, **kwargs)
        
        # Resize profile image if it exists
        if self.profile_image:
            img_path = self.profile_image.path
            if os.path.exists(img_path):
                img = Image.open(img_path)
                
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Resize if larger than 400x400
                if img.height > 400 or img.width > 400:
                    output_size = (400, 400)
                    img.thumbnail(output_size, Image.Resampling.LANCZOS)
                    img.save(img_path, quality=85, optimize=True)
    
    def get_profile_image_url(self):
        """Return profile image URL or default avatar."""
        if self.profile_image:
            return self.profile_image.url
        return None
    
    def get_preferences(self, key=None, default=None):
        """Get user preference by key."""
        if key:
            return self.preferences.get(key, default)
        return self.preferences
    
    def set_preference(self, key, value):
        """Set a user preference."""
        if not isinstance(self.preferences, dict):
            self.preferences = {}
        self.preferences[key] = value
        self.save(update_fields=['preferences'])
    
    def get_activity_stats(self):
        """Get user activity statistics."""
        from apps.dictionary.models import UserFavorite, SearchHistory
        from apps.core.models import SearchLog, TranslationLog
        
        return {
            'favorites_count': UserFavorite.objects.filter(user=self).count(),
            'searches_count': SearchLog.objects.filter(user=self).count(),
            'translations_count': TranslationLog.objects.filter(user=self).count(),
            'member_since': self.date_joined,
            'last_login': self.last_login,
        }
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']