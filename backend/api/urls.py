from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from api_foodgram import settings

router_v1 = DefaultRouter()
router_v1.register(prefix='users', viewset=UserViewSet, basename='users')
router_v1.register(prefix='tags', viewset=TagViewSet, basename='tags')
router_v1.register(prefix='recipes', viewset=RecipeViewSet, basename='recipes')
router_v1.register(
    prefix='ingredients', viewset=IngredientViewSet, basename='ingredients'
)

docs_url = [
    path('', TemplateView.as_view(template_name='docs/redoc.html')),
    path(
        'openapi-schema.yml',
        serve,
        kwargs={
            'path': 'docs/openapi-schema.yml',
            'document_root': settings.BASE_DIR / 'templates',
        },
    ),
]
urlpatterns = [
    path('docs/', include(docs_url)),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
