from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product

from .models import Cart


class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="khaleel",
            email="khaleel@example.com",
            password="StrongPassword123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123",
        )
        self.product = Product.objects.create(
            name="Laptop",
            price="1000.00",
            description="A production-ready laptop",
            images=["https://cdn.example.com/laptop.jpg"],
            videos=[],
            user=self.other_user,
        )

    def test_cart_requires_authentication(self):
        response = self.client.get(reverse("cart-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_product_to_cart(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["item"]["quantity"], 2)
        self.assertEqual(response.data["item"]["subtotal"], "2000.00")

    def test_add_existing_product_increases_quantity(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=2)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-add"),
            {"product_id": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["item"]["quantity"], 5)
        self.assertEqual(Cart.objects.count(), 1)

    def test_list_returns_only_logged_in_users_cart_with_grand_total(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=2)
        Cart.objects.create(user=self.other_user, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("cart-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["grand_total"], "2000.00")

    def test_update_cart_item_quantity(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-update"),
            {"product_id": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["item"]["quantity"], 3)
        self.assertEqual(response.data["item"]["subtotal"], "3000.00")

    def test_remove_cart_item(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-remove"),
            {"product_id": self.product.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_rejects_missing_product(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-add"),
            {"product_id": 999999, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product_id", response.data)

    def test_update_missing_cart_item_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("cart-update"),
            {"product_id": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
