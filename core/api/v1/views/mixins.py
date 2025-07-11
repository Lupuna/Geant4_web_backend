import loguru
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django_elasticsearch_dsl import Document

from elasticsearch_dsl import Q

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request

from api.v1.serializers.utils import resolve_dot_notation
from users.auth.utils import response_cookies
from math import ceil


class ElasticMixin:
    elastic_document_conf = None
    total_count = None

    def get_elastic_document_class(self) -> Document:
        if not hasattr(self, 'elastic_document') or self.elastic_document is None:
            raise AttributeError(
                'If you want to use ElasticSearch you need to set elastic document on "elastic_document" attribute')

        return self.elastic_document

    def setup_elastic_document_conf(self):
        document = self.get_elastic_document_class()
        try:
            document_conf = settings.ELASTIC_PARAMS_CONF['documents'][document.__name__]
            self.elastic_document_conf = document_conf
        except KeyError:
            raise KeyError('Need to setup elastic document in settings')

    def elastic_filter(self, request, search):
        params = request.query_params.copy()
        filter_params = set(
            self.elastic_document_conf['params']['filter']
        ) & set(params.keys())

        resolved_required_filters, filter_params = self.add_required_filters(filter_params, request)
        for param in filter_params:
            if param in resolved_required_filters:
                vals = [resolved_required_filters.get(param)]
            else:
                vals = params.get(param, None)
                if vals is None:
                    continue
                vals = vals.split(',')
            val_filters = [Q("term", **{param: val}) for val in vals]
            q_vals = Q("bool", must=val_filters)
            search = search.filter(q_vals)
        return search

    def add_required_filters(self, filter_params: set, request: Request):
        required_filters = self.elastic_document_conf.get('required_filter')
        resolved_required_filters = {}
        if required_filters:
            for key, value in required_filters.items():
                if isinstance(value, str) and value.startswith('request.'):
                    resolved_value = resolve_dot_notation(request, value.replace('request.', '', 1))
                else:
                    resolved_value = value
                resolved_required_filters[key] = resolved_value
            filter_params.update(resolved_required_filters.keys())
        return resolved_required_filters, filter_params

    def elastic_search(self, request, search):
        params = request.query_params
        search_param = self.elastic_document_conf['params']['search']
        fields = self.elastic_document_conf['fields']
        target = params.get(search_param, None)

        if target:
            q = Q(
                "multi_match", query=target, fields=fields,
                fuzziness="auto"
            )
            search = search.query(q)

        return search

    def elastic_order(self, request, search):
        ordering_param = self.elastic_document_conf['params'].get('order')
        ordering_value = request.query_params.get(ordering_param)

        if ordering_value:
            sort_fields = []
            for field in ordering_value.split(','):
                field = field.strip()
                if field.startswith('-'):
                    sort_fields.append({field[1:]: {"order": "desc"}})
                else:
                    sort_fields.append({field: {"order": "asc"}})
            search = search.sort(*sort_fields)

        return search

    def elastic_pagination(self, request, search):
        page_param_name = self.elastic_document_conf['params']['pagination']
        page = int(request.query_params.get(page_param_name, 1))
        page_size = self.elastic_document_conf['pagination_page_size']
        start = (page - 1) * page_size
        search = search.extra(from_=start, size=page_size)
        return search

    def elastic_full_query_handling(self, request, search):
        for action in self.elastic_document_conf['params']:
            search = getattr(self, f'elastic_{action}', search)(
                request, search)

        self.total_count = search.count()
        return search

    def get_response_data_with_pages_count(self, response_data: list):
        page_size = self.elastic_document_conf['pagination_page_size']
        pages_count = ceil(self.total_count / page_size)
        response_data.append({'pages_count': pages_count})
        return response_data


class ValidationHandlingMixin:
    def perform_create(self, serializer, **kwargs):
        try:
            instance = serializer.save(
                **kwargs) if kwargs else serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError({'error': e.messages})
        except IntegrityError as e:
            raise DRFValidationError({'error': str(e)})

        if hasattr(self, 'post_create'):
            self.post_create(instance)

        return instance

    def perform_update(self, serializer, **kwargs):
        try:
            instance = serializer.save(
                **kwargs) if kwargs else serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError({'error': e.messages})
        except IntegrityError as e:
            raise DRFValidationError({'error': str(e)})

        if hasattr(self, 'post_update'):
            instance = self.post_update(instance)

        return instance


class CookiesMixin:
    cookies_to_delete = []
    request_cookies = {}
    response_cookies = {}

    def check_request(self):
        if not self.request:
            raise AttributeError('Request was not provided')

    def check_request_cookies(self, *keys):
        self.check_request()
        if not keys:
            self.request_cookies = self.request.COOKIES
        else:
            self.request_cookies.update({
                key: self.request.COOKIES.get(key, None) for key in keys if self.request.COOKIES.get(key, None)})

        return all(self.request_cookies.get(key) not in [None, ''] for key in keys)

    def setup_to_delete_cookies(self):
        self.cookies_to_delete = list(self.request_cookies.keys())

    def get_response_del_cookies(self, data, status):
        self.setup_to_delete_cookies()
        return response_cookies(data, status, cookies_data=self.cookies_to_delete, delete=True)

    def get_response_set_cookies(self, data, status):
        return response_cookies(data, status, cookies_data=self.response_cookies)


class QueryParamsMixin:
    order_by = None

    def sort_by_ord(self, queryset):
        ordering = self.request.query_params.get('ord', None)
        order_by = self.order_by
        if order_by:
            if ordering == 'desc':
                order_by = '-' + order_by
            queryset = queryset.order_by(order_by)
        return queryset
