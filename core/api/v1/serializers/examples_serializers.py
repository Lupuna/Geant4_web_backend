from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from geant_examples.models import Example, Tag, UserExample, ExampleGeant, ExamplesTitleRelation

from users.models import User

from api.v1.serializers.users_serializers import UserQuickInfoSerializer
from api.v1.serializers.validators import m2m_validator


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('title', )


class ExampleGeantGETSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    key_s3 = serializers.CharField()


class ExampleGeantPOSTSerializer(serializers.ModelSerializer):
    params = serializers.CharField(source='key_s3')

    class Meta:
        model = ExampleGeant
        fields = ('params', )

    def validate(self, attrs):
        example_pk = self.context.get('example_pk')
        attrs.setdefault('example_id', example_pk)

        try:
            example = Example.objects.get(id=example_pk)
        except Example.DoesNotExist:
            raise ValidationError('Provided Example does not exists')

        try:
            example_geant_title = ExamplesTitleRelation.objects.get(
                title_verbose=example.title).title_not_verbose
        except ExamplesTitleRelation.DoesNotExist:
            raise ValidationError('Example title is impossible')

        attrs.setdefault('title', example_geant_title)

        return attrs


class ExampleGETSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    date_to_update = serializers.DateField()
    users = UserQuickInfoSerializer(many=True)
    tags = TagSerializer(many=True)
    category = serializers.CharField()
    examples_geant = ExampleGeantGETSerializer(many=True)


class ExamplePOSTSerializer(serializers.ModelSerializer):
    users = UserQuickInfoSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title', 'users', 'tags', 'category', )
        extra_kwargs = {
            'category': {'required': False}
        }

    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        tags_data = validated_data.pop('tags', [])
        example = super().create(validated_data)

        if users_data:
            usernames = [user_data['username'] for user_data in users_data]
            users = User.objects.filter(username__in=usernames)
            example.users.add(*users)

        if tags_data:
            tags_titles = [tag_data['title'] for tag_data in tags_data]
            tags = Tag.objects.filter(title__in=tags_titles)
            example.tags.add(*tags)

        return example

    def validate(self, attrs):
        title = attrs.get('title')

        if not ExamplesTitleRelation.objects.filter(title_verbose=title).exists():
            raise ValidationError('This title not in possible title list')

        return ExamplePATCHSerializer().validate(attrs)


class ExamplePATCHSerializer(serializers.ModelSerializer):
    users = UserQuickInfoSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('users', 'tags', 'category', )
        extra_kwargs = {
            'users': {'required': False},
            'tags': {'required': False},
            'category': {'required': False}
        }

    def update(self, instance, validated_data):
        users_data = validated_data.pop('users', [])
        tags_data = validated_data.pop('tags', [])
        updated_instance = super().update(instance, validated_data)

        if users_data:
            usernames = tuple(user_data['username']
                              for user_data in users_data)
            users_to_instanse = User.objects.filter(
                username__in=usernames)
            updated_instance.users.add(*users_to_instanse)

        if tags_data:
            titles = tuple(tag_data['title'] for tag_data in tags_data)
            tags_to_instanse = Tag.objects.filter(title__in=titles)
            updated_instance.tags.add(*tags_to_instanse)

        return updated_instance

    def validate(self, attrs):
        users_data = attrs.get('users', [])
        tags_data = attrs.get('tags', [])

        if users_data:
            m2m_validator(users_data, User, 'username')

        if tags_data:
            m2m_validator(tags_data, Tag, 'title')

        return attrs


class ExampleForUserSerializer(serializers.Serializer):
    title = serializers.CharField()
    tags = TagSerializer(many=True)
    status = serializers.SerializerMethodField(method_name='get_status')
    examples_geant = ExampleGeantGETSerializer(many=True)

    def get_status(self, obj):
        return obj.example_user[0].status
