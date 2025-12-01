#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detector focado no RÓTULO - OCR melhorado para ler MARCA
"""

import os
import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO
import re

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocessar_para_texto(regiao):
    """Múltiplos processamentos para melhorar leitura de texto"""
    processamentos = []
    
    # 1. Original
    processamentos.append(("Original", regiao))
    
    # 2. Escala de cinza
    gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
    processamentos.append(("Cinza", gray))
    
    # 3. Aumentar contraste
    contraste = cv2.convertScaleAbs(gray, alpha=2.5, beta=30)
    processamentos.append(("Contraste", contraste))
    
    # 4. Threshold adaptativo
    thresh_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    processamentos.append(("Threshold_Adapt", thresh_adapt))
    
    # 5. Threshold simples
    _, thresh_simples = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processamentos.append(("Threshold_Otsu", thresh_simples))
    
    # 6. Morphologia para limpar texto
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(thresh_adapt, cv2.MORPH_CLOSE, kernel)
    processamentos.append(("Morfologia", morph))
    
    # 7. Denoising
    denoised = cv2.fastNlMeansDenoising(gray)
    processamentos.append(("Denoised", denoised))
    
    # 8. Blur + Threshold
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    _, blur_thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processamentos.append(("Blur_Thresh", blur_thresh))
    
    return processamentos

def extrair_texto_multiplas_formas(regiao):
    """Extrai texto usando múltiplas configurações de OCR"""
    processamentos = preprocessar_para_texto(regiao)
    
    # Configurações do Tesseract para diferentes tipos de texto
    configs_ocr = [
        '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Só maiúsculas
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Uma linha
        '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Uma palavra
        '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Texto bruto
        '--psm 6',  # Bloco uniforme
        '--psm 7',  # Linha única
        '--psm 8',  # Palavra única
    ]
    
    todos_textos = []
    
    # Testar cada processamento com cada config
    for nome_proc, img_proc in processamentos:
        for config in configs_ocr:
            try:
                texto = pytesseract.image_to_string(img_proc, lang='eng+por', config=config)
                if texto.strip():
                    texto_limpo = re.sub(r'[^A-Z0-9\s]', '', texto.upper().strip())
                    if texto_limpo:
                        todos_textos.append((nome_proc, config, texto_limpo))
            except:
                continue
    
    return todos_textos

def analisar_rotulo_cerveja(img, bbox):
    """Analisa especificamente o rótulo de cerveja"""
    x1, y1, x2, y2 = bbox
    
    # Expandir bbox para capturar rótulo completo
    altura_bbox = y2 - y1
    largura_bbox = x2 - x1
    
    # Foco na parte central-superior onde geralmente fica a marca
    margem_h = int(largura_bbox * 0.1)  # 10% nas laterais
    margem_v = int(altura_bbox * 0.2)   # 20% acima/abaixo
    
    x1_rotulo = max(0, x1 - margem_h)
    y1_rotulo = max(0, y1 + int(altura_bbox * 0.1))  # Começar um pouco abaixo do topo
    x2_rotulo = min(img.shape[1], x2 + margem_h)
    y2_rotulo = min(img.shape[0], y1 + int(altura_bbox * 0.6))  # Só a parte superior/central
    
    print(f"    📍 Região do rótulo: [{x1_rotulo},{y1_rotulo},{x2_rotulo},{y2_rotulo}]")
    
    # Extrair região do rótulo
    regiao_rotulo = img[y1_rotulo:y2_rotulo, x1_rotulo:x2_rotulo]
    
    if regiao_rotulo.size == 0:
        return "PRODUTO_DESCONHECIDO"
    
    # Salvar região para debug
    cv2.imwrite("debug_rotulo.jpg", regiao_rotulo)
    
    # Extrair textos
    textos_encontrados = extrair_texto_multiplas_formas(regiao_rotulo)
    
    print(f"    🔍 Tentativas de OCR: {len(textos_encontrados)}")
    
    # Marcas conhecidas com variações
    marcas_conhecidas = {
        'HEINEKEN': ['HEINEKEN', 'HEINE', 'NEKEN', 'HEINEK', 'HEINKEN'],
        'DEVASSA': ['DEVASSA', 'DEVAS', 'EVASSA', 'VASSA', 'DEAV'],
        'BUDWEISER': ['BUDWEISER', 'BUDWEI', 'WEISER', 'BUD', 'BUDW'],
        'AMSTEL': ['AMSTEL', 'AMSTE', 'MATEL', 'STEL'],
        'STELLA': ['STELLA', 'STELA', 'ARTOIS', 'TELLA'],
        'BRAHMA': ['BRAHMA', 'BRAMA', 'RAHMA', 'BRAHM'],
        'SKOL': ['SKOL', 'SK0L', 'KOLL', '5KOL'],
        'ANTARCTICA': ['ANTARCTICA', 'ANTARTIC', 'ANTART'],
        'PEPSI': ['PEPSI', 'P3PSI', 'PEPS'],
        'COCA': ['COCA', 'COLA', 'C0CA', 'COCACOLA'],
        'KAISER': ['KAISER', 'KAISE', 'ISER'],
        'ITAIPAVA': ['ITAIPAVA', 'ITAIP', 'PAVA'],
        'CRYSTAL': ['CRYSTAL', 'CRYSTA', 'STAL'],
        'ORIGINAL': ['ORIGINAL', 'ORIGIN', 'GINAL']
    }
    
    # Procurar marcas nos textos
    for proc, config, texto in textos_encontrados:
        print(f"      {proc}: '{texto}'")
        
        for marca, variacoes in marcas_conhecidas.items():
            for variacao in variacoes:
                if variacao in texto:
                    print(f"    ✅ MARCA ENCONTRADA: {marca} (via '{variacao}' em '{texto}')")
                    return marca
    
    # Análise por similaridade de palavras
    palavras_validas = []
    for proc, config, texto in textos_encontrados:
        palavras = texto.split()
        for palavra in palavras:
            if len(palavra) >= 4 and palavra.isalpha():
                palavras_validas.append(palavra)
    
    # Procurar palavras similares
    if palavras_validas:
        print(f"    📝 Palavras válidas encontradas: {palavras_validas}")
        
        for palavra in palavras_validas:
            for marca, variacoes in marcas_conhecidas.items():
                for variacao in variacoes:
                    # Similaridade simples por caracteres em comum
                    chars_comuns = len(set(palavra) & set(variacao))
                    if chars_comuns >= min(len(palavra), len(variacao)) * 0.6:
                        print(f"    🔍 Possível marca: {marca} ('{palavra}' similar a '{variacao}')")
                        return marca
    
    # Se encontrou texto mas não identificou marca
    if textos_encontrados:
        melhor_texto = max([texto for _, _, texto in textos_encontrados], key=len)
        print(f"    ❓ Marca não identificada, melhor texto: '{melhor_texto}'")
        return f"MARCA_{melhor_texto.split()[0] if melhor_texto.split() else 'DESCONHECIDA'}"
    
    print(f"    ❌ Nenhum texto legível encontrado")
    return "PRODUTO_DESCONHECIDO"

def main():
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    print("\n" + "="*80)
    print("🏷️  DETECTOR DE RÓTULOS - FOCO NA MARCA")
    print("="*80)
    
    # Carregar imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        print("❌ Erro ao carregar imagem")
        return
    
    altura, largura = img.shape[:2]
    print(f"📷 Imagem: {largura}x{altura} pixels")
    
    # Detectar produto
    print("🤖 Detectando produtos...")
    model = YOLO('yolov8n.pt')
    
    results = model.predict(
        source=caminho_foto,
        conf=0.25,
        iou=0.45,
        max_det=10,
        save=False,
        verbose=False
    )
    
    boxes = results[0].boxes
    print(f"📦 Produtos detectados: {len(boxes)}")
    
    if len(boxes) == 0:
        print("❌ Nenhum produto detectado")
        return
    
    # Analisar cada produto
    img_resultado = img.copy()
    
    for i, box in enumerate(boxes):
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, xyxy)
        conf = float(box.conf[0])
        
        print(f"\n  📦 PRODUTO {i+1}:")
        print(f"     Confiança: {conf*100:.1f}%")
        print(f"     Bbox: [{x1},{y1},{x2},{y2}]")
        
        # Analisar rótulo
        marca_identificada = analisar_rotulo_cerveja(img, (x1, y1, x2, y2))
        
        # Desenhar resultado
        cor = (0, 255, 0) if marca_identificada.startswith(('HEINEKEN', 'DEVASSA', 'BUDWEISER', 'AMSTEL', 'STELLA', 'BRAHMA', 'SKOL')) else (0, 165, 255)
        
        # Bbox principal
        cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 3)
        
        # Bbox do rótulo (para mostrar onde procurou)
        altura_bbox = y2 - y1
        margem_h = int((x2 - x1) * 0.1)
        x1_rot = max(0, x1 - margem_h)
        y1_rot = max(0, y1 + int(altura_bbox * 0.1))
        x2_rot = min(largura, x2 + margem_h)
        y2_rot = min(altura, y1 + int(altura_bbox * 0.6))
        
        cv2.rectangle(img_resultado, (x1_rot, y1_rot), (x2_rot, y2_rot), (255, 255, 0), 2)
        
        # Texto da marca
        cv2.putText(img_resultado, marca_identificada, (x1, y1-40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
        
        # Confiança
        cv2.putText(img_resultado, f"{conf*100:.1f}%", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
        
        print(f"     🎯 RESULTADO: {marca_identificada}")
    
    # Salvar resultado
    cv2.imwrite("resultado_rotulo_focado.jpg", img_resultado)
    print(f"\n💾 Resultado salvo: resultado_rotulo_focado.jpg")
    print(f"🔍 Debug do rótulo salvo: debug_rotulo.jpg")
    
    # Mostrar resultado
    print("\n📺 Mostrando resultado...")
    max_size = 1000
    if largura > max_size or altura > max_size:
        escala = min(max_size/largura, max_size/altura)
        novo_w = int(largura * escala)
        novo_h = int(altura * escala)
        img_resultado = cv2.resize(img_resultado, (novo_w, novo_h))
    
    cv2.imshow("Marca Identificada no Rótulo", img_resultado)
    print("⌨️  Pressione qualquer tecla para fechar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n" + "="*80)
    print("✅ ANÁLISE CONCLUÍDA")
    print("="*80)

if __name__ == "__main__":
    main()