# 🚀 PLANO DE MELHORIAS - PROJETO LOGOS

## 📊 ANÁLISE GERAL DO PROJETO

### ✅ **O QUE ESTÁ BOM**

1. **Arquitetura Django bem estruturada**
   - Multi-tenant com Organization
   - Apps modularizados (accounts, verifik, erp_hub, fuel_prices, cameras)
   - Models bem documentados
   - APIs REST com ViewSets

2. **VerifiK - Sistema de IA**
   - Modelo ProdutoMae funcionando
   - 177 produtos cadastrados
   - Estrutura pronta para treinamento YOLO

3. **Fuel Prices**
   - Scraper Vibra funcionando
   - Dashboard consolidado
   - Matriz de comparação de preços

---

## 🔴 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Falta de requirements.txt completo**
- Dificulta deploy e compartilhamento
- Não sabemos todas as dependências

### 2. **Imports com erro nos scripts**
```python
# ❌ ERRO em scrapers/vibra_scraper.py, treinar_heineken.py, etc
from fuel_prices.models import PostoVibra  # Import não resolvido
from verifik.models import ProdutoMae      # Import não resolvido
```
**Causa:** Scripts standalone não adicionam projeto ao PYTHONPATH

### 3. **Falta de testes automatizados**
- Nenhum arquivo de teste funcional
- tests.py vazio em todos os apps

### 4. **Configurações de produção expostas**
- SECRET_KEY hardcoded em settings.py
- Senhas de banco em texto puro
- DEBUG=True em produção (risco)

### 5. **Sem sistema de logs centralizado**
- Dificulta debug em produção
- Não rastreia erros do usuário

### 6. **Falta Docker/Docker Compose**
- Deploy manual trabalhoso
- Ambiente de dev não padronizado

### 7. **Frontend sem framework moderno**
- HTML puro com Bootstrap
- Sem React/Vue/Next.js
- Dificulta criar SPAs

### 8. **Sem CI/CD**
- Deploy manual
- Sem testes automáticos antes de subir código

---

## 🎯 PLANO DE MELHORIAS PRIORIZADAS

### 🔴 **CRÍTICO (Fazer AGORA)**

#### 1. Criar requirements.txt completo
```bash
pip freeze > requirements.txt
```

#### 2. Corrigir imports dos scripts standalone
**Problema:** Scripts em `fuel_prices/*.py` não encontram módulos Django

**Solução:** Adicionar ao início de CADA script:
```python
import sys
from pathlib import Path

# Adicionar raiz do projeto ao PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

# Agora pode importar
from fuel_prices.models import PostoVibra
from verifik.models import ProdutoMae
```

#### 3. Criar .env para variáveis de ambiente
```bash
# .env
SECRET_KEY=sua-chave-super-secreta-aqui
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/logos_db
ALLOWED_HOSTS=localhost,127.0.0.1

# Vibra Scraper
VIBRA_USERNAME=seu_usuario
VIBRA_PASSWORD=sua_senha
```

#### 4. Instalar python-decouple
```bash
pip install python-decouple
```

**Atualizar settings.py:**
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

#### 5. Criar .gitignore completo
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
db.sqlite3
*.log

# Django
/media
/staticfiles
*.pot

# Sensitive
.env
secrets.json

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# YOLO
runs/
*.pt
```

---

### 🟡 **ALTA PRIORIDADE (Fazer ESTA SEMANA)**

#### 6. Implementar logging estruturado
```python
# logos/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/logos.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'verifik': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
    },
}
```

#### 7. Criar Docker Compose para desenvolvimento
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: logos_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

#### 8. Criar testes básicos
```python
# verifik/tests.py
from django.test import TestCase
from .models import ProdutoMae, CodigoBarrasProdutoMae

class ProdutoMaeTestCase(TestCase):
    def setUp(self):
        self.produto = ProdutoMae.objects.create(
            descricao_produto='HEINEKEN 350ML',
            marca='Heineken',
            tipo='CERVEJA',
            preco=4.50
        )
    
    def test_produto_criado(self):
        self.assertEqual(self.produto.descricao_produto, 'HEINEKEN 350ML')
        self.assertTrue(self.produto.ativo)
    
    def test_adicionar_codigo_barras(self):
        codigo = CodigoBarrasProdutoMae.objects.create(
            produto_mae=self.produto,
            codigo='7891234567890',
            principal=True
        )
        self.assertEqual(self.produto.codigos_barras.count(), 1)
```

#### 9. Melhorar estrutura de pastas
```
ProjetoLogus/
├── apps/                       # ✅ Mover apps para subpasta
│   ├── accounts/
│   ├── verifik/
│   ├── erp_hub/
│   ├── fuel_prices/
│   └── cameras/
├── config/                     # ✅ Separar configurações
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── static/                     # Arquivos estáticos
├── media/                      # Uploads
├── templates/                  # Templates globais
├── scripts/                    # ✅ Scripts utilitários
│   ├── importar_produtos.py
│   ├── treinar_ia.py
│   └── backup_db.py
├── logs/                       # Logs da aplicação
├── docker/                     # Dockerfiles
├── docs/                       # Documentação
├── tests/                      # Testes globais
├── requirements/               # ✅ Separar dependências
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── README.md
```

#### 10. Criar management commands
```python
# verifik/management/commands/import_products.py
from django.core.management.base import BaseCommand
from verifik.models import ProdutoMae
import pandas as pd

