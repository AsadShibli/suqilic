from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]

image_extension_validator = FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)


def validate_file_size(file):
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f"File too large (max {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB).")


IMAGE_VALIDATORS = [image_extension_validator, validate_file_size]
