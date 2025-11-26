"""
╔══════════════════════════════════════════════════════════════════╗
║                    CONFIGURAÇÕES DO PROJETO LOGOS                ║
║                  Sistema Integrado de Gestão - Grupo Lisboa      ║
╚══════════════════════════════════════════════════════════════════╝

📚 O QUE É ESTE ARQUIVO:
------------------------
Este é o arquivo de CONFIGURAÇÕES PRINCIPAIS do Django.
Aqui definimos:
  - Qual banco de dados usar (SQLite local ou PostgreSQL produção)
  - Quais apps/módulos estão instalados
  - Configurações de segurança (senhas, CORS, SSL)
  - Onde ficam arquivos estáticos (CSS, JS) e media (uploads)
  - Middleware (camadas de processamento de requisições)
  - Templates (sistema de páginas HTML)

🔧 COMO FUNCIONA:
-----------------
Django lê este arquivo quando o servidor inicia.
Ele usa variáveis de AMBIENTE para diferenciar:
  - Desenvolvimento (local): DEBUG=True, SQLite
  - Produção (Railway): DEBUG=False, PostgreSQL, SSL

📖 DOCUMENTAÇÃO OFICIAL:
------------------------
https://docs.djangoproject.com/en/5.2/topics/settings/
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os
import dj_database_url  # 📦 Biblioteca para parsear URL do PostgreSQL

# ============================================================
# 📂 DIRETÓRIOS DO PROJETO
# ============================================================

# BASE_DIR = Pasta raiz do projeto (onde está manage.py)
# Exemplo: C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 🔐 SEGURANÇA
# ============================================================

# SECRET_KEY: Chave secreta para criptografia
# ⚠️ EM PRODUÇÃO: Definir via variável de ambiente SECRET_KEY
# 🏠 EM DESENVOLVIMENTO: Usa chave padrão (insegura mas OK local)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-*7*d2c1a3b00b#-qijwx#_uqn!*0z#2q*y$@vesz-n5(9fyr1#')

# DEBUG: Modo de depuração
# ✅ True = Mostra erros detalhados na tela (APENAS DESENVOLVIMENTO!)
# ❌ False = Esconde erros, mostra página 500 genérica (PRODUÇÃO)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS: Lista de domínios permitidos
# 🏠 Desenvolvimento: Aceita localhost
# 🚀 Produção: Domínios específicos via variável de ambiente
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# ============================================================
# 📦 APLICAÇÕES INSTALADAS
# ============================================================
# Lista de apps (módulos) que Django deve carregar
# Ordem importa! Apps no topo têm prioridade

INSTALLED_APPS = [
    # ──────────────────────────────────────────────────────────
    # 🔧 APPS NATIVOS DO DJANGO (built-in)
    # ──────────────────────────────────────────────────────────
    'django.contrib.admin',        # 🛠️ Painel administrativo /admin/
    'django.contrib.auth',         # 👤 Sistema de autenticação (User, login)
    'django.contrib.contenttypes', # 🏷️ Sistema de tipos de conteúdo
    'django.contrib.sessions',     # 🍪 Gerenciamento de sessões (cookies)
    'django.contrib.messages',     # 💬 Sistema de mensagens (alerts)
    'django.contrib.staticfiles',  # 📂 Gerenciamento de arquivos estáticos
    
    # ──────────────────────────────────────────────────────────
    # 📚 BIBLIOTECAS EXTERNAS (third-party apps)
    # ──────────────────────────────────────────────────────────
    'rest_framework',              # 🔌 Django REST Framework - Criar APIs
    'rest_framework_simplejwt',    # 🔐 JWT - Tokens de autenticação
    'corsheaders',                 # 🌐 CORS - Permitir requisições de outros domínios
    
    # ──────────────────────────────────────────────────────────
    # 🏢 APPS DO PROJETO LOGOS (nossos módulos)
    # ──────────────────────────────────────────────────────────
    'accounts',    # 👥 Usuários, Organizações, Multi-tenant
    'erp_hub',     # 🔗 Integrações com ERPs externos
    'cameras',     # 📷 Gestão de câmeras físicas
    'fuel_prices', # ⛽ Preços de combustível (scraping)
    'verifik',     # 🤖 Sistema de IA - Detecção de produtos por câmeras
    'solar_monitor',  #  Monitoramento em tempo real das usinas solares
]

# ============================================================
# 🔄 MIDDLEWARE
# ============================================================
# Camadas de processamento que toda requisição passa
# Ordem importa! Executam de cima para baixo na entrada,
# e de baixo para cima na saída

MIDDLEWARE = [
    # 1️⃣ SecurityMiddleware: Adiciona headers de segurança (HSTS, SSL)
    'django.middleware.security.SecurityMiddleware',
    
    # 2️⃣ WhiteNoise: Serve arquivos estáticos em produção
    #    📌 Deve vir logo após SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    # 3️⃣ SessionMiddleware: Gerencia sessões de usuários (cookies)
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # 4️⃣ CORS: Permite requisições de outros domínios (APIs)
    'corsheaders.middleware.CorsMiddleware',
    
    # 5️⃣ CommonMiddleware: Funcionalidades comuns (redirects, ETags)
    'django.middleware.common.CommonMiddleware',
    
    # 6️⃣ CSRF: Proteção contra Cross-Site Request Forgery
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # 7️⃣ Authentication: Adiciona request.user em todas as views
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # 8️⃣ Messages: Sistema de mensagens (alerts verde/vermelho)
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # 9️⃣ Clickjacking: Proteção contra iframes maliciosos
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================
# 🌐 URLS E TEMPLATES
# ============================================================

# ROOT_URLCONF: Arquivo principal de rotas
# Aponta para logos/urls.py que importa rotas de outros apps
ROOT_URLCONF = 'logos.urls'

# TEMPLATES: Configuração do sistema de templates Django
TEMPLATES = [
    {
        # Backend: Motor de templates (Jinja2 é alternativa)
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        # DIRS: Pastas extras para buscar templates
        # Procura primeiro em templates/ na raiz do projeto
        'DIRS': [BASE_DIR / 'templates'],
        
        # APP_DIRS: Busca também em cada_app/templates/
        'APP_DIRS': True,
        
        # OPTIONS: Configurações extras
        'OPTIONS': {
            # context_processors: Variáveis globais disponíveis em todos templates
            'context_processors': [
                'django.template.context_processors.request',  # {{ request }}
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'logos.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Usar PostgreSQL em produção (Railway) ou SQLite em desenvolvimento
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Recife'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Servir arquivos estáticos em produção
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Email Configuration (development - console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@grupolisboa.com.br'

# For production, use SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'seu-email@grupolisboa.com.br'
# EMAIL_HOST_PASSWORD = 'sua-senha'

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Apenas em desenvolvimento

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
