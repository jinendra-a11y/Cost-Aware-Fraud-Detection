"""
Django settings for core project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Paths & environment
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file (contains secret keys, API tokens, etc.)
load_dotenv(BASE_DIR / ".env")

# ----------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE_ME"  # <-- replace with a real secret in production
)

# DEBUG should be **False** on the public host.
DEBUG = False

# Allow the host that Render/Railway assigns (or just '*')
ALLOWED_HOSTS = ["*"]   # you can tighten this later to the exact domain

# ----------------------------------------------------------------------
# Installed apps
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    "daphne",                     # needed for ASGI (WebSocket) support
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",                   # for WebSocket handling
    # your own apps
    "analytics",
    "jobs",
    "providers",
]

# ----------------------------------------------------------------------
# ASGI / Channels configuration
# ----------------------------------------------------------------------
ASGI_APPLICATION = "core.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ----------------------------------------------------------------------
# Middleware
# ----------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ----------------------------------------------------------------------
# URL configuration
# ----------------------------------------------------------------------
ROOT_URLCONF = "core.urls"

# ----------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],                     # add custom template dirs here if you have any
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------------------------------------------------------
# WSGI (fallback, not used when running via ASGI)
# ----------------------------------------------------------------------
WSGI_APPLICATION = "core.wsgi.application"

# ----------------------------------------------------------------------
# Database – SQLite (good for a small free tier)
# ----------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ----------------------------------------------------------------------
# Password validation (standard)
# ----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------
# Internationalisation
# ----------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------
# Static & media files
# ----------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = Path("/var/www/static")

# **Important for deployment**
MEDIA_URL = "/media/"

# You already changed this line (see your diff):
#   from: MEDIA_ROOT = BASE_DIR / 'media'
#   to:   MEDIA_ROOT = Path("/var/www/media")
# Render mounts a persistent disk at /var/www, Railway at /railway.
# Either path works as long as the platform you choose mounts that location.
MEDIA_ROOT = Path("/var/www/media")   # <-- keep this for Render
# If you later switch to Railway, change to Path("/railway/media")

# ----------------------------------------------------------------------
# Default primary key field type
# ----------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------------------------
# Custom environment variables (your .env)
# ----------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
