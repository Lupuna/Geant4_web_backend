from typing import Type

from django.db.models import Model


def bulk_create_children(parent: Model, child_data: list[dict], child_model: Type[Model], parent_field: str):
    objs = [child_model(**{parent_field: parent}, **data) for data in child_data]
    child_model.objects.bulk_create(objs)