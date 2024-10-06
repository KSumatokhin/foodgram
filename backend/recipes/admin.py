from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

admin.site.empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name__istartswith', )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'image',)
    list_filter = ('tags__name',)
    search_fields = ('author__username', 'name__istartswith', )
    readonly_fields = ('short_link', 'favorites')
    inlines = (RecipeIngredientInline, )
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'name', 'author', 'text', 'cooking_time',
                ],
            }
        ),
        (
            'Дополнительные параметры',
            {
                'classes': ["collapse"],
                'fields': ['favorites'],
            }
        )
    ]

    @admin.display(description='В избранном')
    def favorites(self, obj):
        return obj.favorites.all().count()

    @admin.display(description="Изображение")
    def image(self, obj):
        if obj.image != '':
            return mark_safe(
                f'<img scr={obj.image.url} width="150" height="160">'
            )
        return None


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
