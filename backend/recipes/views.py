from django.shortcuts import redirect

from recipes.models import Recipe


def redirect_short_link(request, short_link):
    pk = Recipe.objects.get(short_link=short_link).pk
    return redirect(f'/recipes/{pk}/')
