# 🚀 CHECKLIST - Colocar grupolisboa.com.br no ar

## ✅ Passo 1: Descobrir sua infraestrutura UOL

### Acesse o painel UOL
📍 https://painel.uol.com.br

Procure por **"Meus Produtos"** ou **"Meus Serviços"**

### O que você vai ver?

**Cenário A - Só tem o domínio (mais comum)**
```
✓ Registro de Domínio: grupolisboa.com.br
✗ Hospedagem: Nenhuma
```
➡️ **Solução:** Railway ou Render (Opção Cloud)

**Cenário B - Hospedagem compartilhada (cPanel)**
```
✓ Hospedagem de Sites UOL Host
✓ Painel cPanel
✗ SSH não disponível
```
➡️ **Solução:** Railway ou Render (cPanel não suporta Django)

**Cenário C - Tem VPS/Cloud**
```
✓ Cloud Server UOL ou Servidor Dedicado
✓ IP do servidor: xxx.xxx.xxx.xxx
✓ Acesso SSH disponível
```
➡️ **Solução:** Deploy no próprio servidor (mais barato a longo prazo)

---

## ✅ Passo 2: Testar se tem acesso SSH

### No PowerShell (Windows):
```powershell
ssh root@IP-DO-SERVIDOR
```

Ou procure no painel UOL por:
- "Dados de Acesso"
- "Terminal"  
- "SSH"

### Se funcionar = você tem VPS! 🎉
### Se NÃO funcionar = precisa usar Railway/Render

---

## ✅ Passo 3: Escolher caminho e CUSTO

### Opção 1: Railway/Render (RECOMENDADO se não tem VPS)

**PRÓS:**
- ✅ Deploy em 30 minutos
- ✅ SSL/HTTPS automático
- ✅ Zero configuração de servidor
- ✅ Escalável automaticamente
- ✅ Backup automático do banco

**CONTRAS:**
- ❌ Custo mensal: $5-10/mês

**CUSTO DETALHADO:**
- Railway: $5/mês (PostgreSQL) + $5/mês (app se passar 500h)
- Render: GRÁTIS (limitado) ou $7/mês (sem limites)

### Opção 2: VPS UOL que você já tem (SE tiver)

**PRÓS:**
- ✅ Custo zero adicional (já paga o VPS)
- ✅ Controle total
- ✅ Pode hospedar outros sites

**CONTRAS:**
- ❌ Configuração manual (2-4 horas)
- ❌ Você gerencia atualizações
- ❌ Precisa conhecimento Linux

**CUSTO:**
- R$0 (se já tem VPS)
- VPS novo UOL: ~R$30-80/mês

---

## ✅ Passo 4: Verificar DNS da UOL

### No painel UOL:
1. "Domínios" → grupolisboa.com.br
2. "Gerenciar DNS" ou "Configurações"

### Você vai ver algo como:

```
Tipo: A
Nome: @
Destino: xxx.xxx.xxx.xxx (IP atual)

Tipo: CNAME  
Nome: www
Destino: grupolisboa.com.br
```

**IMPORTANTE:** Você consegue editar esses registros? Se SIM = perfeito!

---

## 🎯 DECISÃO RÁPIDA - Responda SIM ou NÃO:

1. **Você quer gastar R$25-50/mês?** 
   - SIM = Railway/Render
   - NÃO = Precisa de VPS próprio

2. **Você tem urgência (precisa no ar hoje/amanhã)?**
   - SIM = Railway/Render  
   - NÃO = Pode configurar VPS

3. **Você sabe usar Linux/SSH?**
   - SIM = VPS próprio (mais barato)
   - NÃO = Railway/Render (mais fácil)

---

## 📋 PRÓXIMOS PASSOS - Escolha SEU caminho:

### Caminho A: Railway (Mais rápido e fácil)
Leia: `DEPLOY_RAILWAY.md`

**Resumo ultra-rápido:**
1. Criar conta Railway (login com GitHub)
2. Deploy do projeto (1 clique)
3. Adicionar PostgreSQL (1 clique)
4. Configurar variáveis de ambiente (5 minutos)
5. Atualizar DNS da UOL (10 minutos)
6. Aguardar propagação (1-24 horas)
7. ✅ SITE NO AR!

### Caminho B: VPS próprio
Leia: `DEPLOY.md` → Seção "VPS/Servidor Linux"

**Resumo:**
1. Conectar SSH no servidor
2. Instalar Python, PostgreSQL, Nginx (30 min)
3. Clonar projeto e configurar (30 min)
4. Configurar Gunicorn e Nginx (30 min)
5. Configurar SSL com Certbot (10 min)
6. Atualizar DNS da UOL (10 min)
7. ✅ SITE NO AR!

---

## 🆘 AJUDA - O que fazer AGORA?

### Opção 1: Quer fazer VOCÊ MESMO?
1. Escolha: Railway ou VPS?
2. Siga o guia correspondente passo a passo
3. Se travar, me chame com print do erro!

### Opção 2: Quer que EU te GUIE passo a passo?
Me responda essas 3 perguntas:

1. **Acesse painel.uol.com.br e me diga:**
   - Você vê "Cloud Server" ou "Servidor Dedicado"?
   - Você vê "Hospedagem de Sites" ou só o domínio?

2. **Orçamento:**
   - Pode gastar R$25-50/mês? (SIM/NÃO)

3. **Conhecimento:**
   - Você sabe usar terminal Linux? (SIM/NÃO/MAIS OU MENOS)

Com essas respostas, eu monto o plano perfeito pra você! 🎯
