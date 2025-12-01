"""
Clone do repositório SKU-110K direto do GitHub
Mais rápido que download manual
"""
import subprocess
from pathlib import Path
import os

def clonar_sku110k():
    print("="*70)
    print("📦 CLONE DO SKU-110K DATASET VIA GIT")
    print("="*70)
    
    # Pasta no OneDrive
    onedrive_path = Path(r'C:\Users\gabri\OneDrive')
    destino = onedrive_path / 'Datasets' / 'SKU110K'
    
    print(f"\n📁 Destino: {destino}")
    print("☁️  Será sincronizado automaticamente no OneDrive")
    
    # URL do repositório
    repo_url = "https://github.com/eg4000/SKU110K_CVPR19.git"
    
    print(f"\n📥 Clonando de: {repo_url}")
    print("\n⚠️  ATENÇÃO:")
    print("   • Requer Git instalado")
    print("   • Tamanho: ~5.4 GB")
    print("   • Tempo: 10-30 minutos")
    
    continuar = input("\n▶️  Continuar? (s/N): ").strip().lower()
    
    if continuar != 's':
        print("\n❌ Cancelado")
        return
    
    try:
        # Criar pasta pai
        destino.parent.mkdir(parents=True, exist_ok=True)
        
        # Clonar repositório
        print(f"\n🔄 Clonando repositório...")
        print("   (isso pode demorar bastante...)")
        
        resultado = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, str(destino)],
            capture_output=True,
            text=True
        )
        
        if resultado.returncode == 0:
            print("\n✅ Clone concluído!")
            print(f"📁 Localização: {destino}")
            
            # Verificar conteúdo
            if destino.exists():
                total_imgs = len(list(destino.rglob('*.jpg')))
                total_txt = len(list(destino.rglob('*.txt')))
                total_csv = len(list(destino.rglob('*.csv')))
                
                print(f"\n📊 Arquivos baixados:")
                print(f"   • Imagens: {total_imgs}")
                print(f"   • Anotações TXT: {total_txt}")
                print(f"   • Anotações CSV: {total_csv}")
            
            print("\n💡 PRÓXIMO PASSO:")
            print("   Executar: python converter_sku110k_para_yolo.py")
        else:
            print(f"\n❌ Erro ao clonar: {resultado.stderr}")
            print("\n💡 Alternativa: Baixar manualmente de:")
            print(f"   https://github.com/eg4000/SKU110K_CVPR19/releases")
            
    except FileNotFoundError:
        print("\n❌ Git não encontrado!")
        print("\n💡 SOLUÇÕES:")
        print("   1. Instalar Git: https://git-scm.com/download/win")
        print("   2. Ou usar: python download_sku110k.py (download direto)")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == '__main__':
    clonar_sku110k()
