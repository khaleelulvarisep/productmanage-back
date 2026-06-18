from urllib.parse import urlparse

import cloudinary.uploader
from rest_framework.exceptions import ValidationError


IMAGE_FOLDER = "products/images"
VIDEO_FOLDER = "products/videos"


def upload_image(file):
    return _upload_media(file, folder=IMAGE_FOLDER, resource_type="image")


def upload_video(file):
    return _upload_media(file, folder=VIDEO_FOLDER, resource_type="video")


def delete_media(public_id):
    if not public_id:
        return None

    last_result = None
    for resource_type in ("image", "video"):
        try:
            last_result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True,
            )
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        if last_result.get("result") == "ok":
            return last_result

    return last_result


def _upload_media(file, folder, resource_type):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
    except Exception as exc:
        raise ValidationError(str(exc)) from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        raise ValidationError("Cloudinary did not return a secure URL.")

    return secure_url


def get_public_id_from_url(url):
    if not url:
        return ""

    path = urlparse(url).path
    marker = "/upload/"
    if marker not in path:
        return ""

    public_path = path.split(marker, 1)[1]
    parts = public_path.split("/")
    if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
        public_path = "/".join(parts[1:])

    return public_path.rsplit(".", 1)[0]
