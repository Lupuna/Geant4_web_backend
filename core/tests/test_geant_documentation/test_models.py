from django.test import TestCase

from geant_documentation.models import Category, Chapter, Article, Subscription, Element, File
from django.core.exceptions import ValidationError


class CategoryTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Science")

    def test_str(self):
        self.assertEqual(str(self.category), "Science")


class ChapterModelTest(TestCase):
    def setUp(self):
        self.chapter = Chapter.objects.create(title="Science")

    def test_str(self):
        self.assertEqual(str(self.chapter), "Science")


class ArticleTestCase(TestCase):
    def setUp(self):
        self.chapter = Chapter.objects.create(title="Physics")
        self.category = Category.objects.create(title="Science")
        self.article = Article.objects.create(
            title="My Article",
            description="Interesting description",
            chapter=self.chapter
        )

    def test_str(self):
        self.assertEqual(str(self.article), "My Article")


class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.chapter = Chapter.objects.create(title="Math")
        self.category = Category.objects.create(title="Education")
        self.article = Article.objects.create(
            title="Algebra Basics",
            description="Intro to algebra",
            chapter=self.chapter,
            category=self.category
        )

        self.subscription = Subscription.objects.create(
            title="Lesson 1",
            subscription_order=1,
            article=self.article
        )

    def test_str(self):
        self.assertEqual(str(self.subscription), "Lesson 1")

    def test_meta_data(self):
        self.assertEqual(self.subscription._meta.unique_together, (('article', 'subscription_order'), ('article', 'title')))
        self.assertEqual(self.subscription._meta.ordering, ('subscription_order',))


class ElementTestCase(TestCase):
    def setUp(self):
        self.chapter = Chapter.objects.create(title="Logic")
        self.category = Category.objects.create(title="Math")
        self.article = Article.objects.create(
            title="Logic Basics",
            description="Truth tables and stuff",
            chapter=self.chapter,
            category=self.category
        )
        self.subscription = Subscription.objects.create(
            title="First lesson",
            subscription_order=1,
            article=self.article
        )

    def test_str(self):
        element = Element.objects.create(
            element_order=1,
            type=Element.TypeChoice.TEXT,
            text="Some content",
            subscription=self.subscription
        )
        self.assertEqual(str(element), "text")

    def test_meta_data(self):
        self.assertEqual(Element._meta.unique_together, (('subscription', 'element_order'),))
        self.assertEqual(Element._meta.ordering, ('element_order',))

    def test_text_required_for_text_type(self):
        element = Element(
            element_order=1,
            type=Element.TypeChoice.TEXT,
            subscription=self.subscription
        )
        with self.assertRaises(ValidationError) as context:
            element.clean()
        self.assertIn('Text must be set when type is "text".', str(context.exception))

    def test_text_not_allowed_for_image_type(self):
        element = Element(
            element_order=1,
            type=Element.TypeChoice.IMAGE,
            text="This should not be here",
            subscription=self.subscription
        )
        with self.assertRaises(ValidationError) as context:
            element.clean()
        self.assertIn('Text must NOT be set when type is "webp".', str(context.exception))

    def test_clean_passes_for_valid_image_element(self):
        element = Element(
            element_order=1,
            type=Element.TypeChoice.IMAGE,
            subscription=self.subscription
        )
        try:
            element.clean()
        except ValidationError as e:
            self.fail(f"ValidationError raised unexpectedly: {e}")


class FileTestCase(TestCase):

    def setUp(self):
        self.chapter = Chapter.objects.create(title="Logic")
        self.category = Category.objects.create(title="Math")
        self.article = Article.objects.create(
            title="Logic Basics",
            description="Truth tables and stuff",
            chapter=self.chapter,
            category=self.category
        )
        self.subscription = Subscription.objects.create(
            title="First lesson",
            subscription_order=1,
            article=self.article
        )
        self.element = Element.objects.create(
            element_order=1,
            type=Element.TypeChoice.IMAGE,
            text="Some content",
            subscription=self.subscription
        )
        self.file = File.objects.create(
            format=File.FormatChoice.WEBP,
            element=self.element
        )

    def test_str(self):
        correct_meaning = f'{self.file.uuid}.{self.file.format}'
        self.assertEqual(correct_meaning, str(self.file))

    def test_element_file_limit(self):
        for _ in range(7):
            File.objects.create(
                format=File.FormatChoice.WEBP,
                element=self.element
            )
        with self.assertRaises(ValidationError) as ctx:
            File.objects.create(
                format=File.FormatChoice.WEBP,
                element=self.element
            )
        self.assertIn('Max files for element is 8', str(ctx.exception))
