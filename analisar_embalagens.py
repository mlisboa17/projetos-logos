"""
ANALISE DE EMBALAGENS - Verifica tipos de produtos na base
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).resolve().parent))
django.setup()

from verifik.models_anotacao import ImagemUnificada
from verifik.models import ProdutoMae
from django.db.models import Count
import re

print('\n' + '='*80)
print('ANALISE DE EMBALAGENS NA BASE DE DADOS')
print('='*80)

# Padrões para detectar tipo de embalagem
padoes = {
    'GARRAFAS': [
        r'GARRAFA', r'LONG NECK', r'LONGNECK', r'330\s*ML', r'350\s*ML', r'600\s*ML'
    ],
    'LATAS': [
        r'LATA', r'473\s*ML', r'350\s*ML.*LATA', r'ENERGETICO'
    ],
    'PET 2LITROS': [
        r'PET', r'2\s*L', r'2LITRO', r'2L', r'GARRAFA.*PET'
    ]
}

# Buscar todos os produtos únicos
produtos = ProdutoMae.objects.all().order_by('descricao_produto')

print(f'\nTotal de produtos: {produtos.count()}')
print(f'Total de imagens: {ImagemUnificada.objects.count()}')

# Classificar por embalagem
classificacao = {
    'GARRAFAS': [],
    'LATAS': [],
    'PET 2LITROS': [],
    'OUTROS': []
}

for prod in produtos:
    desc_upper = prod.descricao_produto.upper()
    encontrado = False
    
    for tipo, patterns in padoes.items():
        for pattern in patterns:
            if re.search(pattern, desc_upper):
                count = ImagemUnificada.objects.filter(produto=prod).count()
                classificacao[tipo].append({
                    'nome': prod.descricao_produto,
                    'id': prod.id,
                    'imagens': count
                })
                encontrado = True
                break
        if encontrado:
            break
    
    if not encontrado:
        count = ImagemUnificada.objects.filter(produto=prod).count()
        classificacao['OUTROS'].append({
            'nome': prod.descricao_produto,
            'id': prod.id,
            'imagens': count
        })

# Exibir resultados
print('\n' + '='*80)
print('DISTRIBUIÇÃO POR TIPO DE EMBALAGEM')
print('='*80)

total_geral = 0

for tipo in ['GARRAFAS', 'LATAS', 'PET 2LITROS', 'OUTROS']:
    prods = classificacao[tipo]
    total_imgs = sum(p['imagens'] for p in prods)
    total_geral += total_imgs
    
    print(f'\n🏷️  {tipo}: {len(prods)} produtos, {total_imgs} imagens')
    print('-' * 80)
    
    # Ordenar por quantidade de imagens
    prods.sort(key=lambda x: x['imagens'], reverse=True)
    
    for i, prod in enumerate(prods[:15], 1):  # Top 15
        print(f"   {i:2}. {prod['nome'][:55]:55} {prod['imagens']:6} imgs")
    
    if len(prods) > 15:
        remaining = sum(p['imagens'] for p in prods[15:])
        print(f"   ... +{len(prods)-15} produtos com {remaining} imagens")

print('\n' + '='*80)
print(f'TOTAL GERAL: {total_geral} imagens')
print('='*80 + '\n')
