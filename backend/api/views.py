from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientsFilter, RecipeFilter
from api.permissions import IsSuperUserOrOwnerOrReadOnly
from api.serializers import (FavoriteCreateSerializer, IngredientsSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartCreateSerializer,
                             ShortRecipeSerializer,
                             SubscriptionCreateSerializer,
                             SubscriptionSerializer, TagsSerializer,
                             UserAvatarSerializer)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import MyUser as User
from users.models import Subscription


class UserViewSet(DjoserUserViewSet):

    def get_serializer_class(self):
        if self.action == "subscriptions":
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        qs = User.objects.filter(followers__user=request.user)
        queryset = self.filter_queryset(qs).annotate(
            recipes_count=Count('recipes')
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
        serializer = UserAvatarSerializer(request.user, data=request.data)
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
        author = get_object_or_404(User, pk=id)
        try:
            Subscription.objects.get(user=request.user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            # raise NotFound(detail='Такой подписки нет', code=400)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'ingredients', 'tags'
    ).select_related(
        'author'
    ).order_by('-pub_date', '-pk')
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

    def perform_update(self, serializer):
        serializer.save(
            author=self.request.user
        )

    @staticmethod
    def add_recipe(serializer_class, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        request.data['recipe'] = recipe.id
        request.data['user'] = request.user.id
        serializer = serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.instance.recipe

    @staticmethod
    def delete_recipe(model_class, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            model_class.objects.get(user=request.user, recipe=recipe).delete()
            return status.HTTP_204_NO_CONTENT
        except model_class.DoesNotExist:
            return status.HTTP_400_BAD_REQUEST

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        recipe = self.add_recipe(ShoppingCartCreateSerializer, request, pk)
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        status = self.delete_recipe(ShoppingCart, request, pk)
        return Response(status=status)

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

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        recipe = self.add_recipe(FavoriteCreateSerializer, request, pk)
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        status = self.delete_recipe(Favorite, request, pk)
        return Response(status=status)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny],
            url_path='get-link', url_name='get-link')
    def get_link(self, request, pk=None):
        val = len(request.META['PATH_INFO'])
        domain = request.build_absolute_uri()[:-val]
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {}
        data['short-link'] = f'{domain}/s/{recipe.short_link}'
        return Response(data, status=status.HTTP_200_OK)
