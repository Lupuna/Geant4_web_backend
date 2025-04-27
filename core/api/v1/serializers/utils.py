from typing import Type

from django.db.models import Model
from django.db.utils import IntegrityError
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from functools import wraps


def bulk_create_children(parent: Model, child_data: list[dict], child_model: Type[Model], parent_field: str):
    objs = [child_model(**{parent_field: parent}, **data)
            for data in child_data]
    child_model.objects.bulk_create(objs)


def obj_can_exist(save_method):
    """If you do not want use validation of uniqueness on serialization level,
            you can decorate save method in serializer by this decorator.
            If requirement of uniqueness is satisfied you reduce the number of queries to 1"""

    @wraps(save_method)
    def wrapper(self, *args, **kwargs):
        if issubclass(self.__class__, serializers.ModelSerializer):
            model = self.Meta.model
        else:
            model = self.instance.__class__

        try:
            with transaction.atomic():
                new_obj = save_method(self, *args, **kwargs)
        except IntegrityError as err:
            unique_fields = [
                field.name for field in model._meta.fields if field.unique]
            str_err = str(err)

            for field in unique_fields:
                if f'({field})' in str_err:
                    error_field_name = field
                    break

            error_value = self.validated_data[error_field_name]
            new_obj = model.objects.get(**{error_field_name: error_value})
        return new_obj
    return wrapper


def raise_validation_error_instead_integrity(raising_method):
    @wraps(raising_method)
    def wrapper(self, *args, **kwargs):
        try:
            with transaction.atomic():
                obj = raising_method(self, *args, **kwargs)
        except IntegrityError as err:
            message = str(err).split('\n')[1]
            raise ValidationError(message)
        return obj
    return wrapper


def check_attrs(obj, attrs: dict):
    for key, val in attrs.items():
        obj_field = getattr(obj, key, None)
        if not obj_field or obj_field != val:
            return False
    return True