class Command(BaseCommand):
    help = 'Importa produtos de planilha Excel'
    
    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)
    
    def handle(self, *args, **options):
        df = pd.read_excel(options['excel_file'])
        
        for _, row in df.iterrows():
            ProdutoMae.objects.create(
                descricao_produto=row['Descrição'],
                marca=row.get('Marca', ''),
                tipo=row.get('CATEGORIA', ''),
                preco=row.get('Preço Venda', 0)
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Criado: {row["Descrição"]}')
            )
```

**Uso:**
```bash
python manage.py import_products planilha.xlsx
```

---

### 🟢 **MÉDIA PRIORIDADE (Fazer ESTE MÊS)**

#### 11. Implementar Celery para tarefas assíncronas
```python
# logos/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')

app = Celery('logos')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**Uso:**
```python
# verifik/tasks.py
from celery import shared_task
from ultralytics import YOLO

@shared_task
def treinar_modelo_yolo(produto_id):
    # Treinamento em background
    modelo = YOLO('yolov8s.pt')
    modelo.train(data='dataset.yaml', epochs=50)
    return 'Treinamento concluído'
```

#### 12. Adicionar django-debug-toolbar
```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = ['127.0.0.1']
```

#### 13. Criar API de VerifiK para detecção
```python
# verifik/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ultralytics import YOLO
import cv2
import numpy as np

@api_view(['POST'])
def detectar_produto(request):
    """
    POST /api/verifik/detectar/
    Body: { "imagem": "base64..." }
    """
    imagem_base64 = request.data.get('imagem')
    
    # Decodificar imagem
    img_data = base64.b64decode(imagem_base64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Carregar modelo treinado
    modelo = YOLO('verifik_modelo.pt')
    resultados = modelo(img)
    
    # Processar detecções
    deteccoes = []
    for r in resultados:
        for box in r.boxes:
            deteccoes.append({
                'produto': box.cls,
                'confianca': float(box.conf),
                'bbox': box.xyxy.tolist()
            })
    
    return Response({
        'status': 'success',
        'deteccoes': deteccoes
    })
```

#### 14. Implementar cache com Redis
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache por 15 minutos
def dashboard_consolidado(request):
    # ...
```

#### 15. Adicionar paginação nas APIs
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

---

### 💡 **BAIXA PRIORIDADE (Fazer FUTURO)**

#### 16. Migrar frontend para Next.js
- Criar projeto Next.js separado
- Consumir APIs Django via REST
- Deploy frontend em Vercel

#### 17. Adicionar Swagger/OpenAPI
```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS += ['drf_spectacular']

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
```

#### 18. Implementar webhooks
```python
# verifik/webhooks.py
import requests

def notificar_deteccao(incidente):
    webhook_url = incidente.organization.webhook_url
    
    payload = {
        'event': 'produto_detectado',
        'produto': incidente.produto.descricao_produto,
        'confianca': incidente.confianca,
        'timestamp': incidente.created_at.isoformat()
    }
    
    requests.post(webhook_url, json=payload)
```

#### 19. Adicionar GraphQL
```bash
pip install graphene-django
```

#### 20. Criar app mobile com React Native
- Expo/React Native
- Camera nativa
- Upload de fotos para detecção
- Notificações push

---

## 📝 CHECKLIST DE EXECUÇÃO

### Semana 1 (CRÍTICO)
- [ ] Criar requirements.txt
- [ ] Corrigir imports scripts standalone
- [ ] Criar .env e instalar python-decouple
- [ ] Criar .gitignore
- [ ] Mover SECRET_KEY para .env

### Semana 2 (ALTA)
- [ ] Implementar logging estruturado
- [ ] Criar Docker Compose
- [ ] Criar testes básicos
- [ ] Reorganizar estrutura de pastas
- [ ] Criar management commands

### Semana 3 (MÉDIA)
- [ ] Implementar Celery
- [ ] Adicionar django-debug-toolbar
- [ ] Criar API de detecção VerifiK
- [ ] Implementar cache Redis
- [ ] Adicionar paginação

### Semana 4 (POLIMENTO)
- [ ] Documentar APIs
- [ ] Criar README completo
- [ ] Setup CI/CD (GitHub Actions)
- [ ] Testes de carga
- [ ] Deploy em staging

---

## 🎯 PRIORIDADES IMEDIATAS (HOJE)

1. ✅ **Criar requirements.txt**
2. ✅ **Corrigir imports standalone**
3. ✅ **Criar .env**
4. ✅ **Melhorar CSS dos scripts**
5. ✅ **Criar estrutura de logs/**

---

## 💰 RETORNO SOBRE INVESTIMENTO (ROI)

| Melhoria | Tempo | Impacto | ROI |
|----------|-------|---------|-----|
| Requirements.txt | 5min | ⭐⭐⭐⭐⭐ | 🔥🔥🔥🔥🔥 |
| .env + decouple | 15min | ⭐⭐⭐⭐⭐ | 🔥🔥🔥🔥🔥 |
| Corrigir imports | 30min | ⭐⭐⭐⭐ | 🔥🔥🔥🔥 |
| Logging | 1h | ⭐⭐⭐⭐ | 🔥🔥🔥🔥 |
| Docker Compose | 2h | ⭐⭐⭐⭐⭐ | 🔥🔥🔥🔥 |
| Testes | 4h | ⭐⭐⭐ | 🔥🔥🔥 |
| Celery | 3h | ⭐⭐⭐⭐ | 🔥🔥🔥 |
| API VerifiK | 6h | ⭐⭐⭐⭐⭐ | 🔥🔥🔥🔥🔥 |

---

**Total estimado: 40-60 horas para deixar projeto production-ready** 🚀
