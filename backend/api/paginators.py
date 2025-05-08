from rest_framework.pagination import PageNumberPagination

from api import consts


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = consts.DEFAULT_PAGE_SIZE
