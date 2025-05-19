from django.urls import include, path, re_path
from rest_framework.authtoken import views
from rest_framework import routers
from api.views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    SubscriptionViewSet
)
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    
    
    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view({'get': 'subscriptions'}),
        name='subscriptions'
    ),
    path(
        'users/<int:pk>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='subscribe'
    ),

    path('', include(router.urls)),
    
    path(
        'users/me/',
        UserViewSet.as_view({'get': 'me'}),
        name='me'
    ),
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'}),
        name='set_password'
    ),
    path(
        'users/me/avatar/',
        UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='avatar'
    ),
    
    path(
        'recipes/download_shopping_cart/',
        RecipeViewSet.as_view({'get': 'download_shopping_cart'}),
        name='download_shopping_cart'
    ),
    path(
        'recipes/<int:pk>/favorite/',
        RecipeViewSet.as_view({'post': 'favorite', 'delete': 'favorite'}),
        name='favorite'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        RecipeViewSet.as_view({'post': 'shopping_cart', 'delete': 'shopping_cart'}),
        name='shopping_cart'
    ),
    path(
        'recipes/<int:pk>/get-link/',
        RecipeViewSet.as_view({'get': 'get_link'}),
        name='get_link'
    ),

    

    # Аутентификация
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)
    
urlpatterns += [
    re_path(r'^.*', TemplateView.as_view(template_name='index.html')),
]
