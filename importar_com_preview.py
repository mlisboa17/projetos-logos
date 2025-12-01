"""
Importa imagens coletadas COM PREVIEW e confirmação por produto
Mostra amostras antes de importar
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

def mostrar_preview_produto(produto, imagens, max_preview=9):
    """Mostra grid com preview das imagens do produto"""
    print(f"\n{'='*70}")
    print(f"🖼️  PREVIEW: {produto}")
    print(f"📊 Total de imagens: {len(imagens)}")
    print(f"{'='*70}")
    
    # Selecionar até 9 imagens aleatórias para preview
    import random
    imagens_preview = random.sample(imagens, min(max_preview, len(imagens)))
    
    # Criar grid de imagens
    thumbnails = []
    
    for img_path in imagens_preview:
        try:
            img = cv2.imread(str(img_path))
            if img is not None:
                # Redimensionar para thumbnail
                height, width = img.shape[:2]
                scale = 200 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                thumbnail = cv2.resize(img, (new_width, new_height))
                
                # Adicionar borda
                thumbnail = cv2.copyMakeBorder(
                    thumbnail, 5, 5, 5, 5,
                    cv2.BORDER_CONSTANT,
                    value=(255, 255, 255)
                )
                
                thumbnails.append(thumbnail)
        except Exception as e:
            continue
    
    if thumbnails:
        # Organizar em grid 3x3
        rows = []
        for i in range(0, len(thumbnails), 3):
            row_imgs = thumbnails[i:i+3]
            
            # Preencher linha se necessário
            while len(row_imgs) < 3:
                blank = np.ones_like(row_imgs[0]) * 255
                row_imgs.append(blank)
            
            # Igualar alturas
            max_h = max(img.shape[0] for img in row_imgs)
            row_imgs_padded = []
            for img in row_imgs:
                if img.shape[0] < max_h:
                    pad = max_h - img.shape[0]
                    img = cv2.copyMakeBorder(img, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                row_imgs_padded.append(img)
            
            row = np.hstack(row_imgs_padded)
            rows.append(row)
        
        # Igualar larguras
        if rows:
            max_w = max(row.shape[1] for row in rows)
            rows_padded = []
            for row in rows:
                if row.shape[1] < max_w:
                    pad = max_w - row.shape[1]
                    row = cv2.copyMakeBorder(row, 0, 0, 0, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                rows_padded.append(row)
            
            grid = np.vstack(rows_padded)
            
            # Adicionar título
            title_height = 40
            title_img = np.ones((title_height, grid.shape[1], 3), dtype=np.uint8) * 255
            cv2.putText(title_img, f"{produto} - {len(imagens)} imagens", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            final_img = np.vstack([title_img, grid])
            
            # Mostrar
            window_name = f"Preview - {produto}"
            cv2.imshow(window_name, final_img)
            cv2.waitKey(500)  # Mostrar por 500ms
    
    # Listar primeiras 5 imagens
    print(f"\n📸 Exemplos de arquivos:")
    for i, img_path in enumerate(imagens[:5], 1):
        print(f"   {i}. {img_path.name}")
    
    if len(imagens) > 5:
        print(f"   ... e mais {len(imagens) - 5} imagens")

def importar_imagens_coletadas_com_preview():
    print("="*70)
    print("📥 IMPORTAR IMAGENS DO COLETOR - COM PREVIEW")
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
    
    if total_encontradas == 0:
        print("\n❌ Nenhuma imagem encontrada!")
        return
    
    print(f"\n📊 Total encontrado: {total_encontradas} imagens de {len(produtos_encontrados)} produtos")
    
    # Preview e confirmação POR PRODUTO
    produtos_aprovados = {}
    
    for produto, imagens in produtos_encontrados.items():
        # Mostrar preview
        mostrar_preview_produto(produto, imagens)
        
        # Perguntar
        print(f"\n❓ Importar {len(imagens)} imagens de {produto}?")
        print("   s = Sim, importar")
        print("   n = Não, pular este produto")
        print("   r = Renomear produto antes de importar")
        print("   q = Cancelar tudo e sair")
        
        resposta = input("\n▶️  Escolha (s/n/r/q): ").strip().lower()
        
        # Fechar janela de preview
        cv2.destroyAllWindows()
        
        if resposta == 'q':
            print("\n❌ Importação cancelada")
            return
        elif resposta == 'r':
            novo_nome = input(f"   Digite o novo nome para '{produto}': ").strip().upper()
            if novo_nome:
                produtos_aprovados[novo_nome] = imagens
                print(f"   ✅ '{produto}' será importado como '{novo_nome}'")
        elif resposta == 's':
            produtos_aprovados[produto] = imagens
            print(f"   ✅ {produto} aprovado")
        else:
            print(f"   ⏭️  {produto} pulado")
    
    if not produtos_aprovados:
        print("\n❌ Nenhum produto foi aprovado para importação")
        return
    
    # Importar produtos aprovados
    print("\n" + "="*70)
    print("📦 IMPORTANDO PRODUTOS APROVADOS")
    print("="*70)
    
    total_importadas = 0
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for produto, imagens in produtos_aprovados.items():
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
            
            # Criar anotação YOLO simples
            txt_destino = destino.with_suffix('.txt')
            
            # Buscar o ID da classe do produto
            categorias = sorted([d.name for d in dataset_train.iterdir() if d.is_dir()])
            
            try:
                class_id = categorias.index(produto)
            except ValueError:
                class_id = len(categorias) - 1
            
            with open(txt_destino, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 0.9 0.9\n")
            
            total_importadas += 1
        
        print(f"   ✅ {len(imagens)} imagens importadas")
    
    cv2.destroyAllWindows()
    
    print("\n" + "="*70)
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print("="*70)
    print(f"\n📊 Total importado: {total_importadas} imagens")
    print(f"📁 Localização: {dataset_train.absolute()}")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. python aumentar_dataset.py (aplicar data augmentation)")
    print("   2. python treinar_modelo_yolo.py (retreinar modelo)")

if __name__ == '__main__':
    try:
        importar_imagens_coletadas_com_preview()
    except KeyboardInterrupt:
        print("\n\n⚠️  Importação cancelada pelo usuário")
        cv2.destroyAllWindows()
