from rest_framework.pagination import (PageNumberPagination, 
                                       LimitOffsetPagination)


class StandardPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6 
    max_page_size = 50