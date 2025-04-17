from elasticsearch_dsl import Q

from django_elasticsearch_dsl import Document

from django.conf import settings


class ElasticMixin:
    def get_elastic_document_class(self) -> Document:
        if not hasattr(self, 'elastic_document') or self.elastic_document is None:
            raise AttributeError(
                'If you want to use ElasticSearch you need to set elastic document on "elastic_document" attribute')

        return self.elastic_document

    def get_elastic_document_conf(self) -> dict:
        document = self.get_elastic_document_class()

        try:
            document_conf = settings.ELASTIC_PARAMS_CONF['documents'][document.__name__]
        except KeyError:
            raise KeyError('Need to setup elastic document in settings')

        return document_conf

    def elastic_filter(self, request, search):
        document_params_conf = self.get_elastic_document_conf()
        params = request.query_params
        filter_params = set(
            document_params_conf['params']['filter']) & set(params.keys())

        for param in filter_params:
            vals = params.get(param, None)
            vals = vals.split(',')
            val_filters = [Q("term", **{param: val}) for val in vals]
            q_vals = Q("bool", must=val_filters)
            search = search.filter(q_vals)

        return search

    def elastic_search(self, request, search):
        document_params_conf = self.get_elastic_document_conf()
        params = request.query_params
        search_param = document_params_conf['params']['search']
        target = params.get(search_param, None)

        if target:
            q = Q(
                "multi_match", query=target, fields=settings.ELASTICSEARCH_ANALYZER_FIELDS,
                fuzziness="auto"
            )
            search = search.query(q)

        return search

    def elastic_pagination(self, request, search):
        document_params_conf = self.get_elastic_document_conf()
        page, page_size = document_params_conf['params']['pagination']
        start = (page - 1) * page_size
        search = search.extra(from_=start, size=page_size)

        return search

    def elastic_full_query_handling(self, request, search):
        document_params_conf = self.get_elastic_document_conf()

        for action in document_params_conf['params']:
            search = getattr(self, f'elastic_{action}', search)(
                request, search)

        return search
