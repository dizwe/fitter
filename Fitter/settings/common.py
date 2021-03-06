"""
Django settings for Fitter project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from os.path import abspath, dirname, join
import raven

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# settings.py를 폴더에 넣어서 dirname 한번더 더 씀.
BASE_DIR = dirname(dirname(dirname(abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name):
    """환경 변수를 가져오거나 예외를 반환한다."""
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable".format(var_name)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost',
                 ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'raven.contrib.django.raven_compat',
    'fitterKakao',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Fitter.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': ['django.contrib.staticfiles.templatetags.staticfiles'],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Fitter.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True


##### LOGGING
# LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'site.log')
# ERROR_FILE = os.path.join(os.path.dirname(__file__), '..', 'error.log')
#
# LOGGING = {
#
#     'version': 1,
#
#     'disable_existing_loggers': False,
#
#     'filters': {
#
#         'require_debug_false': {
#
#             '()': 'django.utils.log.RequireDebugFalse'
#
#         }
#
#     },
#
#     'handlers': {
#
#         'error_admin': {
#
#             'level': 'ERROR',
#
#             'filters': ['require_debug_false'],
#
#             'class': 'logging.handlers.WatchedFileHandler',
#             'filename': ERROR_FILE
#
#
#         },
#
#         'logfile': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.WatchedFileHandler',
#
#             'filename': LOG_FILE
#
#         },
#
#
#     },
#
#     'loggers': {
#
#         'django.request': {
#
#             'handlers': ['error_admin'],
#
#             'level': 'ERROR',
#
#             'propagate': True,
#
#         },
#
#         # Might as well log any errors anywhere else in Django
#
#         'django': {
#
#             'handlers': ['logfile'],
#
#             'level': 'DEBUG',
#
#             'propagate': False,
#
#         },
#
#         # Your own app - this assumes all your logger names start with "myapp."
#
#         'timeline': {
#
#             'handlers': ['logfile'],
#
#             'level': 'DEBUG', # Or maybe INFO or DEBUG
#
#             'propagate': False
#
#         },
#
#     }
#
# }

###RAVEN

GIT_ROOT = os.path.dirname(os.pardir) # 현 프로젝트 ROOT 지정
if os.path.exists(os.path.join(GIT_ROOT, '.git')):
    release = raven.fetch_git_sha(GIT_ROOT) # 현재 최근 커밋해시 획득
else:
    release = 'dev'

RAVEN_CONFIG = {
    'dsn': 'https://3cb8fb29193f45bf8613b1841dda05e0:5bff3e9e5f7a451b9b68bb5e718d1571@sentry.io/203343',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': release,
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'root': {
#         'level': 'WARNING',
#         'handlers': ['sentry'],
#     },
#     'formatters': {
#         'verbose': {
#             'format': '%(levelname)s %(asctime)s %(module)s '
#                       '%(process)d %(thread)d %(message)s'
#         },
#     },
#     'handlers': {
#         'sentry': {
#             'level': 'ERROR', # To capture more than ERROR, change to WARNING, INFO, etc.
#             'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
#             'tags': {'custom-tag': 'x'},
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose'
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'ERROR',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#         'raven': {
#             'level': 'DEBUG',
#             'handlers': ['console','sentry'],
#             'propagate': False,
#         },
#         'sentry.errors': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#     },
# }


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
# 프로젝트 단위로할 때에 저장
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'fitterKakao/static'),
)
# 배포할 때 필요한것
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') #C:\Django\Fitter\staticfiles 이런식으로 만들어짐

MEDIA_URL = '/media/' # 항상 / 로 끝나도록 설정
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/clothes'