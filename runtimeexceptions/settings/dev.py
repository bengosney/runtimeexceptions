from runtimeexceptions.settings.base import *  # noqa
from runtimeexceptions.settings.base import BASE_DIR, INSTALLED_APPS, LOGGING, MIDDLEWARE

from runtimeexceptions.utils import deep_merge

SECRET_KEY = "django-insecure-^3nal3e4vwg$jdfob5_6mmqy2sxs1@=6q0trtz1tj7h7i#8m21"

DEBUG = True

INSTALLED_APPS += [
    "django_browser_reload",
    "debug_toolbar",
    "zeal",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "zeal.middleware.zeal_middleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = [
    "127.0.0.1",
]

LOGGING = deep_merge(
    LOGGING,
    {
        "root": {
            "level": "DEBUG",
        },
    },
)


CSP_DEFAULT_SRC = None
CSP_STYLE_SRC = None
CSP_FONT_SRC = None
CSP_IMG_SRC = None

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
