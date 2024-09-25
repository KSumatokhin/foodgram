import base64
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from django.core.files.base import ContentFile
from django.db.models import F, Q

from users.models import Subscription
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag, ShoppingCart, Tag

User = get_user_model()


def all_distinct(iterable):
    seen = set()
    return not any(i in seen or seen.add(i) for i in iterable)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # if data == '':
        #     return None
        if isinstance(data, str) and data.startswith('data:image'):
            # name = self.root.instance.username
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


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
        auth_user = self.context.get('request').user
        if auth_user.is_anonymous:
            return False
        return auth_user.subscriptions.filter(author=obj).exists()


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
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
    ingredients = RecipeIngredientSerializer(many=True, required=True)
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

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('Значение должно быть больше 0')
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount)
        for tag_data in tags_data:
            RecipeTag.objects.create(recipe=recipe, tag=tag_data)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        try:
            ingredients_data = validated_data.pop('ingredients')
            lst = []
            for ingredient_data in ingredients_data:
                ingredient = ingredient_data.get('id')
                amount = ingredient_data.get('amount')
                if instance.ingredients.filter(pk=ingredient.pk).exists():
                    recipe_ingredient = instance.recipeingredient_set.get(
                        ingredient=ingredient)
                    recipe_ingredient.amount = amount
                    recipe_ingredient.save()
                else:
                    recipe_ingredient = RecipeIngredient.objects.create(
                        recipe=instance, ingredient=ingredient, amount=amount)
                lst.append(ingredient)
            instance.ingredients.set(lst)
        except KeyError:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле не может быть пустым'}
            )

        try:
            tags_data = validated_data.pop('tags')
            lst = []
            for tag in tags_data:
                RecipeTag.objects.get_or_create(recipe=instance, tag=tag)
                lst.append(tag)
            instance.tags.set(lst)
        except KeyError:
            raise serializers.ValidationError(
                {'tags': 'Это поле не может быть пустым'}
            )

        instance.save()
        return instance

    def to_representation(self, recipe):
        return RecipeSerializer(recipe).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True)
    author = CustomUserSerializer(many=False)
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        result = []
        ingredients = obj.ingredients.all()
        for ingredient in ingredients:
            ret = {
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': ingredient.recipeingredient_set.get(recipe=obj).amount
            }
            result.append(ret)
        return result

    def get_favorites(self, recipe):
        try:
            auth_user = self.context.get('request').user
        except AttributeError:
            return False
        if auth_user.is_anonymous:
            return False
        return recipe.favorites.filter(user=auth_user).exists()

    def get_shopping_cart(self, recipe):
        try:
            auth_user = self.context.get('request').user
        except AttributeError:
            return False
        if auth_user.is_anonymous:
            return False
        return recipe.shoppingcart.filter(user=auth_user).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class ShoppingCartCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    recipe_id = serializers.IntegerField()

    def validate(self, data):
        if ShoppingCart.objects.filter(
            user__id=data['user_id'],
            recipe__id=data['recipe_id']
        ).exists():
            raise serializers.ValidationError(
                'Данный рецепт уже добавлен в список покупок.'
            )
        return data

    def create(self, validated_data):
        user = User.objects.get(pk=validated_data['user_id'])
        recipe = get_object_or_404(Recipe, pk=validated_data['recipe_id'])
        shopping_cart = ShoppingCart.objects.create(
            user=user, recipe=recipe)
        return shopping_cart


class SubscriptionCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    def validate(self, data):
        user = data['user']
        author = data['author']
        if author == user:
            raise serializers.ValidationError('Нельзя подписаться на самого себя')
        elif user.subscriptions.filter(author=author).exists():
            raise serializers.ValidationError('На данного автора уже есть подписка')
        return data

    def create(self, validated_data):
        subscription = Subscription.objects.create(
            user=validated_data['user'],
            author=validated_data['author']
        )
        return subscription.author

    def to_representation(self, author):
        return SubscriptionSerializer(author, context=self.context).data


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
        recipes_count = Recipe.objects.filter(author=user).count()
        return recipes_count


class FavoriteCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    def create(self, validated_data):
        favorite = Favorite.objects.create(
            user=validated_data['user'],
            favorite=validated_data['recipe']
        )
        return favorite

    def validate_recipe(self, value):
        user = self.context['request'].user
        if user.favorites.filter(user=user).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном')
        return value