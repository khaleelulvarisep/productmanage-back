from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationAPITests(APITestCase):
    def test_register_creates_user(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "khaleel",
                "email": "khaleel@example.com",
                "password": "StrongPassword123",
                "confirm_password": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered successfully")
        self.assertEqual(response.data["user"]["username"], "khaleel")
        self.assertTrue(User.objects.filter(username="khaleel").exists())
        self.assertNotIn("password", response.data["user"])

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="khaleel@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "khaleel",
                "email": "khaleel@example.com",
                "password": "StrongPassword123",
                "confirm_password": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "khaleel",
                "email": "khaleel@example.com",
                "password": "StrongPassword123",
                "confirm_password": "DifferentPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    def test_login_returns_tokens(self):
        User.objects.create_user(
            username="khaleel",
            email="khaleel@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            reverse("auth-login"),
            {"username": "khaleel", "password": "StrongPassword123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "khaleel@example.com")

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "khaleel", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"][0], "Invalid credentials")

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("auth-profile"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_get_and_update(self):
        user = User.objects.create_user(
            username="khaleel",
            email="khaleel@example.com",
            password="StrongPassword123",
        )
        self.client.force_authenticate(user=user)

        update_response = self.client.put(
            reverse("auth-profile"),
            {"first_name": "Khaleel", "last_name": "Varis"},
            format="json",
        )
        get_response = self.client.get(reverse("auth-profile"))

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["first_name"], "Khaleel")
        self.assertEqual(get_response.data["last_name"], "Varis")

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            username="khaleel",
            email="khaleel@example.com",
            password="StrongPassword123",
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "khaleel", "password": "StrongPassword123"},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        response = self.client.post(
            reverse("auth-logout"),
            {"refresh": login_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out successfully")
