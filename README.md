# 🏛️ PROJETO LOGOS
## Sistema Integrado de Gestão - Grupo Lisboa

[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.14.0-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg)](https://getbootstrap.com/)

---

## 📋 ÍNDICE

1. [Sobre o Projeto](#sobre-o-projeto)
2. [Funcionalidades](#funcionalidades)
3. [Tecnologias](#tecnologias)
4. [Instalação](#instalação)
5. [Uso](#uso)
6. [Documentação](#documentação)
7. [Deploy](#deploy)

---

## 🎯 SOBRE O PROJETO

O **LOGOS** é uma plataforma completa de gestão integrada desenvolvida para o **Grupo Lisboa**, focada em:

- ⛽ **Postos de Combustível**
- 🏪 **Lojas de Conveniência**
- 🤖 **Monitoramento por IA**

### Problema que Resolve

Gerenciar múltiplas empresas (postos) com:
- Cadastro centralizado de produtos
- Monitoramento por câmeras com IA
- Detecção de divergências (produtos não registrados)
- Controle de preços de combustível
- Múltiplos usuários com permissões diferentes

---

## ⚙️ FUNCIONALIDADES

### 👥 Módulo ACCOUNTS (Autenticação)
- ✅ Login/Logout seguro
- ✅ Multi-organização (um usuário acessa várias empresas)
- ✅ Permissões granulares por organização
- ✅ Aprovação de novos usuários por admin
- ✅ Troca de organização ativa sem logout

### 🤖 Módulo VERIFIK (IA e Produtos)
- ✅ Cadastro de produtos com múltiplos códigos de barras
- ✅ Upload múltiplo de imagens para treinar IA
- ✅ Detecção de produtos por câmeras
- ✅ Comparação entre produtos detectados e vendas registradas
- ✅ Alertas de divergências (produtos não registrados)
- ✅ Gestão de funcionários e operadores

### ⛽ Módulo FUEL_PRICES (Combustível)
- ✅ Web scraping automático de preços (Vibra Energia)
- ✅ Histórico de preços
- ✅ Comparação com concorrentes

### 🔗 Módulo ERP_HUB (Integrações)
- ✅ Integração com ERPs externos
- ✅ Sincronização de dados
- ✅ Logs de sincronizações

### 📷 Módulo CAMERAS (Hardware)
- ✅ Gestão de câmeras físicas
- ✅ Status de câmeras (ativo/inativo)
- ✅ Eventos e alertas

---

## 🛠️ TECNOLOGIAS

### Backend
- **Python 3.14.0** - Linguagem principal
- **Django 5.2.7** - Framework web
- **Django REST Framework 3.16.1** - APIs REST
- **PostgreSQL** - Banco de dados (produção)
- **SQLite** - Banco de dados (desenvolvimento)

### Frontend
- **Bootstrap 5.3.2** - Framework CSS
- **Bootstrap Icons** - Ícones
- **HTML5 / CSS3** - Estrutura e estilo
- **JavaScript** - Interatividade

### Bibliotecas Python
- **Pillow 11.0.0** - Manipulação de imagens
- **openpyxl 3.1.5** - Leitura/escrita de Excel
- **Selenium 4.27.1** - Web scraping
- **Gunicorn 23.0.0** - Servidor WSGI
- **WhiteNoise 6.8.2** - Arquivos estáticos

### Deploy
- **Railway.app** - Plataforma de hosting
- **Nixpacks** - Build system
- **UOL** - Provedor de domínio

---

## 📥 INSTALAÇÃO

### Pré-requisitos
- Python 3.14+ instalado
- Git instalado
- VS Code (recomendado)

### Passo a Passo

#### 1. Clonar o repositório
```bash
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos
```

#### 2. Criar ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instalar dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configurar variáveis de ambiente
Criar arquivo `.env` na raiz:
```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 5. Executar migrações
```bash
python manage.py migrate
```

#### 6. Criar superusuário
```bash
python manage.py createsuperuser
```

#### 7. Rodar servidor
```bash
python manage.py runserver
```

Acessar: http://127.0.0.1:8000/

---

## 🚀 USO

### Acesso ao Sistema

#### Homepage
- URL: http://127.0.0.1:8000/
- Página inicial com apresentação dos módulos

#### Login
- URL: http://127.0.0.1:8000/login/
- Fazer login com credenciais criadas

#### Admin Django
- URL: http://127.0.0.1:8000/admin/
- Painel administrativo completo

#### VerifiK - Produtos
- URL: http://127.0.0.1:8000/verifik/produtos/
- Listar/criar/editar produtos

### Comandos Úteis

#### Importar produtos do Excel
```bash
python manage.py importar_produtos C:\caminho\produtos.xlsx
```

#### Executar scraper de preços
```bash
python manage.py scrape_vibra
```

#### Coletar arquivos estáticos
```bash
python manage.py collectstatic
```

#### Criar nova migração
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📚 DOCUMENTAÇÃO

Este projeto possui documentação completa em português:

### 📄 Documentos Principais

1. **[DOCUMENTACAO_COMPLETA.md](DOCUMENTACAO_COMPLETA.md)**
   - Visão geral do sistema
   - Estrutura do projeto
   - Modelos de dados explicados
   - Fluxos de funcionamento

2. **[TECNOLOGIAS_EXTERNAS.md](TECNOLOGIAS_EXTERNAS.md)**
   - Guia completo de todas as bibliotecas
   - Exemplos de uso
   - Links para documentação oficial

3. **[GUIA_DEPLOY_SIMPLES.md](GUIA_DEPLOY_SIMPLES.md)**
   - Passo a passo para deploy no Railway
   - Configuração de DNS
   - Troubleshooting

### 📁 Documentação no Código

Todos os arquivos possuem comentários detalhados em **português**:

- **models.py** - O que cada modelo faz, relacionamentos
- **views.py** - Explicação de cada função
- **settings.py** - Configurações documentadas
- **forms.py** - Como funcionam os formsets

---

## 🌐 DEPLOY

### Produção (Railway)

O sistema está configurado para deploy automático no Railway.app:

#### Arquivos de Configuração
- `nixpacks.toml` - Configuração do build
- `Procfile` - Comando de start
- `runtime.txt` - Versão do Python
- `requirements.txt` - Dependências

#### Variáveis de Ambiente Necessárias
```env
SECRET_KEY=chave-secreta-muito-forte
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app,grupolisboa.com.br
DATABASE_URL=postgresql://... (Railway cria automaticamente)
```

#### Passo a Passo Completo
Ver: **[GUIA_DEPLOY_SIMPLES.md](GUIA_DEPLOY_SIMPLES.md)**

---

## 🔐 SEGURANÇA

### Medidas Implementadas

- ✅ **CSRF Protection** - Proteção contra ataques CSRF
- ✅ **SQL Injection** - Django ORM sanitiza queries
- ✅ **XSS Protection** - Templates escapam HTML automaticamente
- ✅ **Senhas Hash** - Nunca armazenadas em texto puro
- ✅ **SSL/HTTPS** - Forçado em produção
- ✅ **HSTS** - HTTP Strict Transport Security
- ✅ **Permissões** - Controle granular por organização

---

## 📊 STATUS DO PROJETO

- ✅ **Backend:** Completo e funcional
- ✅ **Frontend:** Interface moderna implementada
- ✅ **Autenticação:** Multi-org funcionando
- ✅ **VerifiK:** Cadastro de produtos e imagens
- 🔄 **Deploy:** Em processo (Railway)
- ⏳ **IA:** Detecção de produtos (a implementar)
- ⏳ **Mobile:** Planejado para v2.0

---

## 🔄 CHANGELOG

### v1.0.0 (21/11/2025)
- ✅ Sistema de autenticação multi-organização
- ✅ Módulo VerifiK completo
- ✅ Importação de produtos via Excel
- ✅ Upload múltiplo de imagens
- ✅ Scraper Vibra Energia
- ✅ Homepage responsiva
- ✅ Documentação completa em português
- ✅ Preparado para deploy Railway

---

**Desenvolvido com ❤️ para o Grupo Lisboa**

**Última atualização:** 21/11/2025
