#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("=" * 80)
print("🗑️  REMOVENDO PRODUTOS DEVASSA DUPLICADOS")
print("=" * 80)

# Produtos a remover
para_remover = [180, 181]

print(f"\nRemovendo {len(para_remover)} produtos duplicados:\n")

for prod_id in para_remover:
    try:
        produto = ProdutoMae.objects.get(id=prod_id)
        nome = produto.descricao_produto
        
        print(f"❌ Removendo ID {prod_id}: {nome}")
        
        # Deletar
        produto.delete()
        
        print(f"   ✅ Removido com sucesso")
    except ProdutoMae.DoesNotExist:
        print(f"⚠️  ID {prod_id} não encontrado")
    except Exception as e:
        print(f"❌ Erro ao remover ID {prod_id}: {str(e)}")

print("\n" + "=" * 80)
print("✅ LIMPEZA CONCLUÍDA")
print("=" * 80)

# Mostrar produtos Devassa restantes
print("\nProdutos DEVASSA restantes:\n")

devassas = ProdutoMae.objects.filter(descricao_produto__icontains='DEVASSA').order_by('id')

for produto in devassas:
    total_imgs = produto.imagens_treino.count()
    print(f"ID {produto.id}: {produto.descricao_produto} - {total_imgs} imagens")

print("\n" + "=" * 80)
