from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()
router_v1.register(prefix='users', viewset=UserViewSet, basename='users')
router_v1.register(prefix='tags', viewset=TagViewSet, basename='tags')
router_v1.register(prefix='recipes', viewset=RecipeViewSet, basename='recipes')
router_v1.register(
    prefix='ingredients', viewset=IngredientViewSet, basename='ingredients'
)


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
