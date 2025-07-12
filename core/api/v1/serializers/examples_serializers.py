from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.v1.serializers.users_serializers import UserQuickInfoSerializer
from api.v1.serializers.validators import m2m_validator
from geant_examples.models import Example, Tag, ExampleCommand, Command, CommandValue, CommandList, Category


class TagSerializer(serializers.Serializer):
    title = serializers.CharField()


class TagAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ExampleCommandGETSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    users = UserQuickInfoSerializer(many=True)
    key_s3 = serializers.CharField()


class CommandValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandValue
        fields = (
            "value",
        )


class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = (
            "title",
            "default",
            "order_index",
        )


class CommandListSerializer(serializers.ModelSerializer):
    command_values = serializers.SerializerMethodField()

    class Meta:
        model = CommandList
        fields = ('id', 'title', 'command_values')

    def get_command_values(self, obj):
        return [cv.value for cv in getattr(obj, 'prefetched_command_values', [])]


class DetailCommandSerializer(serializers.ModelSerializer):
    command_list = CommandListSerializer()

    class Meta:
        model = Command
        fields = (
            "title",
            "default",
            "order_index",
            "min",
            "max",
            "command_list",
            'signature'
        )


class DetailExampleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_verbose = serializers.CharField()
    title_not_verbose = serializers.CharField()
    description = serializers.CharField()
    date_to_update = serializers.DateField()
    tags = serializers.SerializerMethodField()
    category = serializers.CharField()
    commands = DetailCommandSerializer(many=True)

    def get_tags(self, obj):
        return list(obj.tags.all().values_list('title', flat=True))


class ExampleCommandPOSTSerializer(serializers.ModelSerializer):
    params = serializers.CharField(source='key_s3')

    class Meta:
        model = ExampleCommand
        fields = ('params',)

    def validate(self, attrs):
        example_pk = self.context.get('example_pk')
        user = self.context.get('user', None)

        try:
            example = Example.objects.get(id=example_pk)
        except Example.DoesNotExist:
            raise ValidationError('Provided Example does not exists')

        if not user:
            raise ValidationError(
                'ExampleCommand cannot be unattached to the user')

        return attrs

    def create(self, validated_data):
        user = self.context.get('user', None)
        example_pk = self.context.get('example_pk')
        validated_data.setdefault('example_id', example_pk)
        ex_command = super().create(validated_data)

        if user:
            ex_command.users.add(user)

        return ex_command


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('title', )


class ExampleGETSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_verbose = serializers.CharField()
    title_not_verbose = serializers.CharField()
    description = serializers.CharField()
    date_to_update = serializers.DateField()
    tags = serializers.SerializerMethodField()
    category = CategorySerializer()

    def get_tags(self, obj):
        return list(obj.tags.all().values_list('title', flat=True))

class ExamplePOSTSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title_verbose', 'title_not_verbose',
                  'description', 'tags', 'category',)

    def validate_tags(self, value: list[dict]):
        if value:
            return m2m_validator(value, Tag, 'title')

        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        example = super().create(validated_data)

        if tags:
            example.tags.add(*tags)

        return example


class ExamplePATCHSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title_verbose', 'title_not_verbose',
                  'description', 'date_to_update', 'tags', 'category',)
        extra_kwargs = {
            'description': {'required': False},
            'tags': {'required': False},
            'category': {'required': False},
            'title_verbose': {'required': False},
            'title_not_verbose': {'required': False}
        }

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        updated_instance = super().update(instance, validated_data)

        if tags:
            updated_instance.tags.add(*tags)

        return updated_instance

    def validate_tags(self, value):
        return ExamplePOSTSerializer().validate_tags(value)


class ExampleForUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_verbose = serializers.SerializerMethodField(
        method_name='get_title_verbose')
    description = serializers.SerializerMethodField(
        method_name='get_description')
    creation_date = serializers.DateTimeField()
    date_to_update = serializers.SerializerMethodField(
        method_name='get_date_to_update')
    status = serializers.IntegerField()
    tags = serializers.SerializerMethodField(method_name='get_tags')
    categories = serializers.SerializerMethodField(method_name='get_categories')
    params = serializers.SerializerMethodField()
    example_id = serializers.SerializerMethodField(method_name='get_example_id')

    def get_title_verbose(self, obj):
        return obj.example_command.example.title_verbose

    def get_description(self, obj):
        return obj.example_command.example.description

    def get_date_to_update(self, obj):
        return obj.example_command.example.date_to_update

    def get_params(self, obj):
        key = obj.example_command.key_s3
        raw_params = key.split('__', 1)[1].split('__')

        if not any(raw_params):
            return {}

        params = dict([param.split('=') for param in raw_params])

        return params

    def get_tags(self, obj):
        return list(obj.example_command.example.tags.all().values_list('title', flat=True))

    def get_categories(self, obj):
        return CategorySerializer(obj.example_command.example.category).data

    def get_example_id(self, obj):
        return obj.example_command.example.id


class ExampleCommandUpdateStatusSerializer(serializers.Serializer):
    key_s3 = serializers.CharField()
    err_body = serializers.CharField(required=False)
