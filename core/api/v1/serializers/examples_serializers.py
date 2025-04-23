from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from geant_examples.models import Example, Tag, UserExampleCommand, ExampleCommand, Command, CommandValue
from geant_examples.validators import title_not_verbose_view

from users.models import User

from api.v1.serializers.users_serializers import UserQuickInfoSerializer
from api.v1.serializers.validators import m2m_validator

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

class DetailCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = (
            "title",
            "default",
            "order_index",
            "min",
            "max",
            "values",
        )

class DetailExampleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_verbose = serializers.CharField()
    title_not_verbose = serializers.CharField()
    description = serializers.CharField()
    date_to_update = serializers.DateField()
    tags = TagSerializer(many=True)
    category = serializers.CharField()
    example_commands = ExampleCommandGETSerializer(many=True)
    commands = DetailCommandSerializer(many=True)

class ExampleCommandPOSTSerializer(serializers.ModelSerializer):
    params = serializers.CharField(source='key_s3')

    class Meta:
        model = ExampleCommand
        fields = ('params', )

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

class ExampleGETSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_verbose = serializers.CharField()
    title_not_verbose = serializers.CharField()
    description = serializers.CharField()
    date_to_update = serializers.DateField()
    tags = TagSerializer(many=True)
    category = serializers.CharField()
    example_commands = ExampleCommandGETSerializer(many=True)

class ExamplePOSTSerializer(serializers.ModelSerializer):
    title_verbose = serializers.CharField(required=True)
    title_not_verbose = serializers.CharField(required=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title_verbose', 'title_not_verbose',
                  'description', 'tags', 'category', )

    def validate_tags(self, value):
        if value:
            return m2m_validator(value, Tag, 'title')

        return value

    def validate_title_not_verbose(self, value):
        title_not_verbose_view(value)

        if self.Meta.model.objects.filter(title_not_verbose=value).exists():
            raise ValidationError('This title_not_verbose already in use')

        return value

    def validate_title_verbose(self, value):
        if self.Meta.model.objects.filter(title_verbose=value).exists():
            raise ValidationError('This title_verbose already in use')

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
                  'description', 'date_to_update', 'tags', 'category', )
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
        if value:
            return m2m_validator(value, Tag, 'title')

        return value

class ExampleForUserSerializer(serializers.Serializer):
    title_verbose = serializers.SerializerMethodField(
        method_name='get_title_verbose')
    description = serializers.SerializerMethodField(
        method_name='get_description')
    creation_date = serializers.DateTimeField()
    date_to_update = serializers.SerializerMethodField(
        method_name='get_date_to_update')
    status = serializers.IntegerField()
    tags = serializers.SerializerMethodField(method_name='get_tags')
    params = serializers.SerializerMethodField()

    def get_title_verbose(self, obj):
        return obj.example_command.example.title_verbose

    def get_description(self, obj):
        return obj.example_command.example.description

    def get_date_to_update(self, obj):
        return obj.example_command.example.date_to_update

    def get_params(self, obj):
        key = obj.example_command.key_s3
        raw_params = key.split('___', 1)[1].split('___')

        if not any(raw_params):
            return {}

        params = dict([param.split('=') for param in raw_params])

        return params

    def get_tags(self, obj):
        return TagSerializer(obj.example_command.example.tags.all(), many=True).data

class ExampleCommandUpdateStatusSerializer(serializers.Serializer):
    key_s3 = serializers.CharField()
    err_body = serializers.CharField(required=False)
