# 📚 DOCUMENTAÇÃO COMPLETA - PROJETO LOGOS
## Sistema Integrado de Gestão - Grupo Lisboa

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Tecnologias Utilizadas](#tecnologias-utilizadas)
4. [Módulos do Sistema](#módulos-do-sistema)
5. [Banco de Dados](#banco-de-dados)
6. [Como Funciona](#como-funciona)
7. [Guias de Uso](#guias-de-uso)

---

## 🎯 VISÃO GERAL

### O que é o LOGOS?

O **LOGOS** é uma plataforma completa de gestão integrada para o **Grupo Lisboa**, focada em postos de combustíveis e lojas de conveniência.

### Objetivos do Sistema:

- 🏪 **Gestão de Produtos:** Cadastro centralizado com múltiplos códigos de barras
- 🤖 **VerifiK (IA):** Monitoramento por câmeras com detecção de produtos
- 💰 **Preços de Combustível:** Scraping automatizado de preços
- 🔗 **ERP Hub:** Integração com sistemas externos
- 👥 **Multi-organização:** Múltiplas empresas em um único sistema

### Para quem é?

- **Administradores:** Gerenciar empresas, usuários e configurações
- **Gestores:** Visualizar relatórios e monitorar operações
- **Operadores:** Cadastrar produtos, gerenciar vendas

---

## 📁 ESTRUTURA DO PROJETO

```
ProjetoLogus/
│
├── 📁 logos/                    # Configurações principais do Django
│   ├── settings.py              # Configurações do projeto
│   ├── urls.py                  # Rotas principais (mapa do site)
│   ├── wsgi.py                  # Interface para servidor web
│   └── asgi.py                  # Interface para WebSockets (futuro)
│
├── 📁 accounts/                 # Módulo de autenticação e usuários
│   ├── models.py                # User, Organization, UserOrganization
│   ├── views.py                 # Login, registro, troca de org
│   ├── forms.py                 # Formulários de cadastro
│   └── templates/               # Telas de login, registro
│
├── 📁 verifik/                  # Módulo de câmeras e IA
│   ├── models.py                # Produtos, Câmeras, Detecções
│   ├── views.py                 # Gerenciamento de produtos/imagens
│   ├── forms.py                 # Formulários com formsets
│   ├── urls.py                  # Rotas do VerifiK
│   ├── templates/               # Telas do módulo
│   └── management/              # Comandos personalizados
│       └── commands/
│           └── importar_produtos.py  # Importar do Excel
│
├── 📁 fuel_prices/              # Módulo de preços de combustível
│   ├── models.py                # FuelPrice (a criar)
│   ├── scrapers/                # Web scraping
│   │   └── vibra_scraper.py    # Scraper Vibra Energia
│   └── management/              # Comandos de scraping
│
├── 📁 erp_hub/                  # Integrações com ERPs externos
│   ├── models.py                # Configurações de integração
│   └── api_views.py             # APIs REST
│
├── 📁 cameras/                  # Gestão de câmeras físicas
│   ├── models.py                # Camera, Event, Alert
│   └── api_views.py             # APIs de câmeras
│
├── 📁 templates/                # Templates globais
│   ├── base.html                # Template base (não usado)
│   ├── home.html                # Página inicial do LOGOS
│   └── accounts/
│       └── login.html           # Tela de login
│
├── 📁 static/                   # Arquivos estáticos (CSS, JS, imagens)
│   └── (ainda não criado)
│
├── 📁 media/                    # Upload de arquivos (imagens de produtos)
│   └── produtos/                # Imagens de produtos
│
├── 📄 manage.py                 # Script principal do Django
├── 📄 requirements.txt          # Dependências do Python
├── 📄 db.sqlite3               # Banco de dados (desenvolvimento)
├── 📄 Procfile                  # Configuração para deploy (Railway/Heroku)
├── 📄 nixpacks.toml            # Configuração para Railway
├── 📄 runtime.txt              # Versão do Python
├── 📄 .env.production          # Variáveis de ambiente (produção)
│
└── 📄 GUIA_DEPLOY_SIMPLES.md  # Este guia de deploy
```

---

## 🛠️ TECNOLOGIAS UTILIZADAS

### Backend (Servidor)

#### 🐍 Django 5.2.7
**O que é:** Framework web em Python (como uma "caixa de ferramentas" para criar sites)

**Por que usamos:**
- ✅ Rápido para desenvolver
- ✅ Seguro (proteção contra ataques)
- ✅ Admin integrado (painel de controle automático)
- ✅ ORM (trabalha com banco sem SQL direto)

**Exemplo:**
```python
# models.py - Definir estrutura de dados
class Produto(models.Model):
    nome = models.CharField(max_length=200)  # Campo de texto
    preco = models.DecimalField(max_digits=10, decimal_places=2)  # Dinheiro
    
# Django cria a tabela automaticamente!
```

#### 🔌 Django REST Framework 3.16.1
**O que é:** Extensão do Django para criar APIs (comunicação entre sistemas)

**Por que usamos:**
- ✅ Criar API para apps mobile (futuro)
- ✅ Integrar com outros sistemas
- ✅ Automatizar processos

**Exemplo:**
```python
# API que retorna lista de produtos em JSON
GET /api/produtos/
Resposta:
[
  {"id": 1, "nome": "Cerveja Skol", "preco": "3.50"},
  {"id": 2, "nome": "Coca-Cola 2L", "preco": "7.99"}
]
```

#### 🔐 Simple JWT 5.5.1
**O que é:** Sistema de autenticação com tokens

**Como funciona:**
1. Usuário faz login → Recebe token (chave secreta)
2. Cada requisição envia o token
3. Sistema valida e autoriza

**Exemplo:**
```
Login: user@email.com / senha123
Token: eyJ0eXAiOiJKV1QiLCJhbGc... (chave única)

Requisições futuras:
GET /api/produtos/
Header: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### 🗄️ PostgreSQL (Produção) / SQLite (Desenvolvimento)
**O que é:** Bancos de dados relacionais

**SQLite:**
- Arquivo único (db.sqlite3)
- Bom para desenvolvimento local
- Não precisa instalar nada

**PostgreSQL:**
- Banco profissional
- Usado em produção (Railway)
- Mais recursos e performance

**Como Django usa:**
```python
# Você escreve Python, Django gera SQL
produtos = ProdutoMae.objects.filter(ativo=True)

# Django gera automaticamente:
# SELECT * FROM verifik_produtomae WHERE ativo = True;
```

---

### Frontend (Interface)

#### 🎨 Bootstrap 5.3.2
**O que é:** Biblioteca de componentes visuais prontos

**Por que usamos:**
- ✅ Design responsivo (funciona em celular/tablet/PC)
- ✅ Componentes prontos (botões, cards, modals)
- ✅ Grid system (organizar layout)

**Exemplo:**
```html
<!-- Card bonito com Bootstrap -->
<div class="card">
  <div class="card-header">🍺 Produto</div>
  <div class="card-body">
    <h5>Cerveja Skol 350ml</h5>
    <p class="text-success">R$ 3,50</p>
  </div>
</div>
```

#### 🎭 Bootstrap Icons
**O que é:** Ícones vetoriais gratuitos

**Como usar:**
```html
<i class="bi bi-camera"></i>  <!-- Ícone de câmera -->
<i class="bi bi-box"></i>      <!-- Ícone de caixa -->
<i class="bi bi-graph-up"></i> <!-- Ícone de gráfico -->
```

---

### Bibliotecas Python

#### 📊 Pillow 11.0.0
**O que é:** Manipulação de imagens

**Onde usamos:**
- ✅ Upload de fotos de produtos
- ✅ Redimensionar imagens
- ✅ Validar formato (JPG, PNG)

**Exemplo:**
```python
from PIL import Image

# Abrir imagem
img = Image.open('produto.jpg')

# Redimensionar
img = img.resize((800, 600))

# Salvar
img.save('produto_reduzido.jpg')
```

#### 📑 openpyxl 3.1.5
**O que é:** Ler/escrever arquivos Excel

**Onde usamos:**
- ✅ Importar produtos de planilhas
- ✅ Exportar relatórios (futuro)

**Exemplo:**
```python
from openpyxl import load_workbook

# Abrir Excel
wb = load_workbook('produtos.xlsx')
sheet = wb.active

# Ler células
for row in sheet.iter_rows(min_row=2):
    codigo = row[0].value
    descricao = row[1].value
    preco = row[2].value
```

#### 🌐 Selenium 4.27.1
**O que é:** Automação de navegador (web scraping)

**Onde usamos:**
- ✅ Coletar preços de combustível do site Vibra

**Como funciona:**
```python
from selenium import webdriver

# Abrir navegador
driver = webdriver.Chrome()

# Acessar site
driver.get('https://vibraenergia.com.br/postos')

# Procurar elemento
preco = driver.find_element(By.CLASS_NAME, 'preco').text
```

#### 🔥 Gunicorn 23.0.0
**O que é:** Servidor web para produção

**Por que usamos:**
- ❌ `python manage.py runserver` = só para desenvolvimento
- ✅ Gunicorn = profissional, rápido, múltiplos workers

**Como funciona:**
```bash
# Desenvolvimento (local)
python manage.py runserver

# Produção (Railway)
gunicorn logos.wsgi:application --workers 3
```

#### ❄️ WhiteNoise 6.8.2
**O que é:** Servir arquivos estáticos (CSS, JS, imagens)

**Por que usamos:**
- Em produção, Django não serve arquivos estáticos
- WhiteNoise faz isso de forma eficiente

**Como funciona:**
```python
# settings.py
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Adiciona middleware
    # ...
]

# Arquivos são servidos automaticamente de staticfiles/
```

---

## 🏗️ MÓDULOS DO SISTEMA

### 1. 👤 ACCOUNTS (Autenticação)

**Responsável por:**
- Login/Logout
- Cadastro de usuários
- Aprovação de usuários (admin)
- Troca de organização

**Modelos principais:**

#### User (Usuário)
```python
class User(AbstractUser):
    """
    Usuário do sistema
    
    O que é:
    - Extensão do usuário padrão do Django
    - Adiciona campos customizados
    
    Campos extras:
    - cpf: CPF do usuário (único)
    - telefone: Telefone de contato
    - active_organization: Organização atual (pode trocar)
    - is_approved: Se foi aprovado por admin
    """
    email = models.EmailField(unique=True)  # Email como login
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=15)
    active_organization = models.ForeignKey(Organization, ...)
    is_approved = models.BooleanField(default=False)
```

#### Organization (Organização/Empresa)
```python
class Organization(models.Model):
    """
    Empresa do grupo
    
    Exemplos:
    - Posto Lisboa Centro
    - Posto Lisboa Norte
    - Loja de Conveniência Sul
    
    Campos:
    - name: Nome da empresa
    - cnpj: CNPJ único
    - members: Usuários que têm acesso (ManyToMany)
    """
```

#### UserOrganization (Permissões por Empresa)
```python
class UserOrganization(models.Model):
    """
    Tabela de relação entre User e Organization
    
    Por que existe:
    - Um usuário pode ter acesso a várias empresas
    - Cada acesso tem permissões diferentes
    
    Exemplo:
    João tem acesso a:
    - Posto Centro: Admin (pode tudo)
    - Posto Norte: Apenas visualizar
    
    Campos booleanos (True/False):
    - is_org_admin: Administrador da empresa
    - can_access_verifik: Acessa módulo VerifiK
    - can_access_erp_hub: Acessa ERP Hub
    - can_manage_users: Gerencia usuários
    - can_view_reports: Vê relatórios
    """
```

**Fluxo de autenticação:**
```
1. Usuário acessa /login/
2. Digita email e senha
3. Sistema valida no banco de dados
4. Se correto E aprovado: cria sessão
5. Redireciona para homepage
6. Mostra módulos conforme permissões
```

---

### 2. 📦 VERIFIK (IA e Produtos)

**Responsável por:**
- Cadastro de produtos
- Upload de imagens para IA
- Gestão de códigos de barras
- Monitoramento por câmeras
- Detecção de produtos
- Alertas e incidentes

**Modelos principais:**

#### ProdutoMae (Produto Global)
```python
class ProdutoMae(models.Model):
    """
    Produto do catálogo global
    
    Por que "Mãe":
    - É o produto "original"
    - Todas as empresas usam o mesmo catálogo
    - Cada empresa pode ter códigos diferentes
    
    IMPORTANTE: NÃO tem FK para Organization!
    - Um produto serve para TODAS as empresas
    
    Campos:
    - descricao_produto: Nome completo
    - marca: Marca do produto
    - tipo: Bebida, Alimento, etc
    - preco: Preço sugerido (cada empresa pode alterar)
    - imagem_referencia: Foto principal
    - ativo: Se está ativo ou descontinuado
    
    Related names (relações inversas):
    - codigos_barras: Todos os códigos de barras deste produto
    - imagens_treino: Imagens para treinar IA
    """
    descricao_produto = models.CharField(max_length=255)
    marca = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem_referencia = models.ImageField(upload_to='produtos/')
    ativo = models.BooleanField(default=True)
```

#### CodigoBarrasProdutoMae (Códigos de Barras)
```python
class CodigoBarrasProdutoMae(models.Model):
    """
    Códigos de barras de um produto
    
    Por que existe:
    - Um produto pode ter vários códigos
    - Exemplo: Coca 350ml tem código da lata e da garrafa
    - Fornecedores diferentes = códigos diferentes
    
    Regra: Código ÚNICO globalmente
    - Nenhum outro produto pode ter o mesmo código
    
    Campos:
    - produto_mae: Qual produto (FK)
    - codigo: Código de barras (UNIQUE!)
    - principal: Código principal do produto
    
    Índices (otimização):
    - Index em 'codigo' para busca rápida
    """
    produto_mae = models.ForeignKey(ProdutoMae, 
                                    on_delete=models.CASCADE,
                                    related_name='codigos_barras')
    codigo = models.CharField(max_length=50, unique=True)
    principal = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['codigo']),  # Busca rápida
        ]
```

#### ImagemProduto (Imagens para IA)
```python
class ImagemProduto(models.Model):
    """
    Imagens de um produto para treinar IA
    
    Por que múltiplas imagens:
    - IA precisa ver produto de vários ângulos
    - Diferentes iluminações
    - Diferentes distâncias
    
    Campos:
    - produto: Qual produto (FK para ProdutoMae)
    - imagem: Arquivo da imagem
    - descricao: Opcional (ex: "vista frontal")
    - ordem: Ordem de exibição
    - ativa: Se está ativa para treino
    - data_upload: Quando foi enviada
    
    Uso:
    - Admin envia 5-10 fotos do mesmo produto
    - IA usa para aprender a reconhecer
    - Câmeras detectam produto em tempo real
    """
    produto = models.ForeignKey(ProdutoMae,
                                on_delete=models.CASCADE,
                                related_name='imagens_treino')
    imagem = models.ImageField(upload_to='produtos/treino/')
    descricao = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    ativa = models.BooleanField(default=True)
```

#### Camera (Câmera de Monitoramento)
```python
class Camera(models.Model):
    """
    Câmera física instalada no estabelecimento
    
    Uso:
    - Monitora produtos na prateleira
    - Detecta quando cliente pega produto
    - Compara com venda registrada
    
    Campos:
    - organization: Qual empresa (FK)
    - nome: Nome da câmera (ex: "Câmera Geladeira 1")
    - localizacao: Onde está (ex: "Corredor de bebidas")
    - ip_address: IP da câmera na rede
    - porta: Porta de conexão
    - url_stream: URL do stream RTSP
    - ativa: Se está operacional
    
    Exemplo de stream:
    rtsp://192.168.1.100:554/stream1
    """
```

#### DeteccaoProduto (Detecção por IA)
```python
class DeteccaoProduto(models.Model):
    """
    Registro de quando IA detecta um produto
    
    Fluxo:
    1. Cliente pega produto da prateleira
    2. Câmera envia frame para IA
    3. IA reconhece: "É uma Coca-Cola!"
    4. Cria registro de DeteccaoProduto
    5. Compara com venda registrada
    
    Campos:
    - camera: Qual câmera detectou (FK)
    - produto_identificado: Qual produto (FK ProdutoMae)
    - data_hora_deteccao: Quando aconteceu
    - metodo_deteccao: YOLO, Manual, etc
    - confianca: % de certeza (0-100)
    - imagem_capturada: Frame da detecção
    
    Exemplo:
    Detecção:
    - Camera: Geladeira 1
    - Produto: Coca-Cola 350ml
    - Confiança: 95.5%
    - Hora: 2025-11-21 14:30:15
    """
```

#### Incidente (Divergências)
```python
class Incidente(models.Model):
    """
    Divergência entre detecção e venda
    
    Quando acontece:
    - IA detectou produto sendo pego
    - MAS não foi registrada venda
    - OU quantidade diferente
    
    Tipos:
    - PRODUTO_NAO_REGISTRADO: Pegou mas não passou no caixa
    - QUANTIDADE_DIVERGENTE: Pegou 3, registrou 1
    - TROCO_INCORRETO: Problema com troco
    - SUSPEITA_FURTO: Possível furto
    
    Status:
    - PENDENTE: Precisa analisar
    - EM_ANALISE: Gestor verificando
    - RESOLVIDO: Problema explicado
    - FALSO_POSITIVO: Era falso alarme
    """
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    funcionario = models.ForeignKey(Funcionario, ...)
    deteccao = models.ForeignKey(DeteccaoProduto, ...)
```

**Arquivos importantes:**

##### verifik/views.py
```python
# VIEWS PRINCIPAIS:

def produtos_lista(request):
    """
    Lista todos os produtos com filtros
    
    Filtros disponíveis:
    - tipo: Bebida, Alimento, etc
    - busca: Busca por nome/marca
    - imagens: Só produtos com imagens
    
    Otimizações:
    - prefetch_related: Carrega códigos e imagens juntos
    - Evita N+1 queries (lentidão)
    """

def produto_detalhe(request, pk):
    """
    Detalhes de um produto
    
    Mostra:
    - Dados do produto
    - Todos os códigos de barras
    - Galeria de imagens
    - Estatísticas (quantas vezes foi detectado)
    - Formulário para adicionar imagens (se admin)
    """

def adicionar_imagem(request, produto_id):
    """
    Adiciona múltiplas imagens a um produto
    
    Processo:
    1. Recebe lista de imagens do formulário
    2. Para cada imagem:
       - Salva arquivo em media/produtos/treino/
       - Cria registro ImagemProduto
       - Define ordem sequencial
    3. Define primeira como referência (se não tiver)
    4. Mostra mensagem de sucesso
    
    Segurança:
    - Apenas admins podem adicionar
    - Valida tipo de arquivo (imagem)
    """
```

##### verifik/forms.py
```python
# FORMSETS (Formulários Múltiplos):

# O que é Formset:
# - Vários formulários iguais na mesma página
# - Usado para adicionar vários códigos/imagens de uma vez

CodigoBarrasFormSet = inlineformset_factory(
    ProdutoMae,           # Modelo pai
    CodigoBarrasProdutoMae,  # Modelo filho
    fields=['codigo', 'principal'],  # Campos
    extra=3,              # 3 formulários vazios
    can_delete=True       # Permite deletar
)

# Uso no template:
# - Mostra 3 campos vazios
# - JavaScript adiciona mais dinamicamente
# - management_form controla quantos tem
```

---

### 3. ⛽ FUEL_PRICES (Preços de Combustível)

**Responsável por:**
- Scraping de preços de combustível
- Comparação com concorrentes
- Histórico de preços

**Arquivo principal:**

##### fuel_prices/scrapers/vibra_scraper.py
```python
class VibraScraper:
    """
    Scraper para coletar preços do site Vibra Energia
    
    O que faz:
    1. Abre navegador automatizado (Selenium)
    2. Acessa site da Vibra
    3. Seleciona cada posto
    4. Extrai preços de Gasolina, Etanol, Diesel
    5. Salva no banco de dados
    
    Desafios:
    - Site usa JavaScript (precisa Selenium)
    - Precisa esperar elementos carregarem
    - Estrutura do HTML pode mudar
    
    Métodos:
    - inicializar_driver(): Cria navegador headless
    - acessar_site(): Abre página
    - selecionar_posto(): Troca entre postos
    - extrair_precos(): Pega valores da tela
    - salvar_dados(): Grava no banco
    """
```

**Como funciona o scraping:**
```python
# 1. Criar scraper
scraper = VibraScraper()

# 2. Inicializar navegador
scraper.inicializar_driver()

# 3. Acessar site
scraper.acessar_site()

# 4. Para cada posto:
for posto in postos:
    scraper.selecionar_posto(posto)
    precos = scraper.extrair_precos()
    scraper.salvar_dados(posto, precos)

# 5. Fechar navegador
scraper.fechar()
```

---

### 4. 🔗 ERP_HUB (Integrações)

**Responsável por:**
- Integrar com ERPs externos
- Sincronizar dados
- Logs de sincronização

**Modelos:**
- ERPIntegration: Configuração de integração
- Store: Lojas/Postos
- SyncLog: Histórico de sincronizações

---

### 5. 📷 CAMERAS (Gestão de Câmeras)

**Responsável por:**
- Gerenciar câmeras físicas
- Eventos de câmeras
- Alertas

---

## 🗄️ BANCO DE DADOS

### Relacionamentos

```
┌─────────────┐       ┌──────────────────┐       ┌────────────┐
│ Organization│◄──────┤UserOrganization  ├──────►│    User    │
│             │       │ (permissões)     │       │            │
└─────────────┘       └──────────────────┘       └────────────┘
       │                                                │
       │                                                │
       ▼                                                ▼
┌─────────────┐                               ┌────────────────┐
│   Camera    │                               │  Funcionario   │
└─────────────┘                               └────────────────┘
       │                                                
       │                                                
       ▼                                                
┌──────────────────┐                                   
│DeteccaoProduto   │                                   
└──────────────────┘                                   
       │                                                
       ▼                                                
┌─────────────┐                                        
│ ProdutoMae  │◄──────────┐                           
└─────────────┘           │                           
       │                  │                           
       ├──────────────────┼──────────────┐            
       │                  │              │            
       ▼                  ▼              ▼            
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ImagemProduto │  │CodigoBarras  │  │  ItemVenda   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Estratégia Multi-tenant

**O que é Multi-tenant:**
- Várias empresas no mesmo sistema
- Dados isolados por organização
- Alguns dados compartilhados (produtos)

**Como implementamos:**

```python
# Dados POR organização (cada empresa tem os seus):
class Camera(models.Model):
    organization = models.ForeignKey(Organization)  # ← FK obrigatória
    # Cada empresa vê só suas câmeras

# Dados COMPARTILHADOS (todas empresas usam):
class ProdutoMae(models.Model):
    # SEM FK para Organization!
    # Catálogo global

# Dados HÍBRIDOS (link entre compartilhado e org):
class CodigoBarrasProdutoMae(models.Model):
    produto_mae = models.ForeignKey(ProdutoMae)
    # Código é global, mas organizações podem ter códigos diferentes
```

---

## ⚙️ COMO FUNCIONA

### Fluxo de Login

```
1. User abre https://grupolisboa.com.br
2. Vê tela inicial (home.html)
3. Clica "Fazer Login"
4. Preenche email e senha
5. views.user_login() valida:
   - User existe?
   - Senha correta?
   - is_approved = True?
6. Se OK: cria sessão (Django armazena cookie)
7. Redireciona para home
8. home.html detecta user.is_authenticated
9. Mostra dashboard com módulos
10. Módulos filtrados por permissões UserOrganization
```

### Fluxo de Upload de Imagens

```
1. Admin acessa /verifik/produtos/1/ (Coca-Cola)
2. Rola até "Adicionar Imagens"
3. Clica "Selecionar Imagens"
4. Ctrl+Clique seleciona 5 fotos
5. (Opcional) Digita descrição: "Vista frontal"
6. Clica "Enviar Imagens"
7. Navegador envia POST para /verifik/produtos/1/adicionar-imagem/
8. views.adicionar_imagem() recebe:
   - request.FILES.getlist('imagens') = [img1, img2, ...]
   - request.POST.get('descricao') = "Vista frontal"
9. Para cada imagem:
   - Salva em media/produtos/treino/coca_cola_1.jpg
   - Cria ImagemProduto(produto=produto, imagem=..., ordem=1)
10. Define primeira como imagem_referencia
11. Redireciona com mensagem: "5 imagens adicionadas!"
```

### Fluxo de Detecção (VerifiK)

```
1. Cliente pega Coca-Cola da geladeira
2. Câmera (192.168.1.100) grava frame
3. Frame enviado para IA (YOLO)
4. IA processa:
   - Detecta objeto: Garrafa
   - Compara com imagens_treino
   - Match: ProdutoMae ID=1 (Coca-Cola)
   - Confiança: 95.5%
5. Cria DeteccaoProduto:
   - camera_id = 1
   - produto_identificado_id = 1
   - confianca = 95.5
   - data_hora_deteccao = agora
6. Sistema aguarda venda
7. Se não houver venda em 5min:
   - Cria Incidente(tipo='PRODUTO_NAO_REGISTRADO')
   - Notifica gestor
```

---

## 📚 GUIAS DE USO

### Para Desenvolvedores

#### Adicionar novo modelo

```python
# 1. Criar modelo em models.py
class NovoModelo(models.Model):
    campo = models.CharField(max_length=100)

# 2. Criar migração
python manage.py makemigrations

# 3. Aplicar migração
python manage.py migrate

# 4. Registrar no admin (opcional)
# admin.py
from .models import NovoModelo
admin.site.register(NovoModelo)
```

#### Adicionar nova view

```python
# 1. Criar função em views.py
def minha_view(request):
    # Lógica aqui
    return render(request, 'template.html', context)

# 2. Adicionar rota em urls.py
urlpatterns = [
    path('minha-rota/', views.minha_view, name='minha_view'),
]

# 3. Criar template
# templates/minha_app/template.html
```

#### Fazer query no banco

```python
# Buscar todos
produtos = ProdutoMae.objects.all()

# Filtrar
bebidas = ProdutoMae.objects.filter(tipo='Bebida')

# Buscar um
coca = ProdutoMae.objects.get(id=1)

# Com relacionamento
produto_com_codigos = ProdutoMae.objects.prefetch_related('codigos_barras').get(id=1)
codigos = produto_com_codigos.codigos_barras.all()
```

---

### Para Administradores

#### Aprovar novo usuário

```
1. Acesse /admin/
2. Accounts → Users
3. Encontre usuário (is_approved = False)
4. Marque "Is approved"
5. Salve
6. Usuário receberá email (futuro)
```

#### Importar produtos

```bash
# Via comando
python manage.py importar_produtos C:\caminho\produtos.xlsx

# Formato Excel:
# Coluna A: Código de barras
# Coluna B: Descrição
# Coluna C: Categoria
# Coluna D: Preço
```

---

## 🔐 SEGURANÇA

### Proteções implementadas

```python
# 1. CSRF Protection (Cross-Site Request Forgery)
# Django adiciona token em todos os forms
<form method="POST">
    {% csrf_token %}  <!-- Token único por sessão -->
    ...
</form>

# 2. SQL Injection
# Django ORM sanitiza automaticamente
# MAL: f"SELECT * FROM produtos WHERE id = {user_input}"
# BOM: ProdutoMae.objects.get(id=user_input)

# 3. XSS (Cross-Site Scripting)
# Templates escapam HTML automaticamente
# {{ user_input }}  ← Escapa <script> automaticamente

# 4. Autenticação
# Senhas são hash (não armazenadas em texto)
from django.contrib.auth.hashers import make_password
senha_hash = make_password('senha123')  # Nunca reversível

# 5. Permissões
# Decorators protegem views
@login_required  # Precisa estar logado
def minha_view(request):
    ...
```

---

## 🚀 DEPLOY

Ver arquivo: **GUIA_DEPLOY_SIMPLES.md**

---

## 📝 CHANGELOG

### Versão 1.0.0 (21/11/2025)
- ✅ Sistema de autenticação multi-org
- ✅ Módulo VerifiK completo
- ✅ Importação de produtos do Excel
- ✅ Upload múltiplo de imagens
- ✅ Scraper Vibra Energia
- ✅ Homepage responsiva
- ✅ Preparado para deploy Railway

---

## 👥 EQUIPE

- **Desenvolvedor:** GitHub Copilot + mlisboa17
- **Cliente:** Grupo Lisboa
- **Tecnologia:** Django + PostgreSQL + Bootstrap

---

## 📞 SUPORTE

Para dúvidas sobre código:
- Consulte este arquivo
- Veja comentários nos arquivos
- Pergunte ao desenvolvedor

---

**Última atualização:** 21/11/2025
