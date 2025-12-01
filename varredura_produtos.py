#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from django.db.models import Count, Q

print("=" * 80)
print("🔍 VARREDURA DE PRODUTOS PROBLEMÁTICOS - BANCO INTEIRO")
print("=" * 80)

# ============================================================================
# 1. PRODUTOS SEM IMAGENS
# ============================================================================
print("\n1️⃣  PRODUTOS SEM IMAGENS")
print("-" * 80)

sem_imagens = ProdutoMae.objects.filter(imagens_treino__isnull=True).order_by('id')

print(f"Total: {sem_imagens.count()} produtos\n")

if sem_imagens.count() > 0:
    print("Primeiros 20:")
    for i, produto in enumerate(sem_imagens[:20], 1):
        status = "✅" if produto.ativo else "❌"
        preco = f"R$ {produto.preco}" if produto.preco > 0 else "R$ 0.00"
        print(f"  {i:2d}. {status} ID {produto.id:3d} - {produto.descricao_produto:50s} ({preco})")

# ============================================================================
# 2. PRODUTOS COM PREÇO ZERADO
# ============================================================================
print("\n\n2️⃣  PRODUTOS COM PREÇO ZERADO")
print("-" * 80)

preco_zero = ProdutoMae.objects.filter(preco=0).order_by('id')

print(f"Total: {preco_zero.count()} produtos\n")

if preco_zero.count() > 0:
    print("Lista completa:")
    for i, produto in enumerate(preco_zero, 1):
        total_imgs = produto.imagens_treino.count()
        status = "✅" if produto.ativo else "❌"
        print(f"  {i:2d}. {status} ID {produto.id:3d} - {produto.descricao_produto:50s} ({total_imgs} imagens)")

# ============================================================================
# 3. PRODUTOS INATIVOS
# ============================================================================
print("\n\n3️⃣  PRODUTOS INATIVOS")
print("-" * 80)

inativos = ProdutoMae.objects.filter(ativo=False).order_by('id')

print(f"Total: {inativos.count()} produtos\n")

if inativos.count() > 0:
    print("Primeiros 20:")
    for i, produto in enumerate(inativos[:20], 1):
        total_imgs = produto.imagens_treino.count()
        preco = f"R$ {produto.preco}" if produto.preco > 0 else "R$ 0.00"
        print(f"  {i:2d}. ID {produto.id:3d} - {produto.descricao_produto:50s} ({total_imgs} imgs, {preco})")

# ============================================================================
# 4. PRODUTOS COM INFORMAÇÕES INCOMPLETAS
# ============================================================================
print("\n\n4️⃣  PRODUTOS COM INFORMAÇÕES INCOMPLETAS")
print("-" * 80)

# Sem marca
sem_marca = ProdutoMae.objects.filter(Q(marca__isnull=True) | Q(marca='') | Q(marca='A definir')).count()

# Sem tipo
sem_tipo = ProdutoMae.objects.filter(Q(tipo__isnull=True) | Q(tipo='')).count()

print(f"Sem marca ou 'A definir': {sem_marca}")
print(f"Sem tipo: {sem_tipo}")

produtos_incompletos = ProdutoMae.objects.filter(
    Q(marca__in=['', 'A definir', None]) | 
    Q(tipo__isnull=True) | 
    Q(tipo='')
).distinct().order_by('id')

print(f"\nTotal de produtos com info incompleta: {produtos_incompletos.count()}\n")

if produtos_incompletos.count() > 0:
    print("Primeiros 15:")
    for i, produto in enumerate(produtos_incompletos[:15], 1):
        total_imgs = produto.imagens_treino.count()
        marca_display = produto.marca if produto.marca else "❌ SEM MARCA"
        tipo_display = produto.tipo if produto.tipo else "❌ SEM TIPO"
        print(f"  {i:2d}. ID {produto.id:3d} - {marca_display:20s} | {tipo_display:20s} | {total_imgs} imgs")

# ============================================================================
# 5. CANDIDATOS PARA LIMPEZA
# ============================================================================
print("\n\n5️⃣  CANDIDATOS PARA REMOÇÃO")
print("-" * 80)

# Produtos que devem ser removidos: inativos + sem preço + sem imagens
candidatos = ProdutoMae.objects.filter(
    ativo=False,
    preco=0,
    imagens_treino__isnull=True
).distinct().order_by('id')

print(f"Produtos (INATIVO + PREÇO ZERO + SEM IMAGENS): {candidatos.count()}\n")

if candidatos.count() > 0:
    print("Lista completa:")
    for i, produto in enumerate(candidatos, 1):
        print(f"  {i:2d}. ID {produto.id:3d} - {produto.descricao_produto}")

# ============================================================================
# 6. RESUMO FINAL
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 RESUMO GERAL")
print("=" * 80)

total = ProdutoMae.objects.count()
com_imagens = ProdutoMae.objects.exclude(imagens_treino__isnull=True).count()
ativos = ProdutoMae.objects.filter(ativo=True).count()

print(f"\n✅ Total de produtos: {total}")
print(f"🖼️  Com imagens: {com_imagens} ({com_imagens/total*100:.1f}%)")
print(f"❌ Sem imagens: {total - com_imagens} ({(total-com_imagens)/total*100:.1f}%)")
print(f"✅ Ativos: {ativos}")
print(f"❌ Inativos: {total - ativos}")

print(f"\n⚠️  PROBLEMAS ENCONTRADOS:")
print(f"   • Sem imagens: {sem_imagens.count()}")
print(f"   • Preço zero: {preco_zero.count()}")
print(f"   • Inativos: {inativos.count()}")
print(f"   • Info incompleta: {produtos_incompletos.count()}")
print(f"   • Candidatos remoção: {candidatos.count()}")

print("\n" + "=" * 80)
