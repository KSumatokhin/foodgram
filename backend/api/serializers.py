from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class UserAvatarSerializer(UserSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar', )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(
        'get_subscriptions',
        read_only=True,
    )

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_subscriptions(self, obj):
        if self.context.get('request') is None:
            return False
        user_id = self.context.get('request').user.id
        return Subscription.objects.filter(user=user_id, author=obj).exists()


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        many=False, required=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Значение должно быть больше 0')
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        if len(value) > len(set(x['id'] for x in value)):
            raise serializers.ValidationError(
                'Обнаружены повторяющиеся ингредиенты')
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value

    def validate_tags(self, value):
        if len(value) > len(set(value)):
            raise serializers.ValidationError('Обнаружены повторяющиеся теги')
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError('Это поле не может быть пустым')
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('Значение должно быть больше 0')
        return value

    @staticmethod
    def create_recipeingredients(recipe, ingredients_data):
        lst = []
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            lst.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(lst)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_recipeingredients(recipe, ingredients_data)
        recipe.tags.add(*tags_data)
        return recipe

    def update(self, instance, validated_data):
        for name in ['ingredients', 'tags']:
            if validated_data.get(name) is None:
                raise serializers.ValidationError(
                    {name: 'Это поле не может быть пустым'}
                )
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        self.create_recipeingredients(instance, ingredients_data)
        instance.tags.add(*tags_data)
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        return RecipeSerializer(recipe, context=self.context).data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(method_name='get_id')
    name = serializers.SerializerMethodField(method_name='get_name')
    measurement_unit = serializers.SerializerMethodField(
        method_name='get_measurement_unit'
    )

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True)
    author = CustomUserSerializer(many=False)
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipeingredient_set'
    )
    image = Base64ImageField(required=False, allow_null=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_shopping_cart',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField(
        'get_favorites',
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_favorites(self, recipe):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Favorite.objects.filter(
                recipe=recipe, user=request.user
            ).exists()
        )

    def get_shopping_cart(self, recipe):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                recipe=recipe, user=request.user
            ).exists()
        )


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author',)

    def validate(self, data):
        user = data['user']
        author = data['author']
        if author == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        if user.subscriptions.filter(author=author).exists():
            raise serializers.ValidationError(
                'На данного автора уже есть подписка')
        return data

    def to_representation(self, subscription):
        return SubscriptionSerializer(
            subscription.author, context=self.context).data


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(
        'get_recipe',
        read_only=True,
    )
    recipes_count = serializers.SerializerMethodField(
        'get_recipes_count',
        read_only=True,
    )

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields.copy()
        fields += ['recipes', 'recipes_count']

    def get_recipe(self, user):
        limit = self.context['request'].query_params.get('recipes_limit', None)
        recipes = Recipe.objects.filter(author=user)
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, user):
        return Recipe.objects.filter(author=user).count()


class ShoppingCartCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate_recipe(self, value):
        user = self.context['request'].user
        model = self.__class__.Meta.model
        if model.objects.filter(user=user, recipe=value).exists():
            raise serializers.ValidationError('Этот рецепт уже добавлен')
        return value


class FavoriteCreateSerializer(ShoppingCartCreateSerializer):
    class Meta:
        model = Favorite

# class FavoriteCreateSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Favorite
#         fields = ('user', 'recipe',)

#     def validate_recipe(self, value):
#         user = self.context['request'].user
#         if Favorite.objects.filter(user=user, recipe=value).exists():
#             raise serializers.ValidationError('Этот рецепт уже в избранном')
#         return value
