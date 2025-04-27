import io
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from file_client.exceptions import FileClientException
from users.models import User

from unittest.mock import patch

from geant_examples.models import Example, ExampleCommand, UserExampleCommand

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.users_serializers import UserProfileSerializer

from rest_framework.exceptions import ErrorDetail


class UserProfileTestCase(AuthSettingsTest):
    def setUp(self):
        self.url = reverse('user-profile')

    def test_retrieve_user_ok(self):
        self.login_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, UserProfileSerializer(self.user).data)

    def test_not_loggined_in(self):
        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'Authentication credentials were not provided.'})

    @patch('api.tasks.send_celery_mail.delay')
    def test_update_ok(self, mock_send):
        self.login_user()
        new_data = {'first_name': 'new_fname',
                    'email': 'test_email2@gmail.com'}
        response = self.client.patch(
            self.url, data=new_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once()
        self.assertEqual(User.objects.get(
            username=self.user.username).first_name, new_data['first_name'])

    @patch('api.tasks.send_celery_mail.delay')
    def test_email_update_bad(self, mock_send):
        data_to_update = {'email': 'test_email1@gmail.com'}
        self.login_user()
        response = self.client.patch(
            self.url, data=data_to_update, content_type='application/json')
        mock_send.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'email': [ErrorDetail(
            string='You already use this email', code='invalid')]})

    def test_delete_user(self):
        self.login_user()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(
            username=self.user.username).exists())

    def test_change_username(self):
        data = {
            'new_username': 'afs',
        }
        self.login_user()

        response = self.client.post(
            reverse('user-profile-update-username'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(
            username=self.user.username).exists())
        self.assertTrue(User.objects.filter(
            username=data['new_username']).exists())

    def test_username_already_exists(self):
        self.login_user()
        user2 = User.objects.create(username='any', email='any@gmail.com')
        data = {
            'new_username': user2.username,
        }

        response = self.client.post(
            reverse('user-profile-update-username'), data=data)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.data, [ErrorDetail(
            string='DETAIL:  Key (username)=(any) already exists.', code='invalid')])


class ConfirmEmailUpdateAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        self.url = reverse('user-profile')

    @patch('api.tasks.send_celery_mail.delay')
    def test_update_email_confirmed(self, mock_send):
        self.login_user()
        data_to_update = {'email': 'any@mail.ru'}
        self.client.patch(
            self.url, data=data_to_update, content_type='application/json')
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        token = args[1].split('/')[-1]
        confirm_url = reverse('confirm-email-update', kwargs={'token': token})
        confirm_response = self.client.get(confirm_url)
        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.data, {
                         'detail': 'Email updated successfully'})

    @patch('api.tasks.send_celery_mail.delay')
    def test_update_email_already_exists(self, mock_send):
        user2 = User.objects.create(username='ozzy', email='ozzy@mail.ru')
        data_to_update = {'email': user2.email}
        self.login_user()
        self.client.patch(
            self.url, data=data_to_update, content_type='application/json')
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        token = token = args[1].split('/')[-1]
        confirm_url = reverse('confirm-email-update', kwargs={'token': token})
        confirm_response = self.client.get(confirm_url)
        self.assertEqual(confirm_response.status_code, 400)
        self.assertEqual(confirm_response.data, [ErrorDetail(
            string='This email already in use', code='invalid')])


class UserExampleViewTestCase(AuthSettingsTest):
    @patch('geant_examples.documents.ExampleDocument.search')
    def test_get_examples(self, mock_exaples):
        mock_exaples.return_value.to_queryset.return_value = Example.objects.all()
        ex_data = {
            "title_verbose": "test_verbose",
            'title_not_verbose': 'TSU_XX_00',
            "category": "Optics"
        }
        example = Example.objects.create(**ex_data)
        ex_command = ExampleCommand.objects.create(
            key_s3='key-s3-TSU_XX_00___v=11', example=example)
        ex_command.users.add(self.user)
        us_ex_command = UserExampleCommand.objects.get(user=self.user)

        self.login_user()
        response = self.client.get(reverse('user-examples'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, [{'title_verbose': ex_data['title_verbose'], 'description': '', 'creation_date': str(us_ex_command.creation_date)[:-6].replace(' ', 'T') + 'Z', 'date_to_update': example.date_to_update, 'status': 0, 'tags': [], 'params': {'v': '11'}}])


class UserProfileImageViewSetTestCase(AuthSettingsTest):

    def setUp(self):
        self.url = reverse('user-profile-image')

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('api.v1.views.users_views.render_and_upload_profile_image_task.delay')
    @patch('api.v1.views.users_views.handle_file_upload')
    def test_create_image_ok(self, mock_handle, mock_task):
        self.login_user()
        image_file = create_temp_image()
        mock_handle.return_value = "/fake/path/test.png"

        boundary = 'BoUnDaRyStRiNg123'
        content_type = f'multipart/form-data; boundary={boundary}'
        response = self.client.post(
            self.url, data={'image': image_file}, content_type=content_type)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_handle.assert_called_once()
        mock_task.assert_called_once()

    @patch('api.v1.views.users_views.render_and_update_profile_image_task.delay')
    @patch('api.v1.views.users_views.handle_file_upload')
    def test_update_image_ok(self, mock_handle, mock_task):
        self.login_user()
        image_file = create_temp_image()
        mock_handle.return_value = "/fake/path/test.png"

        boundary = 'BoUnDaRyStRiNg123'
        content_type = f'multipart/form-data; boundary={boundary}'
        response = self.client.patch(
            self.url, data={'image': image_file}, content_type=content_type)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_handle.assert_called_once()
        mock_task.assert_called_once()

    @patch('file_client.files_clients.ProfileImageRendererClient.delete')
    def test_delete_image_ok(self, mock_delete):
        self.login_user()
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Image deleted'})
        mock_delete.assert_called_once()

    @patch('file_client.files_clients.ProfileImageRendererClient.download')
    def test_download_image_ok(self, mock_download):
        self.login_user()
        mock_download.return_value = BytesIO(b"image data")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.getvalue(), b"image data")

    @patch('file_client.files_clients.ProfileImageRendererClient.download')
    def test_download_image_not_found(self, mock_download):
        self.login_user()
        mock_download.side_effect = FileClientException(
            404, {"detail": "Downloaded file not found on disk."})

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data, {"detail": "Downloaded file not found on disk."})


def create_temp_image() -> SimpleUploadedFile:
    image = Image.new('RGB', (100, 100), color='red')

    image_file = io.BytesIO()
    image.save(image_file, format='PNG')
    image_file.seek(0)
    uploaded_image = SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png")
    uploaded_image.seek(0)

    return uploaded_image
