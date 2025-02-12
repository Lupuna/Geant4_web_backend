from rest_framework import serializers

from geant_examples.models import Example, Tag, UserExample

from users.models import User

from api.v1.serializers.users_serializers import UserQuickInfoSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('title', )


class ExampleSerializer(serializers.ModelSerializer):
    users = UserQuickInfoSerializer(many=True, required=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ('title', 'key_s3', 'date_to_update',
                  'users', 'tags', 'category', )

    def create(self, validated_data):
        users_data = validated_data.pop('users')
        tags_data = validated_data.pop('tags', [])
        example = Example.objects.create(**validated_data)

        usernames = (user_data['username'] for user_data in users_data)
        users = User.objects.filter(username__in=usernames)

        if tags_data:
            tags_titles = (tag_data['title'] for tag_data in tags_data)
            tags = Tag.objects.filter(title__in=tags_titles)

            for tag in tags:
                example.tags.add(tag)

        for user in users:
            example.users.add(user)

        return example


class ExampleForUserSerializer(serializers.Serializer):
    title = serializers.CharField()
    tags = TagSerializer(many=True)
    status = serializers.SerializerMethodField(method_name='get_status')

    def get_status(self, obj):
        return obj.example_user[0].status
