from rest_framework.exceptions import ValidationError
from loguru import logger


def m2m_add_validators(objects_data, model, identificator):
    values = [user_data[identificator] for user_data in objects_data]

    if len(values) == len(set(values)):
        objects = model.objects.filter(**{f'{identificator}__in': values})

        if len(objects) != len(values):
            existing_values = set(
                objects.values_list(identificator, flat=True))
            missing_values = set(values) - existing_values

            raise ValidationError(
                f'Theese users: ({', '.join(missing_values)}) - do not exist')
    else:
        raise ValidationError(f'{identificator}s must be unique')

    return values
