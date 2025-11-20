# Migração LOGOS: FastAPI → Django

## Por que Django?

Django é um framework **batteries-included** mais robusto e completo:

✅ **ORM mais poderoso** - Migrações automáticas, relacionamentos complexos
✅ **Admin integrado** - Painel administrativo pronto (sem código)
✅ **Autenticação completa** - Sistema de usuários, permissões, grupos
✅ **Multi-tenancy** - Bibliotecas prontas (django-tenants)
✅ **Ecosystem maduro** - Mais de 15 anos de desenvolvimento
✅ **Django REST Framework** - API REST profissional
✅ **Celery integration** - Tasks assíncronas nativas
✅ **Documentação superior** - Comunidade gigante

## Estrutura do Projeto Django

```
projetologos/
├── manage.py
├── logos/                    # Projeto Django principal
│   ├── __init__.py
│   ├── settings.py          # Configurações
│   ├── urls.py              # Rotas principais
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/            # Autenticação e usuários
│   │   ├── models.py        # User, Organization
│   │   ├── serializers.py   # DRF serializers
│   │   ├── views.py         # APIs
│   │   └── admin.py         # Django Admin
│   ├── erp_hub/             # Central de ERPs
│   │   ├── models.py        # ERPIntegration
│   │   ├── connectors/      # Conectores (WebPostos, Bling, etc)
│   │   └── views.py
│   ├── verifik/             # Sistema de câmeras
│   │   ├── models.py        # Camera, Detection, Product
│   │   └── tasks.py         # Celery tasks (YOLOv8)
│   └── fuel_prices/         # Preços combustíveis
│       ├── models.py
│       └── scrapers/        # Vibra scraper
├── frontend/                # Templates Django
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── base.html
│       ├── erp-hub.html
│       └── dashboard.html
└── requirements.txt
```

## Comparação: FastAPI vs Django

| Recurso | FastAPI | Django |
|---------|---------|--------|
| **Velocidade** | ⚡ Muito rápida | 🐢 Média |
| **Admin Panel** | ❌ Não tem | ✅ Nativo |
| **ORM** | SQLAlchemy (manual) | Django ORM (automático) |
| **Migrações** | Alembic (manual) | Automáticas (`makemigrations`) |
| **Auth** | Manual (JWT) | Nativo + extensível |
| **Multi-tenant** | Manual | django-tenants (pronto) |
| **Curva aprendizado** | Menor | Maior |
| **Ecosystem** | Novo (2018) | Maduro (2005) |
| **Melhor para** | APIs rápidas | Apps completos |

## Instalação Django

```bash
cd projetologos

# Criar novo projeto Django
pip install django djangorestframework django-tenants django-cors-headers celery redis

# Criar estrutura
django-admin startproject logos .
python manage.py startapp accounts
python manage.py startapp erp_hub
python manage.py startapp verifik
python manage.py startapp fuel_prices

# Migrar banco
python manage.py makemigrations
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver
```

## Django Admin - Painel Grátis!

Ao usar Django, você ganha **automaticamente** um painel administrativo:

- ✅ **CRUD completo** de todas as tabelas
- ✅ **Filtros e busca** automáticos
- ✅ **Relacionamentos** visuais
- ✅ **Permissões** por usuário/grupo
- ✅ **Histórico de alterações** (audit log)
- ✅ **Exportação** para CSV/JSON

Acesso: `http://localhost:8000/admin`

## Multi-Tenancy com django-tenants

```python
# settings.py
INSTALLED_APPS = [
    'django_tenants',  # Multi-tenant automático
    'apps.accounts',
    'apps.erp_hub',
    ...
]

# Cada organização terá seu próprio schema PostgreSQL
TENANT_MODEL = "accounts.Organization"
TENANT_DOMAIN_MODEL = "accounts.Domain"

# URLs isoladas por tenant
PUBLIC_SCHEMA_URLCONF = 'logos.urls_public'
ROOT_URLCONF = 'logos.urls_tenants'
```

Com django-tenants:
- ✅ Cada cliente = schema PostgreSQL isolado
- ✅ Dados 100% separados
- ✅ Performance superior
- ✅ Backup individual por tenant

## Models Django (exemplo)

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django_tenants.models import TenantMixin, DomainMixin

class Organization(TenantMixin):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    subscription_plan = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    auto_create_schema = True  # Cria schema PostgreSQL automaticamente

class Domain(DomainMixin):
    pass  # grupolisboa.logos.com.br

class User(AbstractUser):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
```

## Django REST Framework (API)

```python
# apps/accounts/serializers.py
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'organization']

# apps/accounts/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
```

Ganha automaticamente:
- ✅ GET /api/users/ (listar)
- ✅ POST /api/users/ (criar)
- ✅ GET /api/users/{id}/ (detalhes)
- ✅ PUT /api/users/{id}/ (atualizar)
- ✅ DELETE /api/users/{id}/ (deletar)
- ✅ Paginação, filtros, busca

## Celery + Redis (Tasks Assíncronas)

```python
# apps/verifik/tasks.py
from celery import shared_task
from ultralytics import YOLO

@shared_task
def detect_products(camera_id, frame_path):
    model = YOLO('yolov8n.pt')
    results = model(frame_path)
    # Processar detecções...
    return results

# Chamar task
detect_products.delay(camera_id=1, frame_path='frame.jpg')
```

## Próximos Passos

1. ✅ **Decidir:** Continuar FastAPI ou migrar Django?
2. ⏳ Configurar PostgreSQL (necessário para multi-tenancy)
3. ⏳ Migrar models para Django ORM
4. ⏳ Criar Django Admin customizado
5. ⏳ Implementar django-tenants
6. ⏳ Setup Celery + Redis
7. ⏳ Deploy (Heroku, AWS, ou UOL)

## Recomendação

Para o LOGOS (plataforma SaaS multi-tenant complexa):

**🎯 RECOMENDO DJANGO** porque:
- Multi-tenancy robusto (django-tenants)
- Admin panel grátis (economiza semanas de dev)
- Ecosystem maduro para SaaS
- Melhor para equipes maiores

FastAPI é ótimo para:
- Microserviços rápidos
- APIs simples
- Protótipos rápidos

Quer que eu **migre para Django** ou **continue com FastAPI**?
