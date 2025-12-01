#!/usr/bin/env python
import os
import django
from pathlib import Path
from PIL import Image
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto

print("=" * 80)
print("🔍 VARREDURA COMPLETA DE ERROS - IMAGENS E ASSOCIAÇÕES")
print("=" * 80)

# ============================================================================
# 1. VERIFICAR INTEGRIDADE DE ARQUIVOS FÍSICOS
# ============================================================================
print("\n1️⃣  VERIFICANDO INTEGRIDADE DE ARQUIVOS FÍSICOS")
print("-" * 80)

problemas_arquivo = []
imagens_treino = ImagemProduto.objects.all()

for img in imagens_treino:
    try:
        if not img.imagem:
            problemas_arquivo.append({
                'tipo': 'Arquivo vazio',
                'id': img.id,
                'produto': img.produto.descricao_produto,
                'path': 'NULL'
            })
            continue
        
        arquivo_path = img.imagem.path
        
        # Verificar se arquivo existe
        if not os.path.exists(arquivo_path):
            problemas_arquivo.append({
                'tipo': 'Arquivo não encontrado',
                'id': img.id,
                'produto': img.produto.descricao_produto,
                'path': arquivo_path
            })
            continue
        
        # Verificar se é uma imagem válida
        try:
            image = Image.open(arquivo_path)
            image.verify()
            tamanho_kb = os.path.getsize(arquivo_path) / 1024
            
            # Aviso se arquivo muito pequeno (< 10KB)
            if tamanho_kb < 10:
                problemas_arquivo.append({
                    'tipo': 'Arquivo muito pequeno (possível corrupção)',
                    'id': img.id,
                    'produto': img.produto.descricao_produto,
                    'path': arquivo_path,
                    'tamanho_kb': round(tamanho_kb, 2)
                })
        except Exception as e:
            problemas_arquivo.append({
                'tipo': f'Imagem corrompida: {str(e)[:50]}',
                'id': img.id,
                'produto': img.produto.descricao_produto,
                'path': arquivo_path
            })
    except Exception as e:
        problemas_arquivo.append({
            'tipo': f'Erro ao verificar: {str(e)[:50]}',
            'id': img.id,
            'produto': 'DESCONHECIDO'
        })

print(f"✅ Total de imagens de treino verificadas: {imagens_treino.count()}")
print(f"⚠️  Problemas encontrados com arquivos: {len(problemas_arquivo)}")

if problemas_arquivo:
    print("\n📋 Detalhes dos problemas:")
    for i, prob in enumerate(problemas_arquivo[:20], 1):
        print(f"  {i}. [{prob['tipo']}] Imagem ID {prob['id']} - {prob['produto']}")
        if 'tamanho_kb' in prob:
            print(f"     └─ Tamanho: {prob['tamanho_kb']}KB")

# ============================================================================
# 2. VERIFICAR ASSOCIAÇÕES DE PRODUTOS ESTRANHAS
# ============================================================================
print("\n\n2️⃣  VERIFICANDO ASSOCIAÇÕES DE PRODUTOS ESTRANHAS")
print("-" * 80)

erros_associacao = []

# Produtos com muitas imagens (possível erro de batch)
produtos_muitas_imgs = ImagemProduto.objects.raw(
    'SELECT p.id, p.descricao_produto, COUNT(i.id) as total FROM verifik_produtomae p '
    'LEFT JOIN verifik_imagemproduto i ON p.id = i.produto_id '
    'GROUP BY p.id, p.descricao_produto HAVING COUNT(i.id) > 100 '
    'ORDER BY COUNT(i.id) DESC'
)

for p in produtos_muitas_imgs:
    erros_associacao.append({
        'tipo': 'Muitas imagens (possível erro de batch)',
        'produto': p.descricao_produto,
        'id': p.id,
        'quantidade': p.total
    })

# Produtos sem imagens
produtos_sem_imagens = ProdutoMae.objects.filter(imagens_treino__isnull=True).count()

# Imagens órfãs (produto deletado)
from django.db.models import Q
imagens_orfas = ImagemProduto.objects.filter(produto__isnull=True).count()

print(f"✅ Produtos verificados: {ProdutoMae.objects.count()}")
print(f"⚠️  Produtos sem imagens: {produtos_sem_imagens}")
print(f"❌ Imagens órfãs (produto deletado): {imagens_orfas}")

if erros_associacao:
    print(f"\n📋 Produtos com muitas imagens:")
    for i, erro in enumerate(erros_associacao, 1):
        print(f"  {i}. {erro['produto']} (ID {erro['id']}) - {erro['quantidade']} imagens")

# ============================================================================
# 3. VERIFICAR IMAGENS ANOTADAS
# ============================================================================
print("\n\n3️⃣  VERIFICANDO INTEGRIDADE DE IMAGENS ANOTADAS")
print("-" * 80)

problemas_anotacao = []
imagens_anotadas = ImagemAnotada.objects.all()

for img in imagens_anotadas:
    try:
        # Verificar se arquivo existe
        if not img.imagem:
            problemas_anotacao.append({
                'tipo': 'Arquivo vazio',
                'id': img.id,
                'anotacoes': img.anotacoes.count()
            })
            continue
        
        arquivo_path = img.imagem.path
        if not os.path.exists(arquivo_path):
            problemas_anotacao.append({
                'tipo': 'Arquivo não encontrado',
                'id': img.id,
                'path': arquivo_path,
                'anotacoes': img.anotacoes.count()
            })
            continue
        
        # Verificar se é uma imagem válida
        try:
            image = Image.open(arquivo_path)
            image.verify()
        except Exception as e:
            problemas_anotacao.append({
                'tipo': f'Imagem corrompida: {str(e)[:40]}',
                'id': img.id,
                'anotacoes': img.anotacoes.count()
            })
    except Exception as e:
        problemas_anotacao.append({
            'tipo': f'Erro ao verificar: {str(e)[:40]}',
            'id': img.id
        })

