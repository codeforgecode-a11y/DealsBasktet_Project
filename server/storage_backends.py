from django.conf import settings
from django.core.files.storage import FileSystemStorage
from cloudinary import CloudinaryResource
import os


class LocalMediaStorage(FileSystemStorage):
    """
    Custom storage backend for media files using local filesystem
    """
    def __init__(self):
        super().__init__(
            location=os.path.join(settings.BASE_DIR, 'media'),
            base_url='/media/'
        )


class LocalStaticStorage(FileSystemStorage):
    """
    Custom storage backend for static files using local filesystem
    """
    def __init__(self):
        super().__init__(
            location=os.path.join(settings.BASE_DIR, 'staticfiles'),
            base_url='/static/'
        )


class CloudinaryOnlyStorage:
    """
    Storage that uses only Cloudinary for all media files
    """
    def _is_image_or_video(self, name):
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        video_extensions = ['.mp4', '.mov', '.avi', '.webm']
        ext = name.lower()
        return any(ext.endswith(x) for x in image_extensions + video_extensions)

    def save(self, name, content, max_length=None):
        # Use Cloudinary for all files
        response = CloudinaryResource(name).upload(content)
        return response['secure_url']