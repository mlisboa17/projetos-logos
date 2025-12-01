#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def testar_sistema():
    print("=== TESTE DO SISTEMA ORGANIZADO ===")
    
    # 1. Testar arquivo
    caminho = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if os.path.exists(caminho):
        size = os.path.getsize(caminho)
        print(f"✅ Arquivo: {size} bytes")
    else:
        print("❌ Arquivo não encontrado")
        return
    
    # 2. Testar OpenCV
    try:
        import cv2
        img = cv2.imread(caminho)
        if img is not None:
            h, w = img.shape[:2]
            print(f"✅ OpenCV: {w}x{h}")
        else:
            print("❌ OpenCV: Erro ao carregar")
            return
    except Exception as e:
        print(f"❌ OpenCV: {e}")
        return
    
    # 3. Testar YOLO
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        print("✅ YOLO: Carregado")
        
        # Teste rápido
        results = model.predict(source=caminho, verbose=False, save=False)
        boxes = results[0].boxes
        print(f"✅ Detecção: {len(boxes)} objetos")
        
    except Exception as e:
        print(f"❌ YOLO: {e}")
        return
    
    # 4. Testar Tesseract
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Testar em uma pequena região
        regiao = img[100:200, 100:200]
        texto = pytesseract.image_to_string(regiao)
        print(f"✅ Tesseract: Funcionando")
        
    except Exception as e:
        print(f"❌ Tesseract: {e}")
        return
    
    print("\n🎯 TODOS OS COMPONENTES FUNCIONANDO!")
    print("✅ Sistema pronto para executar detecção completa")

if __name__ == "__main__":
    testar_sistema()