#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detector direto com foto específica - versão simplificada
"""

import os
import sys
import cv2
import numpy as np
import django
import pytesseract
from pathlib import Path
from ultralytics import YOLO

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'fuel_prices'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
try:
    django.setup()
    from verifik.models import ProdutoMae
    USAR_PRODUTOS_MAE = True
    print("✅ Django carregado com sucesso")
except Exception as e:
    USAR_PRODUTOS_MAE = False
    print(f"⚠️  Django não carregado: {e}")

# Configurar Tesseract
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    print("✅ Tesseract configurado")
except:
    print("⚠️  Tesseract não encontrado")

def main():
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    print("\n" + "="*80)
    print("🔍 INICIANDO DETECÇÃO DE PRODUTOS")
    print("="*80)
    print(f"📷 Foto: {Path(caminho_foto).name}")
    
    # Carregar imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        print("❌ Erro ao carregar imagem")
        return
    
    altura, largura = img.shape[:2]
    print(f"📐 Dimensões: {largura}x{altura}")
    
    # Carregar modelo YOLO
    caminhos_modelo = [
        r"verifik\verifik_yolov8.pt",  # Modelo treinado específico
        r"verifik\runs\treino_continuado\weights\best.pt",
        r"yolov8n.pt",  # Modelo padrão se não encontrar o treinado
    ]
    
    modelo_encontrado = None
    for caminho in caminhos_modelo:
        if os.path.exists(caminho):
            modelo_encontrado = caminho
            break
    
    if not modelo_encontrado:
        print("❌ Nenhum modelo YOLO encontrado")
        return
    
    print(f"🤖 Carregando modelo: {modelo_encontrado}")
    
    try:
        model = YOLO(modelo_encontrado)
        print("✅ Modelo YOLO carregado")
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        return
    
    # Fazer detecção
    print("\n🔍 Executando detecção...")
    
    try:
        results = model.predict(
            source=caminho_foto,
            conf=0.25,  # Confiança mínima
            iou=0.45,   # IoU threshold
            max_det=20, # Máximo de detecções
            save=False,
            verbose=True
        )
        
        print(f"✅ Detecção concluída")
        
        # Processar resultados
        boxes = results[0].boxes
        print(f"📦 Produtos detectados: {len(boxes)}")
        
        if len(boxes) > 0:
            # Mostrar detecções
            img_resultado = img.copy()
            
            for i, box in enumerate(boxes):
                # Extrair informações
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                
                # Nome da classe
                if hasattr(model, 'names') and cls_id in model.names:
                    nome_classe = model.names[cls_id]
                else:
                    nome_classe = f"Classe_{cls_id}"
                
                print(f"  {i+1}. {nome_classe} ({conf*100:.1f}%) - [{x1},{y1},{x2},{y2}]")
                
                # Desenhar bbox
                cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Texto
                texto = f"{nome_classe} {conf*100:.1f}%"
                cv2.putText(img_resultado, texto, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Salvar resultado
            resultado_path = "resultado_deteccao.jpg"
            cv2.imwrite(resultado_path, img_resultado)
            print(f"\n💾 Resultado salvo em: {resultado_path}")
            
            # Mostrar resultado
            print("\n📺 Mostrando resultado (pressione qualquer tecla para fechar)...")
            
            # Redimensionar se muito grande
            max_size = 1200
            if largura > max_size or altura > max_size:
                escala = min(max_size/largura, max_size/altura)
                novo_w = int(largura * escala)
                novo_h = int(altura * escala)
                img_resultado = cv2.resize(img_resultado, (novo_w, novo_h))
            
            cv2.imshow("Detecções Encontradas", img_resultado)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        else:
            print("⚠️  Nenhum produto detectado com confiança >= 25%")
            
            # Tentar com confiança mais baixa
            print("\n🔍 Tentando com confiança mais baixa (5%)...")
            results2 = model.predict(
                source=caminho_foto,
                conf=0.05,
                iou=0.3,
                max_det=50,
                save=False,
                verbose=False
            )
            
            boxes2 = results2[0].boxes
            print(f"📦 Detecções com baixa confiança: {len(boxes2)}")
            
            if len(boxes2) > 0:
                for i, box in enumerate(boxes2[:10]):  # Mostrar apenas os 10 primeiros
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    if hasattr(model, 'names') and cls_id in model.names:
                        nome_classe = model.names[cls_id]
                    else:
                        nome_classe = f"Classe_{cls_id}"
                    
                    print(f"  {i+1}. {nome_classe} ({conf*100:.1f}%)")
    
    except Exception as e:
        print(f"❌ Erro durante detecção: {e}")
        return
    
    print("\n" + "="*80)
    print("✅ DETECÇÃO CONCLUÍDA")
    print("="*80)

if __name__ == "__main__":
    main()