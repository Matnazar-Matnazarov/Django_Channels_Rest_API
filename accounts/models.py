from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.models import PermissionsMixin


class CustomUserManager(UserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(username, email, password, **extra_fields)

# Create your models here.
class CustomUser(AbstractUser, PermissionsMixin):
    image = models.ImageField(upload_to='users/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    objects = CustomUserManager()

    def __str__(self):
        return self.username