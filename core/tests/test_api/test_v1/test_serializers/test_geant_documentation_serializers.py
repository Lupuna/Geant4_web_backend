from uuid import uuid4

from django.test import TestCase

from api.v1.serializers.geant_documentation_serializers import (
    FileSerializer,
    ElementSerializer,
    SubscriptionSerializer,
    ArticleSerializer
)
from geant_documentation.models import File, Element, Category, Chapter, Article, Subscription


# TODO не забыть добавить в сенин Base класс сигналы всякие интересные


class FileSerializerTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title='test_title',
            description='test_description',
        )
        self.subscription = Subscription.objects.create(
            title='test_title',
            subscription_order=1,
            article=self.article
        )
        self.element = Element.objects.create(
            text="Old",
            element_order=1,
            type="image",
            subscription=self.subscription
        )

    def test_file_serializer(self):
        file = File.objects.create(format="webp", element=self.element)
        serializer = FileSerializer(instance=file)
        self.assertEqual(serializer.data['format'], "webp")
        self.assertIn('uuid', serializer.data)
        self.assertTrue(serializer.data['uuid'], uuid4)


class ElementSerializerTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title='test_title',
            description='test_description',
        )
        self.subscription = Subscription.objects.create(
            title='test_title',
            subscription_order=1,
            article=self.article
        )

    def test_create_element_with_files(self):
        data = {
            "text": "Some text",
            "element_order": 1,
            "type": "webp",
            "files": [
                {"format": "webp"},
                {"format": "webp"},
            ]
        }
        serializer = ElementSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        element = serializer.save(subscription_id=self.subscription.id)
        self.assertEqual(element.files.count(), 2)
        self.assertEqual(element.text, "Some text")


class SubscriptionSerializerTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title='test_title',
            description='test_description',
        )

    def test_create_subscription_with_elements(self):
        data = {
            "title": "Basic Plan",
            "subscription_order": 1,
            "elements": [
                {
                    "text": "Element 1",
                    "element_order": 1,
                    "type": "text",
                    "files": []
                },
                {
                    "text": "Element 2",
                    "element_order": 2,
                    "type": "text",
                    "files": []
                }
            ]
        }
        serializer = SubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        sub = serializer.save(article_id=self.article.id)
        self.assertEqual(sub.elements.count(), 2)
        self.assertEqual(sub.title, "Basic Plan")


class ArticleSerializerTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Physics")
        self.chapter = Chapter.objects.create(title="Quantum Mechanics")

    def test_create_article_with_subscriptions(self):
        data = {
            "title": "Article 1",
            "description": "Quantum Basics",
            "chosen": False,
            "category": self.category.id,
            "chapter": self.chapter.id,
            "subscriptions": [
                {
                    "title": "Free Plan",
                    "subscription_order": 1,
                    "elements": [
                        {
                            "text": "Intro",
                            "element_order": 1,
                            "type": "text",
                            "files": []
                        }
                    ]
                }
            ]
        }

        serializer = ArticleSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        article = serializer.save()
        self.assertEqual(article.subscriptions.count(), 1)
        self.assertEqual(article.title, "Article 1")

    def test_update_deletes_old_subscriptions(self):
        article = Article.objects.create(
            title="Article X",
            description="Description",
            chosen=False,
            category=self.category,
            chapter=self.chapter
        )

        sub = Subscription.objects.create(
            title="Old Plan", subscription_order=1, article=article)
        self.assertEqual(article.subscriptions.count(), 1)

        update_data = {
            "title": "Article Updated",
            "description": "New description",
            "chosen": True,
            "category": self.category.id,
            "chapter": self.chapter.id,
            "subscriptions": [
                {
                    "title": "Updated Plan",
                    "subscription_order": 2,
                    "elements": []
                }
            ]
        }

        serializer = ArticleSerializer(instance=article, data=update_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.title, "Article Updated")
        self.assertEqual(updated.subscriptions.count(), 1)
        self.assertEqual(updated.subscriptions.first().title, "Updated Plan")