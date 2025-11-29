# ============================================================================
# COMO RESOLVER BLOQUEIO DO ANTIVÍRUS - VERIFIK COLETA
# ============================================================================

## 🛡️ PROBLEMA
O executável VerifiK_ColetaImagens_v2.exe está sendo bloqueado por antivírus
porque não possui assinatura digital e faz downloads da internet.

## ✅ SOLUÇÕES

### 1. ADICIONAR EXCEÇÃO NO WINDOWS DEFENDER (Mais Rápido)

**No seu computador:**
1. Abra "Segurança do Windows"
2. Clique em "Proteção contra vírus e ameaças"
3. Em "Configurações de proteção...", clique em "Gerenciar configurações"
4. Role até "Exclusões"
5. Clique em "Adicionar ou remover exclusões"
6. Clique em "Adicionar uma exclusão" → "Pasta"
7. Selecione: C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist\

**Nos computadores dos funcionários:**
- Repita o processo acima
- OU adicione o arquivo: VerifiK_ColetaImagens_v2.exe diretamente

### 2. ASSINAR DIGITALMENTE O EXECUTÁVEL (Profissional)

**Opção A: Certificado Pago (R$ 200-500/ano)**
- Comprar certificado code signing da:
  * Certum
  * GlobalSign
  * DigiCert
  * Sectigo

**Opção B: Auto-Assinatura (Gratuito, mas limitado)**
```powershell
# Criar certificado auto-assinado (apenas para testes internos)
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
    -Subject "CN=Grupo Lisboa" `
    -CertStoreLocation "Cert:\CurrentUser\My"

# Assinar executável
Set-AuthenticodeSignature `
    -FilePath "dist\VerifiK_ColetaImagens_v2.exe" `
    -Certificate $cert
```

**Limitação:** Auto-assinatura não é reconhecida por antivírus.
Só funciona se importar o certificado em cada PC.

### 3. USAR VERSÃO PYTHON (Sem Executável)

Em vez de distribuir .exe, distribua o código Python:

**Vantagens:**
- Antivírus não bloqueia scripts Python
- Mais leve
- Fácil de atualizar

**Desvantagens:**
- Requer Python instalado
- Menos "profissional"

**Como fazer:**
1. Instale Python nos PCs dos funcionários
2. Copie a pasta do projeto
3. Crie um .bat para executar:
```batch
@echo off
python sistema_coleta_standalone_v2.py
pause
```

### 4. WHITELIST CORPORATIVO

Se usar antivírus empresarial (Kaspersky, ESET, etc.):
- Contate o administrador de TI
- Solicite whitelist do executável via hash SHA256

Para obter o hash:
```powershell
Get-FileHash dist\VerifiK_ColetaImagens_v2.exe -Algorithm SHA256
```

### 5. ALTERNATIVA: WEBAPP EM VEZ DE EXECUTÁVEL

Em vez de executável desktop, criar interface web:
- Funciona no navegador
- Sem bloqueio de antivírus
- Acesso de qualquer dispositivo
- Centralizado no servidor

## 📋 RECOMENDAÇÃO PARA GRUPO LISBOA

**Curto Prazo (Agora):**
→ Adicionar exceção no Windows Defender

**Médio Prazo (1-2 meses):**
→ Comprar certificado code signing (R$ 300/ano)
→ Assinar todos os executáveis

**Longo Prazo (6 meses):**
→ Migrar para webapp centralizada
→ Eliminar necessidade de executáveis

## 🚀 AÇÃO IMEDIATA

Execute este comando para adicionar exceção:
```powershell
Add-MpPreference -ExclusionPath "C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist"
```

Ou manualmente:
1. Windows + I
2. Privacidade e Segurança
3. Segurança do Windows
4. Proteção contra vírus e ameaças
5. Gerenciar configurações
6. Exclusões → Adicionar
7. Pasta → Selecione "dist"

## ⚠️ IMPORTANTE

- Nunca desative completamente o antivírus
- Adicione apenas pastas específicas às exclusões
- Revise exclusões periodicamente
- Considere investir em certificado digital
