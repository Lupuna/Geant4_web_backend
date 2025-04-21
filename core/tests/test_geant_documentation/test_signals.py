from django.test import TestCase

from geant_documentation.models import Chapter, Category, Article, Subscription, Element, File


class ElementSignalTestCase(TestCase):
    def setUp(self):
        self.chapter = Chapter.objects.create(title="Signals")
        self.category = Category.objects.create(title="Programming")
        self.article = Article.objects.create(
            title="Signal Basics",
            description="How Django signals work",
            chapter=self.chapter,
            category=self.category
        )
        self.subscription = Subscription.objects.create(
            title="Signal Lesson",
            subscription_order=1,
            article=self.article
        )

    def test_file_created_for_valid_type(self):
        element = Element.objects.create(
            subscription=self.subscription,
            element_order=1,
            type=Element.TypeChoice.GRAPHIC
        )
        self.assertTrue(File.objects.filter(element=element, format=element.type).exists())

    def test_file_not_created_for_non_file_type(self):
        element = Element.objects.create(
            subscription=self.subscription,
            element_order=1,
            type=Element.TypeChoice.TEXT
        )
        self.assertFalse(File.objects.filter(element=element).exists())

    def test_file_not_created_on_update(self):
        element = Element.objects.create(
            subscription=self.subscription,
            element_order=1,
            type=Element.TypeChoice.IMAGE
        )
        File.objects.all().delete()  # reset
        element.text = "Some image description"
        element.save()
        self.assertEqual(File.objects.count(), 0)