"""
Django settings for mobiotrip_main project.

Generated by 'django-admin startproject' using Django 4.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import redis
import kafka
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*ug_$-0&k0-f&)tni#y&trjs73c$l#tuz*!a7*n5mg3lh$-nly'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]   # Bad thing for production


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_yasg',
    'rest_framework',
    'django_filters',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    "debug_toolbar",
    'users_manager.apps.UsersManagerConfig',
    'vehicles_manager.apps.VehiclesManagerConfig',
    'stations_manager.apps.StationsManagerConfig',
    'employees_manager.apps.EmployeesManagerConfig',
    'wallet_app.apps.WalletAppConfig',
    'news_platform.apps.NewsPlatformConfig',
    'trips_manager.apps.TripsManagerConfig',
    'road_recommendation_system.apps.RoadRecommendationSystemConfig',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT_URLCONF = 'mobiotrip_main.urls'

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mobiotrip_main.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mobiotrip',
        'USER': 'root',
        'PASSWORD': 'mypass',
        'HOST':'127.0.0.1',
        'PORT':'3306',
    }
}

# System Cache
# https://redis.io/
REDIS_SETTINGS = {
    'HOST' : 'localhost' , 
    'PORT' : '6379',
}

BUSY_DRIVERS_KEY_FORMAT = "cache:busy_drivers:{}"
BUSY_RIDERS_KEY_FORMAT  = "cache:busy_riders:{}"

RUNNING_TRIPS_KEY_FORMAT = "cache:running_trips:{}"
ACTIVE_DRIVER_KEY_FORMAT = "cache:drivers:{}"
TRACKING_KEY = "cache:tracker"

SYSTEM_CACHE = redis.Redis(
    host= REDIS_SETTINGS["HOST"] , 
    port= REDIS_SETTINGS["PORT"], 
    decode_responses=True
)

# Main Kafka Producer
# https://kafka.apache.org/
PRODUCER_SETTINGS = {
    'KAFKA_BOOTSTRAP_SERVERS' : 'localhost:9092' , 
    'KAFKA_API_VERESION' : '0.1.0'
}

TRACKER_TOPIC = "tracking-v1-topic"
TIMER_TOPIC = "timing-v1-topic"

SYSTEM_PRODUCER = kafka.KafkaProducer(
    bootstrap_servers = PRODUCER_SETTINGS['KAFKA_BOOTSTRAP_SERVERS'],
    api_version = PRODUCER_SETTINGS['KAFKA_API_VERESION']
)

# DRF-YASG (Swagger/OpenAPI 2 generation tool)
# https://github.com/axnsan12/drf-yasg/
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        }
    }
}

# Django REST-Framework settings
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Note: i have no idea about optimal pagination style, so i will work with the default
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
}

# CORS settings
# https://pypi.org/project/django-cors-headers/

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'ngrok-skip-browser-warning',
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

# Optionally, allow all headers
CORS_ALLOW_ALL_HEADERS = True

# Optionally, allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True   # Bad for production

# Simple-JWT settings
# https://pypi.org/project/djangorestframework-simplejwt/

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=180),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',

    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Authentication User Model

AUTH_USER_MODEL = "users_manager.User"

# Authentication Backends

# AUTHENTICATION_BACKENDS = [
#     "users_manager.backends.UserAuthenticationBackend",
# ]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
