import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project apps
    'assistant',
    'forum',
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

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'

# Database configuration (MongoDB with Djongo)
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'mingenially_learn',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': os.environ.get("MONGODB_URI"),
        }
    }
}

# AI Services Configuration
# Default LLM is gemma2 as requested
LLM_MODEL = os.environ.get('LLM_MODEL', 'gemma2')
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-m3')
CHROMA_PATH = os.environ.get("CHROMA_PATH", os.path.join(BASE_DIR, "chroma_db"))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'