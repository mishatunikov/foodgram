from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, TagViewSet

router = DefaultRouter()
router.register(prefix='users', viewset=UserViewSet)
router.register(prefix='tags', viewset=TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
