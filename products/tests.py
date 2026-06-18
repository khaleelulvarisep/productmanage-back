from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product


class ProductAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPassword123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123",
        )
        self.product = Product.objects.create(
            name="Laptop",
            price="999.99",
            description="A production-ready laptop",
            images=["https://cdn.example.com/laptop.jpg"],
            videos=["https://cdn.example.com/laptop.mp4"],
            user=self.owner,
        )

    def test_list_products_is_public(self):
        response = self.client.get(reverse("product-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_product_requires_authentication(self):
        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "Phone",
                "price": "499.99",
                "description": "A reliable smartphone",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_product(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "Phone",
                "price": "499.99",
                "description": "A reliable smartphone",
                "images": ["https://cdn.example.com/phone.jpg"],
                "videos": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_id"], self.owner.id)
        self.assertEqual(response.data["images"], ["https://cdn.example.com/phone.jpg"])
        self.assertIn("createdAt", response.data)

    def test_owner_can_update_product(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            {"price": "899.99"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["price"], "899.99")

    def test_non_owner_cannot_update_product(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            {"price": "899.99"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_product(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_search_products_by_name(self):
        response = self.client.get(reverse("product-list-create"), {"search": "lap"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Laptop")

    def test_rejects_invalid_product_data(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "A",
                "price": "0.00",
                "description": "short",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("price", response.data)
        self.assertIn("description", response.data)

    def test_rejects_invalid_media_arrays(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            reverse("product-list-create"),
            {
                "name": "Camera",
                "price": "299.99",
                "description": "A useful camera product",
                "images": ["https://cdn.example.com/camera.jpg", ""],
                "videos": "https://cdn.example.com/camera.mp4",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", response.data)
        self.assertIn("videos", response.data)
