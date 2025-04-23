from rest_framework.exceptions import ValidationError


def m2m_validator(objects_data, model, identificator):
    values = [data[identificator] for data in objects_data]

    if len(values) == len(set(values)):
        objects = model.objects.filter(**{f'{identificator}__in': values})

        if len(objects) != len(values):
            existing_values = set(
                objects.values_list(identificator, flat=True))
            missing_values = set(values) - existing_values

            raise ValidationError(
                f'Theese {identificator}s: ({", ".join(missing_values)}) - do not exist')
    else:
        raise ValidationError(f'{identificator}s must be unique')

    return objects
