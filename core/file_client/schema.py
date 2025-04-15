from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes

image_schema = {
    'multipart/form-data': {
        'type': 'object',
        'properties': {
            'image': build_basic_type(OpenApiTypes.BINARY)
        },
        'required': ['image']
    }
}
