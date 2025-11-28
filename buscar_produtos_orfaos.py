"""
Buscar produtos cadastrados que possam corresponder às pastas órfãs
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

keywords = ['heineken', 'smirnoff', 'pringles', 'ruffles', 'pipoca', 'bokus']

print("=" * 80)
print("PRODUTOS CADASTRADOS QUE PODEM CORRESPONDER ÀS PASTAS ÓRFÃS")
print("=" * 80)

for keyword in keywords:
    print(f"\n🔍 Buscando '{keyword}':")
    print("-" * 80)
    
    produtos = ProdutoMae.objects.filter(ativo=True).filter(
        descricao_produto__icontains=keyword
    ) | ProdutoMae.objects.filter(ativo=True).filter(
        marca__icontains=keyword
    )
    
    if produtos.exists():
        for p in produtos:
            print(f"  ID {p.id:3d} | {p.descricao_produto[:45]:45s} | {p.marca or 'Sem marca':<15s} | {p.imagens_treino.count()} imgs")
    else:
        print(f"  ❌ Nenhum produto encontrado")

print("\n" + "=" * 80)
print("TODOS OS PRODUTOS DE SNACKS/SALGADINHOS")
print("=" * 80)

snacks = ProdutoMae.objects.filter(ativo=True).filter(
    tipo__icontains='snack'
) | ProdutoMae.objects.filter(ativo=True).filter(
    tipo__icontains='salgadinho'
) | ProdutoMae.objects.filter(ativo=True).filter(
    tipo__icontains='pipoca'
)

if snacks.exists():
    for p in snacks:
        print(f"  ID {p.id:3d} | {p.descricao_produto[:45]:45s} | {p.tipo or 'Sem tipo':<20s} | {p.imagens_treino.count()} imgs")
else:
    print("  ❌ Nenhum produto de snacks encontrado")
