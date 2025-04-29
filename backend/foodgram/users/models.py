from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        'email address',
        unique=True, 
        blank=False, 
        null=False
    )

    avatar = models.ImageField(
        'аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
