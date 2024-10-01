from django.contrib import admin
from django.db.models import Count

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

admin.site.empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name__istartswith', )
    # search_help_text = 'Введите название ингредиента'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('tags__name',)
    search_fields = ('author__username', 'name__istartswith', )
    readonly_fields = ('short_link', 'favorites')
    # inlines = (RecipeIngredientInline, )
    # fields = ('favorites', )
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'name', 'author', 'text', 'cooking_time', 'short_link'
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(favorite=Count('favorites__favorite'))

    @admin.display(description='В избранном')
    def favorites(self, obj):
        return obj.favorites.all().count()
