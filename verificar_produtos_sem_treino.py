"""
Script para identificar produtos sem imagens de treinamento
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count

def listar_produtos_sem_treino():
    """Lista todos os produtos que ainda não têm imagens de treinamento"""
    
    print("="*70)
    print("📊 ANÁLISE DE PRODUTOS - TREINAMENTO VERIFIK")
    print("="*70)
    
    # Produtos COM imagens
    produtos_com_imagens = ProdutoMae.objects.filter(
        imagens_treino__isnull=False
    ).distinct().annotate(
        total_imagens=Count('imagens_treino')
    ).order_by('marca', 'descricao_produto')
    
    # Produtos SEM imagens
    produtos_sem_imagens = ProdutoMae.objects.filter(
        imagens_treino__isnull=True
    ).order_by('marca', 'descricao_produto')
    
    # Estatísticas gerais
    total_produtos = ProdutoMae.objects.count()
    total_com_imagens = produtos_com_imagens.count()
    total_sem_imagens = produtos_sem_imagens.count()
    total_imagens = ImagemProduto.objects.count()
    
    print(f"\n📈 ESTATÍSTICAS GERAIS:")
    print(f"   Total de produtos no sistema: {total_produtos}")
    print(f"   ✅ Produtos COM imagens: {total_com_imagens} ({total_com_imagens/total_produtos*100:.1f}%)")
    print(f"   ❌ Produtos SEM imagens: {total_sem_imagens} ({total_sem_imagens/total_produtos*100:.1f}%)")
    print(f"   🖼️  Total de imagens: {total_imagens}")
    
    # Listar produtos com imagens
    if produtos_com_imagens.exists():
        print(f"\n✅ PRODUTOS JÁ TREINADOS ({total_com_imagens} produtos):")
        print("-" * 70)
        for i, produto in enumerate(produtos_com_imagens, 1):
            marca = produto.marca or "SEM MARCA"
            descricao = produto.descricao_produto or "SEM DESCRIÇÃO"
            print(f"   {i:2d}. [{produto.total_imagens:3d} imgs] {marca} - {descricao}")
    
    # Listar produtos sem imagens
    if produtos_sem_imagens.exists():
        print(f"\n❌ PRODUTOS AINDA NÃO TREINADOS ({total_sem_imagens} produtos):")
        print("-" * 70)
        
        # Agrupar por marca
        marcas = {}
        for produto in produtos_sem_imagens:
            marca = produto.marca or "SEM MARCA"
            if marca not in marcas:
                marcas[marca] = []
            marcas[marca].append(produto)
        
        contador = 1
        for marca, produtos in sorted(marcas.items()):
            print(f"\n   📦 {marca}:")
            for produto in produtos:
                descricao = produto.descricao_produto or "SEM DESCRIÇÃO"
                print(f"      {contador:3d}. {descricao}")
                contador += 1
    
    # Sugestões
    print("\n" + "="*70)
    print("💡 PRÓXIMOS PASSOS:")
    print("="*70)
    if produtos_sem_imagens.exists():
        print(f"   1. Use 'marcar_produtos_manual.py' para marcar produtos em fotos")
        print(f"   2. Use 'ensinar_modelo_interativo.py' para corrigir detecções")
        print(f"   3. Foque em produtos mais vendidos/importantes primeiro")
        print(f"   4. Meta sugerida: 20-30 imagens por produto")
    else:
        print(f"   ✅ Todos os produtos já possuem imagens de treinamento!")
        print(f"   💪 Continue adicionando mais imagens para melhorar a precisão")
    
    print("\n" + "="*70)
    
    return {
        'total_produtos': total_produtos,
        'com_imagens': total_com_imagens,
        'sem_imagens': total_sem_imagens,
        'total_imagens': total_imagens
    }

if __name__ == '__main__':
    listar_produtos_sem_treino()
