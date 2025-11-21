# 🚀 GUIA COMPLETO - Deploy do LOGOS no Railway
## Linguagem Simples - Passo a Passo

---

## 📋 O QUE VAMOS FAZER?

Colocar o site **grupolisboa.com.br** no ar usando o Railway.

**Tempo estimado:** 30-60 minutos
**Custo:** ~R$25-50/mês
**Dificuldade:** ⭐ Fácil

---

## PARTE 1: CRIAR CONTA NO RAILWAY

### Passo 1: Acessar o Railway
1. Abra o navegador
2. Acesse: **https://railway.app**
3. Você verá a página inicial do Railway

### Passo 2: Fazer Login com GitHub
1. Clique no botão **"Login"** (canto superior direito)
2. Escolha **"Login with GitHub"** (entrar com GitHub)
3. Se já estiver logado no GitHub, vai pedir autorização
4. Se NÃO estiver logado, vai pedir:
   - Seu email do GitHub (mlisboa17)
   - Sua senha do GitHub
5. Clique **"Authorize Railway"** (autorizar Railway)

### Passo 3: Confirmar acesso
1. Railway vai pedir permissão para acessar seus repositórios
2. Pode deixar marcado tudo (ele precisa ver o código)
3. Clique **"Authorize"** de novo
4. ✅ Pronto! Conta criada!

### O que aconteceu?
- Railway agora pode ver seus projetos no GitHub
- Ele vai usar isso para pegar o código do LOGOS
- É como dar uma "chave de entrada" para o Railway

---

## PARTE 2: CRIAR PROJETO E FAZER DEPLOY

### Passo 4: Criar novo projeto
1. Na tela inicial do Railway, clique **"+ New Project"** ou **"+ Novo Projeto"**
2. Você verá opções:
   - Deploy from GitHub repo (implantar do GitHub)
   - Deploy template (modelo pronto)
   - Empty project (projeto vazio)
3. Escolha: **"Deploy from GitHub repo"**

### Passo 5: Selecionar repositório
1. Vai aparecer lista dos seus repositórios do GitHub
2. Procure e clique: **projetos-logos** (ou mlisboa17/projetos-logos)
3. Clique **"Deploy Now"** (implantar agora)

### O que aconteceu?
- Railway copiou seu código do GitHub
- Ele detectou que é um projeto Django (Python)
- Está tentando instalar tudo automaticamente

### Passo 6: Aguardar primeiro build
⏳ **AGUARDE 3-5 MINUTOS**

Você verá:
- Um card/cartão com nome do projeto
- Status "Building..." (construindo) 🔄
- Barras de progresso

**O que o Railway está fazendo agora:**
- Instalando Python 3.11
- Instalando todas as bibliotecas (Django, PostgreSQL, etc)
- Preparando o ambiente

**Possíveis resultados:**
- ✅ Verde = Sucesso!
- ❌ Vermelho = Erro (normal, vamos corrigir)

---

## PARTE 3: ADICIONAR BANCO DE DADOS

### Passo 7: Adicionar PostgreSQL
1. No painel do projeto, procure o botão **"+ New"** ou **"+ Novo"**
2. Clique nele
3. Escolha **"Database"** (banco de dados)
4. Selecione **"Add PostgreSQL"**
5. ✅ Aguarde 1-2 minutos (ele cria o banco automaticamente)

### O que é PostgreSQL?
- É onde seus dados ficam salvos (usuários, produtos, vendas)
- Como um "arquivo Excel gigante" super organizado
- O Railway instala e configura sozinho

### Passo 8: Conectar banco ao projeto
**IMPORTANTE:** O Railway faz isso automaticamente!

Ele cria uma variável chamada `DATABASE_URL` que conecta tudo.
Você não precisa fazer nada aqui. ✅

---

## PARTE 4: CONFIGURAR VARIÁVEIS DE AMBIENTE

### O que são variáveis de ambiente?
São "configurações secretas" do seu site, como:
- Senhas do banco de dados
- Chave secreta do Django
- Se está em modo de teste ou produção

### Passo 9: Acessar configurações de variáveis
1. Clique no card/cartão do seu projeto (projetos-logos)
2. Procure as abas no topo:
   - Deployments
   - **Variables** ← CLIQUE AQUI
   - Metrics
   - Settings

### Passo 10: Adicionar variáveis obrigatórias

Clique em **"+ New Variable"** ou **"+ Nova Variável"** para cada uma:

#### Variável 1: SECRET_KEY
```
Nome: SECRET_KEY
Valor: django-insecure-railway-2024-grupo-lisboa-super-secret-key-change-in-production
```
**O que é:** Chave secreta do Django (como senha do sistema)

