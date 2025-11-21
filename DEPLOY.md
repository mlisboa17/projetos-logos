# Guia de Deploy - LOGOS (grupolisboa.com.br)

## Opções de Hospedagem

### Opção 1: Railway (Mais Fácil - ~$5/mês)
1. Acesse https://railway.app
2. Conecte seu GitHub e faça fork do repositório
3. Crie novo projeto → Deploy from GitHub
4. Adicione PostgreSQL addon
5. Configure variáveis de ambiente (.env.production)
6. No painel DNS da UOL, crie registro CNAME:
   - Nome: www
   - Tipo: CNAME
   - Valor: [url-do-railway].up.railway.app

### Opção 2: VPS/Servidor Linux (Mais Controle)

#### Pré-requisitos no servidor:
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Instalar Nginx
sudo apt install nginx -y

# Instalar Git
sudo apt install git -y
```

#### 1. Configurar PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE logos_db;
CREATE USER logos_user WITH PASSWORD 'senha-segura-aqui';
ALTER ROLE logos_user SET client_encoding TO 'utf8';
ALTER ROLE logos_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE logos_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE logos_db TO logos_user;
\q
```

#### 2. Clonar e configurar projeto
```bash
cd /var/www
sudo git clone [SEU-REPOSITORIO] logos
cd logos
sudo chown -R $USER:$USER /var/www/logos

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.production .env
nano .env  # Editar com suas credenciais
```

#### 3. Configurar Django
```bash
# Gerar SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copie e cole no .env

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser
```

#### 4. Configurar Gunicorn
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Conteúdo:
```ini
[Unit]
Description=gunicorn daemon for LOGOS
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/logos
EnvironmentFile=/var/www/logos/.env
ExecStart=/var/www/logos/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/logos/gunicorn.sock \
          logos.wsgi:application

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

#### 5. Configurar Nginx
```bash
sudo nano /etc/nginx/sites-available/logos
```

Conteúdo:
```nginx
server {
    listen 80;
    server_name grupolisboa.com.br www.grupolisboa.com.br;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/logos/staticfiles/;
    }

    location /media/ {
        alias /var/www/logos/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/logos/gunicorn.sock;
    }
}
```

Ativar:
```bash
sudo ln -s /etc/nginx/sites-available/logos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Configurar SSL (HTTPS) - Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d grupolisboa.com.br -d www.grupolisboa.com.br
```

#### 7. DNS na UOL
No painel da UOL (https://painel.uol.com.br):
1. Acesse "Domínios" → grupolisboa.com.br
2. Gerenciar DNS
3. Adicione/Edite registros:
   - Tipo A: @ → [IP-DO-SEU-SERVIDOR]
   - Tipo A: www → [IP-DO-SEU-SERVIDOR]

### Opção 3: DigitalOcean App Platform (~$5/mês)
1. Crie conta em https://digitalocean.com
2. App Platform → Create App
3. Conecte GitHub
4. Configure build:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn logos.wsgi:application`
5. Adicione PostgreSQL como componente
6. Configure variáveis de ambiente
7. Na UOL DNS: CNAME apontando para [app].ondigitalocean.app

## Manutenção

### Atualizar código (com deploy.sh)
```bash
cd /var/www/logos
chmod +x deploy.sh
./deploy.sh
```

### Ver logs
```bash
# Gunicorn
sudo journalctl -u gunicorn -f

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### Backup do banco
```bash
pg_dump logos_db > backup_$(date +%Y%m%d).sql
```

## Próximos Passos

Me informe qual opção você prefere:
1. **Railway** - Mais rápido, sem gerenciar servidor
2. **VPS próprio** - Você tem servidor/VPS na UOL ou outra empresa?
3. **DigitalOcean** - Boa opção intermediária

Também preciso saber:
- Você tem acesso SSH a algum servidor?
- Orçamento disponível para hospedagem?
- Precisa de ajuda para configurar o DNS na UOL?
