# Sistema de Processamento de Imagens - App `acessorios`

## Estrutura Criada

### 1. App Django: `acessorios`

```
acessorios/
├── models.py          # ProcessadorImagens - Registro de processamentos
├── admin.py           # Painel administrativo
├── apps.py            # Configuração da app
├── filtrador.py       # FiltrorImagens - Múltiplos filtros
├── processador.py     # ProcessadorImagensGenerico - Processamentos
└── migrations/
    └── 0001_initial.py
```

### 2. Componentes Principais

#### A. `ProcessadorImagensGenerico` (processador.py)
Classe para processar imagens com múltiplas operações:

- **`remover_fundo()`** - Remove fundo usando rembg
- **`redimensionar()`** - Redimensiona mantendo qualidade
- **`normalizar_cores()`** - Normaliza histograma de cores
- **`aumentar_contraste()`** - Aumenta contraste da imagem
- **`processar_lote()`** - Processa múltiplas imagens

**Uso:**
```python
from acessorios.processador import ProcessadorImagensGenerico

processador = ProcessadorImagensGenerico()
caminho_saida = processador.remover_fundo('media/imagem.jpg')
```

#### B. `FiltrorImagens` (filtrador.py)
Classe para filtrar imagens por múltiplos critérios:

- **`por_categoria()`** - Filtra por categoria
- **`por_produto()`** - Filtra por um produto
- **`por_multiplos_produtos()`** - Filtra por vários produtos
- **`por_marca()`** - Filtra por marca
- **`por_status()`** - Filtra por status (ativa/inativa)
- **`nao_anotadas()`** - Filtra imagens não anotadas
- **`obter_caminhos()`** - Retorna caminhos dos arquivos

**Uso:**
```python
from acessorios.filtrador import FiltrorImagens
from verifik.models import ImagemProduto

filtrador = FiltrorImagens(ImagemProduto)
imagens = filtrador.por_categoria(5)
imagens = imagens.filter(ativa=True)
```

#### C. `ProcessadorImagens` (models.py)
Modelo para registrar histórico de processamentos:

- `tipo` - Tipo de processamento (remover_fundo, redimensionar, etc)
- `imagem_original` - Caminho da imagem original
- `imagem_processada` - Caminho da imagem processada
- `status` - sucesso/erro/processando
- `mensagem_erro` - Detalhes do erro
- `parametros` - JSON com parâmetros usados
- `data_criacao` - Data/hora do processamento

### 3. Script de Linha de Comando: `processador_em_lote.py`

Menu interativo com as seguintes opções:

#### Modo Interativo:
```bash
python processador_em_lote.py
```

Mostra menu com:
1. Processar por CATEGORIA
2. Processar por MARCA
3. Processar um PRODUTO
4. Processar MÚLTIPLOS PRODUTOS
5. Processar TODAS as imagens NÃO anotadas
6. Listar Categorias
7. Listar Marcas
8. Listar Produtos
9. Sair

#### Modo Linha de Comando:
```bash
# Processar todas as não anotadas
python processador_em_lote.py todas

# Processar por categoria (ID 1)
python processador_em_lote.py categoria 1

# Processar por marca (ID 2)
python processador_em_lote.py marca 2

# Processar um produto (ID 10)
python processador_em_lote.py produto 10
```

### 4. Painel Administrativo

Acesso em: `http://localhost:8000/admin/acessorios/`

Mostra:
- Lista de todos os processamentos realizados
- Filtros por tipo e status
- Busca por caminho de imagem
- Detalhes de cada processamento

## Como Usar

### Exemplo 1: Remover fundo de TODAS as imagens não anotadas

```bash
python processador_em_lote.py todas
```

### Exemplo 2: Remover fundo de um produto específico

```python
# Via Python
from processador_em_lote import ProcessadorEmLote

proc = ProcessadorEmLote()
proc.processar_produto(51)  # Produto ID 51
```

### Exemplo 3: Processar múltiplos produtos

```python
from processador_em_lote import ProcessadorEmLote

proc = ProcessadorEmLote()
proc.processar_multiplos_produtos([51, 49, 50, 52])
```

### Exemplo 4: Usar filtrador customizado

```python
from acessorios.filtrador import FiltrorImagens
from verifik.models import ImagemProduto, Categoria
from verifik.models_anotacao import ImagemAnotada

# Filtrar por categoria 2, apenas não anotadas
categoria = Categoria.objects.get(id=2)
imagens = ImagemProduto.objects.filter(produto__categoria=categoria)

filtrador = FiltrorImagens()
imagens_nao_anotadas = filtrador.nao_anotadas(ImagemAnotada)

caminhos = filtrador.obter_caminhos(imagens_nao_anotadas)
```

## Requisitos

```
django>=5.2.0
Pillow>=11.0.0
rembg>=0.0.0
numpy>=1.24.0
```

Instalar rembg:
```bash
pip install rembg
```

## Saída dos Processamentos

As imagens processadas são salvas em:
```
media/produtos/processadas/
```

Com nomes como:
```
cat_2_imagem_no_bg.png       # Categoria 2
marca_1_imagem_resized.jpg   # Marca 1
prod_51_imagem_contrast.jpg  # Produto 51
todas_imagem_normalized.jpg  # Todas não anotadas
```

## Logs

Todos os processamentos são registrados em:
- `acessorios.models.ProcessadorImagens` - Banco de dados
- Acessível via admin Django
- Histórico completo com datas e erros

---

## Próximas Funcionalidades

- [ ] Web interface para processamento (Django templates)
- [ ] Fila de tarefas (Celery) para processamentos grandes
- [ ] Processamento em paralelo
- [ ] Preview das imagens antes/depois
- [ ] Exportar processamentos como relatório
- [ ] Webhooks para integração com outros sistemas
