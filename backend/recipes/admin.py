from django.contrib import admin

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag

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
    list_display = ('name', 'author', 'favorites')
    list_filter = ('tags__name',)
    search_fields = ('author__username', 'name__istartswith', )
    readonly_fields = ('short_link', )
    # inlines = (RecipeIngredientInline, )
    # fields = ('favorites', )

    @admin.display(description='В избранном')
    def favorites(self, obj):
        return obj.favorites.all().count()
