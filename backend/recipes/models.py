import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram_backend.constants import (MAX_NAME, MAX_OUT_NAME, MAX_SHORT_LINK,
                                        MIN_VALUE)


def slug_random(num_char: int) -> str:
    symbols = string.ascii_letters + string.digits
    return ''.join(random.sample(symbols, num_char))


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        ordering = ('slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Название'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/',
        null=True,
        default=None
    )
    text = models.TextField(
        verbose_name='Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MaxValueValidator(
                limit_value=1500,
                message='Постарайтесь уложиться в 24 часа!'
            ),
        )
    )
    pub_date = models.DateField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_link = models.SlugField(
        verbose_name='Короткая ссылка',
        null=True,
        max_length=MAX_SHORT_LINK
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:MAX_OUT_NAME]

    def save(self, *args, **kwargs):
        if self.short_link is None:
            slug = slug_random(MAX_SHORT_LINK)
            while Recipe.objects.filter(short_link=slug).exists():
                slug = slug_random(MAX_SHORT_LINK)
            self.short_link = slug
        super(Recipe, self).save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                limit_value=MIN_VALUE,
                message=f'Количество не может быть меньше чем {MIN_VALUE}!'
            ),
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
                violation_error_message='Этот ингредиент уже добавлен.'
            )
        ]
        verbose_name = 'Ингредиенты рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'


class ShoppingCartFavorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Избранное',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.user.username


class ShoppingCart(ShoppingCartFavorite):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shoppingcart'


class Favorite(ShoppingCartFavorite):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'
