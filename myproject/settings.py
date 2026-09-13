from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "temporary-development-key"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = []

MIDDLEWARE = []

ROOT_URLCONF = "myproject.urls"

TEMPLATES = []

WSGI_APPLICATION = "myproject.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
