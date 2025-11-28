"""
Verifica quais produtos têm novas imagens desde o último treinamento
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count

# Produtos que foram treinados (do último treino com 10 classes)
produtos_treinados = {
    'AMSTEL CERVEJA AMSTEL 473ML': 34,
    'BUDWEISER CERVEJA BUDWEISER LN 330ML': 27,
    'DEVASSA CERVEJA DEVASSA LAGER 350 ML': 50,
    'DEVASSA CERVEJA DEVASSA LAGER 473ML': 106,
    'HEINEKEN CERVEJA HEINEKEN 330ML': 27,
    'HEINEKEN CERVEJA HEINEKEN LATA 350ML': 20,
    'PETRA CERVEJA PETRA 473ML': 5,
    'PILSEN CERVEJA PILSEN LOKAL LATA 473ML': 24,
    'STELLA CERVEJA STELLA PURE GOLD S GLUTEN LONG 330ML': 40,
    'REFRIGERANTE REFRIGERANTE BLACK PEPSI 350ML': 54,
}

print("\n" + "="*80)
print("📊 ANÁLISE DE IMAGENS NOVAS")
print("="*80)

# Listar todos os produtos com imagens
produtos = ProdutoMae.objects.annotate(
    num_imgs=Count('imagens_treino')
).filter(num_imgs__gt=0).order_by('marca')

total_novas = 0
produtos_com_novas = []

print("\n🆕 PRODUTOS COM NOVAS IMAGENS:")
print("-"*80)

for p in produtos:
    classe_nome = f"{p.marca} {p.descricao_produto}"
    num_atual = p.imagens_treino.count()
    
    if classe_nome in produtos_treinados:
        num_treinado = produtos_treinados[classe_nome]
        novas = num_atual - num_treinado
        
        if novas > 0:
            total_novas += novas
            produtos_com_novas.append((p, novas, num_atual))
            print(f"  ✅ {p.marca:15} - {p.descricao_produto[:45]:45} (+{novas:2} imgs) Total: {num_atual}")

print("-"*80)
print(f"\n📈 RESUMO:")
print(f"   Produtos com novas imagens: {len(produtos_com_novas)}")
print(f"   Total de novas imagens: {total_novas}")

print("\n" + "="*80)
print("💡 OPÇÕES:")
print("="*80)
print("1. Treinar APENAS com os produtos que têm novas imagens")
print("2. Retreinar TUDO (recomendado para melhor precisão)")
print("="*80)
