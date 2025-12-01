"""
Script para testar o reconhecimento de imagens da IA
IMPORTANTE: Cada imagem pode ter VARIOS produtos!
Usamos YOLO para detectar cada BBox e analisar individualmente.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente
from verifik.models import ProdutoMae
import cv2

# Importar funcoes
from verifik.views_coleta import (
    detectar_codigo_barras, 
    classificar_forma_produto, 
    extrair_texto_ocr, 
    sugerir_produto_ia,
    get_yolo_model
)


def testar_imagem_com_multiplos_produtos(imagem_obj):
    """
    Testa uma imagem que pode conter VARIOS produtos.
    Usa YOLO para detectar cada bbox e analisa cada produto individualmente.
    """
    print("="*70)
    print(f"🖼️  IMAGEM ID: {imagem_obj.id}")
    print(f"📁 Path: {imagem_obj.imagem.path}")
    print("="*70)
    
    # Carregar imagem
    img = cv2.imread(imagem_obj.imagem.path)
    if img is None:
        print("❌ ERRO: Nao conseguiu carregar imagem!")
        return []
    
    height, width = img.shape[:2]
    print(f"📐 Dimensoes: {width}x{height} pixels\n")
    
    # Carregar modelo YOLO
    print("🤖 Carregando modelo YOLO...")
    model = get_yolo_model()
    
    # Detectar objetos (cada objeto = 1 produto potencial)
    print("🔍 Detectando produtos na imagem...\n")
    results = model(img, conf=0.25, iou=0.45)
    
    produtos_db = list(ProdutoMae.objects.all())
    produtos_encontrados = []
    
    for result in results:
        boxes = result.boxes
        total_objetos = len(boxes)
        
        if total_objetos == 0:
            print("❌ Nenhum produto detectado pelo YOLO!")
            return []
        
        print(f"📦 {total_objetos} PRODUTO(S) DETECTADO(S) NA IMAGEM")
        print("-"*70)
        
        for i, box in enumerate(boxes):
            conf_yolo = float(box.conf[0].cpu().numpy())
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Calcular bbox normalizado (para salvar no banco)
            x_center = ((x1 + x2) / 2) / width
            y_center = ((y1 + y2) / 2) / height
            bbox_width = (x2 - x1) / width
            bbox_height = (y2 - y1) / height
            
            print(f"\n┌─────────────────────────────────────────────────────────────────┐")
            print(f"│  PRODUTO {i+1}/{total_objetos}                                              │")
            print(f"└─────────────────────────────────────────────────────────────────┘")
            print(f"  📍 BBox pixels: ({x1}, {y1}) -> ({x2}, {y2})")
            print(f"  📍 BBox normalizado: x={x_center:.3f} y={y_center:.3f} w={bbox_width:.3f} h={bbox_height:.3f}")
            print(f"  🎯 Confianca YOLO: {conf_yolo:.1%}")
            
            # Cortar apenas a regiao do bbox (produto individual)
            bbox_img = img[y1:y2, x1:x2]
            
            if bbox_img.size == 0:
                print("  ⚠️  BBox vazio, pulando...")
                continue
            
            # === ANALISAR O PRODUTO DENTRO DO BBOX ===
            
            # 1. Detectar codigo de barras
            codigo, tipo = detectar_codigo_barras(bbox_img)
            if codigo:
                print(f"  🏷️  Codigo de barras: {codigo} ({tipo})")
            else:
                print(f"  🏷️  Codigo de barras: Nao detectado")
            
            # 2. Classificar forma/recipiente
            forma = classificar_forma_produto(bbox_img)
            print(f"  📦 Forma/Recipiente: {forma}")
            
            # 3. Extrair texto OCR
            texto = extrair_texto_ocr(bbox_img)
            if texto:
                textos_validos = [t for t in texto if t.strip()]
                print(f"  📝 OCR ({len(textos_validos)} textos):")
                for t in textos_validos[:5]:
                    print(f"      • {t}")
                if len(textos_validos) > 5:
                    print(f"      ... e mais {len(textos_validos)-5}")
            else:
                print(f"  📝 OCR: Nenhum texto detectado")
            
            # 4. SUGERIR PRODUTO baseado em tudo
            prod_id, conf, razao = sugerir_produto_ia(texto, forma, produtos_db, codigo)
            
            print(f"\n  {'='*50}")
            if prod_id:
                prod = ProdutoMae.objects.get(id=prod_id)
                print(f"  ✅ SUGESTAO DA IA:")
                print(f"     🏷️  {prod.descricao_produto}")
                print(f"     📊 Confianca: {conf}%")
                print(f"     💡 Razao: {razao}")
                
                produtos_encontrados.append({
                    'bbox': {
                        'x': x_center,
                        'y': y_center,
                        'width': bbox_width,
                        'height': bbox_height,
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
                    },
                    'produto_id': prod_id,
                    'produto_nome': prod.descricao_produto,
                    'confianca': conf,
                    'razao': razao,
                    'codigo_barras': codigo,
                    'forma': forma,
                    'ocr': texto
                })
            else:
                print(f"  ❌ IA NAO CONSEGUIU IDENTIFICAR")
                print(f"     💡 Razao: {razao}")
                
                produtos_encontrados.append({
                    'bbox': {
                        'x': x_center,
                        'y': y_center,
                        'width': bbox_width,
                        'height': bbox_height,
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
                    },
                    'produto_id': None,
                    'produto_nome': 'DESCONHECIDO',
                    'confianca': 0,
                    'razao': razao,
                    'codigo_barras': codigo,
                    'forma': forma,
                    'ocr': texto
                })
    
    # Resumo final
    print("\n" + "="*70)
    print("📊 RESUMO DA IMAGEM")
    print("="*70)
    print(f"Total de produtos detectados: {len(produtos_encontrados)}")
    
    identificados = [p for p in produtos_encontrados if p['produto_id']]
    print(f"Identificados com sucesso: {len(identificados)}")
    
    if identificados:
        print("\nProdutos encontrados:")
        for p in identificados:
            print(f"  • {p['produto_nome']} ({p['confianca']}%)")
    
    return produtos_encontrados


def salvar_imagem_com_bboxes(imagem_obj, produtos_encontrados, output_path=None):
    """Salva a imagem com os bboxes desenhados para visualizacao"""
    img = cv2.imread(imagem_obj.imagem.path)
    if img is None:
        return
    
    for i, prod in enumerate(produtos_encontrados):
        bbox = prod['bbox']
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        
        # Cor baseada na confianca
        if prod['confianca'] >= 80:
            cor = (0, 255, 0)  # Verde
        elif prod['confianca'] >= 50:
            cor = (0, 255, 255)  # Amarelo
        else:
            cor = (0, 0, 255)  # Vermelho
        
        # Desenhar bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), cor, 2)
        
        # Label
        label = f"{prod['produto_nome'][:30]} ({prod['confianca']:.0f}%)"
        cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
    
    # Salvar
    if output_path is None:
        output_path = f"teste_bbox_{imagem_obj.id}.jpg"
    
    cv2.imwrite(output_path, img)
    print(f"\n📸 Imagem salva com bboxes: {output_path}")


if __name__ == "__main__":
    from django.db.models import Q
    
    print("\n" + "#"*70)
    print("#  TESTE DE RECONHECIMENTO DE IMAGENS COM MULTIPLOS PRODUTOS")
    print("#"*70 + "\n")
    
    # Buscar imagens pendentes
    pendentes = ImagemProdutoPendente.objects.filter(
        Q(produto__descricao_produto__icontains='DESCONHECIDO') |
        Q(produto__descricao_produto__icontains='FAMILIA_HEINEKEN_MANUAL')
    ).filter(status='pendente')[:3]
    
    print(f"🔍 Encontradas {pendentes.count()} imagens pendentes para testar\n")
    
    for imagem in pendentes:
        produtos = testar_imagem_com_multiplos_produtos(imagem)
        
        # Salvar imagem com bboxes para visualizacao
        if produtos:
            salvar_imagem_com_bboxes(imagem, produtos)
        
        print("\n" + "="*70 + "\n")
