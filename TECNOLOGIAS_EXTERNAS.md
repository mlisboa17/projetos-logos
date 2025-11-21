# 📚 TECNOLOGIAS EXTERNAS - GUIA COMPLETO
## Frameworks, Bibliotecas e Ferramentas Usadas no Projeto LOGOS

---

## 📋 ÍNDICE

1. [Python e Django](#python-e-django)
2. [Django REST Framework](#django-rest-framework)
3. [Bibliotecas Python](#bibliotecas-python)
4. [Frontend](#frontend)
5. [Banco de Dados](#banco-de-dados)
6. [Deploy e Produção](#deploy-e-produção)
7. [Desenvolvimento](#desenvolvimento)

---

## 🐍 PYTHON E DJANGO

### Python 3.14.0

**O que é:**
Linguagem de programação usada no backend (servidor).

**Por que Python:**
- ✅ Fácil de aprender e ler
- ✅ Muitas bibliotecas prontas
- ✅ Ótimo para IA/Machine Learning
- ✅ Comunidade gigante

**Sintaxe básica:**
```python
# Variáveis
nome = "João"
idade = 25
preco = 10.50

# Estruturas
if idade >= 18:
    print("Maior de idade")

# Loops
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# Listas
produtos = ["Coca", "Pepsi", "Guaraná"]
produtos.append("Fanta")  # Adiciona item

# Dicionários (como JSON)
usuario = {
    "nome": "João",
    "email": "joao@email.com",
    "idade": 25
}
```

**Documentação:**
- Site oficial: https://www.python.org/
- Tutorial: https://docs.python.org/3/tutorial/

---

### Django 5.2.7

**O que é:**
Framework web em Python. É como uma "caixa de ferramentas" completa para criar sites.

**Analogia:**
- Construir site do zero = Construir casa tijolo por tijolo
- Usar Django = Usar casa pré-fabricada (já vem com tudo)

**O que Django oferece:**

#### 1. ORM (Mapeamento Objeto-Relacional)
**Problema:** SQL é difícil e verboso
**Solução:** Escrever Python, Django gera SQL

```python
# ❌ SEM Django (SQL puro):
cursor.execute("SELECT * FROM produtos WHERE ativo = 1")

# ✅ COM Django (Python):
produtos = Produto.objects.filter(ativo=True)
```

#### 2. Admin Automático
**Problema:** Criar painel admin dá trabalho
**Solução:** Django cria automaticamente

```python
# admin.py
from django.contrib import admin
from .models import Produto

admin.site.register(Produto)
# Pronto! Agora /admin/ tem CRUD completo de Produto
```

#### 3. Sistema de Templates
**Problema:** Misturar HTML e Python é confuso
**Solução:** Templates com lógica simples

```html
<!-- template.html -->
<h1>Produtos</h1>
{% for produto in produtos %}
    <div>{{ produto.nome }} - R$ {{ produto.preco }}</div>
{% endfor %}
```

#### 4. Autenticação Integrada
**Problema:** Sistema de login é complexo
**Solução:** Django já vem com User, login, logout

```python
from django.contrib.auth.decorators import login_required

@login_required  # Apenas usuários logados
def minha_view(request):
    user = request.user  # Usuário atual
    return render(request, 'template.html')
```

#### 5. Migrações de Banco
**Problema:** Alterar estrutura do banco é perigoso
**Solução:** Migrações versionadas

```bash
# 1. Criar modelo
class Produto(models.Model):
    nome = models.CharField(max_length=100)

# 2. Criar migração
python manage.py makemigrations

# 3. Aplicar no banco
python manage.py migrate
```

**Estrutura de um projeto Django:**
```
meu_projeto/
├── manage.py           # Comandos do Django
├── meu_projeto/        # Configurações
│   ├── settings.py     # Configurações
│   ├── urls.py         # Rotas principais
│   └── wsgi.py         # Interface com servidor
├── app1/               # Aplicação 1
│   ├── models.py       # Modelos (banco)
│   ├── views.py        # Views (lógica)
│   ├── urls.py         # Rotas
│   └── templates/      # HTMLs
└── app2/               # Aplicação 2
```

**Comandos principais:**
```bash
# Criar projeto
django-admin startproject nome_projeto

# Criar app
python manage.py startapp nome_app

# Rodar servidor local
python manage.py runserver

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superuser (admin)
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

**Documentação:**
- Site oficial: https://www.djangoproject.com/
- Tutorial: https://docs.djangoproject.com/en/5.2/intro/tutorial01/
- Documentação completa: https://docs.djangoproject.com/en/5.2/

---

## 🔌 DJANGO REST FRAMEWORK

### Django REST Framework 3.16.1

**O que é:**
Extensão do Django para criar APIs REST (comunicação entre sistemas).

**Por que usar:**
- ✅ Apps mobile precisam de API
- ✅ Integrar com outros sistemas
- ✅ Frontend separado do backend

**Conceitos principais:**

#### 1. Serializers (Conversores)
Convertem objetos Python ↔ JSON

```python
# serializers.py
from rest_framework import serializers
from .models import Produto

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'preco', 'ativo']

# Uso:
produto = Produto.objects.get(id=1)
serializer = ProdutoSerializer(produto)
print(serializer.data)
# {'id': 1, 'nome': 'Coca-Cola', 'preco': '3.50', 'ativo': True}
```

#### 2. ViewSets (Views Automáticas)
CRUD completo em 5 linhas

```python
# views.py
from rest_framework import viewsets
from .models import Produto
from .serializers import ProdutoSerializer

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

# Pronto! Isso cria:
# GET /produtos/ - Listar
# POST /produtos/ - Criar
# GET /produtos/1/ - Detalhe
# PUT /produtos/1/ - Atualizar
# DELETE /produtos/1/ - Deletar
```

#### 3. Routers (Rotas Automáticas)
```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import ProdutoViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet)

urlpatterns = router.urls
```

**Exemplo de requisição:**
```bash
# Listar produtos
GET http://localhost:8000/api/produtos/
Resposta:
[
    {"id": 1, "nome": "Coca-Cola", "preco": "3.50"},
    {"id": 2, "nome": "Pepsi", "preco": "3.20"}
]

# Criar produto
POST http://localhost:8000/api/produtos/
Body: {"nome": "Fanta", "preco": "3.00"}
Resposta: {"id": 3, "nome": "Fanta", "preco": "3.00"}
```

**Documentação:**
- Site oficial: https://www.django-rest-framework.org/
- Tutorial: https://www.django-rest-framework.org/tutorial/quickstart/

---

### Simple JWT 5.5.1

**O que é:**
Autenticação por tokens JWT (JSON Web Tokens).

**Como funciona:**

```
┌─────────┐                          ┌─────────┐
│ Cliente │                          │ Servidor│
└────┬────┘                          └────┬────┘
     │                                    │
     │ 1. POST /login/                    │
     │    {"email": "...", "senha": "..."}│
     ├───────────────────────────────────►│
     │                                    │
     │ 2. Token JWT                       │
     │    {"access": "eyJ0...", ...}      │
     │◄───────────────────────────────────┤
     │                                    │
     │ 3. GET /api/produtos/              │
     │    Header: Authorization: Bearer eyJ0...
     ├───────────────────────────────────►│
     │                                    │
     │ 4. Dados dos produtos              │
     │◄───────────────────────────────────┤
```

**Configuração:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view()),
]
```

**Uso no cliente:**
```javascript
// 1. Fazer login
fetch('/api/token/', {
    method: 'POST',
    body: JSON.stringify({
        username: 'user@email.com',
        password: 'senha123'
    })
})
.then(r => r.json())
.then(data => {
    // Salvar token
    localStorage.setItem('token', data.access);
});

// 2. Usar token em requisições
fetch('/api/produtos/', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
});
```

**Documentação:**
- GitHub: https://github.com/jazzband/djangorestframework-simplejwt

---

## 📚 BIBLIOTECAS PYTHON

### Pillow 11.0.0

**O que é:**
Biblioteca para manipular imagens.

**Funcionalidades:**
- ✅ Abrir/salvar imagens
- ✅ Redimensionar
- ✅ Rotacionar
- ✅ Aplicar filtros
- ✅ Converter formatos

**Exemplos:**
```python
from PIL import Image

# Abrir imagem
img = Image.open('foto.jpg')

# Ver informações
print(img.size)     # (1920, 1080)
print(img.format)   # JPEG
print(img.mode)     # RGB

# Redimensionar
img_pequena = img.resize((800, 600))

# Thumbnail (mantém proporção)
img.thumbnail((300, 300))

# Rotacionar
img_rotacionada = img.rotate(90)

# Converter formato
img.save('foto.png', 'PNG')

# Aplicar filtro
from PIL import ImageFilter
img_blur = img.filter(ImageFilter.BLUR)

# Recortar
caixa = (100, 100, 400, 400)  # (left, top, right, bottom)
img_cortada = img.crop(caixa)

# Colar imagem em outra
img1.paste(img2, (0, 0))
```

**Uso no Django:**
```python
# models.py
class Produto(models.Model):
    foto = models.ImageField(upload_to='produtos/')
    # Pillow é NECESSÁRIO para ImageField funcionar!

# views.py
def processar_imagem(request):
    if request.FILES.get('foto'):
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import InMemoryUploadedFile
        
        # Abrir imagem do upload
        img = Image.open(request.FILES['foto'])
        
        # Redimensionar
        img.thumbnail((800, 800))
        
        # Salvar em memória
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        # Criar arquivo Django
        foto_final = InMemoryUploadedFile(
            buffer, None, 'foto.jpg', 'image/jpeg',
            buffer.getbuffer().nbytes, None
        )
        
        # Salvar no modelo
        produto = Produto(foto=foto_final)
        produto.save()
```

**Documentação:**
- Site oficial: https://python-pillow.org/
- Tutorial: https://pillow.readthedocs.io/en/stable/handbook/tutorial.html

---

### openpyxl 3.1.5

**O que é:**
Ler e escrever arquivos Excel (.xlsx).

**Exemplos:**

#### Ler Excel:
```python
from openpyxl import load_workbook

# Abrir arquivo
wb = load_workbook('dados.xlsx')

# Pegar planilha
sheet = wb.active  # Primeira planilha
# ou
sheet = wb['NomePlanilha']  # Por nome

# Ler célula específica
valor = sheet['A1'].value  # Célula A1
valor = sheet.cell(row=1, column=1).value  # Mesmo resultado

# Iterar linhas
for row in sheet.iter_rows(min_row=2, values_only=True):
    codigo, descricao, preco = row
    print(f"{codigo} - {descricao}: R$ {preco}")

# Ler intervalo
for row in sheet['A1':'C10']:
    for cell in row:
        print(cell.value)
```

#### Escrever Excel:
```python
from openpyxl import Workbook

# Criar workbook
wb = Workbook()
sheet = wb.active

# Escrever célula
sheet['A1'] = 'Nome'
sheet['B1'] = 'Preço'

# Escrever linha
sheet.append(['Coca-Cola', 3.50])
sheet.append(['Pepsi', 3.20])

# Salvar
wb.save('produtos.xlsx')
```

#### Formatação:
```python
from openpyxl.styles import Font, Alignment, PatternFill

# Negrito
sheet['A1'].font = Font(bold=True)

# Cor de fundo
sheet['A1'].fill = PatternFill(start_color="FFFF00", fill_type="solid")

# Alinhamento
sheet['A1'].alignment = Alignment(horizontal='center')

# Tamanho da coluna
sheet.column_dimensions['A'].width = 30
```

**Uso no LOGOS (importar produtos):**
```python
# management/commands/importar_produtos.py
from openpyxl import load_workbook
from verifik.models import ProdutoMae, CodigoBarrasProdutoMae

def handle(self, *args, **options):
    wb = load_workbook(options['caminho_arquivo'])
    sheet = wb.active
    
    for row in sheet.iter_rows(min_row=2, values_only=True):
        codigo, descricao, categoria, preco = row
        
        # Criar produto
        produto = ProdutoMae.objects.create(
            descricao_produto=descricao,
            tipo=categoria,
            preco=preco
        )
        
        # Criar código de barras
        CodigoBarrasProdutoMae.objects.create(
            produto_mae=produto,
            codigo=codigo,
            principal=True
        )
```

**Documentação:**
- Site oficial: https://openpyxl.readthedocs.io/

---

### Selenium 4.27.1

**O que é:**
Automação de navegador (web scraping).

**Conceitos:**

#### WebDriver
Controla o navegador programaticamente

```python
from selenium import webdriver

# Criar driver (Chrome)
driver = webdriver.Chrome()

# Acessar página
driver.get('https://www.google.com')

# Encontrar elemento
search_box = driver.find_element(By.NAME, 'q')

# Digitar
search_box.send_keys('Python Django')

# Enviar formulário
search_box.submit()

# Esperar
driver.implicitly_wait(5)  # Espera até 5s

# Fechar
driver.quit()
```

#### Seletores:
```python
from selenium.webdriver.common.by import By

# Por ID
elemento = driver.find_element(By.ID, 'meu-id')

# Por classe CSS
elementos = driver.find_elements(By.CLASS_NAME, 'produto')

# Por nome
elemento = driver.find_element(By.NAME, 'username')

# Por tag
elementos = driver.find_elements(By.TAG_NAME, 'a')

# Por CSS Selector
elemento = driver.find_element(By.CSS_SELECTOR, 'div.preco > span')

# Por XPath
elemento = driver.find_element(By.XPATH, '//div[@class="preco"]')
```

#### Interações:
```python
# Clicar
botao = driver.find_element(By.ID, 'submit-btn')
botao.click()

# Digitar
campo = driver.find_element(By.NAME, 'email')
campo.send_keys('user@email.com')

# Limpar campo
campo.clear()

# Pegar texto
texto = elemento.text

# Pegar atributo
href = link.get_attribute('href')

# Screenshot
driver.save_screenshot('tela.png')
```

#### Esperas:
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Esperar elemento aparecer
wait = WebDriverWait(driver, 10)  # Espera até 10s
elemento = wait.until(
    EC.presence_of_element_located((By.ID, 'resultado'))
)

# Esperar elemento clicável
botao = wait.until(
    EC.element_to_be_clickable((By.ID, 'submit'))
)
```

**Uso no LOGOS (Vibra Scraper):**
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configurar headless (sem janela)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')

# Criar driver
driver = webdriver.Chrome(options=chrome_options)

# Acessar site Vibra
driver.get('https://vibraenergia.com.br/postos')

# Esperar carregar
driver.implicitly_wait(10)

# Selecionar posto
select_posto = driver.find_element(By.ID, 'posto-select')
select_posto.click()
opcao = driver.find_element(By.XPATH, '//option[text()="Posto Centro"]')
opcao.click()

# Extrair preços
preco_gasolina = driver.find_element(By.CLASS_NAME, 'preco-gasolina').text
preco_etanol = driver.find_element(By.CLASS_NAME, 'preco-etanol').text

# Fechar
driver.quit()
```

**Documentação:**
- Site oficial: https://www.selenium.dev/
- Python: https://selenium-python.readthedocs.io/

---

## 🎨 FRONTEND

### Bootstrap 5.3.2

**O que é:**
Framework CSS com componentes prontos.

**Vantagens:**
- ✅ Design responsivo automático
- ✅ Componentes bonitos (buttons, cards, modals)
- ✅ Grid system (organizar layout)

**Grid System:**
```html
<div class="container">
    <div class="row">
        <div class="col-md-6">Coluna 1 (50%)</div>
        <div class="col-md-6">Coluna 2 (50%)</div>
    </div>
</div>

<!-- Breakpoints:
- col-12: 100% em mobile
- col-md-6: 50% em tablets e acima
- col-lg-4: 33% em desktops e acima
-->
```

**Componentes:**
```html
<!-- Botões -->
<button class="btn btn-primary">Primário</button>
<button class="btn btn-success">Sucesso</button>
<button class="btn btn-danger">Perigo</button>

<!-- Cards -->
<div class="card">
    <div class="card-header">Título</div>
    <div class="card-body">
        <h5 class="card-title">Subtítulo</h5>
        <p class="card-text">Texto do card</p>
        <a href="#" class="btn btn-primary">Ação</a>
    </div>
</div>

<!-- Alerts -->
<div class="alert alert-success">Operação bem-sucedida!</div>
<div class="alert alert-danger">Erro ao processar</div>

<!-- Modal -->
<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#meuModal">
    Abrir Modal
</button>

<div class="modal fade" id="meuModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Título</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Conteúdo do modal
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                <button class="btn btn-primary">Salvar</button>
            </div>
        </div>
    </div>
</div>
```

**Utilitários:**
```html
<!-- Margens e Padding -->
<div class="m-3">Margin 3</div>
<div class="p-4">Padding 4</div>
<div class="mt-5">Margin Top 5</div>

<!-- Texto -->
<p class="text-center">Centralizado</p>
<p class="text-primary">Azul</p>
<p class="fw-bold">Negrito</p>

<!-- Background -->
<div class="bg-primary text-white">Fundo azul</div>
<div class="bg-success">Fundo verde</div>

<!-- Display -->
<div class="d-none d-md-block">Visível apenas em desktop</div>
<div class="d-flex justify-content-between">Flexbox</div>
```

**Documentação:**
- Site oficial: https://getbootstrap.com/
- Exemplos: https://getbootstrap.com/docs/5.3/examples/

---

## 🗄️ BANCO DE DADOS

### SQLite (Desenvolvimento)

**O que é:**
Banco de dados em arquivo único.

**Vantagens:**
- ✅ Não precisa instalar nada
- ✅ Arquivo único (db.sqlite3)
- ✅ Perfeito para desenvolvimento

**Desvantagens:**
- ❌ Não suporta múltiplos acessos simultâneos
- ❌ Limitado em tamanho
- ❌ Não recomendado para produção

**Comandos SQL básicos:**
```sql
-- Ver tabelas
.tables

-- Ver estrutura
.schema verifik_produtomae

-- Query
SELECT * FROM verifik_produtomae WHERE ativo = 1;
```

---

### PostgreSQL (Produção)

**O que é:**
Banco de dados profissional open-source.

**Vantagens:**
- ✅ Robusto e confiável
- ✅ Suporta milhões de registros
- ✅ Múltiplos acessos simultâneos
- ✅ Recursos avançados (JSON, Full-text search)

**Tipos de dados:**
```sql
-- Texto
VARCHAR(100)   -- Texto limitado
TEXT           -- Texto ilimitado

-- Números
INTEGER        -- Inteiro
DECIMAL(10,2)  -- Decimal (10 dígitos, 2 casas)

-- Data/Hora
DATE           -- Data (2025-11-21)
TIMESTAMP      -- Data + Hora completa

-- Outros
BOOLEAN        -- True/False
JSON           -- Dados JSON
```

**Comandos básicos:**
```sql
-- Listar tabelas
\dt

-- Ver estrutura
\d+ verifik_produtomae

-- Queries
SELECT * FROM verifik_produtomae;
SELECT COUNT(*) FROM verifik_deteccaoproduto;
```

**Documentação:**
- Site oficial: https://www.postgresql.org/
- Tutorial: https://www.postgresqltutorial.com/

---

## 🚀 DEPLOY E PRODUÇÃO

### Gunicorn 23.0.0

**O que é:**
Servidor WSGI para rodar Django em produção.

**Por que usar:**
- ❌ `python manage.py runserver` = APENAS desenvolvimento
- ✅ Gunicorn = Produção, múltiplos workers, robusto

**Comandos:**
```bash
# Básico
gunicorn logos.wsgi:application

# Com bind (porta)
gunicorn logos.wsgi:application --bind 0.0.0.0:8000

# Múltiplos workers
gunicorn logos.wsgi:application --workers 3

# Logs
gunicorn logos.wsgi:application --access-logfile - --error-logfile -
```

**Railway (Procfile):**
```
web: gunicorn logos.wsgi:application --bind 0.0.0.0:$PORT
```

**Documentação:**
- Site oficial: https://gunicorn.org/
- Docs: https://docs.gunicorn.org/en/stable/

---

### WhiteNoise 6.8.2

**O que é:**
Serve arquivos estáticos (CSS, JS, imagens) em produção.

**Por que usar:**
- Django não serve arquivos estáticos em produção (DEBUG=False)
- WhiteNoise resolve isso de forma eficiente

**Configuração:**
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Logo após Security
    # ...
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Como funciona:**
```
1. python manage.py collectstatic
   → Copia todos arquivos estáticos para staticfiles/

2. WhiteNoise serve arquivos de staticfiles/
   → Com compressão Gzip
   → Com cache headers
```

**Documentação:**
- Site oficial: http://whitenoise.evans.io/

---

### Railway.app

**O que é:**
Plataforma de deploy (PaaS - Platform as a Service).

**Analogia:**
- VPS tradicional = Comprar terreno e construir casa
- Railway = Alugar apartamento mobiliado

**O que Railway faz:**
- ✅ Hosting (servidor)
- ✅ PostgreSQL (banco de dados)
- ✅ SSL automático (HTTPS)
- ✅ Deploy automático do GitHub
- ✅ Domínio gratuito (.up.railway.app)

**Workflow:**
```
1. Push código para GitHub
   ↓
2. Railway detecta mudanças
   ↓
3. Build automático
   ↓
4. Deploy automático
   ↓
5. Site atualizado!
```

**Variáveis de ambiente:**
```
SECRET_KEY=chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app,grupolisboa.com.br
DATABASE_URL=postgresql://... (Railway cria automaticamente)
```

**Documentação:**
- Site oficial: https://railway.app/
- Docs: https://docs.railway.app/

---

## 🛠️ DESENVOLVIMENTO

### VS Code

**Extensões recomendadas:**
- Python (Microsoft)
- Django (Baptiste Darthenay)
- Pylance (Microsoft)
- SQLite Viewer
- GitLens

**Atalhos úteis:**
- `Ctrl+P`: Abrir arquivo
- `Ctrl+Shift+P`: Comandos
- `Ctrl+B`: Toggle sidebar
- `Ctrl+``: Terminal
- `F12`: Ir para definição

---

### Git

**Comandos básicos:**
```bash
# Status
git status

# Adicionar arquivos
git add .

# Commit
git commit -m "Mensagem"

# Push
git push origin main

# Pull
git pull origin main

# Branches
git checkout -b nova-feature
git checkout main
```

---

## 📞 SUPORTE E APRENDIZADO

### Recursos online:

**Português:**
- Python Brasil: https://python.org.br/
- Django Girls Tutorial: https://tutorial.djangogirls.org/pt/

**Inglês:**
- MDN Web Docs: https://developer.mozilla.org/
- Stack Overflow: https://stackoverflow.com/
- Real Python: https://realpython.com/

**YouTube:**
- Curso de Django (Português)
- Traversy Media (Inglês)
- Corey Schafer (Inglês)

---

**Última atualização:** 21/11/2025
