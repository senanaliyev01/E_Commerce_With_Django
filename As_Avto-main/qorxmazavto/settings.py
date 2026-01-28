

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Prod üçün False qoyun, testdə True ola bilər

ALLOWED_HOSTS = ['localhost','127.0.0.1','0.0.0.0', 'as-avto.com', 'www.as-avto.com']

CSRF_TRUSTED_ORIGINS = [
    'https://as-avto.com',
    'https://www.as-avto.com',
]

# Application definition

INSTALLED_APPS = [
    "simpleui",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',  # Sitemap üçün əlavə edildi
    'home',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'home.middleware.GlobalDataMiddleware',
    'home.middleware.Custom404Middleware',
    'home.middleware.AdminFaviconMiddleware',
]

ROOT_URLCONF = 'qorxmazavto.urls'

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

WSGI_APPLICATION = 'qorxmazavto.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# DATABASES = {

#     'default': {

#         'ENGINE': 'django.db.backends.postgresql_psycopg2',

#         'NAME': os.getenv('POSTGRES_DB'),

#         'USER': os.getenv('POSTGRES_USER'),

#         'PASSWORD': os.getenv('POSTGRES_PASSWORD'),

#         'HOST': os.getenv('POSTGRES_HOST'),

#         'PORT': os.getenv('POSTGRES_PORT'),

#     }

# }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

# SEO və Google üçün uyğun dil və zaman qurşağı
LANGUAGE_CODE = 'az-az'
TIME_ZONE = 'Asia/Baku'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings
SESSION_COOKIE_AGE = 2592000  # 30 gün (saniyə ilə: 30 * 24 * 60 * 60 = 2592000)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Brauzer bağlandıqda sessiyanın bitməməsi
SESSION_SAVE_EVERY_REQUEST = False  # Hər sorğuda sessiyanın yenilənməməsi
LOGIN_URL = '/'  # Sessiya bitdikdə yönləndiriləcək səhifə

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SIMPLEUI_LOGO = '/static/images/Header_Logo.png'
SIMPLEUI_FAVICON = '/static/images/favicon.png'

# ============================================
# BAŞLIQLAR
# ============================================

SIMPLEUI_CONFIG = {
    'system_title': 'Avto Ehtiyat Hissələri – Admin',
    'system_header': 'Avto Ehtiyat Hissələri',
    'system_name': 'Admin Panel',

    # favicon
    'favicon': '/static/images/favicon.png',
}

# ============================================
# MENYU VƏ İKONLAR
# ============================================

SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menu_display': ['Məhsullar', 'Sifarişlər', 'İstifadəçilər', 'Parametrlər'],
    'dynamic': True,
    'menus': [
        {
            'name': 'Məhsullar',
            'icon': 'fas fa-box-open',
            'models': [
                {
                    'name': 'Məhsullar',
                    'icon': 'fas fa-shopping-bag',
                    'url': 'home/mehsul/'
                },
                {
                    'name': 'Kateqoriyalar',
                    'icon': 'fas fa-list',
                    'url': 'home/kateqoriya/'
                },
                {
                    'name': 'Firmalar',
                    'icon': 'fas fa-building',
                    'url': 'home/firma/'
                },
                {
                    'name': 'Avtomobillər',
                    'icon': 'fas fa-car',
                    'url': 'home/avtomobil/'
                },
                {
                    'name': 'Vitrinlər',
                    'icon': 'fas fa-store',
                    'url': 'home/vitrin/'
                },
            ]
        },
        {
            'name': 'Sifarişlər',
            'icon': 'fas fa-shopping-cart',
            'models': [
                {
                    'name': 'Sifarişlər',
                    'icon': 'fas fa-receipt',
                    'url': 'home/sifaris/'
                },
            ]
        },
        {
            'name': 'İstifadəçilər',
            'icon': 'fas fa-users',
            'models': [
                {
                    'name': 'İstifadəçilər',
                    'icon': 'fas fa-user',
                    'url': 'auth/user/'
                },
                {
                    'name': 'Profillər',
                    'icon': 'fas fa-id-card',
                    'url': 'home/profile/'
                },
                {
                    'name': 'Qruplar',
                    'icon': 'fas fa-users-cog',
                    'url': 'auth/group/'
                },
            ]
        },
        {
            'name': 'Parametrlər',
            'icon': 'fas fa-cogs',
            'models': [
                {
                    'name': 'Header Mesajları',
                    'icon': 'fas fa-comment',
                    'url': 'home/header_message/'
                },
                {
                    'name': 'Popup Şəkillər',
                    'icon': 'fas fa-images',
                    'url': 'home/popupimage/'
                },
            ]
        },
    ]
}

# ============================================
# GÖRÜNÜŞ TƏNZİMLƏMƏLƏRİ
# ============================================

# SimpleUI reklam və logosunu gizlət
SIMPLEUI_HOME_PAGE = False
SIMPLEUI_ANALYSIS = False

# Loading animasiya
SIMPLEUI_LOADING = True