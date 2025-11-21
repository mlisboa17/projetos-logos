# Passo a passo - Deploy Railway

## 1. Preparar GitHub (se ainda não fez)

No terminal do VS Code:
```bash
git add .
git commit -m "Preparar para deploy em produção"
git push origin main
```

## 2. Deploy no Railway

### A. Criar projeto
1. Acesse https://railway.app
2. Login with GitHub
3. Clique "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha: mlisboa17/projetos-logos
6. Clique "Deploy Now"

### B. Adicionar PostgreSQL
1. No dashboard do projeto
2. Clique "+ New"
3. Selecione "Database" → "Add PostgreSQL"
4. Aguarde provisionamento (1-2 minutos)

### C. Configurar variáveis de ambiente
1. Clique no serviço "projetos-logos"
2. Aba "Variables"
3. Clique "+ New Variable"
4. Adicione uma por uma:

```
DJANGO_SETTINGS_MODULE=logos.settings_production
SECRET_KEY=railway-vai-gerar-automaticamente-ou-gere-uma
DEBUG=False
ALLOWED_HOSTS=*.railway.app,grupolisboa.com.br,www.grupolisboa.com.br

# PostgreSQL (Railway preenche automaticamente se vincular o banco)
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### D. Configurar build e deploy
1. Na aba "Settings"
2. Seção "Build"
   - Build Command: (deixe vazio, usa requirements.txt automaticamente)
3. Seção "Deploy"
   - Start Command: `gunicorn logos.wsgi:application --bind 0.0.0.0:$PORT`
4. Clique "Save"

### E. Deploy
1. Aba "Deployments"
2. Clique "Deploy" ou aguarde deploy automático
3. Aguarde build (5-10 minutos na primeira vez)
4. Quando ficar verde = sucesso!

### F. Executar migrações
1. Clique nos 3 pontinhos do serviço
2. "View Logs"
3. Se der erro de migrations, execute:
   - Railway → Settings → Generate Domain (anote a URL)
   - No terminal local:
   ```bash
   railway login
   railway link
   railway run python manage.py migrate
   railway run python manage.py createsuperuser
   ```

### G. Pegar URL do Railway
1. Aba "Settings"
2. Seção "Domains"
3. Clique "Generate Domain"
4. Vai gerar algo como: `projetos-logos-production.up.railway.app`
5. Anote essa URL!

## 3. Configurar DNS na UOL

### A. Acessar painel UOL
1. https://painel.uol.com.br
2. Login
3. "Domínios" → grupolisboa.com.br
4. "Gerenciar DNS"

### B. Adicionar registros
Adicione/Edite os seguintes registros:

**Para domínio principal:**
```
Tipo: CNAME
Nome: @
Destino: projetos-logos-production.up.railway.app
TTL: 3600
```

**Para www:**
```
Tipo: CNAME
Nome: www
Destino: projetos-logos-production.up.railway.app
TTL: 3600
```

**OU se não permitir CNAME no @:**
```
Tipo: A
Nome: @
Destino: [IP que o Railway fornece]
TTL: 3600

Tipo: CNAME
Nome: www
Destino: projetos-logos-production.up.railway.app
TTL: 3600
```

### C. Adicionar domínio customizado no Railway
1. Railway → Settings → Domains
2. Clique "Custom Domain"
3. Digite: grupolisboa.com.br
4. Clique "Add"
5. Repita para www.grupolisboa.com.br

## 4. Aguardar propagação DNS
- Pode levar de 5 minutos a 24 horas
- Geralmente fica pronto em 1-2 horas
- Teste em: https://dnschecker.org

## 5. Configurar SSL (HTTPS)
O Railway configura SSL automaticamente após DNS propagar!

## Custos Railway
- 500 horas grátis/mês (suficiente para 1 app sempre ativo)
- PostgreSQL: $5/mês
- Se passar das horas grátis: ~$5/mês adicional
- **Total estimado: $5-10/mês**

## Alternativa GRATUITA: Render.com
Se quiser começar 100% grátis:
1. Usar Render.com (similar ao Railway)
2. Tem plano gratuito (com limitações)
3. PostgreSQL gratuito por 90 dias
