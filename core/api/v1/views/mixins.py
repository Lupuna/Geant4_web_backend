from elasticsearch_dsl import Q

from django_elasticsearch_dsl import Document

from django.conf import settings

from users.auth.utils import response_cookies


class ElasticMixin:
    elastic_document_conf = None

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
        params = request.query_params
        filter_params = set(
            self.elastic_document_conf['params']['filter']) & set(params.keys())

        for param in filter_params:
            vals = params.get(param, None)
            vals = vals.split(',')
            val_filters = [Q("term", **{param: val}) for val in vals]
            q_vals = Q("bool", must=val_filters)
            search = search.filter(q_vals)

        return search

    def elastic_search(self, request, search):
        params = request.query_params
        search_param = self.elastic_document_conf['params']['search']
        target = params.get(search_param, None)

        if target:
            q = Q(
                "multi_match", query=target, fields=settings.ELASTICSEARCH_ANALYZER_FIELDS,
                fuzziness="auto"
            )
            search = search.query(q)

        return search

    def elastic_pagination(self, request, search):
        page, page_size = self.elastic_document_conf['params']['pagination']
        start = (page - 1) * page_size
        search = search.extra(from_=start, size=page_size)

        return search

    def elastic_full_query_handling(self, request, search):
        for action in self.elastic_document_conf['params']:
            search = getattr(self, f'elastic_{action}', search)(
                request, search)

        return search


class CookiesMixin:
    cookies_to_delete = []
    request_cookies = {}
    response_cookies = {}

    def check_request_cookies(self, *keys):
        if not keys:
            self.request_cookies = self.request.COOKIES

        self.request_cookies.update({
            key: self.request.COOKIES.get(key, None) for key in keys if self.request.COOKIES.get(key, None)})

        return bool(self.request_cookies)

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