#### Variável 2: DEBUG
```
Nome: DEBUG
Valor: False
```
**O que é:** Modo de produção (False = site real, True = modo teste)

#### Variável 3: ALLOWED_HOSTS
```
Nome: ALLOWED_HOSTS
Valor: *.railway.app,grupolisboa.com.br,www.grupolisboa.com.br
```
**O que é:** Quais domínios podem acessar o site

#### Variável 4: DATABASE_URL
**NÃO ADICIONE ESTA!** 
O Railway já criou automaticamente quando você adicionou PostgreSQL ✅

### Como adicionar cada variável:
1. Clique **"+ New Variable"**
2. Campo "Name" (nome): cole o nome (ex: SECRET_KEY)
3. Campo "Value" (valor): cole o valor correspondente
4. Enter ou clique fora para salvar
5. Repita para as 3 variáveis

---

## PARTE 5: CONFIGURAR COMANDO DE INICIALIZAÇÃO

### Passo 11: Definir como iniciar o site
1. Clique no card do projeto
2. Vá na aba **"Settings"** (configurações)
3. Role a página até achar **"Deploy"**
4. Procure campo **"Start Command"** (comando de início)
5. Cole:
```
gunicorn logos.wsgi:application --bind 0.0.0.0:$PORT
```
6. Salva automaticamente ou clique "Save"

### O que é Gunicorn?
- É o "motor" que faz o Django funcionar em produção
- Como o "garçom" que serve seu site para os visitantes
- Necessário para sites profissionais (runserver é só para testes)

---

## PARTE 6: FORÇAR NOVO DEPLOY

### Passo 12: Fazer o site subir com as configurações
1. Vá na aba **"Deployments"**
2. Clique nos 3 pontinhos ⋮ do último deployment
3. Escolha **"Redeploy"** (reimplantar)
4. ⏳ Aguarde 3-5 minutos novamente

### O que está acontecendo:
- Railway pega as variáveis que você configurou
- Instala tudo de novo
- Inicia com Gunicorn
- Se tudo der certo, fica VERDE ✅

---

## PARTE 7: EXECUTAR MIGRAÇÕES DO BANCO

### O que são migrações?
- São "instruções" para criar as tabelas no banco de dados
- Como criar as "planilhas" onde seus dados vão ficar
- Sem isso, o site funciona mas não salva nada

### Passo 13: Executar migrações via Railway CLI

#### Opção A: Via Linha de Comando (Windows)

**Instalar Railway CLI:**
```powershell
# No PowerShell (como Administrador)
npm install -g @railway/cli
```

**Se não tiver npm/node, baixe aqui:**
https://nodejs.org (instale a versão LTS)

**Depois de instalar:**
```powershell
# Fazer login no Railway
railway login

# Conectar ao projeto
railway link

# Executar migrações
railway run python manage.py migrate

# Criar usuário administrador
railway run python manage.py createsuperuser
```

#### Opção B: Via Railway Web (se CLI não funcionar)

**EM BREVE:** Railway vai adicionar terminal web.
Por enquanto, use a Opção A ou me avise que eu te ajudo de outra forma.

---

## PARTE 8: GERAR DOMÍNIO PÚBLICO

### Passo 14: Criar URL pública
1. Vá na aba **"Settings"**
2. Procure seção **"Domains"** ou **"Networking"**
3. Clique **"Generate Domain"** (gerar domínio)
4. Railway cria algo como:
   ```
   projetos-logos-production.up.railway.app
   ```
5. **COPIE ESSA URL!** Você vai precisar!

### Para que serve essa URL?
- É o endereço "temporário" do seu site
- Você pode testar antes de colocar o domínio real
- Vamos usar ela para configurar o DNS na UOL

---

## PARTE 9: CONFIGURAR DNS NA UOL

### Passo 15: Acessar painel UOL
1. Acesse: https://painel.uol.com.br
2. Faça login
3. Vá em **"Domínios"**
4. Clique em **grupolisboa.com.br**
5. Clique no botão roxo **"Administrar DNS"**

### Passo 16: Adicionar registros DNS

**Você verá uma tabela com registros DNS. Vamos ADICIONAR ou EDITAR:**

#### Registro 1: Domínio principal
```
Tipo: CNAME
Nome: @ (ou deixe vazio)
Destino: [SUA-URL-DO-RAILWAY]
TTL: 3600
```

**Exemplo real:**
```
Tipo: CNAME
Nome: @
Destino: projetos-logos-production.up.railway.app
TTL: 3600
```

#### Registro 2: Subdomínio www
```
Tipo: CNAME
Nome: www
Destino: [SUA-URL-DO-RAILWAY]
TTL: 3600
```

