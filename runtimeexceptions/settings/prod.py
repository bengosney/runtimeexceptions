import os

import dj_database_url
import structlog

from runtimeexceptions.settings.base import *  # noqa
from runtimeexceptions.settings.base import DATABASES, LOGGING, MIDDLEWARE
from runtimeexceptions.utils import deep_merge

logger = structlog.get_logger(__name__)

DEBUG = False

env = os.environ.copy()

ALLOWED_HOSTS = ["localhost:8000", "localhost", *env["ALLOWED_HOSTS"].split(",")]

BASE_URL = env["BASE_URL"]

CSRF_TRUSTED_ORIGINS = [
    BASE_URL,
]

if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config()  # type: ignore
    DATABASES["default"].update(
        {
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "pool": {
                    "min_size": 4,
                    "max_size": 16,
                    "timeout": 10,
                    "max_lifetime": 1800,
                    "max_idle": 300,
                },
            },
        }
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECRET_KEY = env["SECRET_KEY"]

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "honeybadger.contrib.DjangoHoneybadgerMiddleware",
]

HONEYBADGER = {
    "API_KEY": os.environ.get("HONEYBADGER_KEY", ""),
}

THUMBNAIL_DEFAULT_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_REGION", "eu-west-1")
AWS_QUERYSTRING_AUTH = False

AWS_S3_OBJECT_PARAMETERS = {
    "Expires": "Thu, 31 Dec 2099 20:00:00 GMT",
    "CacheControl": "max-age=94608000",
}

try:
    EMAIL_HOST = env["SMTP_HOST"]
    EMAIL_HOST_USER = env["SMTP_USER"]
    EMAIL_HOST_PASSWORD = env["SMTP_PASS"]
    EMAIL_PORT = env["SMTP_PORT"]
    EMAIL_USE_TLS = (env.get("SMTP_TLS", "True") or "True") != "False"
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
except KeyError as e:
    logger.warning(f"Missing SMTP environment variable: {e}")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default",
    },
    "renditions": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "renditions",
    },
}

LOGGING = deep_merge(
    LOGGING,
    {
        "formatters": {
            "verbose": {
                "format": "{levelname}: ({module}) {message}",
            },
        },
    },
)

TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
    },
}