print(f"✅ Total de imagens anotadas verificadas: {imagens_anotadas.count()}")
print(f"⚠️  Problemas encontrados: {len(problemas_anotacao)}")

if problemas_anotacao:
    print("\n📋 Problemas em imagens anotadas:")
    for i, prob in enumerate(problemas_anotacao[:10], 1):
        print(f"  {i}. [ID {prob['id']}] {prob['tipo']}")

# ============================================================================
# 4. VERIFICAR ANOTAÇÕES INVÁLIDAS
# ============================================================================
print("\n\n4️⃣  VERIFICANDO ANOTAÇÕES INVÁLIDAS (BBOX)")
print("-" * 80)

anotacoes_invalidas = []
todas_anotacoes = AnotacaoProduto.objects.all()

for anotacao in todas_anotacoes:
    problemas = []
    
    # Verificar coordenadas negativas
    if anotacao.bbox_x < 0 or anotacao.bbox_y < 0:
        problemas.append('Coordenadas negativas')
    
    # Verificar coordenadas muito grandes (provavelmente fora da imagem)
    if anotacao.bbox_x > 10000 or anotacao.bbox_y > 10000 or \
       anotacao.bbox_width > 10000 or anotacao.bbox_height > 10000:
        problemas.append('Coordenadas muito grandes')
    
    # Verificar dimensões zero
    if anotacao.bbox_width <= 0 or anotacao.bbox_height <= 0:
        problemas.append('Dimensões zero ou negativas')
    
    # Verificar confiança fora do intervalo
    if anotacao.confianca and (anotacao.confianca < 0 or anotacao.confianca > 1):
        problemas.append('Confiança fora do intervalo [0, 1]')
    
    # Verificar produto nulo
    if not anotacao.produto:
        problemas.append('Produto nulo')
    
    if problemas:
        anotacoes_invalidas.append({
            'id': anotacao.id,
            'imagem': anotacao.imagem_anotada.id if anotacao.imagem_anotada else 'NULL',
            'produto': anotacao.produto.descricao_produto if anotacao.produto else 'NULL',
            'problemas': problemas,
            'coords': f"({anotacao.bbox_x}, {anotacao.bbox_y}, {anotacao.bbox_width}, {anotacao.bbox_height})"
        })

print(f"✅ Total de anotações verificadas: {todas_anotacoes.count()}")
print(f"⚠️  Anotações com problemas: {len(anotacoes_invalidas)}")

if anotacoes_invalidas:
    print("\n📋 Detalhes das anotações inválidas:")
    for i, anotacao in enumerate(anotacoes_invalidas[:15], 1):
        print(f"  {i}. Anotação ID {anotacao['id']} - Imagem {anotacao['imagem']}")
        print(f"     Produto: {anotacao['produto']}")
        print(f"     Coords: {anotacao['coords']}")
        print(f"     Problemas: {', '.join(anotacao['problemas'])}")

# ============================================================================
# 5. VERIFICAR DUPLICATAS
# ============================================================================
print("\n\n5️⃣  VERIFICANDO DUPLICATAS DE IMAGENS")
print("-" * 80)

from django.db.models import Count

# Buscar imagens com mesmo arquivo
duplicatas = ImagemProduto.objects.values('imagem').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

print(f"✅ Grupos de imagens duplicadas encontradas: {duplicatas.count()}")

if duplicatas:
    print("\n📋 Detalhes das duplicatas:")
    for i, dup in enumerate(list(duplicatas)[:10], 1):
        imagens_dup = ImagemProduto.objects.filter(imagem=dup['imagem'])
        print(f"  {i}. {dup['imagem']} - {dup['count']} cópias")
        for img in imagens_dup:
            print(f"     └─ ID {img.id}: {img.produto.descricao_produto}")

# ============================================================================
# 6. RESUMO FINAL
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 RESUMO FINAL DA VARREDURA")
print("=" * 80)

total_problemas = (
    len(problemas_arquivo) + 
    len(erros_associacao) + 
    len(problemas_anotacao) + 
    len(anotacoes_invalidas) + 
    duplicatas.count()
)

print(f"\n✅ Imagens de treino verificadas: {imagens_treino.count()}")
print(f"✅ Imagens anotadas verificadas: {imagens_anotadas.count()}")
print(f"✅ Anotações verificadas: {todas_anotacoes.count()}")
print(f"\n⚠️  TOTAL DE PROBLEMAS ENCONTRADOS: {total_problemas}")

print(f"\n📋 Detalhamento:")
print(f"   • Problemas com arquivos: {len(problemas_arquivo)}")
print(f"   • Erros de associação: {len(erros_associacao)}")
print(f"   • Problemas em anotações: {len(problemas_anotacao)}")
print(f"   • Anotações inválidas: {len(anotacoes_invalidas)}")
print(f"   • Duplicatas encontradas: {duplicatas.count()}")

if total_problemas == 0:
    print("\n✨ EXCELENTE! Nenhum problema encontrado! ✨")
else:
    print(f"\n⚠️  Recomendações de ação:")
    if len(problemas_arquivo) > 0:
        print(f"   • Remover ou recuperar {len(problemas_arquivo)} imagens corrompidas")
    if len(anotacoes_invalidas) > 0:
        print(f"   • Revisar {len(anotacoes_invalidas)} anotações com bbox inválidos")
    if duplicatas.count() > 0:
        print(f"   • Remover {duplicatas.count()} grupos de imagens duplicadas")

print("\n" + "=" * 80)
