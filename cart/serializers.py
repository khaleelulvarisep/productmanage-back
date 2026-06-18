from rest_framework import serializers

from products.models import Product
from products.serializers import ProductSerializer

from .models import Cart


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = (
            "id",
            "product",
            "quantity",
            "subtotal",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CartActionSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError("Product not found.") from exc
        self.context["product"] = product
        return value


class CartRemoveSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError("Product not found.") from exc
        self.context["product"] = product
        return value
