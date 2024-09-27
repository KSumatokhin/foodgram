from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework import mixins, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from djoser.views import UserViewSet
from django.db.models import Sum
from django.db.models import Count

from api.serializers import (
    CustomUserSerializer, FavoriteCreateSerializer, IngredientsSerializer, RecipeCreateSerializer,
    RecipeSerializer, ShoppingCartCreateSerializer, ShortRecipeSerializer, SubscriptionCreateSerializer,
    SubscriptionSerializer,
    TagsSerializer, UserAvatarSerializer
)
from api.filters import IngredientsFilter, RecipeFilter
from api.permissions import IsSuperUserOrOwnerOrReadOnly
from users.models import Subscription
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

User = get_user_model()


def redirect_short_link(request, short_link):
    id = Recipe.objects.get(short_link=short_link).pk
    return redirect(f'/recipes/{id}/')


class MyUserViewSet(UserViewSet):

    def get_serializer_class(self):
        if self.action == "subscriptions":
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        qs = User.objects.filter(followers__user=user)
        queryset = self.filter_queryset(qs).annotate(
            recipes_count=Count('recipe')
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IngredientsListRetrieve(
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filterset_class = IngredientsFilter
    pagination_class = None


class TagsListRetrieve(
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = None


class UserAvatarViewSet(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def put(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        username = request.user.username
        User.objects.filter(username=username).update(avatar=None)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(APIView):
    queryset = Subscription.objects.all()
    permission_classes = (IsAuthenticated, )

    def post(self, request, id):
        author = get_object_or_404(User, pk=id)
        request.data['user'] = request.user.id
        request.data['author'] = author.id
        serializer = SubscriptionCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        subscription = user.subscriptions.filter(author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'ingredients', 'tags').select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsSuperUserOrOwnerOrReadOnly, )
    filterset_class = RecipeFilter
    filterset_fields = (
        'author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            data = {}
            data['user_id'] = request.user.id
            data['recipe_id'] = pk
            serializer = ShoppingCartCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ShortRecipeSerializer(serializer.instance.recipe).data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            recipe = get_object_or_404(Recipe, pk=pk)
            shopping_cart = user.shoppingcart.filter(recipe=recipe)
            if shopping_cart.exists():
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request, pk=None):
        user = request.user
        ingredients = Ingredient.objects.prefetch_related(
            'recipes', 'recipes__shoppingcart'
        ).filter(
            recipes__shoppingcart__user=user
        ).annotate(
            total_amount=Sum('recipeingredient__amount')
        )
        if ingredients.exists():
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="file.txt"'
            for ingredient in ingredients:
                response.write(
                    f'{ingredient.name} - {ingredient.total_amount} '
                    f'{ingredient.measurement_unit} \n'
                )
        return response

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            request.data['recipe'] = recipe.id
            request.data['user'] = request.user.id
            serializer = FavoriteCreateSerializer(
                data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ShortRecipeSerializer(serializer.instance.favorite).data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = user.favorites.filter(favorite=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny], url_path='get-link', url_name='get-link')
    def get_link(self, request, pk=None):
        val = len(request.META['PATH_INFO'])
        domain = request.build_absolute_uri()[:-val]
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {}
        data['short-link'] = f'{domain}/s/{recipe.short_link}'
        return Response(data, status=status.HTTP_200_OK)
