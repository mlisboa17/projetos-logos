# LOGUS - Ecossistema Python

Desenvolvimento backend em Python para os projetos LOGUS.

## 🐍 Setup Ambiente

### 1. Criar ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar ambiente
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
copy .env.example .env
# Editar .env com suas configurações
```

## 🚀 Rodar API

### Desenvolvimento
```bash
cd backend
python main.py
```

Ou com uvicorn:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Acessar
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 📁 Estrutura Backend

```
backend/
├── main.py              # FastAPI app principal
├── verifik/             # Módulo VerifiK
│   ├── detector.py      # Detecção YOLOv8
│   ├── api.py           # Endpoints VerifiK
│   └── models.py        # Schemas Pydantic
├── core/                # Core utilities
│   ├── config.py        # Configurações
│   ├── database.py      # SQLAlchemy setup
│   └── security.py      # Auth & JWT
└── models/              # Database models
```

## 🔧 Dependências Principais

- **FastAPI** - Framework web moderno
- **YOLOv8** (ultralytics) - Detecção de objetos
- **OpenCV** - Processamento de vídeo
- **SQLAlchemy** - ORM para banco de dados
- **Celery** - Tarefas assíncronas
- **Redis** - Cache e message broker

## 🎯 Próximos Passos

1. [ ] Configurar PostgreSQL
2. [ ] Implementar models do banco
3. [ ] Criar endpoints VerifiK
4. [ ] Integrar com câmeras IP
5. [ ] Treinar modelo YOLOv8 com produtos
6. [ ] Sistema de alertas em tempo real