**Exemplo real:**
```
Tipo: CNAME
Nome: www
Destino: projetos-logos-production.up.railway.app
TTL: 3600
```

### Como adicionar:
1. Procure botão **"Adicionar Registro"** ou **"Add Record"**
2. Preencha os campos
3. Salve
4. Repita para o segundo registro

---

## PARTE 10: ADICIONAR DOMÍNIO CUSTOMIZADO NO RAILWAY

### Passo 17: Configurar domínio próprio
1. Volte ao Railway
2. Aba **"Settings"** → Seção **"Domains"**
3. Clique **"Custom Domain"** (domínio customizado)
4. Digite: `grupolisboa.com.br`
5. Clique **"Add"**
6. Repita para: `www.grupolisboa.com.br`

### O que isso faz?
- Diz ao Railway que seu site deve responder por grupolisboa.com.br
- Railway configura SSL (HTTPS/cadeado) automaticamente
- Depois do DNS propagar, tudo funciona!

---

## PARTE 11: AGUARDAR PROPAGAÇÃO DNS

### Passo 18: Ter paciência 😊
⏳ **Tempo de espera: 30 minutos a 24 horas**

**O que é propagação DNS?**
- É como "avisar a internet inteira" do novo endereço
- Demora porque tem servidores no mundo todo
- Normalmente fica pronto em 1-2 horas

### Como testar se já funcionou?
1. Acesse: https://dnschecker.org
2. Digite: grupolisboa.com.br
3. Tipo: CNAME
4. Clique "Search"
5. Se aparecer verde em vários países = funcionou! ✅

### Ou simplesmente:
Tente acessar https://grupolisboa.com.br no navegador.
Se abrir o site = funcionou! 🎉

---

## ✅ CHECKLIST COMPLETO

Use isso para acompanhar seu progresso:

- [ ] 1. Criar conta Railway com GitHub
- [ ] 2. Criar novo projeto
- [ ] 3. Selecionar repositório projetos-logos
- [ ] 4. Aguardar primeiro build
- [ ] 5. Adicionar PostgreSQL
- [ ] 6. Configurar variável SECRET_KEY
- [ ] 7. Configurar variável DEBUG
- [ ] 8. Configurar variável ALLOWED_HOSTS
- [ ] 9. Configurar Start Command (gunicorn)
- [ ] 10. Forçar redeploy
- [ ] 11. Instalar Railway CLI
- [ ] 12. Executar railway migrate
- [ ] 13. Criar superusuário
- [ ] 14. Gerar domínio Railway (.up.railway.app)
- [ ] 15. Anotar URL do Railway
- [ ] 16. Acessar painel DNS UOL
- [ ] 17. Adicionar registro CNAME @
- [ ] 18. Adicionar registro CNAME www
- [ ] 19. Adicionar domínio customizado no Railway
- [ ] 20. Aguardar propagação DNS (1-24h)
- [ ] 21. Testar https://grupolisboa.com.br
- [ ] 22. 🎉 SITE NO AR!

---

## 🆘 PROBLEMAS COMUNS E SOLUÇÕES

### Erro: "Application failed to respond"
**Solução:** Verifique se configurou o Start Command com gunicorn

### Erro: "Bad Gateway 502"
**Solução:** Aguarde mais tempo, o banco pode estar iniciando

### Erro: "This site can't be reached"
**Solução:** DNS ainda não propagou, aguarde mais 30-60 min

### Site abre mas sem estilo (sem CSS)
**Solução:** Execute `railway run python manage.py collectstatic --noinput`

### Não consigo fazer login no admin
**Solução:** Execute `railway run python manage.py createsuperuser`

---

## 💰 CUSTOS DETALHADOS

### Plano FREE (inicial):
- $5 de crédito grátis
- 500 horas/mês grátis
- Perfeito para começar

### Depois que acabar o grátis:
- **PostgreSQL:** $5/mês (~R$25)
- **App (se passar 500h/mês):** $5/mês (~R$25)
- **Total estimado:** R$25-50/mês

### Como economizar:
- Se o site ficar parado, não consome horas
- 500h = ~20 dias rodando 24/7
- Sites pequenos geralmente ficam no grátis!

---

## 📞 PRECISA DE AJUDA?

Se travar em algum passo:
1. Anote em qual PASSO parou (número)
2. Tire print do erro (se houver)
3. Me chame!

Vou te ajudar em tempo real! 🚀

---

**Última atualização:** 21/11/2025
**Criado por:** GitHub Copilot para mlisboa17
**Projeto:** LOGOS - Grupo Lisboa
