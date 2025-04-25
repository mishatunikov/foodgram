from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, TagViewSet, RecipeViewSet

router = DefaultRouter()
router.register(prefix='users', viewset=UserViewSet)
router.register(prefix='tags', viewset=TagViewSet)
router.register(prefix='recipes', viewset=RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
