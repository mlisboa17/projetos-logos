#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE AVANÇADO COM MASK R-CNN e SAM
Segmentação de instância muito superior para remoção de fundo
"""

import cv2
import numpy as np
import os
from datetime import datetime
import sys

# Configurações básicas
try:
    import pytesseract
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\gabri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    TESSERACT_DISPONIVEL = True
except ImportError:
    TESSERACT_DISPONIVEL = False

# SAM (Segment Anything Model)
try:
    from segment_anything import sam_model_registry, SamPredictor
    SAM_DISPONIVEL = True
except ImportError:
    SAM_DISPONIVEL = False

# Mask R-CNN (via detectron2)
try:
    import detectron2
    from detectron2 import model_zoo
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg
    from detectron2.utils.visualizer import Visualizer
    from detectron2.data import MetadataCatalog
    MASK_RCNN_DISPONIVEL = True
except ImportError:
    MASK_RCNN_DISPONIVEL = False

# YOLO
try:
    from ultralytics import YOLO
    YOLO_DISPONIVEL = True
except ImportError:
    YOLO_DISPONIVEL = False

def setup_mask_rcnn():
    """Configurar Mask R-CNN"""
    cfg = get_cfg()
    # Modelo pré-treinado do COCO (detecta bottles, cans, etc.)
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # Threshold para detecção
    cfg.MODEL.DEVICE = "cpu"  # Usar CPU (ou "cuda" se tiver GPU)
    
    predictor = DefaultPredictor(cfg)
    return predictor, cfg

def segmentacao_mask_rcnn(img, predictor):
    """Segmentação com Mask R-CNN"""
    print("🔍 Executando Mask R-CNN...")
    
    # Executar predição
    outputs = predictor(img)
    
    # Extrair máscaras, classes e scores
    instances = outputs["instances"]
    
    # Classes de interesse: bottle (39), cup (41), wine glass (40), etc.
    # Verificar classes COCO: https://tech.amikelive.com/node-718/what-object-categories-labels-are-in-coco-dataset/
    classes_produtos = [39, 40, 41]  # bottle, wine glass, cup
    
    mascaras_produtos = []
    deteccoes = []
    
    if len(instances) > 0:
        masks = instances.pred_masks.cpu().numpy()
        classes = instances.pred_classes.cpu().numpy()
        scores = instances.scores.cpu().numpy()
        boxes = instances.pred_boxes.tensor.cpu().numpy()
        
        for i, (mask, classe, score, box) in enumerate(zip(masks, classes, scores, boxes)):
            if classe in classes_produtos and score > 0.5:
                mascaras_produtos.append(mask)
                deteccoes.append({
                    'classe': classe,
                    'score': score,
                    'mask': mask,
                    'box': box
                })
                print(f"✓ Produto detectado: Classe {classe}, Score: {score:.2f}")
    
    return mascaras_produtos, deteccoes

def segmentacao_sam(img, predictor_sam):
    """Segmentação com SAM"""
    print("🔍 Executando SAM...")
    
    # SAM precisa de pontos ou bounding boxes como prompt
    # Vamos usar detecção automática de pontos interessantes
    predictor_sam.set_image(img)
    
    # Gerar grid de pontos para segmentação automática
    height, width = img.shape[:2]
    points = []
    labels = []
    
    # Grid de pontos na imagem
    for y in range(height//4, height, height//4):
        for x in range(width//4, width, width//4):
            points.append([x, y])
            labels.append(1)  # 1 = foreground
    
    points = np.array(points)
    labels = np.array(labels)
    
    # Gerar máscaras
    masks, scores, logits = predictor_sam.predict(
        point_coords=points,
        point_labels=labels,
        multimask_output=True,
    )
    
    # Selecionar melhor máscara
    if len(masks) > 0:
        best_mask = masks[np.argmax(scores)]
        return [best_mask], [{'score': np.max(scores), 'mask': best_mask}]
    
    return [], []

def main():
    """Pipeline com Mask R-CNN e SAM"""
    print("=" * 70)
    print("🚀 PIPELINE AVANÇADO - MASK R-CNN & SAM")
    print("=" * 70)
    
    # Verificar bibliotecas disponíveis
    print("\n📋 VERIFICANDO BIBLIOTECAS:")
    print(f"✓ OpenCV: Disponível")
    print(f"{'✓' if MASK_RCNN_DISPONIVEL else '❌'} Mask R-CNN (detectron2): {'Disponível' if MASK_RCNN_DISPONIVEL else 'Não instalado'}")
    print(f"{'✓' if SAM_DISPONIVEL else '❌'} SAM: {'Disponível' if SAM_DISPONIVEL else 'Não instalado'}")
    print(f"{'✓' if YOLO_DISPONIVEL else '❌'} YOLO: {'Disponível' if YOLO_DISPONIVEL else 'Não instalado'}")
    print(f"{'✓' if TESSERACT_DISPONIVEL else '❌'} Tesseract: {'Disponível' if TESSERACT_DISPONIVEL else 'Não instalado'}")
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_avancado_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"\n📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"\n📥 Imagem carregada: {largura}x{altura}")
    
    # ====================================
    # MÉTODO 1: MASK R-CNN
    # ====================================
    if MASK_RCNN_DISPONIVEL:
        print(f"\n🎯 MÉTODO 1: MASK R-CNN")
        try:
            predictor_rcnn, cfg_rcnn = setup_mask_rcnn()
            mascaras_rcnn, deteccoes_rcnn = segmentacao_mask_rcnn(img, predictor_rcnn)
            
            if mascaras_rcnn:
                # Combinar todas as máscaras
                mascara_final = np.zeros((altura, largura), dtype=np.uint8)
                for mask in mascaras_rcnn:
                    mascara_final = np.logical_or(mascara_final, mask)
                
                # Aplicar máscara
                img_mask_rcnn = img.copy()
                img_mask_rcnn[~mascara_final] = [255, 255, 255]
                
                # Salvar
                cv2.imwrite(os.path.join(pasta_resultado, "mask_rcnn_resultado.jpg"), img_mask_rcnn)
                cv2.imwrite(os.path.join(pasta_resultado, "mask_rcnn_mascara.jpg"), mascara_final.astype(np.uint8) * 255)
                
                print(f"✅ Mask R-CNN: {len(mascaras_rcnn)} produtos segmentados")
            else:
                print("❌ Mask R-CNN: Nenhum produto detectado")
                
        except Exception as e:
            print(f"❌ Erro no Mask R-CNN: {e}")
    else:
        print(f"\n❌ MÉTODO 1: Mask R-CNN não disponível")
        print("💡 Para instalar: pip install detectron2")
    
    # ====================================
    # MÉTODO 2: SAM
    # ====================================
    if SAM_DISPONIVEL:
        print(f"\n🎯 MÉTODO 2: SAM (Segment Anything)")
        try:
            # Configurar SAM (precisa baixar modelo)
            sam_checkpoint = "sam_vit_h_4b8939.pth"  # Modelo grande
            model_type = "vit_h"
            
            if os.path.exists(sam_checkpoint):
                sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
                predictor_sam = SamPredictor(sam)
                
                mascaras_sam, deteccoes_sam = segmentacao_sam(img, predictor_sam)
                
                if mascaras_sam:
                    # Aplicar máscara
                    img_sam = img.copy()
                    mascara_sam = mascaras_sam[0]
                    img_sam[~mascara_sam] = [255, 255, 255]
                    
                    # Salvar
                    cv2.imwrite(os.path.join(pasta_resultado, "sam_resultado.jpg"), img_sam)
                    cv2.imwrite(os.path.join(pasta_resultado, "sam_mascara.jpg"), mascara_sam.astype(np.uint8) * 255)
                    
                    print(f"✅ SAM: Segmentação realizada")
                else:
                    print("❌ SAM: Nenhuma segmentação gerada")
            else:
                print(f"❌ SAM: Modelo não encontrado ({sam_checkpoint})")
                print("💡 Baixe de: https://github.com/facebookresearch/segment-anything")
                
        except Exception as e:
            print(f"❌ Erro no SAM: {e}")
    else:
        print(f"\n❌ MÉTODO 2: SAM não disponível")
        print("💡 Para instalar: pip install segment-anything")
    
    # ====================================
    # MÉTODO 3: FALLBACK - OpenCV Tradicional
    # ====================================
    print(f"\n🎯 MÉTODO 3: FALLBACK OpenCV")
    
    # Método tradicional como backup
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_produtos = [c for c in contornos if cv2.contourArea(c) > 3000]
    
    mask_opencv = np.zeros(gray.shape, dtype=np.uint8)
    for contorno in contornos_produtos:
        cv2.fillPoly(mask_opencv, [contorno], 255)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    mask_opencv = cv2.morphologyEx(mask_opencv, cv2.MORPH_DILATE, kernel, iterations=2)
    
    img_opencv = img.copy()
    img_opencv[mask_opencv == 0] = [255, 255, 255]
    
    cv2.imwrite(os.path.join(pasta_resultado, "opencv_resultado.jpg"), img_opencv)
    cv2.imwrite(os.path.join(pasta_resultado, "opencv_mascara.jpg"), mask_opencv)
    
    print(f"✅ OpenCV: {len(contornos_produtos)} contornos detectados (backup)")
    
    # ====================================
    # COMPARAÇÃO E RECOMENDAÇÕES
    # ====================================
    print(f"\n📊 COMPARAÇÃO DOS MÉTODOS:")
    print(f"")
    print(f"🥇 MASK R-CNN:")
    print(f"   + Melhor para detectar produtos específicos")
    print(f"   + Segmentação precisa de instâncias")
    print(f"   + Treinado em datasets grandes (COCO)")
    print(f"   - Requer detectron2")
    print(f"")
    print(f"🥈 SAM (Segment Anything):")
    print(f"   + Segmenta qualquer objeto")
    print(f"   + Muito versátil")
    print(f"   + Estado da arte em segmentação")
    print(f"   - Requer modelo grande (~2.5GB)")
    print(f"   - Precisa de prompts (pontos/boxes)")
    print(f"")
    print(f"🥉 OpenCV Tradicional:")
    print(f"   + Sempre disponível")
    print(f"   + Rápido")
    print(f"   + Sem dependências pesadas")
    print(f"   - Menos preciso")
    print(f"   - Sensível a iluminação")
    
    # Salvar relatório
    with open(os.path.join(pasta_resultado, "comparacao_metodos.txt"), 'w', encoding='utf-8') as f:
        f.write("=== COMPARAÇÃO MÉTODOS SEGMENTAÇÃO ===\n\n")
        f.write("MASK R-CNN:\n")
        f.write(f"- Status: {'✓ Disponível' if MASK_RCNN_DISPONIVEL else '❌ Não instalado'}\n")
        f.write("- Vantagens: Segmentação precisa, detecta produtos específicos\n")
        f.write("- Instalação: pip install detectron2\n\n")
        
        f.write("SAM (Segment Anything):\n")
        f.write(f"- Status: {'✓ Disponível' if SAM_DISPONIVEL else '❌ Não instalado'}\n")
        f.write("- Vantagens: Segmenta qualquer coisa, estado da arte\n")
        f.write("- Instalação: pip install segment-anything\n")
        f.write("- Modelo: Baixar sam_vit_h_4b8939.pth (2.5GB)\n\n")
        
        f.write("OpenCV Tradicional:\n")
        f.write("- Status: ✓ Sempre disponível\n")
        f.write("- Vantagens: Rápido, sem dependências pesadas\n")
        f.write("- Desvantagens: Menos preciso\n")
    
    print(f"\n📁 Resultados salvos em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
    except:
        pass
    
    print("=" * 70)

if __name__ == "__main__":
    main()