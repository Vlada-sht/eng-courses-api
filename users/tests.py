from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from users.models import UserProfile

class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/users/register/'
        self.login_url = '/api/users/login/'
        self.refresh_url = '/api/users/refresh/'
        self.me_url = '/api/users/me/'
        self.logout_url = '/api/users/logout/'

    def test_registration_success(self):
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "ValidPassword123!",
            "password_confirm": "ValidPassword123!",
            "english_level": "B2"
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertEqual(response.data["user"]["english_level"], "B2")

        # Verify password is saved hashed in DB
        user = User.objects.get(username="testuser")
        self.assertNotEqual(user.password, "ValidPassword123!")
        self.assertTrue(user.check_password("ValidPassword123!"))

    def test_registration_validation_errors_400(self):
        # Missing required fields
        response = self.client.post(self.register_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("details", response.data)
        self.assertIn("username", response.data["details"])
        self.assertIn("email", response.data["details"])
        self.assertIn("password", response.data["details"])

        # Password mismatch
        mismatch_payload = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "Password123!",
            "password_confirm": "DifferentPassword123!"
        }
        response = self.client.post(self.register_url, mismatch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data["details"])

        # Weak password (too short)
        weak_payload = {
            "username": "user3",
            "email": "user3@example.com",
            "password": "123",
            "password_confirm": "123"
        }
        response = self.client.post(self.register_url, weak_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_user(self):
        User.objects.create_user(username="existing", email="existing@example.com", password="Password123!")
        payload = {
            "username": "existing",
            "email": "different@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!"
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data["details"])

    def test_login_and_jwt_tokens(self):
        user = User.objects.create_user(username="loginuser", email="login@example.com", password="SecretPassword123")
        user.profile.english_level = "C1"
        user.profile.save()

        # Login with username
        response = self.client.post(self.login_url, {
            "username": "loginuser",
            "password": "SecretPassword123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        # Access protected endpoint with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["username"], "loginuser")
        self.assertEqual(me_response.data["english_level"], "C1")

        # Refresh token test
        refresh_response = self.client.post(self.refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_unauthorized_access_401(self):
        # Protected endpoint without credentials returns 401
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
