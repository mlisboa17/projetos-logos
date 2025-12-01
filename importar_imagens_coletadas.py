"""
Importa imagens coletadas pelos usuários para o dataset de treinamento
Organiza por produto e prepara para YOLO
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

def importar_imagens_coletadas():
    print("="*70)
    print("📥 IMPORTAR IMAGENS DO COLETOR DE PRODUTOS")
    print("="*70)
    
    # Pastas de origem
    pastas_origem = [
        Path('dados_coleta'),
        Path('media/produtos')
    ]
    
    # Pasta de destino
    dataset_train = Path('assets/dataset/train')
    
    print(f"\n📁 Destino: {dataset_train.absolute()}")
    print("\n🔍 Procurando imagens nas pastas de coleta...")
    
    total_encontradas = 0
    produtos_encontrados = {}
    
    # Buscar em todas as pastas de origem
    for pasta_origem in pastas_origem:
        if not pasta_origem.exists():
            print(f"   ⚠️  {pasta_origem} não existe, pulando...")
            continue
        
        print(f"\n📂 Escaneando: {pasta_origem}")
        
        # Buscar por subpastas de produtos
        for subpasta in pasta_origem.rglob('*'):
            if not subpasta.is_dir():
                continue
            
            # Buscar imagens na subpasta
            imagens = list(subpasta.glob('*.jpg')) + list(subpasta.glob('*.jpeg')) + list(subpasta.glob('*.png'))
            
            if imagens:
                nome_produto = subpasta.name.upper()
                
                if nome_produto not in produtos_encontrados:
                    produtos_encontrados[nome_produto] = []
                
                produtos_encontrados[nome_produto].extend(imagens)
                total_encontradas += len(imagens)
                
                print(f"   ✅ {nome_produto}: {len(imagens)} imagens")
    
    if total_encontradas == 0:
        print("\n❌ Nenhuma imagem encontrada nas pastas de coleta!")
        print("\n💡 DICA: Coloque imagens organizadas em subpastas por produto:")
        print("   dados_coleta/")
        print("   ├── COCA_COLA/")
        print("   │   ├── foto1.jpg")
        print("   │   └── foto2.jpg")
        print("   └── HEINEKEN/")
        print("       ├── foto1.jpg")
        print("       └── foto2.jpg")
        return
    
    print(f"\n📊 Total encontrado: {total_encontradas} imagens de {len(produtos_encontrados)} produtos")
    
    # Perguntar se quer importar
    print("\n" + "="*70)
    continuar = input("▶️  Importar essas imagens para o dataset? (s/N): ").strip().lower()
    
    if continuar != 's':
        print("\n❌ Importação cancelada")
        return
    
    # Importar imagens
    total_importadas = 0
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for produto, imagens in produtos_encontrados.items():
        # Criar pasta do produto no dataset
        pasta_produto = dataset_train / produto
        pasta_produto.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📦 Importando {produto}...")
        
        for idx, img_path in enumerate(imagens, 1):
            # Nome do arquivo de destino
            nome_destino = f"coleta_{timestamp}_{idx}{img_path.suffix}"
            destino = pasta_produto / nome_destino
            
            # Copiar imagem
            shutil.copy2(img_path, destino)
            
            # Criar anotação YOLO simples (produto ocupa 90% da imagem)
            # Assumindo que o produto está centralizado
            txt_destino = destino.with_suffix('.txt')
            
            # Buscar o ID da classe do produto
            categorias = sorted([d.name for d in dataset_train.iterdir() if d.is_dir()])
            
            try:
                class_id = categorias.index(produto)
            except ValueError:
                class_id = len(categorias) - 1  # Última classe
            
            with open(txt_destino, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 0.9 0.9\n")
            
            total_importadas += 1
        
        print(f"   ✅ {len(imagens)} imagens importadas")
    
    print("\n" + "="*70)
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print("="*70)
    print(f"\n📊 Total importado: {total_importadas} imagens")
    print(f"📁 Localização: {dataset_train.absolute()}")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. python aumentar_dataset.py (aplicar data augmentation)")
    print("   2. python treinar_modelo_yolo.py (retreinar modelo)")
    
    # Verificar total atual no dataset
    total_dataset = len(list(dataset_train.rglob('*.jpg'))) + len(list(dataset_train.rglob('*.png')))
    print(f"\n📈 Dataset atual: {total_dataset} imagens")

if __name__ == '__main__':
    importar_imagens_coletadas()
