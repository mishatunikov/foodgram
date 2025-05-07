from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(prefix='users', viewset=UserViewSet, basename='users')
router.register(prefix='tags', viewset=TagViewSet, basename='tags')
router.register(prefix='recipes', viewset=RecipeViewSet, basename='recipes')
router.register(
    prefix='ingredients', viewset=IngredientViewSet, basename='ingredients'
)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
