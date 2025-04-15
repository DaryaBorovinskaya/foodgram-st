from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        'email address',
        unique=True,  # делаем email уникальным
        blank=False,  # делаем обязательным
        null=False
    )
    avatar = models.ImageField(
        'аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )
    
    # Убираем username, если хотим использовать email для входа
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']  # если оставим username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'