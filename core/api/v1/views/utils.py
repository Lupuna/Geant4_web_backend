from .mixins import ElasticMixin

from django.db.models import Model

from math import ceil


def get_response_data_with_pages_count(self, model: Model, response_data: list):
    if not issubclass(self.__class__, ElasticMixin):
        raise TypeError(
            'Can add count of pages only in ElasticMixin inheritor')

    document_conf = self.elastic_document_conf
    page_size = document_conf['pagination_page_size']
    objs_count = model.objects.count()
    pages_count = ceil(objs_count/page_size)
    response_data.append({'pages_count': pages_count})
    return response_data
