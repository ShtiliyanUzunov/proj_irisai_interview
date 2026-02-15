"""
Django settings for the arXiv classification web service.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent  # interview_irisai/

# Load .env from project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

# No database needed — all state is in-memory
DATABASES = {}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "UNAUTHENTICATED_USER": None,
}

# --- Custom app settings (from .env) ---
LOG_DIR = os.getenv("LOG_DIR", "./logs")
CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.95"))
CACHE_EMBEDDING_MODEL = os.getenv("CACHE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MODEL_NAME = os.getenv("MODEL_NAME", "allenai/specter2_base")
LAZY_INIT = os.getenv("LAZY_INIT", "False").lower() in ("true", "1", "yes")

# Logging configuration
LOG_DIR_PATH = Path(LOG_DIR)
LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": str(LOG_DIR_PATH / "service.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "api": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "services": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
