from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from geant_examples.models import Example, Tag, UserExample, ExampleGeant, ExamplesTitleRelation

from users.models import User

from api.v1.serializers.users_serializers import UserQuickInfoSerializer


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
    examples_geant = ExampleGeantGETSerializer(many=True)

    def get_status(self, obj):
        return obj.example_user[0].status
