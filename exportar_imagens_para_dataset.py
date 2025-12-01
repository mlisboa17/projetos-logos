"""
Exporta imagens do Django para a estrutura de dataset do Albumentations
"""
import os
import sys
import django
from pathlib import Path
import shutil

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count


def exportar_imagens():
    """Exporta imagens do banco para assets/dataset/train/"""
    
    print("\n" + "="*60)
    print("📤 EXPORTANDO IMAGENS DO BANCO PARA DATASET")
    print("="*60)
    
    # Buscar produtos com imagens
    produtos = ProdutoMae.objects.annotate(
        num_imagens=Count('imagens_treino')
    ).filter(num_imagens__gt=0).order_by('tipo', 'marca', 'descricao_produto')
    
    if not produtos.exists():
        print("\n❌ Nenhum produto com imagens encontrado no banco!")
        print("💡 As imagens estão em ImagemProduto.imagem (campo FileField)")
        print("💡 Verifique se as imagens foram importadas corretamente")
        return
    
    print(f"\n✅ {produtos.count()} produtos com imagens encontrados:\n")
    
    total_exportadas = 0
    dataset_base = Path('assets/dataset/train')
    dataset_base.mkdir(parents=True, exist_ok=True)
    
    for produto in produtos:
        # Nome da pasta do produto
        nome_produto = f"{produto.tipo} {produto.marca} {produto.descricao_produto}".strip().upper()
        pasta_produto = dataset_base / nome_produto
        pasta_produto.mkdir(parents=True, exist_ok=True)
        
        # Buscar imagens
        imagens = produto.imagens_treino.all()
        print(f"📦 {nome_produto}")
        print(f"   🖼️  {imagens.count()} imagens")
        
        contador = 0
        for img in imagens:
            if not img.imagem:
                continue
            
            # Caminho original
            src_path = Path(img.imagem.path)
            if not src_path.exists():
                print(f"   ⚠️  Imagem não encontrada: {src_path}")
                continue
            
            # Nome do arquivo de destino
            # Usar mesmo padrão dos arquivos .txt: anotada_{id}_{timestamp}
            timestamp = img.imagem.name.split('_')[-1].replace('.jpg', '').replace('.png', '')
            dst_filename = f"anotada_{img.id}_{timestamp}.jpg"
            dst_path = pasta_produto / dst_filename
            
            # Copiar imagem
            shutil.copy2(src_path, dst_path)
            contador += 1
            total_exportadas += 1
        
        print(f"   ✅ {contador} imagens exportadas para {pasta_produto}\n")
    
    print("="*60)
    print(f"✅ EXPORTAÇÃO CONCLUÍDA!")
    print(f"📊 Total: {total_exportadas} imagens")
    print(f"📁 Localização: {dataset_base.absolute()}")
    print("="*60)
    print("\n💡 Agora execute: python aumentar_dataset.py")
    print()


if __name__ == '__main__':
    try:
        exportar_imagens()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
