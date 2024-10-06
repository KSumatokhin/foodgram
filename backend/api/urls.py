from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsListRetrieve, UserViewSet, RecipeViewSet,
                       SubscribeViewSet, TagsListRetrieve, UserAvatarViewSet)

router = DefaultRouter()

router.register(
    prefix='ingredients',
    viewset=IngredientsListRetrieve, basename='ingredients'
)
router.register(
    prefix='tags', viewset=TagsListRetrieve,
    basename='tags'
)
router.register(
    prefix='recipes', viewset=RecipeViewSet,
    basename='recipes'
)
router.register("users", viewset=UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path(r'users/me/avatar/', UserAvatarViewSet.as_view()),
    path('users/<int:id>/subscribe/', SubscribeViewSet.as_view()),
    path('auth/', include('djoser.urls.authtoken')),
]
