from django.urls import path

from .views import CartAddView, CartListView, CartRemoveView, CartUpdateView


urlpatterns = [
    path("cart/", CartListView.as_view(), name="cart-list"),
    path("cart/add/", CartAddView.as_view(), name="cart-add"),
    path("cart/update/", CartUpdateView.as_view(), name="cart-update"),
    path("cart/remove/", CartRemoveView.as_view(), name="cart-remove"),
]
