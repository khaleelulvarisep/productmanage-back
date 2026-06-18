import json

from rest_framework import serializers

from .models import Product
from .services.cloudinary_service import (
    delete_media,
    get_public_id_from_url,
    upload_image,
    upload_video,
)


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
VIDEO_EXTENSIONS = {"mp4", "mov", "webm"}
IMAGE_MAX_SIZE = 10 * 1024 * 1024
VIDEO_MAX_SIZE = 100 * 1024 * 1024
MIN_IMAGE_COUNT = 3


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "description",
            "images",
            "videos",
            "user",
            "user_id",
            "createdAt",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_id", "createdAt", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Product name must be at least 2 characters long.")
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_images(self, value):
        return self._validate_string_list(value, "images")

    def validate_videos(self, value):
        return self._validate_string_list(value, "videos")

    def _validate_string_list(self, value, field_name):
        if not isinstance(value, list):
            raise serializers.ValidationError(f"{field_name} must be a list.")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise serializers.ValidationError(f"{field_name} must contain only non-empty strings.")
        return [item.strip() for item in value]


class ProductMediaSerializer(ProductSerializer):
    remove_images = serializers.JSONField(required=False, write_only=True, default=list)
    remove_videos = serializers.JSONField(required=False, write_only=True, default=list)
    replace_media = serializers.BooleanField(required=False, write_only=True, default=False)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + (
            "remove_images",
            "remove_videos",
            "replace_media",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        image_files = self._get_files(request, "images")
        video_files = self._get_files(request, "videos")

        self._validate_files(image_files, IMAGE_EXTENSIONS, IMAGE_MAX_SIZE, "image")
        self._validate_files(video_files, VIDEO_EXTENSIONS, VIDEO_MAX_SIZE, "video")

        replace_media = attrs.get("replace_media", False)
        remove_images = self._validate_url_list(attrs.get("remove_images", []), "remove_images")
        remove_videos = self._validate_url_list(attrs.get("remove_videos", []), "remove_videos")
        attrs["remove_images"] = remove_images
        attrs["remove_videos"] = remove_videos
        existing_images = [] if replace_media or not self.instance else list(self.instance.images)
        remaining_images = [url for url in existing_images if url not in remove_images]
        direct_images = attrs.get("images")
        if direct_images is not None and not image_files:
            remaining_images = direct_images

        if len(remaining_images) + len(image_files) < MIN_IMAGE_COUNT:
            raise serializers.ValidationError(
                {"images": f"At least {MIN_IMAGE_COUNT} images are required."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("remove_images", None)
        validated_data.pop("remove_videos", None)
        validated_data.pop("replace_media", None)

        request = self.context.get("request")
        validated_data["images"] = [upload_image(file) for file in self._get_files(request, "images")]
        validated_data["videos"] = [upload_video(file) for file in self._get_files(request, "videos")]
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove_images = validated_data.pop("remove_images", [])
        remove_videos = validated_data.pop("remove_videos", [])
        replace_media = validated_data.pop("replace_media", False)
        request = self.context.get("request")

        existing_images = [] if replace_media else list(instance.images)
        existing_videos = [] if replace_media else list(instance.videos)
        images_to_delete = list(instance.images) if replace_media else []
        videos_to_delete = list(instance.videos) if replace_media else []

        for url in remove_images:
            if url in existing_images:
                existing_images.remove(url)
                images_to_delete.append(url)

        for url in remove_videos:
            if url in existing_videos:
                existing_videos.remove(url)
                videos_to_delete.append(url)

        if "images" in validated_data and not self._get_files(request, "images"):
            existing_images = validated_data.pop("images")
        else:
            validated_data.pop("images", None)

        if "videos" in validated_data and not self._get_files(request, "videos"):
            existing_videos = validated_data.pop("videos")
        else:
            validated_data.pop("videos", None)

        existing_images.extend(upload_image(file) for file in self._get_files(request, "images"))
        existing_videos.extend(upload_video(file) for file in self._get_files(request, "videos"))
        validated_data["images"] = existing_images
        validated_data["videos"] = existing_videos

        product = super().update(instance, validated_data)
        for url in images_to_delete + videos_to_delete:
            delete_media(get_public_id_from_url(url))

        return product

    def _get_files(self, request, field_name):
        if not request:
            return []
        return list(request.FILES.getlist(field_name)) + list(request.FILES.getlist(f"{field_name}[]"))

    def _validate_files(self, files, allowed_extensions, max_size, media_type):
        for file in files:
            extension = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
            if extension not in allowed_extensions:
                raise serializers.ValidationError(
                    {f"{media_type}s": f"{file.name} is not an allowed {media_type} format."}
                )
            if file.size > max_size:
                size_mb = max_size // (1024 * 1024)
                raise serializers.ValidationError(
                    {f"{media_type}s": f"{file.name} must be {size_mb}MB or smaller."}
                )

    def _validate_url_list(self, value, field_name):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError({field_name: "Expected a list of URLs."}) from exc

        if not isinstance(value, list):
            raise serializers.ValidationError({field_name: "Expected a list of URLs."})
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise serializers.ValidationError({field_name: "Expected a list of URLs."})
        return [item.strip() for item in value]
