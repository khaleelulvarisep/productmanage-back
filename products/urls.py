from django.urls import path

from .views import ProductDetailView, ProductListCreateView, TestCloudinaryView


urlpatterns = [
    path("test-cloudinary", TestCloudinaryView.as_view(), name="test-cloudinary"),
    path("test-cloudinary/", TestCloudinaryView.as_view(), name="test-cloudinary-slash"),
    path("products", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/", ProductListCreateView.as_view(), name="product-list-create-slash"),
    path("products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail-slash"),
]
