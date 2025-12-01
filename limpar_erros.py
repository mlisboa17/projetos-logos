#!/usr/bin/env python
import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from django.db.models import Count

print("=" * 80)
print("🧹 LIMPEZA AUTOMÁTICA DE ERROS")
print("=" * 80)

# ============================================================================
# 1. REMOVER IMAGENS CORROMPIDAS (< 10KB)
# ============================================================================
print("\n1️⃣  REMOVENDO IMAGENS CORROMPIDAS")
print("-" * 80)

imagens_pequenas = []
removidas = 0

for img in ImagemProduto.objects.all():
    try:
        if not img.imagem:
            continue
        
        arquivo_path = img.imagem.path
        if os.path.exists(arquivo_path):
            tamanho_kb = os.path.getsize(arquivo_path) / 1024
            
            # Remover se < 10KB
            if tamanho_kb < 10:
                print(f"  ❌ Removendo: ID {img.id} ({tamanho_kb:.2f}KB) - {img.produto.descricao_produto}")
                imagens_pequenas.append({
                    'id': img.id,
                    'produto': img.produto.descricao_produto,
                    'tamanho': tamanho_kb
                })
                
                # Deletar arquivo e registro
                img.imagem.delete(save=False)
                img.delete()
                removidas += 1
    except Exception as e:
        print(f"  ⚠️  Erro ao processar ID {img.id}: {str(e)[:50]}")

print(f"\n✅ Total de imagens corrompidas removidas: {removidas}")

# ============================================================================
# 2. LIMPAR DUPLICATAS (MANTER APENAS UMA CÓPIA POR ARQUIVO)
# ============================================================================
print("\n\n2️⃣  REMOVENDO IMAGENS DUPLICADAS")
print("-" * 80)

# Buscar imagens com mesmo arquivo
duplicatas = ImagemProduto.objects.values('imagem').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

duplicatas_removidas = 0

for dup in duplicatas:
    imagens_dup = ImagemProduto.objects.filter(imagem=dup['imagem']).order_by('id')
    
    # Manter a primeira, remover as outras
    imagens_para_remover = list(imagens_dup[1:])
    
    print(f"  📋 {dup['imagem']}: {dup['count']} cópias")
    
    for img_remover in imagens_para_remover:
        print(f"     └─ ❌ Removendo ID {img_remover.id} ({img_remover.produto.descricao_produto})")
        img_remover.delete()
        duplicatas_removidas += 1

print(f"\n✅ Total de imagens duplicadas removidas: {duplicatas_removidas}")

# ============================================================================
# 3. RELATÓRIO FINAL
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 RESUMO DA LIMPEZA")
print("=" * 80)

print(f"\n✅ Imagens removidas por corrupção: {removidas}")
print(f"✅ Duplicatas removidas: {duplicatas_removidas}")
print(f"✅ Total removido: {removidas + duplicatas_removidas}")

# Novo total
novo_total = ImagemProduto.objects.count()
print(f"\n📈 Imagens restantes: {novo_total}")

print("\n" + "=" * 80)
print("✨ Limpeza concluída! ✨")
print("=" * 80)
