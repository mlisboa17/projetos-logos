"""
RESUMO DO BANCO DE DADOS - ImagemUnificada
Mostra estatísticas de imagens por tipo
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

print("\n" + "=" * 80)
print("RESUMO - IMAGEMUNIFICADA")
print("=" * 80)

# Total geral
total = ImagemUnificada.objects.count()
print(f"\n📊 TOTAL DE IMAGENS: {total}")

# Por tipo
tipos = ImagemUnificada.objects.values('tipo_imagem').annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id')).order_by('tipo_imagem')

print(f"\n📁 DISTRIBUIÇÃO POR TIPO:")
for t in tipos:
    tipo = t['tipo_imagem']
    count = t['count']
    percent = (count / total * 100) if total > 0 else 0
    print(f"   {tipo:20} {count:6} ({percent:5.1f}%)")

# Augmentacoes por tipo
print(f"\n🎨 AUGMENTACOES POR TIPO:")
augmentacoes = ImagemUnificada.objects.filter(
    tipo_imagem='augmentada'
).values('tipo_augmentacao').annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id')).order_by('-count')

for a in augmentacoes:
    tipo = a['tipo_augmentacao']
    count = a['count']
    print(f"   {tipo:20} {count:6}")

# Produtos com mais imagens
print(f"\n🏆 TOP 10 PRODUTOS (por quantidade de imagens):")
top_produtos = []
for produto in ProdutoMae.objects.all():
    count = ImagemUnificada.objects.filter(produto=produto).count()
    if count > 0:
        top_produtos.append((produto.descricao_produto[:40], count))

top_produtos.sort(key=lambda x: x[1], reverse=True)
for i, (desc, count) in enumerate(top_produtos[:10], 1):
    print(f"   {i:2}. {desc:40} {count:6}")

# Status de treino
print(f"\n🔬 STATUS DE TREINO:")
treinadas = ImagemUnificada.objects.filter(num_treinos__gt=0).count()
nao_treinadas = total - treinadas
print(f"   Já treinadas: {treinadas} ({treinadas/total*100:.1f}%)" if total > 0 else "   Já treinadas: 0")
print(f"   Não treinadas: {nao_treinadas} ({nao_treinadas/total*100:.1f}%)" if total > 0 else "   Não treinadas: 0")

# Ativas vs inativas
print(f"\n✅ STATUS DE ATIVACAO:")
ativas = ImagemUnificada.objects.filter(ativa=True).count()
inativas = total - ativas
print(f"   Ativas: {ativas} ({ativas/total*100:.1f}%)" if total > 0 else "   Ativas: 0")
print(f"   Inativas: {inativas} ({inativas/total*100:.1f}%)" if total > 0 else "   Inativas: 0")

print("\n" + "=" * 80)
