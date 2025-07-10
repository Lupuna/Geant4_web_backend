from typing import Type

from django.db.models import Model
from django.db.utils import IntegrityError
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from functools import wraps

from users.models import User


def bulk_create_children(parent: Model, child_data: list[dict], child_model: Type[Model], parent_field: str):
    objs = [child_model(**{parent_field: parent}, **data)
            for data in child_data]
    child_model.objects.bulk_create(objs)


def get_serializer_model(serializer: serializers.Serializer):
    if issubclass(serializer.__class__, serializers.ModelSerializer):
        model = serializer.Meta.model
    else:
        model = serializer.instance.__class__
    return model


def get_unique_model_fields(model: Model):
    return [field.name for field in model._meta.fields if field.unique]


def get_unique_error_field(unique_fields, integrity_error_message: str):
    for field in unique_fields:
        if f'({field})' in integrity_error_message:
            return field


def obj_can_exist(save_method):
    """If you do not want use validation of uniqueness on serialization level,
            you can decorate save method in serializer by this decorator.
            If requirement of uniqueness is satisfied you reduce the number of queries to 1"""

    @wraps(save_method)
    def wrapper(self, *args, **kwargs):
        model = get_serializer_model(self)

        try:
            with transaction.atomic():
                new_obj = save_method(self, *args, **kwargs)
        except IntegrityError as err:
            unique_fields = get_unique_model_fields(model)
            str_err = str(err)
            error_field_name = get_unique_error_field(unique_fields, str_err)
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


def get_existing_conflicts(data: dict) -> list:
    conflicts = []
    if User.objects.filter(username=data.get('username'), is_active=True).exists():
        conflicts.append('username')
    if User.objects.filter(email=data.get('email'), is_active=True).exists():
        conflicts.append('email')
    return conflicts


def get_custom_absolute_uri(request, path):
    host = request.META.get("HTTP_X_FORWARDED_HOST", request.get_host())
    proto = request.META.get("HTTP_X_FORWARDED_PROTO", request.scheme)
    port = request.META.get("HTTP_X_FORWARDED_PORT", "")

    if port and port not in ["80", "443"]:
        host = f"{host}:{port}"

    return f"{proto}://{host}{path}"

def resolve_dot_notation(obj, path: str):
    for part in path.split('.'):
        obj = getattr(obj, part)
    return obj
