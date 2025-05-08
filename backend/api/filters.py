from django.db.models import Case, IntegerField, Value, When
from django.db.models.functions import Lower
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from foodgram.models import Recipe, Tag


class RecipeFilterSet(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and value:
            return queryset.filter(users_favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and value:
            return queryset.filter(users_purchase__user=user)
        return queryset


class DoubleSearchName(SearchFilter):
    search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get(self.search_param)
        if name:
            queryset = (
                queryset.annotate(lower_name=Lower('name'))
                .filter(lower_name__icontains=name.lower())
                .annotate(
                    priority=Case(
                        When(
                            lower_name__istartswith=name.lower(), then=Value(0)
                        ),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
                .order_by('priority', 'name')
            )
        return queryset
