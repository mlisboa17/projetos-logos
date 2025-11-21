#!/bin/bash

# Script de deploy para servidor Linux

echo "====================================="
echo "Deploy LOGOS - Grupo Lisboa"
echo "====================================="

# Atualizar código
echo "Atualizando código..."
git pull origin main

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migrações
echo "Aplicando migrações..."
python manage.py migrate

# Reiniciar Gunicorn
echo "Reiniciando Gunicorn..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "====================================="
echo "Deploy concluído!"
echo "====================================="
