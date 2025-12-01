import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from django.db.models import Count

print("=" * 70)
print("RESUMO ATUALIZADO DO BANCO DE DADOS")
print("=" * 70)
print()

produtos = ImagemProduto.objects.values(
    'produto_id', 
    'produto__descricao_produto'
).annotate(
    total=Count('id')
).order_by('-total')

for p in produtos:
    prod_id = p['produto_id']
    nome = p['produto__descricao_produto']
    total = p['total']
    print(f"  ID {prod_id}: {nome} = {total} imgs")

print()
print(f"Total geral: {ImagemProduto.objects.count()} imagens")
print("=" * 70)
