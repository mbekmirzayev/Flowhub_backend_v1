import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
load_dotenv(BASE_DIR / "env" / ".env")

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'jazzmin',  # must be before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',

    # my apps
    'apps.users',
    'apps.payment',
    'apps.organization',
    'apps.notification',
    'apps.history',
    'apps.enrollment',
    'apps.device',
    'apps.course',
    'apps.common',
    'apps.category',
    'apps.attendance',

    # third party apps
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'rest_framework_simplejwt',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.TenantMiddleware',
    'root.jwt_middleware.CheckSessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'root.urls'
AUTH_USER_MODEL = 'users.User'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'root.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
IS_DOCKER = os.getenv('DOCKER_MODE', 'false').lower() == 'true'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_NAME'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        # Terminalda bo'lsa localhost, Dockerda bo'lsa service nomi
        'HOST': os.getenv('POSTGRES_HOST') if IS_DOCKER else 'localhost',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_ROUTER_TRAILING_SLASH': False,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Secure-by-default: every endpoint requires authentication unless it
    # explicitly overrides permission_classes (e.g. the login endpoint).
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': -1,
        'defaultModelExpandDepth': 3,
    }
}

SIMPLE_JWT = {
    # 30 minutes is the standard for staff CRMs — reduces exposure window
    # if a token is stolen (e.g. from a logged-in device left unattended).
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=360),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
CORS_ALLOWED_ORIGINS = [
    "https://flowhub.uz",
    "https://www.flowhub.uz",
]
CORS_ORIGIN_ALLOW_ALL = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'defy-tribune-oppose.ngrok-free.dev',
]

# ---------------------------------------------------------------------------
# STATIC files (production collectstatic target)
# ---------------------------------------------------------------------------
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# Django Jazzmin — Admin UI Configuration
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    # ── Branding ────────────────────────────────────────────────────────────
    "site_title": "Flowhub Admin",
    "site_header": "Flowhub CRM",
    "site_brand": "Flowhub",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Welcome to Flowhub CRM Admin",
    "copyright": "Flowhub © 2026",

    # ── Search ──────────────────────────────────────────────────────────────
    "search_model": ["users.User", "apps.course.Group", "apps.payment.Payment"],

    # ── User avatar ─────────────────────────────────────────────────────────
    "user_avatar": None,

    # ── Top Menu ────────────────────────────────────────────────────────────
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "📊 Dashboard", "url": "/admin/dashboard/", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"model": "users.User"},
    ],

    # ── User menu (top-right) ────────────────────────────────────────────────
    "usermenu_links": [
        {"name": "Support", "url": "#", "new_window": True},
        {"model": "auth.user"},
    ],

    # ── Sidebar ─────────────────────────────────────────────────────────────
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Custom order and icons for sidebar
    "order_with_respect_to": [
        "organization",
        "users",
        "course",
        "enrollment",
        "payment",
        "attendance",
        "history",
        "notification",
        "category",
        "device",
        "auth",
    ],

    # FontAwesome 5 icons per model
    "icons": {
        # Auth
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        # Organization
        "organization": "fas fa-building",
        "organization.Organization": "fas fa-building",
        # Users
        "users": "fas fa-users",
        "users.User": "fas fa-user-circle",
        "users.StaffProfile": "fas fa-user-tie",
        "users.StudentProfile": "fas fa-user-graduate",
        "users.TeacherProfile": "fas fa-chalkboard-teacher",
        # Category
        "category": "fas fa-tags",
        "category.Category": "fas fa-tag",
        # Course
        "course": "fas fa-book-open",
        "course.Course": "fas fa-book",
        "course.Group": "fas fa-layer-group",
        "course.GroupSchedule": "fas fa-calendar-alt",
        "course.Lesson": "fas fa-chalkboard",
        # Enrollment
        "enrollment": "fas fa-clipboard-list",
        "enrollment.Enrollment": "fas fa-user-plus",
        # Payment
        "payment": "fas fa-money-bill-wave",
        "payment.Payment": "fas fa-receipt",
        # Attendance
        "attendance": "fas fa-calendar-check",
        "attendance.Attendance": "fas fa-user-check",
        # History
        "history": "fas fa-history",
        "history.History": "fas fa-scroll",
        # Notification
        "notification": "fas fa-bell",
        "notification.Notification": "fas fa-bell",
        # Device
        "device": "fas fa-laptop",
        "device.Device": "fas fa-mobile-alt",
        "device.UserSession": "fas fa-shield-alt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ── UI toggles ──────────────────────────────────────────────────────────
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    # ── Changeform ──────────────────────────────────────────────────────────
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },

    # ── Language chooser ────────────────────────────────────────────────────
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    # ── Theme ───────────────────────────────────────────────────────────────
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",         # Bootstrap dark theme
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
