from django.db import transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart
from .serializers import CartActionSerializer, CartItemSerializer, CartRemoveSerializer


class CartListView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return Cart.objects.select_related("product", "product__user").filter(
            user=self.request.user
        )

    def get(self, request):
        cart_items = self.get_queryset()
        serializer = self.get_serializer(cart_items, many=True)
        grand_total = sum(item.subtotal for item in cart_items)

        return Response(
            {
                "items": serializer.data,
                "grand_total": f"{grand_total:.2f}",
            },
            status=status.HTTP_200_OK,
        )


class CartAddView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartActionSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)
        product = serializer.context["product"]
        quantity = serializer.validated_data["quantity"]

        cart_item, created = Cart.objects.select_for_update().get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save(update_fields=("quantity", "updated_at"))

        return Response(
            {
                "message": "Product added to cart",
                "item": CartItemSerializer(cart_item).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartActionSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)
        product = serializer.context["product"]
        quantity = serializer.validated_data["quantity"]

        try:
            cart_item = Cart.objects.get(user=request.user, product=product)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Product is not in your cart."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=("quantity", "updated_at"))

        return Response(
            {
                "message": "Cart item updated",
                "item": CartItemSerializer(cart_item).data,
            },
            status=status.HTTP_200_OK,
        )


class CartRemoveView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartRemoveSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)
        product = serializer.context["product"]

        deleted_count, _ = Cart.objects.filter(
            user=request.user,
            product=product,
        ).delete()

        if deleted_count == 0:
            return Response(
                {"error": "Product is not in your cart."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": "Product removed from cart"},
            status=status.HTTP_200_OK,
        )
