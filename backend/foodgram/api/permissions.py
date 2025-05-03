from rest_framework import permissions


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение для администратора или только для чтения.
    Позволяет изменять данные только администраторам.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or 
                request.user.is_staff)


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение для автора или только для чтения.
    Позволяет изменять рецепт только его автору.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsSubscriberOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение для подписчика или только для чтения.
    Позволяет управлять подписками только их владельцу.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAuthenticatedAndNotAuthorPermission(permissions.BasePermission):
    """
    Разрешение для аутентифицированных пользователей, не являющихся автором.
    Используется для запрета подписки на самого себя.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user != obj.following
