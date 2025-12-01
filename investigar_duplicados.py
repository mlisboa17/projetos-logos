#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("=" * 80)
print("🔍 INVESTIGAÇÃO - PRODUTOS DEVASSA DUPLICADOS")
print("=" * 80)

# Buscar todos os produtos com DEVASSA
devassas = ProdutoMae.objects.filter(
    descricao_produto__icontains='DEVASSA'
).order_by('id')

print(f"\nTotal de produtos DEVASSA: {devassas.count()}\n")

# Agrupar por nome similar
grupos = {}

for produto in devassas:
    nome = produto.descricao_produto.upper()
    
    # Normalizar nome para comparação
    nome_norm = nome.replace('CERVEJA ', '').replace('LATA', 'LATA').replace('LATÃO', 'LATAO').strip()
    
    if nome_norm not in grupos:
        grupos[nome_norm] = []
    
    grupos[nome_norm].append(produto)

print("📋 AGRUPAMENTO POR SIMILARIDADE:\n")

for nome_norm, produtos_grupo in sorted(grupos.items()):
    if len(produtos_grupo) > 1:
        print(f"🚨 DUPLICADOS - {nome_norm}:")
    else:
        print(f"✅ ÚNICO - {nome_norm}:")
    
    for produto in produtos_grupo:
        total_imgs = produto.imagens_treino.count()
        print(f"   ID {produto.id:3d}: {produto.descricao_produto}")
        print(f"             Marca: {produto.marca}")
        print(f"             Tipo: {produto.tipo}")
        print(f"             Preço: R$ {produto.preco}")
        print(f"             Imagens: {total_imgs}")
        print()

# Listar todos com detalhes
print("\n" + "=" * 80)
print("📊 LISTA COMPLETA COM DETALHES")
print("=" * 80 + "\n")

for produto in devassas:
    total_imgs = produto.imagens_treino.count()
    status = "✅ ATIVO" if produto.ativo else "❌ INATIVO"
    
    print(f"ID {produto.id}")
    print(f"   Nome: {produto.descricao_produto}")
    print(f"   Marca: {produto.marca}")
    print(f"   Tipo: {produto.tipo}")
    print(f"   Preço: R$ {produto.preco}")
    print(f"   Status: {status}")
    print(f"   Imagens: {total_imgs}")
    print()

# Identificar quais podem ser removidos
print("\n" + "=" * 80)
print("🗑️  CANDIDATOS PARA REMOÇÃO (INATIVOS/VAZIOS)")
print("=" * 80 + "\n")

para_remover = []

for produto in devassas:
    total_imgs = produto.imagens_treino.count()
    
    # Marcar se: inativo OU sem imagens OU preço zero
    if not produto.ativo or total_imgs == 0 or produto.preco == 0:
        para_remover.append(produto)
        print(f"ID {produto.id}: {produto.descricao_produto}")
        print(f"   Status: {'INATIVO' if not produto.ativo else 'ATIVO'}")
        print(f"   Preço: R$ {produto.preco}")
        print(f"   Imagens: {total_imgs}")
        print(f"   → PODE SER REMOVIDO")
        print()

print("\n" + "=" * 80)
print("💡 RECOMENDAÇÕES")
print("=" * 80)
print(f"""
1. Verificar se {len(para_remover)} produtos duplicados podem ser removidos
2. Manter apenas produtos com:
   - Nome diferente/claro
   - Informações corretas (marca, tipo, preço)
   - Ou imagens associadas
3. Consolidar imagens em produtos principais
""")

print("=" * 80)
