"""
Exporta imagens e anotações do banco Django para dataset de treino
Prepara para data augmentation
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from pathlib import Path
import shutil

def exportar_dataset(pasta_destino='assets/dataset/train'):
    """
    Exporta imagens do banco para estrutura de pastas por produto
    """
    
    print("="*70)
    print("📤 EXPORTANDO DATASET DO BANCO DE DADOS")
    print("="*70)
    
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    # Buscar produtos com imagens
    produtos = ProdutoMae.objects.filter(imagens_treino__isnull=False).distinct()
    
    print(f"\n📦 Produtos encontrados: {produtos.count()}")
    
    total_imagens = 0
    
    for produto in produtos:
        print(f"\n{'='*70}")
        print(f"📦 {produto.descricao_produto}")
        print(f"{'='*70}")
        
        # Criar pasta do produto
        pasta_produto = pasta_destino / produto.descricao_produto
        pasta_produto.mkdir(exist_ok=True)
        
        # Buscar imagens do produto
        imagens = produto.imagens_treino.all()
        
        print(f"   📸 Imagens: {imagens.count()}")
        
        for idx, img in enumerate(imagens, 1):
            if not img.imagem:
                continue
            
            try:
                # Copiar imagem
                origem = Path(img.imagem.path)
                
                if not origem.exists():
                    print(f"   ⚠️ Imagem não encontrada: {origem}")
                    continue
                
                # Nome do arquivo
                extensao = origem.suffix
                nome_destino = f"img_{idx:03d}{extensao}"
                destino = pasta_produto / nome_destino
                
                shutil.copy2(origem, destino)
                total_imagens += 1
                
                print(f"   ✅ {nome_destino}")
                
            except Exception as e:
                print(f"   ❌ Erro ao copiar {img.imagem.name}: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ EXPORTAÇÃO CONCLUÍDA!")
    print(f"{'='*70}")
    print(f"📊 Total de imagens exportadas: {total_imagens}")
    print(f"📁 Dataset salvo em: {pasta_destino}")
    print(f"\n🎯 PRÓXIMO PASSO:")
    print(f"   python aumentar_dataset.py")
    print()


if __name__ == '__main__':
    exportar_dataset()
