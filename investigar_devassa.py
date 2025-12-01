#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from django.db.models import Count

print("=" * 80)
print("🔍 INVESTIGAÇÃO DETALHADA - PRODUTOS DEVASSA")
print("=" * 80)

# ============================================================================
# 1. LISTAR TODOS OS PRODUTOS DEVASSA
# ============================================================================
print("\n1️⃣  LISTANDO TODOS OS PRODUTOS DEVASSA")
print("-" * 80)

devassas = ProdutoMae.objects.filter(
    descricao_produto__icontains='DEVASSA'
).order_by('id')

print(f"\nTotal de produtos com 'DEVASSA' no nome: {devassas.count()}\n")

devassa_info = []

for produto in devassas:
    total_imagens = produto.imagens_treino.count()
    devassa_info.append({
        'id': produto.id,
        'nome': produto.descricao_produto,
        'marca': produto.marca,
        'tipo': produto.tipo,
        'preco': produto.preco,
        'ativo': produto.ativo,
        'total_imagens': total_imagens
    })
    
    status_ativo = "✅ ATIVO" if produto.ativo else "❌ INATIVO"
    print(f"ID {produto.id}: {produto.descricao_produto}")
    print(f"   Marca: {produto.marca}")
    print(f"   Tipo: {produto.tipo}")
    print(f"   Preço: R$ {produto.preco}")
    print(f"   Status: {status_ativo}")
    print(f"   🖼️  Total de imagens: {total_imagens}")
    print()

# ============================================================================
# 2. VERIFICAR SE AS 159 IMAGENS SÃO MESMO DA ID 35
# ============================================================================
print("\n2️⃣  VERIFICANDO IMAGENS DA DEVASSA ID 35")
print("-" * 80)

devassa_35 = ProdutoMae.objects.get(id=35)
imagens_35 = devassa_35.imagens_treino.all().order_by('id')

print(f"\nProduto ID 35: {devassa_35.descricao_produto}")
print(f"Total de imagens: {imagens_35.count()}\n")

# Mostrar primeiras 10
print("Primeiras 10 imagens:")
for i, img in enumerate(imagens_35[:10], 1):
    print(f"  {i}. ID {img.id}: {img.imagem.name}")

print(f"\n... ({imagens_35.count() - 10} imagens adicionais)")

# ============================================================================
# 3. ANALISAR ORIGEM DAS IMAGENS
# ============================================================================
print("\n3️⃣  ANALISANDO ORIGEM DAS IMAGENS")
print("-" * 80)

# Agrupar por pasta de origem
origem_mapping = {}

for img in imagens_35:
    # Extrair pasta/origem do caminho
    path_parts = img.imagem.name.split('/')
    
    if len(path_parts) > 1:
        origem = '/'.join(path_parts[:-1])  # Tudo menos o arquivo
    else:
        origem = 'raiz'
    
    if origem not in origem_mapping:
        origem_mapping[origem] = []
    
    origem_mapping[origem].append(img)

print(f"\nOrigem das imagens da Devassa ID 35:\n")

for origem in sorted(origem_mapping.keys()):
    count = len(origem_mapping[origem])
    print(f"  📁 {origem}: {count} imagens")

# ============================================================================
# 4. COMPARAR COM OUTROS PRODUTOS DEVASSA
# ============================================================================
print("\n4️⃣  COMPARANDO COM OUTROS PRODUTOS DEVASSA")
print("-" * 80)

print("\nDistribuição de imagens entre produtos Devassa:\n")

total_devassa_imagens = 0
for info in devassa_info:
    total_devassa_imagens += info['total_imagens']
    barra = "█" * (info['total_imagens'] // 5)
    print(f"ID {info['id']:3d} - {info['nome']:50s} | {barra} ({info['total_imagens']:3d})")

print(f"\nTotal de imagens em produtos Devassa: {total_devassa_imagens}")

# ============================================================================
# 5. VERIFICAR SE HÁ ERRO DE ASSOCIAÇÃO
# ============================================================================
print("\n5️⃣  ANALISANDO POSSÍVEIS ERROS DE ASSOCIAÇÃO")
print("-" * 80)

# Buscar imagens com "devassa" no nome do arquivo
devassa_em_nome = 0
outras_no_35 = 0

for img in imagens_35:
    nome_arquivo = img.imagem.name.lower()
    
    if 'devassa' in nome_arquivo:
        devassa_em_nome += 1
    else:
        outras_no_35 += 1
        if outras_no_35 <= 5:  # Mostrar primeiras 5
            print(f"⚠️  Imagem sem 'devassa' no nome: {img.imagem.name}")

print(f"\n✅ Imagens com 'devassa' no nome: {devassa_em_nome}")
print(f"⚠️  Imagens SEM 'devassa' no nome: {outras_no_35}")

if outras_no_35 > 0:
    print(f"\n🚨 POSSÍVEL ERRO: {outras_no_35} imagens não parecem ser Devassa!")

# ============================================================================
# 6. RESUMO E RECOMENDAÇÕES
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 RESUMO E RECOMENDAÇÕES")
print("=" * 80)

print(f"\n📦 Produtos Devassa identificados: {devassas.count()}")
print(f"🖼️  Total de imagens Devassa: {total_devassa_imagens}")
print(f"🔴 Concentração em ID 35: {(imagens_35.count()/total_devassa_imagens*100):.1f}%")

if outras_no_35 > 0:
    print(f"\n⚠️  AVISO: {outras_no_35} imagens em ID 35 podem estar erroneamente associadas")
    print("   Recomendação: Revisar origem dessas imagens e reasociar se necessário")
else:
    print(f"\n✅ Todas as imagens em ID 35 parecem ser legítimas")

if imagens_35.count() > 80:
    print(f"\n💡 Dica: {imagens_35.count()} imagens é muito para um produto.")
    print("   Considere:")
    print("   • Dividir em variantes (Devassa Lager, Devassa Ipa, etc)")
    print("   • Ou verificar se há imagens incorretas associadas")

print("\n" + "=" * 80)
