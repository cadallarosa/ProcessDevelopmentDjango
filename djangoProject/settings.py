from pathlib import Path
import os
from .ssh_tunnel import start_ssh_tunnel
# from.my_sql import reset_mysql_connection
import time

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-vv7v88x+dqlx+*^-&5#9ws7gcqx@ss#xgq&w@swn%g68t!jj08'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # Keep only this occurrence
    'plotly_integration',
    'development',  # HTMX development apps
    'analytical',  # HTMX analytical apps (SEC, etc.)
    'dashboard',  # Main dashboard with collapsible sidebar
    'corsheaders',
    'channels',
    'channels_redis',
    'django_plotly_dash',
    'django_celery_beat',
    'django_celery_results',
    # 'sslserver',
    'django_extensions'

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_plotly_dash.middleware.BaseMiddleware',
    'django_plotly_dash.middleware.ExternalRedirectionMiddleware',
    'django_plotly_dash.middleware.BaseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangoProject.urls'

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

WSGI_APPLICATION = 'djangoProject.wsgi.application'
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join('C:/Users/cdallarosa/DataAlchemy/Database Management/Database Management/Empower.db'),
#     }
# }

start_ssh_tunnel()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'djangoP1_db',
        'USER': 'cdallarosa',
        'PASSWORD': '$ystImmun3!2022',
        'HOST': '127.0.0.1',  # Use server IP if remote
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'connect_timeout': 600,  # Wait longer before timing out
            'autocommit': True,  # Ensure automatic commits
        },

    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'systimmune',
#         'USER': 'root',
#         'PASSWORD': 'C@nyon2025!',
#         'HOST': '127.0.0.1',  # Use server IP if remote
#         'PORT': '3308',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'connect_timeout': 600,  # Wait longer before timing out
#             'autocommit': True,  # Ensure automatic commits
#         },
#
#     }
# }


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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Pacific'
USE_I18N = True
USE_TZ = True

# ASGI_APPLICATION = 'plotly_django_tutorial.routing.application'
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [('127.0.0.1', 6379),],
#         }
#     }
# }

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_plotly_dash.finders.DashAssetFinder',
    'django_plotly_dash.finders.DashComponentFinder'
]

# PLOTLY_COMPONENTS = [
#
#     'dash_core_components',
#     'dash_html_components',
#     # 'dash_renderer',
#     'dash_bootstrap_components',
#     'dpd_components'
# ]

# PLOTLY_COMPONENTS = None  # Let django-plotly-dash use default CDNs


# DPD_STATIC_SERVE = False
STATICFILES_LOCATION = 'static'
# STATIC_URL = '/static/'
# STATIC_ROOT = 'static'
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'djangoProject/static')
# ]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # Change to 'staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

X_FRAME_OPTIONS = 'SAMEORIGIN'
CORS_ALLOW_ALL_ORIGINS = True

# # Use the CDN for Plotly resources instead of local static files
# PLOTLY_COMPONENTS = {
#     'plotly': {
#         'js': 'https://cdn.plot.ly/plotly-latest.min.js',  # Plotly JS CDN
#         'css': None  # Dash uses the default CSS from the CDN
#     },
#     'dash_core_components': {
#         'js': 'https://cdn.jsdelivr.net/npm/dash-core-components@2.9.0/dash_core_components/dash-core-components.min.js',
#         'css': 'https://cdn.jsdelivr.net/npm/dash-core-components@2.9.0/dash_core_components/dash-core-components.min.css',
#     },
#     'dash_html_components': {
#         'js': 'https://cdn.jsdelivr.net/npm/dash-html-components@2.9.0/dash_core_components/dash-html-components.min.js',
#         'css': 'https://cdn.jsdelivr.net/npm/dash-html-components@2.9.0/dash_core_components/dash-html-components.min.css',
#     }
# }

# PLOTLY_COMPONENTS = {
#     'plotly': {
#         'js': 'static/dash/component/plotly/package_data/plotly.min.js',  # Plotly JS CDN
#         'css': None  # Dash uses the default CSS from the CDN
#     },
#     'dash_core_components': {
#         'js': 'static/dash/component/dash/dcc/dash_core_components.js',
#         'css': None  # Dash uses the default CSS from the CDN',
#     },
#     'dash_html_components': {
#         'js': 'static/dash/component/dash/html/dash_html_components.min.js',
#         'css': None  # Dash uses the default CSS from the CDN,
#     }
# }

# Use CDN for remote server to avoid static file issues
# PLOTLY_COMPONENTS = None  # Let django-plotly-dash use default CDNs
CRISPY_TEMPLATE_PACK = 'bootstrap4'


# Increase Django's file upload size limit (e.g., 100MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
