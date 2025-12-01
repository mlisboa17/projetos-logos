"""
Download do SKU-110K Dataset
Dataset com 11.762 imagens de produtos de supermercado
"""
import os
import requests
from pathlib import Path
import zipfile
from tqdm import tqdm

# URLs do dataset SKU-110K
URLS = {
    'train_images': 'https://github.com/eg4000/SKU110K_CVPR19/releases/download/v1.0/SKU110K_fixed.zip',
    'annotations': 'https://github.com/eg4000/SKU110K_CVPR19/raw/master/annotations/annotations_train.csv'
}

def download_file(url, destino):
    """Download com barra de progresso"""
    print(f"\n📥 Baixando de: {url}")
    print(f"📁 Salvando em: {destino}")
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destino, 'wb') as f, tqdm(
        desc=destino.name,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))
    
    print(f"✅ Download concluído: {destino}")

def extrair_zip(arquivo_zip, destino):
    """Extrai arquivo ZIP"""
    print(f"\n📦 Extraindo {arquivo_zip}...")
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        zip_ref.extractall(destino)
    
    print(f"✅ Extração concluída em: {destino}")

def main():
    print("="*70)
    print("📦 DOWNLOAD DO SKU-110K DATASET")
    print("="*70)
    print("\n⚠️  ATENÇÃO:")
    print("   • Tamanho: ~5.4 GB")
    print("   • Tempo estimado: 10-30 minutos (depende da internet)")
    print("   • Espaço necessário: 10 GB livre")
    
    continuar = input("\n▶️  Deseja continuar? (s/N): ").strip().lower()
    
    if continuar != 's':
        print("\n❌ Download cancelado pelo usuário")
        return
    
    # Criar pasta de destino no projeto
    dataset_dir = Path('datasets/sku110k')
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Salvando em: {dataset_dir.absolute()}")
    
    try:
        # 1. Download das imagens
        zip_file = dataset_dir / 'SKU110K_fixed.zip'
        
        if not zip_file.exists():
            download_file(URLS['train_images'], zip_file)
        else:
            print(f"\n✅ Arquivo ZIP já existe: {zip_file}")
        
        # 2. Extrair ZIP
        images_dir = dataset_dir / 'images'
        if not images_dir.exists():
            extrair_zip(zip_file, dataset_dir)
        else:
            print(f"\n✅ Imagens já extraídas em: {images_dir}")
        
        # 3. Download das anotações
        annotations_file = dataset_dir / 'annotations_train.csv'
        
        if not annotations_file.exists():
            download_file(URLS['annotations'], annotations_file)
        else:
            print(f"\n✅ Anotações já existem: {annotations_file}")
        
        # Verificar resultado
        print("\n" + "="*70)
        print("✅ DOWNLOAD CONCLUÍDO!")
        print("="*70)
        
        if images_dir.exists():
            total_imgs = len(list(images_dir.rglob('*.jpg')))
            print(f"\n📊 Total de imagens baixadas: {total_imgs}")
        
        print(f"\n📁 Localização: {dataset_dir.absolute()}")
        print(f"📄 Anotações: {annotations_file}")
        
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Converter anotações CSV para formato YOLO")
        print("   2. Mesclar com seu dataset atual")
        print("   3. Retreinar modelo YOLO")
        
        # Limpar ZIP para economizar espaço
        if zip_file.exists():
            remover = input("\n🗑️  Remover arquivo ZIP para economizar espaço? (s/N): ").strip().lower()
            if remover == 's':
                zip_file.unlink()
                print(f"✅ {zip_file.name} removido")
        
    except Exception as e:
        print(f"\n❌ Erro durante download: {e}")
        print("\n💡 Tente novamente ou baixe manualmente de:")
        print(f"   {URLS['train_images']}")

if __name__ == '__main__':
    main()
