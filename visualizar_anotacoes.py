import os
import json
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont

def visualizar_exportacoes(pasta_base):
    """Visualiza imagens com bounding boxes das exportações"""
    
    pasta_base = Path(pasta_base)
    pastas_exportacao = [d for d in pasta_base.iterdir() if d.is_dir() and d.name.startswith('exportacao_')]
    
    print(f"📦 Encontradas {len(pastas_exportacao)} exportações\n")
    
    # Cores para diferentes produtos
    cores = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', 
        '#00FFFF', '#FFA500', '#800080', '#FFC0CB', '#A52A2A'
    ]
    
    for pasta_exp in pastas_exportacao:
        dados_json = pasta_exp / "dados_exportacao.json"
        produtos_json = pasta_exp / "produtos.json"
        pasta_imagens = pasta_exp / "imagens"
        
        if not dados_json.exists():
            continue
            
        print(f"\n🔍 {pasta_exp.name}")
        print("="*60)
        
        # Carregar produtos
        with open(produtos_json, 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            produtos_dict = {p['id']: p for p in produtos}
        
        # Carregar dados
        with open(dados_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Processar cada imagem
        for img_data in dados['imagens']:
            arquivo = img_data['arquivo']
            anotacoes = img_data.get('anotacoes', [])
            
            if not anotacoes:
                continue
                
            caminho_img = pasta_imagens / arquivo
            
            if not caminho_img.exists():
                continue
            
            print(f"\n📷 {arquivo}")
            print(f"   Anotações: {len(anotacoes)}")
            
            # Abrir imagem
            img = Image.open(caminho_img)
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Desenhar cada bounding box
            for idx, anotacao in enumerate(anotacoes):
                produto_id = anotacao['produto_id']
                produto = produtos_dict.get(produto_id, {})
                produto_nome = produto.get('nome', f'Produto {produto_id}')
                
                # Converter coordenadas normalizadas para pixels
                x_center = anotacao['x'] * width
                y_center = anotacao['y'] * height
                bbox_width = anotacao['width'] * width
                bbox_height = anotacao['height'] * height
                
                # Calcular cantos da caixa
                x1 = int(x_center - bbox_width / 2)
                y1 = int(y_center - bbox_height / 2)
                x2 = int(x_center + bbox_width / 2)
                y2 = int(y_center + bbox_height / 2)
                
                # Cor para este produto
                cor = cores[idx % len(cores)]
                
                # Desenhar retângulo
                draw.rectangle([x1, y1, x2, y2], outline=cor, width=3)
                
                # Desenhar label
                label = f"{produto_nome}"
                
                # Fundo para o texto
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    font = ImageFont.load_default()
                
                # Pegar tamanho do texto
                bbox_text = draw.textbbox((x1, y1-25), label, font=font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]
                
                # Fundo do label
                draw.rectangle([x1, y1-text_height-8, x1+text_width+8, y1], fill=cor)
                
                # Texto
                draw.text((x1+4, y1-text_height-4), label, fill='white', font=font)
                
                print(f"   ✅ {produto_nome}: [{x1},{y1},{x2},{y2}]")
            
            # Salvar imagem anotada
            output_dir = Path('media/visualizacoes_bbox')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"bbox_{pasta_exp.name}_{arquivo}"
            img.save(output_path)
            
            print(f"   💾 Salvo em: {output_path}")
    
    print("\n" + "="*60)
    print("✅ Visualizações criadas em: media/visualizacoes_bbox/")
    print("="*60)


if __name__ == '__main__':
    pasta = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\FAMILIA HEINEKEN"
    visualizar_exportacoes(pasta)
