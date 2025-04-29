from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email')
    search_fields = ('email', 'username')


admin.site.empty_value_display = 'Не задано'
admin.site.register(User, CustomUserAdmin)
# Register your models here.
