from elasticsearch_dsl import Q

from django.conf import settings


class ElasticMixin:
    def get_elastic_document_conf(self):
        if not hasattr(self, 'elastic_document') or self.elastic_document == None:
            raise AttributeError(
                'If you want to use ElasticSearch you need to set elastic document on "elastic_document" attribute')

        document = self.elastic_document

        return settings.ELASTIC_PARAMS_CONF['documents'][document.__name__]

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
