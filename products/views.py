from rest_framework import status
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from .models import Product
from .serializers import ProductMediaSerializer, ProductSerializer
from .services.cloudinary_service import upload_image


SAMPLE_IMAGE_DATA_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class TestCloudinaryView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            secure_url = upload_image(SAMPLE_IMAGE_DATA_URI)
        except Exception as exc:
            return Response(
                {
                    "success": False,
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "success": True,
                "url": secure_url,
            }
        )


class ProductListCreateView(ListCreateAPIView):
    queryset = Product.objects.select_related("user").all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("price", "created_at", "updated_at")
    ordering = ("-created_at",)
    pagination_class = None
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductMediaSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("user").all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return ProductMediaSerializer
        return ProductSerializer
