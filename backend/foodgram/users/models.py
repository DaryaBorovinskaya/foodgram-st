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
        upload_to='users/',
        blank=True,
        null=True
    )

    first_name = models.CharField(
        'first name',
        max_length=150,
        blank=False,  
        null=False   
    )
    
    last_name = models.CharField(
        'last name',
        max_length=150,
        blank=False,  
        null=False    
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'



