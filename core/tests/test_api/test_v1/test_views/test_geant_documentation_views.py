import uuid
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from api.v1.views.geant_documentation_views import ArticleViewSet, ElementViewSet, SubscriptionViewSet
from file_client.exceptions import FileClientException
from geant_documentation.models import Article, Category, Chapter, Subscription, Element
from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest


class ArticleViewSetTestCase(AuthSettingsTest):

    def setUp(self):
        self.category = Category.objects.create(title='Cat 1')
        self.chapter = Chapter.objects.create(title='Chap 1')

        self.article = Article.objects.create(
            title='test_title',
            description='test_description',
            category=self.category,
            chapter=self.chapter,
        )

        self.subscription = Subscription.objects.create(
            title='Old Sub',
            subscription_order=1,
            article=self.article
        )
        self.factory = APIRequestFactory()
        self.view = ArticleViewSet
        self.url_list = reverse('articles-list')
        self.detail_url = reverse('articles-detail', kwargs={'pk': self.article.id})
        self.user.is_staff = True

    def test_retrieve_action(self):
        view = self.view.as_view({'get': 'retrieve'})
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscriptions', response.data)

    def test_create_article_requires_auth(self):
        data = {
            'title': 'New Article',
            'description': 'Desc',
            'chosen': True,
            'category': self.category.id,
            'chapter': self.chapter.id,
            'subscriptions': []
        }
        view = self.view.as_view({'post': 'create'})
        request = self.factory.post(self.url_list, data, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_article_success(self):
        view = self.view.as_view({'post': 'create'})
        data = {
            'title': 'Created',
            'description': 'Desc',
            'chosen': False,
            'category': self.category.id,
            'chapter': self.chapter.id,
            'subscriptions': []
        }
        request = self.factory.post(self.url_list, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Article.objects.filter(title='Created').exists())

    def test_update_article_deletes_old_subscriptions(self):
        view = self.view.as_view({'put': 'update'})
        self.assertEqual(self.article.subscriptions.count(), 1)

        new_sub_data = [
            {'title': 'Updated Sub', 'subscription_order': 2, 'elements': []}
        ]
        data = {
            'title': self.article.title,
            'description': self.article.description,
            'chosen': self.article.chosen,
            'category': self.category.id,
            'chapter': self.chapter.id,
            'subscriptions': new_sub_data
        }

        request = self.factory.put(self.detail_url, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article = Article.objects.get(id=self.article.id)
        self.assertEqual(article.subscriptions.count(), 1)
        self.assertEqual(article.subscriptions.first().title, 'Updated Sub')

    def test_delete_article(self):
        view = self.view.as_view({'delete': 'destroy'})
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())


class SubscriptionViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = SubscriptionViewSet
        self.user.is_staff = True

        self.category = Category.objects.create(title='Category')
        self.chapter = Chapter.objects.create(title='Chapter')

        self.article = Article.objects.create(
            title='Article',
            description='Some desc',
            category=self.category,
            chapter=self.chapter,
        )

        self.subscription = Subscription.objects.create(
            title='Subscription',
            subscription_order=1,
            article=self.article,
        )

        self.list_url = reverse(
            'article-subscriptions-list',
            kwargs={'article_pk': self.article.id}
        )

        self.detail_url = reverse(
            'article-subscriptions-detail',
            kwargs={'article_pk': self.article.id, 'pk': self.subscription.id}
        )

    def test_list_subscriptions(self):
        self.login_user()
        view = self.view.as_view({'get': 'list'})
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_subscription(self):
        view = self.view.as_view({'get': 'retrieve'})
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id, pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.subscription.title)

    def test_create_subscription_requires_auth(self):
        view = self.view.as_view({'post': 'create'})
        data = {'title': 'New Subscription'}
        request = self.factory.post(self.list_url, data, format='json')
        response = view(request, article_pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_subscription_success(self):
        view = self.view.as_view({'post': 'create'})
        data = {'title': 'New Subscription', 'elements': [], 'subscription_order': 2}
        request = self.factory.post(self.list_url, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subscription.objects.filter(title='New Subscription').exists())

    def test_update_subscription(self):
        view = self.view.as_view({'put': 'update'})
        data = {'title': 'Updated Subscription', 'elements': [], 'subscription_order': 1}
        request = self.factory.put(self.detail_url, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id, pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.title, 'Updated Subscription')

    def test_delete_subscription(self):
        view = self.view.as_view({'delete': 'destroy'})
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id, pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subscription.objects.filter(id=self.subscription.id).exists())


class ElementViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ElementViewSet
        self.user.is_staff = True
        self.category = Category.objects.create(title='Category')
        self.chapter = Chapter.objects.create(title='Chapter')
        self.article = Article.objects.create(
            title='Article',
            description='Some desc',
            category=self.category,
            chapter=self.chapter,
        )
        self.subscription = Subscription.objects.create(
            title='Subscription',
            subscription_order=1,
            article=self.article,
        )
        self.element = Element.objects.create(
            text='Element',
            subscription=self.subscription,
            element_order=1
        )
        self.list_url = reverse(
            'article-subscription-elements-list',
            kwargs={'article_pk': self.article.id, 'subscription_pk': self.subscription.id}
        )
        self.detail_url = reverse(
            'article-subscription-elements-detail',
            kwargs={
                'article_pk': self.article.id,
                'subscription_pk': self.subscription.id,
                'pk': self.element.id
            }
        )

    def test_list_elements(self):
        view = self.view.as_view({'get': 'list'})
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id, subscription_pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_element(self):
        view = self.view.as_view({'get': 'retrieve'})
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, subscription_pk=self.subscription.id, pk=self.element.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], self.element.text)

    def test_create_element_requires_auth(self):
        view = self.view.as_view({'post': 'create'})
        data = {'text': 'New Element', 'files': []}
        request = self.factory.post(self.list_url, data, format='json')
        response = view(request, article_pk=self.article.id, subscription_pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_element_success(self):
        view = self.view.as_view({'post': 'create'})
        data = {'text': 'New Element', 'files': [], 'element_order': 2}
        request = self.factory.post(self.list_url, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, subscription_pk=self.subscription.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Element.objects.filter(text='New Element').exists())

    def test_update_element(self):
        view = self.view.as_view({'put': 'update'})
        data = {'text': 'Updated Title', 'files': [], 'element_order': 1}
        request = self.factory.put(self.detail_url, data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, article_pk=self.article.id, subscription_pk=self.subscription.id, pk=self.element.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.element.refresh_from_db()
        self.assertEqual(self.element.text, 'Updated Title')

    def test_delete_element(self):
        view = self.view.as_view({'delete': 'destroy'})
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        response = view(request, subscription_pk=self.subscription.id, pk=self.element.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Element.objects.filter(id=self.element.id).exists())


class FileViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.uuid = str(uuid.uuid4())
        self.user.is_staff = True
        self.user.save()

    @patch('api.v1.views.geant_documentation_views.render_and_upload_documentation_image_task.delay')
    @patch('api.v1.views.geant_documentation_views.handle_file_upload')
    def test_create_webp_ok(self, mock_handle, mock_task):
        self.login_user()
        file = create_temp_file()
        mock_handle.return_value = "/fake/path/file.png"

        url = reverse('file-manage', args=[self.uuid, 'csv'])
        response = self.client.post(url, data={'file': file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_handle.assert_called_once()

    @patch('api.v1.views.geant_documentation_views.render_and_upload_documentation_graphic_task.delay')
    @patch('api.v1.views.geant_documentation_views.handle_file_upload')
    def test_create_csv_ok(self, mock_handle, mock_task):
        self.login_user()
        file = create_temp_file()
        mock_handle.return_value = "/fake/path/file.csv"

        url = reverse('file-manage', args=[self.uuid, 'csv'])
        response = self.client.post(url, data={'file': file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_handle.assert_called_once()
        mock_task.assert_called_once_with("/fake/path/file.csv", self.uuid)

    @patch('file_client.files_clients.ReadOnlyClient.delete')
    def test_delete_ok(self, mock_delete):
        self.login_user()
        url = reverse('file-manage', args=[self.uuid, 'csv'])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Image deleted"})
        mock_delete.assert_called_once()

    @patch('file_client.files_clients.ReadOnlyClient.download')
    def test_retrieve_ok(self, mock_download):
        self.login_user()
        mock_download.return_value = BytesIO(b'binary content')
        url = reverse('file-manage', args=[self.uuid, 'webp'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('Content-Disposition'), f'attachment; filename="{self.uuid}.webp"')

    @patch('file_client.files_clients.ReadOnlyClient.download')
    def test_retrieve_not_found(self, mock_download):
        self.login_user()
        mock_download.side_effect = FileClientException(404, {"detail": "Not found on disk"})

        url = reverse('file-manage', args=[self.uuid, 'webp'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Not found on disk"})


def create_temp_file():
    image = Image.new('RGB', (100, 100), color='blue')
    file_io = BytesIO()
    image.save(file_io, format='PNG')
    file_io.seek(0)
    return SimpleUploadedFile("test_file.png", file_io.read(), content_type="image/png")

