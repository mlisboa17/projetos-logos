#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("=" * 80)
print("🗑️  REMOVENDO PRODUTOS COM PREÇO ZERO")
print("=" * 80)

# Produtos com preço zero
preco_zero = ProdutoMae.objects.filter(preco=0)

print(f"\nTotal de produtos a remover: {preco_zero.count()}\n")

removidos = 0

for produto in preco_zero:
    try:
        nome = produto.descricao_produto
        print(f"❌ Removendo ID {produto.id}: {nome}")
        
        # Deletar
        produto.delete()
        removidos += 1
        
        print(f"   ✅ Removido com sucesso")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)[:50]}")

print("\n" + "=" * 80)
print(f"✅ TOTAL REMOVIDO: {removidos} produtos")
print("=" * 80)

# Verificar novamente
preco_zero_agora = ProdutoMae.objects.filter(preco=0).count()

print(f"\nProdutos com preço zero restantes: {preco_zero_agora}")

if preco_zero_agora == 0:
    print("✨ PERFEITO! Nenhum produto com preço zero!")
else:
    print(f"⚠️  Ainda existem {preco_zero_agora} produtos com preço zero")

total_agora = ProdutoMae.objects.count()
print(f"\nTotal de produtos na base: {total_agora}")

print("\n" + "=" * 80)
