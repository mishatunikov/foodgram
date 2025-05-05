from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Lower
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from foodgram.models import Recipe


class RecipeFilterSet(FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        tag_list = self.request.query_params.getlist('tags')
        if tag_list:
            return queryset.filter(tags__slug__in=tag_list).distinct()
        return queryset

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


# class DoubleSearchName(SearchFilter):
#     search_param = 'name'
#
#     def filter_queryset(self, request, queryset, view):
#         name = request.query_params.get(self.search_param)
#         if name:
#             queryset = (
#                 queryset.filter(name__icontains=name.lower())
#                 .annotate(
#                     priority=Case(
#                         When(name__istartswith=name, then=Value(0)),
#                         default=Value(1),
#                         output_field=IntegerField(),
#                     )
#                 )
#                 .order_by('priority', 'name')
#             )
#         return queryset
