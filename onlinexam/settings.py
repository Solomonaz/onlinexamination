"""
Django settings for onlinexam project - LAN Production Configuration
"""

from pathlib import Path
import os
import socket

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security - adjust for LAN environment
SECRET_KEY = '@k0#p3kidu)yaaa3u1hplxz)f@^6xiy384*(+n@@s5x#1bx@m5'
DEBUG = False

# Get local IP address for LAN access
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    hostname,
    local_ip,
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'exam',
    'teacher',
    'student',
    'widget_tweaks',
    'examiner',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Added for static files
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'teacher.middleware.TeacherAccessMiddleware',
    'onlinexam.middleware.SessionTimeoutMiddleware',

]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    ]

CSRF_COOKIE_SECURE=False
ROOT_URLCONF = 'onlinexam.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'onlinexam.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_L10N = True

USE_TZ = True


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'examdb',
        'USER': 'examuser',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c timezone=UTC',
            'client_encoding': 'UTF8',
        }
    }
}



# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False  # Helps with cache issues during development

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings (adjusted for LAN)
CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Login redirect
LOGIN_REDIRECT_URL = '/afterlogin'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'





