# ============================================================================
#   INSTRUÇÕES - Após Clonar do GitHub
# ============================================================================

## 📥 COMO USAR APÓS CLONAR O REPOSITÓRIO

### Para Windows:

1️⃣ Clone o repositório:
```bash
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos
```

2️⃣ Execute o script de setup:
```bash
criar_executavel.bat
```

3️⃣ Aguarde o processo (3-5 minutos)

4️⃣ Pronto! O executável estará em: `dist\VerifiK_ColetaImagens.exe`


### Para Linux/Mac:

1️⃣ Clone o repositório:
```bash
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos
```

2️⃣ Dê permissão de execução ao script:
```bash
chmod +x criar_executavel.sh
```

3️⃣ Execute o script:
```bash
./criar_executavel.sh
```

4️⃣ Pronto! O executável estará em: `dist/VerifiK_ColetaImagens`


### Passo a Passo Manual (caso os scripts não funcionem):

```bash
# 1. Instalar dependências
pip install pillow opencv-python pyinstaller

# 2. Criar executável
pyinstaller --name=VerifiK_ColetaImagens --onefile --windowed --clean sistema_coleta_standalone.py

# 3. Executável criado em: dist/
```


## 📦 O QUE FAZER COM O EXECUTÁVEL

### Distribuição:
- Copie o arquivo da pasta `dist/` para um pendrive
- Ou compartilhe via rede/email
- Envie para os funcionários

### Uso:
- Basta executar o arquivo (duplo clique)
- Não precisa instalação
- Funciona offline
- Dados salvos localmente

### Sincronização:
1. Funcionários exportam dados (botão no sistema)
2. Trazem a pasta exportada
3. No servidor, execute:
   ```bash
   python importar_dados_coletados.py <caminho_pasta_exportada>
   ```


## 🗄️ BANCO DE DADOS

### Onde está o banco de dados principal?

O banco de dados `db.sqlite3` **NÃO está no GitHub** (gitignore).
Está compartilhado via **OneDrive** para fácil acesso.

### Como obter o banco de dados?

**Opção 1: Download via OneDrive (RECOMENDADO)**
```bash
# Execute o script automático:
baixar_banco_onedrive.bat

# Ou baixe manualmente:
# 1. Abra o link do OneDrive (veja README.md)
# 2. Clique em "Download"
# 3. Mova db.sqlite3 para: projetos-logos/
```

**Opção 2: Criar novo banco (vazio)**
```bash
cd projetos-logos
python manage.py migrate
python manage.py createsuperuser
```

**Opção 3: Sincronização automática via OneDrive**
```powershell
# Crie link simbólico (PowerShell como Admin):
cd projetos-logos
New-Item -ItemType SymbolicLink -Path "db.sqlite3" -Target "C:\Users\SEU_USUARIO\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos\db.sqlite3"
```

📚 **Documentação completa:** Veja `COMPARTILHAR_BANCO_ONEDRIVE.md`


## 🔧 ESTRUTURA DE ARQUIVOS

```
projetos-logos/
├── sistema_coleta_standalone.py    ← Sistema principal
├── criar_executavel.bat           ← Setup Windows
├── criar_executavel.sh            ← Setup Linux/Mac
├── importar_dados_coletados.py    ← Sincronização
├── README_SISTEMA_COLETA.txt      ← Manual do usuário
├── GUIA_SISTEMA_COLETA_STANDALONE.txt ← Guia técnico
├── db.sqlite3                     ← Banco (NÃO no Git)
└── dist/                          ← Executável (após build)
    └── VerifiK_ColetaImagens.exe
```


## ⚠️ ARQUIVOS NO .gitignore

Estes arquivos NÃO estão no GitHub:
- `db.sqlite3` (banco de dados)
- `media/` (uploads de imagens)
- `dados_coleta/` (dados do sistema standalone)
- `dist/` (executável compilado)
- `build/` (arquivos temporários)
- `*.pyc` (cache Python)


## 🚀 FLUXO COMPLETO

### 1. No servidor principal (com Django):
```bash
# Clone o repositório
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos

# Copie ou crie o banco de dados
cp /caminho/backup/db.sqlite3 .

# Rode o servidor
python manage.py runserver
```

### 2. Na máquina de build (para criar .exe):
```bash
# Clone o repositório
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos

# Execute o setup
criar_executavel.bat

# Distribua o arquivo em: dist/VerifiK_ColetaImagens.exe
```

### 3. Nas máquinas dos funcionários:
```
# Copie e execute: VerifiK_ColetaImagens.exe
# Use normalmente
# Exporte ao final do dia
```

### 4. Sincronização:
```bash
# No servidor, importe os dados
python importar_dados_coletados.py C:\dados_exportados\exportacao_20251126_143052
```


## 📞 PROBLEMAS COMUNS

### "Python não encontrado"
**Solução:** Instale Python 3.8+ de https://www.python.org/downloads/
Marque "Add Python to PATH" durante instalação

### "ModuleNotFoundError: No module named 'PIL'"
**Solução:** Execute: `pip install pillow opencv-python pyinstaller`

### "db.sqlite3 não encontrado"
**Solução:** Copie o banco da máquina principal ou crie um novo com `python manage.py migrate`

### Executável muito grande
**Solução:** Normal! PyInstaller inclui todas as dependências. Tamanho esperado: 40-80 MB

### Antivírus bloqueia o executável
**Solução:** Adicione exceção no antivírus ou recrie o executável na própria máquina


## 🔐 SEGURANÇA

### Antes de commitar no Git:
```bash
# Verifique o que vai ser enviado
git status

# NUNCA commite:
# - db.sqlite3 (dados sensíveis)
# - arquivos em media/ (imagens privadas)
# - .env (credenciais)
```

### .gitignore já configurado para:
```
db.sqlite3
*.pyc
media/
dados_coleta/
dist/
build/
*.spec
```


## 📊 TAMANHOS ESPERADOS

- Repositório clonado: ~50 MB
- Executável compilado: 40-80 MB
- Banco de dados: Varia (1-500 MB dependendo dos dados)


## ✅ CHECKLIST

Antes de distribuir o executável:
- [ ] Testou em outra máquina Windows
- [ ] Verificou se funciona offline
- [ ] Testou adicionar produto
- [ ] Testou desenhar bounding box
- [ ] Testou exportar dados
- [ ] Testou importar dados no servidor
- [ ] Criou manual de instruções
- [ ] Treinou pelo menos 1 funcionário


Última atualização: 26/11/2025
