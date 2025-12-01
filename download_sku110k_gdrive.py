"""
Download SKU-110K do Google Drive (fonte oficial)
"""
import gdown
from pathlib import Path

def download_sku110k_gdrive():
    print("="*70)
    print("📦 DOWNLOAD SKU-110K - GOOGLE DRIVE (FONTE OFICIAL)")
    print("="*70)
    
    # IDs dos arquivos no Google Drive
    FILES = {
        'train_images_part1': '1iq5nLUbpPQqISoH9BvzKYKj-TgVIOKcN',
        'train_images_part2': '1LqnhHJ_EkDrL5-0HJ4Rq9DTFhI0U8Bv1',
        'test_images': '1s6HZfAOjdNSfmOIjLSKh3-z8GdKPRHfH',
        'annotations': '1sQQb3xOqfPRyBBBj6BqmPJtpfD0F3VH2'
    }
    
    dataset_dir = Path('datasets/sku110k')
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Destino: {dataset_dir.absolute()}")
    print("\n⚠️  ATENÇÃO:")
    print("   • Tamanho total: ~5.4 GB")
    print("   • 4 arquivos para baixar")
    print("   • Tempo: 15-40 minutos")
    
    continuar = input("\n▶️  Continuar? (s/N): ").strip().lower()
    
    if continuar != 's':
        print("\n❌ Cancelado")
        return
    
    try:
        # Instalar gdown se necessário
        try:
            import gdown
        except ImportError:
            print("\n📦 Instalando gdown...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'gdown'])
            import gdown
        
        # Download de cada arquivo
        for nome, file_id in FILES.items():
            output_file = dataset_dir / f'{nome}.zip'
            
            if output_file.exists():
                print(f"\n✅ {nome} já existe, pulando...")
                continue
            
            print(f"\n📥 Baixando: {nome}")
            url = f'https://drive.google.com/uc?id={file_id}'
            
            gdown.download(url, str(output_file), quiet=False)
            print(f"✅ {nome} baixado!")
        
        print("\n" + "="*70)
        print("✅ DOWNLOADS CONCLUÍDOS!")
        print("="*70)
        print(f"\n📁 Localização: {dataset_dir.absolute()}")
        print("\n💡 PRÓXIMO PASSO:")
        print("   Executar: python extrair_sku110k.py")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n💡 DOWNLOAD MANUAL:")
        print("   1. Acesse: https://github.com/eg4000/SKU110K_CVPR19")
        print("   2. Vá em 'Releases'")
        print("   3. Baixe os arquivos ZIP")
        print(f"   4. Extraia em: {dataset_dir.absolute()}")

if __name__ == '__main__':
    download_sku110k_gdrive()
