# 📋 INSTRUÇÕES - Sistema de Coleta de Imagens v2

## 🎯 Como Funciona

O sistema agora sincroniza os produtos automaticamente via rede local.

### ✅ Vantagens da Nova Versão:
- ✔️ Produtos sempre atualizados automaticamente
- ✔️ Usuários NÃO podem adicionar produtos (apenas você)
- ✔️ Sincronização pela rede local (rápido e confiável)
- ✔️ Não depende de OneDrive ou internet

---

## 🖥️ COMPUTADOR CENTRAL (Seu)

### 1️⃣ Iniciar Servidor HTTP

**Sempre que quiser que os funcionários usem o sistema:**

```cmd
python servidor_banco_http.py
```

**Você verá:**
```
======================================================================
🌐 SERVIDOR HTTP - BANCO DE DADOS SQLITE
======================================================================

📁 Arquivo: db.sqlite3
📊 Tamanho: 1.07 MB
🔌 Porta: 8080

📡 URLs para download:
   Local:  http://localhost:8080/banco
   Rede:   http://192.168.68.102:8080/banco

✅ Servidor iniciado com sucesso!
🔄 Aguardando requisições...
```

### 2️⃣ Deixar Rodando

- ⚠️ **NÃO FECHE** esta janela enquanto os funcionários estiverem trabalhando
- Para parar: Pressione `Ctrl+C`
- Você pode minimizar a janela

### 3️⃣ Atualizar Produtos

Quando adicionar novos produtos no Django Admin:

1. O arquivo `db.sqlite3` já tem os novos produtos
2. Funcionários clicam em **"Atualizar Produtos"** no sistema deles
3. Download automático dos produtos atualizados

---

## 💻 COMPUTADORES DOS FUNCIONÁRIOS

### 1️⃣ Distribuir Executável

Copie o arquivo para cada computador:
```
dist\VerifiK_ColetaImagens_v2.exe
```

### 2️⃣ Executar Sistema

1. Clique duas vezes em `VerifiK_ColetaImagens_v2.exe`
2. Aguarde sincronização automática dos produtos
3. Pronto para usar!

### 3️⃣ Atualizar Produtos

Quando você adicionar novos produtos:

1. Clique no botão **"Atualizar Produtos"**
2. Aguarde mensagem de sucesso
3. Novos produtos aparecem na lista

---

## 🔥 FIREWALL (Muito Importante!)

Se os funcionários não conseguirem sincronizar:

### Windows Defender Firewall

1. Pesquisar: **"Firewall do Windows"**
2. Clicar em **"Configurações avançadas"**
3. **Regras de Entrada** → **Nova Regra**
4. Tipo: **Porta**
5. Porta TCP: **8080**
6. Ação: **Permitir a conexão**
7. Nome: **"Servidor Banco VerifiK"**

### OU Execute (Como Administrador):

```powershell
New-NetFirewallRule -DisplayName "Servidor Banco VerifiK" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

---

## 🧪 TESTAR CONEXÃO

### No Computador Central:

```cmd
python testar_servidor_http.py
```

**Deve mostrar:**
```
✅ SUCESSO! Arquivo SQLite válido baixado!
```

### Nos Computadores dos Funcionários:

1. Abrir navegador
2. Acessar: `http://192.168.68.102:8080/banco`
3. Deve **baixar** o arquivo `banco` (1 MB)

Se **não baixar** → problema de firewall ou rede

---

## 🐛 SOLUCIONANDO PROBLEMAS

### Erro: "file is not a database"
**Causa:** Servidor HTTP não está rodando
**Solução:** Execute `python servidor_banco_http.py`

### Erro: "Erro ao sincronizar produtos"
**Causa:** Computador funcionário não consegue acessar servidor
**Soluções:**
1. Verificar se servidor está rodando
2. Testar acesso: `http://192.168.68.102:8080/banco` no navegador
3. Verificar firewall (ver seção acima)
4. Verificar se estão na mesma rede

### Erro: "Connection timeout"
**Causa:** Rede bloqueando conexão
**Soluções:**
1. Verificar firewall
2. Verificar antivírus (pode bloquear)
3. Verificar se estão na mesma rede Wi-Fi

### Produtos não aparecem
**Causa:** Banco desatualizado
**Solução:** Clicar em "Atualizar Produtos"

---

## 📊 WORKFLOW COMPLETO

### Início do Dia:
1. ✅ Você: Executar `python servidor_banco_http.py`
2. ✅ Funcionários: Executar `VerifiK_ColetaImagens_v2.exe`
3. ✅ Sistema sincroniza produtos automaticamente

### Durante o Dia:
1. ✅ Funcionários coletam imagens normalmente
2. ✅ Se você adicionar produtos: funcionários clicam "Atualizar Produtos"

### Fim do Dia:
1. ✅ Funcionários fecham sistema
2. ✅ Você: Pressiona `Ctrl+C` no servidor (ou deixa rodando)

---

## 🎓 NOTAS TÉCNICAS

### Arquitetura:
- **Servidor:** HTTP simples na porta 8080
- **Cliente:** Executável Tkinter com requests
- **Banco:** SQLite sincronizado via HTTP
- **IP Servidor:** 192.168.68.102 (seu computador)

### Arquivos Importantes:
- `servidor_banco_http.py` - Servidor HTTP
- `sistema_coleta_standalone_v2.py` - Código-fonte do executável
- `db.sqlite3` - Banco de dados central
- `dist\VerifiK_ColetaImagens_v2.exe` - Executável distribuível

### Segurança:
- ⚠️ Servidor aceita conexões apenas da rede local
- ⚠️ Não expor porta 8080 para internet
- ✅ Funcionários não podem alterar produtos
- ✅ Apenas visualização e anotação de imagens

---

## 📞 SUPORTE

### Logs do Servidor:
O servidor mostra cada download:
```
✅ Banco enviado para 192.168.68.103
```

### Testar Manualmente:
```cmd
# Testar servidor
python testar_servidor_http.py

# Testar link específico
curl http://192.168.68.102:8080/banco -o teste.db
```

---

**Versão:** 2.0  
**Data:** 26/11/2025  
**Autor:** Sistema VerifiK
