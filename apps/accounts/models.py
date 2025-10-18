from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

# Create your models here.

'''Explanation:

AbstractBaseUser = bare minimum user model (email, password, last login).

PermissionsMixin = gives us groups, permissions, and is_superuser.

BaseUserManager = custom manager for creating users/superusers.

USERNAME_FIELD = "email" = tells Django to use email for login.

REQUIRED_FIELDS = [] = no extra fields required when creating superusers.'''
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
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # optional nickname
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"   # login with email
    REQUIRED_FIELDS = []       # no username required

    def __str__(self):
        return self.email
    

