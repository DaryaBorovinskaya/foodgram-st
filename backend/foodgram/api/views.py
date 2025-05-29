from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .pagination import StandardPagination
from rest_framework.permissions import IsAuthenticated
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from io import BytesIO
import matplotlib.font_manager as fm
from rest_framework.permissions import AllowAny
from recipes.models import (
    User,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription, Favorite 
)
from .serializers import (UserSerializer, UserCreateSerializer,
                          IngredientSerializer,
                          RecipeSerializer, ShortRecipeSerializer,
                          SubscriptionSerializer, SetPasswordSerializer,
                          AvatarSerializer)
from .permissions import IsAuthorOrReadOnlyPermission

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filtersSearchIngr


LEFT_MARGIN = 100
TOP_MARGIN_INITIAL = 800
LINE_HEIGHT = 20
TITLE_OFFSET = 30
BOTTOM_MARGIN = 50
FONT_NAME = "CyrillicFont"
FONT_SIZE = 14


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], 
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], 
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], 
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if request.method == 'PUT':
                serializer = AvatarSerializer(data=request.data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                user = serializer.update(request.user, serializer.validated_data)
                avatar_url = user.avatar.url if user.avatar else None
                response = Response(
                    {
                        'avatar': request.build_absolute_uri(avatar_url) if avatar_url else None
                    },
                    status=status.HTTP_200_OK
                )
            
            elif request.method == 'DELETE':
                user = request.user
                if user.avatar: 
                    user.avatar.delete()
                    user.avatar = None
                    user.save()
                avatar_url = None
                response = Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            
            return response
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    

class IngredientFilter(filtersSearchIngr.FilterSet):
    name = filtersSearchIngr.CharFilter(
        field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, )  # filters.SearchFilter)
    filterset_class = IngredientFilter
    # search_fields = ('name',) 


class RecipeViewSet(viewsets.ModelViewSet):
    
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient'
    )
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnlyPermission]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', 'author__username')
    ordering_fields = ['pub_date', 'cooking_time']
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if self.request.query_params.get('is_favorited') == '1':
            if user.is_authenticated:
                queryset = queryset.filter(favorites__user=user)
            else:
                queryset = queryset.none()
        
        if self.request.query_params.get('is_in_shopping_cart') == '1':
            if user.is_authenticated:
                queryset = queryset.filter(shopping_cart__user=user)
            else:
                queryset = queryset.none()
        
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], 
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user.favorites.filter(
                recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        deleted_count, _ = user.favorites.filter(recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], 
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user.shopping_cart.filter(
                recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        deleted_count, _ = user.shopping_cart.filter(recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], 
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        font_path = fm.findfont("DejaVu Sans", fallback_to_default=True)
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont(FONT_NAME, FONT_SIZE)
        
        y = TOP_MARGIN_INITIAL
        p.drawString(LEFT_MARGIN, y, "Список покупок:")
        y -= TITLE_OFFSET

        for item in ingredients:
            p.drawString(LEFT_MARGIN, y, 
                         f"{item['ingredient__name']} "
                         f"({item['ingredient__measurement_unit']}) - "
                         f"{item['total_amount']}")
            y -= LINE_HEIGHT
            if y < BOTTOM_MARGIN:  # Переход на новую страницу
                p.showPage()
                p.setFont("CyrillicFont", FONT_SIZE)
                y = TOP_MARGIN_INITIAL

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"'
        )
        return response

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f"https://foodgram.example.org/s/{recipe.id}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]  
    pagination_class = StandardPagination

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        
        if request.method == 'POST':
            return self._subscribe(request.user, author)
        elif request.method == 'DELETE':
            return self._unsubscribe(request.user, author)

    def _subscribe(self, user, author):
        serializer = self.get_serializer(data={}, context={
            'request': self.request,
            'author': author
        })
        serializer.is_valid(raise_exception=True)

        if user.follower.filter(author=author).exists():
            return Response(
                {"error": "Already subscribed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription.objects.create(user=user, author=author)
        return Response(
            self.get_serializer(subscription).data,
            status=status.HTTP_201_CREATED
        )
        
    def _unsubscribe(self, user, author):
        try:
            subscription = Subscription.objects.get(user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
