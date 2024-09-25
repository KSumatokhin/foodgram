from django.forms import CheckboxInput
import django_filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientsFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', )


# def shopping_carts(request):
#     if request is None:
#         return Recipe.objects.all()
#     user = request.user
#     return Recipe.objects.filter(shoppingcart__user=user)


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(
        field_name='author',
        lookup_expr='id__exact'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        widget=CheckboxInput(),
        field_name='shoppingcart',
        method='filter_users'
    )
    is_favorited = django_filters.BooleanFilter(
        widget=CheckboxInput(),
        field_name='favorites',
        method='filter_users'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def filter_users(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user.is_anonymous or value is False:
            return queryset.all()
        lookup = '__'.join([name, 'user'])
        return queryset.filter(**{lookup: user})

    # def filter_favorites(self, queryset, name, value):
    #     user = getattr(self.request, 'user', None)
    #     if user.is_anonymous or value is False:
    #         return queryset.all()
    #     lookup = '__'.join([name, 'user'])
    #     return queryset.filter(**{lookup: user})
