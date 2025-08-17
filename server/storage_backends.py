from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from cloudinary import CloudinaryResource

class MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for media files using S3
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'


class StaticStorage(S3Boto3Storage):
    """
    Custom storage backend for static files using S3
    """
    location = 'static'
    file_overwrite = True
    default_acl = 'public-read'


class HybridCloudinaryStorage:
    """
    Hybrid storage that uses both Cloudinary and S3
    - Cloudinary for images and videos
    - S3 for other media files
    """
    def __init__(self):
        self.s3_storage = MediaStorage()

    def _is_image_or_video(self, name):
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        video_extensions = ['.mp4', '.mov', '.avi', '.webm']
        ext = name.lower()
        return any(ext.endswith(x) for x in image_extensions + video_extensions)

    def save(self, name, content, max_length=None):
        if self._is_image_or_video(name):
            # Use Cloudinary for images and videos
            response = CloudinaryResource(name).upload(content)
            return response['secure_url']
        else:
            # Use S3 for other files
            return self.s3_storage.save(name, content)