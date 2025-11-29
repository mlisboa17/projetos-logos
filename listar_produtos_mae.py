"""
Lista produtos da base produtos_mae
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

produtos = ProdutoMae.objects.all().order_by('marca', 'descricao_produto')

for p in produtos:
    print(f"{p.id}|{p.marca}|{p.descricao_produto}")
