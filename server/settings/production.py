from .base import *
import cloudinary
import cloudinary.uploader
import cloudinary.api
import boto3
import os

# AWS Parameter Store helper function
def get_parameter(name, default=None, decrypt=True):
    """
    Get parameter from AWS Systems Manager Parameter Store
    Falls back to environment variable if not in AWS environment
    """
    try:
        if os.environ.get('AWS_EXECUTION_ENV') or os.environ.get('ECS_CONTAINER_METADATA_URI'):
            # Running in AWS environment
            ssm = boto3.client('ssm', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-south-1'))
            response = ssm.get_parameter(Name=name, WithDecryption=decrypt)
            return response['Parameter']['Value']
        else:
            # Local development - fall back to environment variable
            env_name = name.split('/')[-1].upper()
            return os.environ.get(env_name, default)
    except Exception as e:
        print(f"Warning: Could not retrieve parameter {name}: {e}")
        return default

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# AWS Configuration
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_DEFAULT_ACL = config('AWS_DEFAULT_ACL', default='public-read')
AWS_LOCATION = 'static'

# Cloudinary Configuration - Use AWS Parameter Store in production
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': get_parameter('/dealsbasket/cloudinary_cloud_name', config('CLOUDINARY_CLOUD_NAME', default='')),
    'API_KEY': get_parameter('/dealsbasket/cloudinary_api_key', config('CLOUDINARY_API_KEY', default='')),
    'API_SECRET': get_parameter('/dealsbasket/cloudinary_api_secret', config('CLOUDINARY_API_SECRET', default='')),
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET']
)

# Database - Use AWS Parameter Store for sensitive data
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': get_parameter('/dealsbasket/db_password', config('DB_PASSWORD', default='')),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# CORS Configuration for production
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
CORS_ALLOW_CREDENTIALS = True

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Storage Configuration
STATICFILES_STORAGE = config(
    'STATICFILES_STORAGE',
    default='server.storage_backends.StaticStorage'
)
DEFAULT_FILE_STORAGE = config(
    'DEFAULT_FILE_STORAGE',
    default='server.storage_backends.HybridCloudinaryStorage'
)
MEDIA_URL = config('MEDIA_URL')
STATIC_URL = config('STATIC_URL')

# Email configuration for production - Use AWS Parameter Store
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = get_parameter('/dealsbasket/email_host', config('EMAIL_HOST', default='smtp-relay.brevo.com'))
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = get_parameter('/dealsbasket/email_host_user', config('EMAIL_HOST_USER', default=''))
EMAIL_HOST_PASSWORD = get_parameter('/dealsbasket/email_host_password', config('EMAIL_HOST_PASSWORD', default=''))
DEFAULT_FROM_EMAIL = get_parameter('/dealsbasket/default_from_email', config('DEFAULT_FROM_EMAIL', default=''))

# Override JWT secret key with Parameter Store value
JWT_SECRET_KEY = get_parameter('/dealsbasket/jwt_secret_key', config('JWT_SECRET_KEY', default=SECRET_KEY))

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
