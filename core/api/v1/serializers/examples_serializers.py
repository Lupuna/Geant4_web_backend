from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from geant_examples.models import Example, Tag, UserExample

from users.models import User

from api.v1.serializers.users_serializers import UserQuickInfoSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('title', )


class ExampleSerializer(serializers.ModelSerializer):
    users = UserQuickInfoSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title', 'key_s3', 'date_to_update',
                  'users', 'tags', 'category', )
        extra_kwargs = {
            'key_s3': {'required': False},
            'title': {'required': False}
        }

    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        tags_data = validated_data.pop('tags', [])
        example = super().create(validated_data)

        if users_data:
            usernames_set = {user_data['username'] for user_data in users_data}
            usernames = tuple(user_data['username']
                              for user_data in users_data)

            if len(usernames) == len(usernames_set):
                users = User.objects.filter(username__in=usernames)

                for user in users:
                    example.users.add(user)
            else:
                raise ValidationError(
                    'Cannot add more than one user with the same username')

        if tags_data:
            tags_titles_set = {tag_data['title'] for tag_data in tags_data}
            tags_titles = tuple(tag_data['title'] for tag_data in tags_data)

            if len(tags_titles_set) == len(tags_titles):
                tags = Tag.objects.filter(title__in=tags_titles)

                for tag in tags:
                    example.tags.add(tag)
            else:
                raise ValidationError(
                    'Cannot add more than one tag with the same title')

        return example

    def update(self, instance, validated_data):
        users_data = validated_data.pop('users', [])
        tags_data = validated_data.pop('tags', [])
        updated_instance = super().update(instance, validated_data)

        if users_data:
            usernames = tuple(user_data['username']
                              for user_data in users_data)
            users_to_instanse = User.objects.filter(
                username__in=usernames)

            for user in users_to_instanse:
                updated_instance.users.add(user)

        if tags_data:
            titles = tuple(tag_data['title'] for tag_data in tags_data)
            tags_to_instanse = Tag.objects.filter(title__in=titles)

            for tag in tags_to_instanse:
                updated_instance.tags.add(tag)

        return updated_instance

    def validate(self, attrs):
        users_data = attrs.get('users', [])
        tags_data = attrs.get('tags', [])

        if users_data:
            usernames_set = {user_data['username'] for user_data in users_data}
            usernames = tuple(user_data['username']
                              for user_data in users_data)

            if len(usernames) == len(usernames_set):
                users = User.objects.filter(username__in=usernames)

                if len(users) != len(usernames):
                    raise ValidationError('Any of given users do not exist')
            else:
                raise ValidationError('Users must be unique')

        if tags_data:
            tags_titles_set = {tag_data['title'] for tag_data in tags_data}
            tags_titles = tuple(tag_data['title'] for tag_data in tags_data)

            if len(tags_titles_set) == len(tags_titles):
                tags = Tag.objects.filter(title__in=tags_titles)

                if len(tags) != len(tags_titles):
                    raise ValidationError('Any of given tags do not exist')
            else:
                raise ValidationError('Tags must be unique')

        return attrs


class ExampleForUserSerializer(serializers.Serializer):
    title = serializers.CharField()
    tags = TagSerializer(many=True)
    status = serializers.SerializerMethodField(method_name='get_status')

    def get_status(self, obj):
        return obj.example_user[0].status
