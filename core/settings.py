from pathlib import Path
import os
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Configurações Dinâmicas (leitura do .env)
SECRET_KEY = os.getenv('SECRET_KEY', 'chave-padrao-para-desenvolvimento')
DEBUG = os.getenv('DEBUG') == 'True'

# Pastas dos anexos
MEDIA_URL = '/media/'
# Força o uso exclusivo do HD Externo. Se a variável do .env não existir, ele bloqueia ou usa o caminho absoluto externo obrigatoriamente.
MEDIA_ROOT = os.getenv('MEDIA_ROOT_EXTERNO', '/mnt/hd_externo/media')

# Converte a string do .env em uma lista de hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

CLIENT_NAME = os.getenv('CLIENT_NAME')
CLIENT_LOGO_URL = os.getenv('CLIENT_LOGO_URL')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'denuncias',
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
                'denuncias.context_processors.dados_cliente',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'), 
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Validação de senhas e internacionalização mantidas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'assets']

# 3. Configurações de E-mail Profissionais
# E-mail de produção
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Backend fantasma para ignorar os envios:
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# Converte a string de e-mails em lista
DESTINATARIO_DENUNCIA = os.getenv('DESTINATARIO_DENUNCIA', 'admin@exemplo.com').split(',')
DESTINATARIOS_ADMIN = []

email_res = os.getenv('EMAIL_RES')

if email_res:
    DESTINATARIOS_ADMIN.append(email_res)
    
csrf_trusted = os.getenv('CSRF_TRUSTED_ORIGINS')
CSRF_TRUSTED_ORIGINS = csrf_trusted.split(',') if csrf_trusted else []

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


