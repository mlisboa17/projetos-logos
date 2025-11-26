# 🗄️ Compartilhar Banco de Dados via OneDrive

## 📤 COMO COMPARTILHAR O BANCO (VOCÊ)

### Opção 1: Link Direto do OneDrive (Recomendado)

1️⃣ **Localize o arquivo db.sqlite3:**
```
c:\Users\gabri\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos\db.sqlite3
```

2️⃣ **Abra o OneDrive:**
- Vá para a pasta no navegador ou Windows Explorer
- Caminho: `OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos`

3️⃣ **Compartilhe o arquivo:**
- Clique com botão direito em `db.sqlite3`
- Selecione "Compartilhar" ou "Share"
- Escolha "Qualquer pessoa com o link pode editar" ou "Somente visualizar" (recomendado)
- Copie o link gerado

4️⃣ **Adicione o link ao README:**
```markdown
## 📥 Download do Banco de Dados

Baixe o banco de dados atualizado:
[Clique aqui para baixar db.sqlite3](SEU_LINK_DO_ONEDRIVE_AQUI)

Coloque na raiz do projeto: `projetos-logos/db.sqlite3`
```

### Opção 2: Via GitHub Release (Para backups específicos)

```bash
# 1. Criar uma release no GitHub
# 2. Fazer upload do db.sqlite3 como "Asset"
# 3. Compartilhar o link da release
```

## 📥 COMO BAIXAR O BANCO (OUTRAS PESSOAS)

### Método 1: Download Direto

1️⃣ **Acesse o link do OneDrive**

2️⃣ **Clique em "Download"**

3️⃣ **Mova para a pasta do projeto:**
```powershell
# Windows
Move-Item C:\Users\SEU_USUARIO\Downloads\db.sqlite3 C:\caminho\projetos-logos\db.sqlite3

# Ou manualmente:
# 1. Copie db.sqlite3 de Downloads
# 2. Cole em projetos-logos\
```

### Método 2: Script Automático (recomendado)

Crie um arquivo `baixar_banco.bat`:
```batch
@echo off
echo Baixando banco de dados do OneDrive...
echo.
echo Por favor:
echo 1. Abra o link do OneDrive no navegador
echo 2. Clique em Download
echo 3. Aguarde o download terminar
echo.
echo Link: [COLOCAR_LINK_AQUI]
echo.
start "" "[COLOCAR_LINK_AQUI]"
echo.
echo Pressione qualquer tecla APÓS o download terminar...
pause >nul

echo.
echo Procurando arquivo baixado...

if exist "%USERPROFILE%\Downloads\db.sqlite3" (
    echo Arquivo encontrado! Copiando...
    copy "%USERPROFILE%\Downloads\db.sqlite3" "db.sqlite3"
    echo.
    echo ✓ Banco de dados instalado com sucesso!
    del "%USERPROFILE%\Downloads\db.sqlite3"
) else (
    echo.
    echo ✗ Arquivo não encontrado em Downloads
    echo Por favor, mova manualmente db.sqlite3 para esta pasta
)

pause
```

## 🔄 SINCRONIZAÇÃO AUTOMÁTICA

### Para manter o banco atualizado via OneDrive:

#### Opção A: Link Simbólico (Windows)

```powershell
# No projeto, crie um link para o OneDrive
cd projetos-logos
del db.sqlite3  # Remove o arquivo local

# Cria link simbólico (requer admin)
New-Item -ItemType SymbolicLink -Path "db.sqlite3" -Target "C:\Users\gabri\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos\db.sqlite3"
```

Vantagem: Qualquer alteração sincroniza automaticamente!

#### Opção B: Script de Sincronização

Crie `sincronizar_banco.bat`:
```batch
@echo off
echo Sincronizando banco de dados com OneDrive...

set ORIGEM=C:\Users\%USERNAME%\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos\db.sqlite3
set DESTINO=db.sqlite3

if exist "%ORIGEM%" (
    copy /Y "%ORIGEM%" "%DESTINO%"
    echo ✓ Banco sincronizado!
) else (
    echo ✗ Arquivo não encontrado no OneDrive
)

pause
```

## 📋 INSTRUÇÕES NO README DO GITHUB

Adicione ao README.md:

```markdown
## 🗄️ Configuração do Banco de Dados

Este projeto usa SQLite. O banco de dados NÃO está incluído no repositório.

### Opção 1: Download via OneDrive (Recomendado)
1. [Clique aqui para baixar db.sqlite3](LINK_DO_ONEDRIVE)
2. Coloque o arquivo na raiz do projeto: `projetos-logos/db.sqlite3`

### Opção 2: Criar banco vazio
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Opção 3: Sincronização automática (OneDrive)
Se você tem acesso ao OneDrive, use link simbólico:
```powershell
# Windows (PowerShell como Admin)
cd projetos-logos
New-Item -ItemType SymbolicLink -Path "db.sqlite3" -Target "C:\Users\USUARIO\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos\db.sqlite3"
```
```

## 🔐 SEGURANÇA E BOAS PRÁTICAS

### ✅ Recomendações:

1. **Link de visualização apenas:** Evite "edição" para evitar corrupção
2. **Backup regular:** Mantenha cópias em outro local
3. **Versionamento:** Renomeie antes de atualizar:
   ```
   db.sqlite3 → db_backup_20251126.sqlite3
   ```

### ⚠️ Cuidados:

- **NÃO compartilhe publicamente** se tiver dados sensíveis
- Use link privado ou com senha se possível
- Considere usar `.env` para guardar o link

### 🔄 Atualização periódica:

Crie versões datadas:
```
db_20251126.sqlite3  (26/11/2025)
db_20251201.sqlite3  (01/12/2025)
```

## 🌐 LINK DO BANCO ATUAL

**Última atualização:** 26/11/2025

**Link OneDrive:** [ADICIONAR_LINK_AQUI]

**Tamanho:** ~[TAMANHO] MB

**Inclui:**
- ✓ Produtos cadastrados
- ✓ Usuários
- ✓ Histórico de imagens
- ✓ Anotações

---

## 📝 TEMPLATE DE COMPARTILHAMENTO

Copie e cole ao compartilhar:

```
🗄️ Banco de Dados - VerifiK

Para usar o sistema, você precisa do banco de dados.

📥 Download:
[LINK DO ONEDRIVE]

📁 Onde colocar:
projetos-logos/db.sqlite3

❓ Problemas?
Leia: COMPARTILHAR_BANCO_ONEDRIVE.md
```

## 🔧 TROUBLESHOOTING

### Erro: "database is locked"
```bash
# Feche todos os programas que usam o banco
# Ou copie para arquivo temporário:
copy db.sqlite3 db_temp.sqlite3
# Use db_temp.sqlite3
```

### Arquivo muito grande
```bash
# Limpe dados antigos ou use:
python manage.py dbshell
VACUUM;
```

### OneDrive não sincroniza
- Verifique espaço em disco
- Pause e retome a sincronização
- Verifique se OneDrive está atualizado
