from pathlib import Path

from .secrets import get_secret, load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = get_secret("DJANGO_DEBUG", "0") == "1"
SECRET_KEY = get_secret("DJANGO_SECRET_KEY", "dev-secret-change-me")
ALLOWED_HOSTS = [host.strip() for host in get_secret("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [host.strip() for host in get_secret("DJANGO_CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if host.strip()]

SECURE_PROXY_SSL_HEADER = None
if get_secret("DJANGO_SECURE_PROXY_SSL_HEADER", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = get_secret("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
SESSION_COOKIE_SECURE = get_secret("DJANGO_SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = get_secret("DJANGO_CSRF_COOKIE_SECURE", "0") == "1"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "audioweb.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "audioweb.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_secret("POSTGRES_DB", "audioweb"),
        "USER": get_secret("POSTGRES_USER", "audioweb"),
        "PASSWORD": get_secret("POSTGRES_PASSWORD", "audioweb"),
        "HOST": get_secret("POSTGRES_HOST", "127.0.0.1"),
        "PORT": get_secret("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(get_secret("POSTGRES_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "connect_timeout": 5,
            "sslmode": get_secret("POSTGRES_SSLMODE", "prefer"),
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
FFMPEG_BINARY = get_secret("FFMPEG_BINARY", "ffmpeg")
LOGIN_REDIRECT_URL = "/archive/"
LOGOUT_REDIRECT_URL = "/archive/"
LOGIN_URL = "/accounts/login/"
SITE_URL = get_secret("SITE_URL", "http://127.0.0.1:8000")
DEFAULT_FROM_EMAIL = get_secret("DEFAULT_FROM_EMAIL", "no-reply@example.com")
EMAIL_BACKEND = get_secret("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
PAYMENT_PROVIDER = get_secret("PAYMENT_PROVIDER", "demo")
PAYMENT_MODE = get_secret("PAYMENT_MODE", "test")
PAYMENT_CURRENCY = get_secret("PAYMENT_CURRENCY", "RUB")
CONSENT_VERSION = "2026-08-25"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
