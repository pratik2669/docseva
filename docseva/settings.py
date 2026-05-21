"""
Production-hardened Django settings for DocSeva.

Environment-variable driven. Defaults are safe for local development;
every production-only control is gated on DEBUG=False or explicit env vars.

Quick-start:
  1. Copy .env.example to .env and fill in the values.
  2. Set DEBUG=False and provide a strong SECRET_KEY in production.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Required environment variable '{name}' is not set."
        )
    return value


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise ImproperlyConfigured(
            f"Environment variable '{name}' must be an integer, got: {value!r}"
        )


def env_list(name: str, default: str = "") -> list[str]:
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY", "dev-only-change-this-secret-key")
DEBUG = env_bool("DEBUG", False)  # Default OFF — must be explicitly enabled locally

TESTING = "test" in sys.argv

if not DEBUG and SECRET_KEY == "dev-only-change-this-secret-key":
    raise ImproperlyConfigured(
        "Set a strong SECRET_KEY when DEBUG=False.  "
        'Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,testserver")
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # App
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Content-Security-Policy headers (django-csp)
    "csp.middleware.CSPMiddleware",
    # Structured request logging
    "django_structlog.middlewares.RequestMiddleware",
    # Permissions-Policy header
    "core.middleware.PermissionsPolicyMiddleware",
]

ROOT_URLCONF = "docseva.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.docseva_context",
            ],
        },
    },
]

WSGI_APPLICATION = "docseva.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = env("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=env_int("DB_CONN_MAX_AGE", 600),
            ssl_require=env_bool("DATABASE_SSL_REQUIRE", not DEBUG),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Cache  (Redis preferred in production, in-memory fallback for dev/test)
# ---------------------------------------------------------------------------

REDIS_URL = env("REDIS_URL")
if REDIS_URL and not TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
            },
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ---------------------------------------------------------------------------
# Auth / Password
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "core.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "landing"

# Password reset tokens expire after 1 hour in production
PASSWORD_RESET_TIMEOUT = env_int("PASSWORD_RESET_TIMEOUT", 3600)

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / env("STATIC_ROOT", "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / env("MEDIA_ROOT", "media")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------

FILE_UPLOAD_MAX_MEMORY_SIZE = env_int(
    "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024
)  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", 15 * 1024 * 1024
)  # 15 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = env_int("DATA_UPLOAD_MAX_NUMBER_FIELDS", 100)

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "DocSeva <noreply@docseva.local>")
SERVER_EMAIL = env("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)

# Admins receive 500 error emails when DEBUG=False
_admin_emails = env("ADMINS", "")
if _admin_emails and not DEBUG:
    ADMINS = [("Admin", e.strip()) for e in _admin_emails.split(",") if e.strip()]

# ---------------------------------------------------------------------------
# Session security
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = env_int("SESSION_COOKIE_AGE", 86400)  # 24 h default
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool("SESSION_EXPIRE_AT_BROWSER_CLOSE", False)

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

CSRF_COOKIE_HTTPONLY = False  # JS needs to read CSRF token for fetch calls
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", False)

# Permissions-Policy (send via middleware – see core/middleware.py)
PERMISSIONS_POLICY = env(
    "PERMISSIONS_POLICY",
    "camera=(), microphone=(), geolocation=(), payment=()",
)

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0)
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ---------------------------------------------------------------------------
# Content-Security-Policy  (django-csp)
# ---------------------------------------------------------------------------

CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://cdn.tailwindcss.com",
)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.tailwindcss.com",
    "https://unpkg.com",
)
CSP_IMG_SRC = ("'self'", "data:", "blob:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_BASE_URI = ("'self'",)
# Flip to True to only report violations without blocking (useful during rollout)
CSP_REPORT_ONLY = env_bool("CSP_REPORT_ONLY", DEBUG)

# ---------------------------------------------------------------------------
# Rate limiting  (django-ratelimit defaults — views apply decorators)
# ---------------------------------------------------------------------------

RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", not DEBUG)
RATELIMIT_USE_CACHE = "default"

# ---------------------------------------------------------------------------
# External integrations
# ---------------------------------------------------------------------------

GOV_API_MODE = env("GOV_API_MODE", "mock").lower()  # "mock" | "live"

# Optional absolute base URL used for QR/share links.
# Local LAN example: http://192.168.1.10:8000
# Render example: https://docseva.onrender.com
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", "").rstrip("/")
if PUBLIC_BASE_URL:
    parsed_public_base_url = urlparse(PUBLIC_BASE_URL)
    if (
        parsed_public_base_url.scheme not in {"http", "https"}
        or not parsed_public_base_url.netloc
    ):
        raise ImproperlyConfigured(
            "PUBLIC_BASE_URL must be an absolute http(s) URL, e.g. https://docseva.onrender.com"
        )
    if not DEBUG and parsed_public_base_url.scheme != "https":
        raise ImproperlyConfigured("PUBLIC_BASE_URL must use https when DEBUG=False.")
SECURITY_CONTACT = env("SECURITY_CONTACT", "")

# ---------------------------------------------------------------------------
# Logging  (structured JSON in production, human-friendly in dev)
# ---------------------------------------------------------------------------

LOG_LEVEL = env("LOG_LEVEL", "INFO")

if DEBUG:
    # Human-readable dev logging
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
        "formatters": {
            "verbose": {
                "format": "[{asctime}] {levelname} {name}: {message}",
                "style": "{",
            }
        },
        "root": {"handlers": ["console"], "level": LOG_LEVEL},
        "loggers": {
            "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "core": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        },
    }
else:
    # Structured JSON logging for production log aggregators (e.g. Papertrail, Loki)
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "formatters": {
            "json": {
                "()": "core.logging.JsonFormatter",
            }
        },
        "root": {"handlers": ["console"], "level": LOG_LEVEL},
        "loggers": {
            "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "django.security": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "core": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        },
    }

# ---------------------------------------------------------------------------
# Gunicorn hints (used by entrypoint.sh)
# ---------------------------------------------------------------------------

GUNICORN_WORKERS = env_int("GUNICORN_WORKERS", 3)
GUNICORN_TIMEOUT = env_int("GUNICORN_TIMEOUT", 60)
GUNICORN_MAX_REQUESTS = env_int("GUNICORN_MAX_REQUESTS", 1200)
GUNICORN_MAX_REQUESTS_JITTER = env_int("GUNICORN_MAX_REQUESTS_JITTER", 200)
