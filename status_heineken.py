#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto

print("=" * 80)
print("🍺 STATUS DE HEINEKEN - RESUMO COMPLETO")
print("=" * 80)

# Buscar todos os produtos Heineken
heinekens = ProdutoMae.objects.filter(descricao_produto__icontains='HEINEKEN').order_by('id')

print(f"\nTotal de produtos HEINEKEN: {heinekens.count()}\n")

total_imagens_heineken = 0
produtos_com_imagens = []
produtos_sem_imagens = []

for produto in heinekens:
    total_imgs = produto.imagens_treino.count()
    total_imagens_heineken += total_imgs
    
    status = "✅" if total_imgs > 0 else "❌"
    
    if total_imgs > 0:
        produtos_com_imagens.append({
            'id': produto.id,
            'nome': produto.descricao_produto,
            'imagens': total_imgs
        })
        barra = "█" * (total_imgs // 5)
        print(f"{status} ID {produto.id:3d} - {produto.descricao_produto:50s} | {barra} ({total_imgs:3d})")
    else:
        produtos_sem_imagens.append({
            'id': produto.id,
            'nome': produto.descricao_produto
        })
        print(f"{status} ID {produto.id:3d} - {produto.descricao_produto:50s} | (  0)")

print("\n" + "=" * 80)
print("📊 RESUMO HEINEKEN")
print("=" * 80)

print(f"\n✅ Produtos com imagens: {len(produtos_com_imagens)}")
for item in produtos_com_imagens:
    print(f"   • ID {item['id']}: {item['nome']} ({item['imagens']} imagens)")

print(f"\n❌ Produtos SEM imagens: {len(produtos_sem_imagens)}")
for item in produtos_sem_imagens[:10]:
    print(f"   • ID {item['id']}: {item['nome']}")

if len(produtos_sem_imagens) > 10:
    print(f"   ... e mais {len(produtos_sem_imagens) - 10}")

print(f"\n🖼️  Total de imagens HEINEKEN: {total_imagens_heineken}")

print("\n" + "=" * 80)
print("📥 O QUE FAZER?")
print("=" * 80)
print("""
1. IMPORTAR MAIS DADOS:
   python importar_coletas.py
   
   - Opção 1: Importar uma pasta (Passo 1 ou Passo 2)
   - Opção 2: Importar todas as 11 pastas Heineken disponíveis

2. VER DADOS IMPORTADOS:
   http://127.0.0.1:8000/verifik/imagens-anotadas/

3. DEPOIS: Treinar modelo YOLO com dados limpos
""")

print("=" * 80)
