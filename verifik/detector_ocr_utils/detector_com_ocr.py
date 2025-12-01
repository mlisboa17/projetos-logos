#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detector com OCR para identificar nome real do produto
"""

import os
import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO
import re

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def limpar_texto_ocr(texto):
    """Limpa e normaliza texto do OCR"""
    if not texto:
        return ""
    
    # Remover caracteres especiais, manter apenas letras e números
    texto_limpo = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    texto_limpo = texto_limpo.strip().upper()
    
    # Correções comuns de OCR
    correções = {
        'HEINEKEN': ['HEINKEN', 'HEIEKEN', 'HEINEKN'],
        'BUDWEISER': ['BUDWISER', 'BUDWEIZER', 'BUDWESER'],
        'AMSTEL': ['AMSTE', 'AMSTEI', 'AMST3L'],
        'STELLA': ['STELA', 'STEILA', 'ST3LLA'],
        'DEVASSA': ['DEVAS5A', 'DEVASA', 'D3VASSA'],
        'BRAHMA': ['BRAHM4', 'BR4HMA', 'BRAMA'],
        'SKOL': ['SK0L', '5KOL', 'SKOI'],
        'ANTARCTICA': ['ANTARTICA', 'ANT4RTICA'],
        'PEPSI': ['P3PSI', 'PEPS1'],
        'COCA': ['C0CA', 'COCA', 'COOA']
    }
    
    for marca_correta, variacoes in correções.items():
        for variacao in variacoes:
            if variacao in texto_limpo:
                texto_limpo = texto_limpo.replace(variacao, marca_correta)
    
    return texto_limpo

def detectar_marca_por_ocr(img, bbox):
    """Detecta marca usando OCR na região da bbox"""
    x1, y1, x2, y2 = bbox
    
    # Expandir bbox um pouco para capturar mais texto
    margem = 20
    x1 = max(0, x1 - margem)
    y1 = max(0, y1 - margem)
    x2 = min(img.shape[1], x2 + margem)
    y2 = min(img.shape[0], y2 + margem)
    
    # Extrair região
    regiao = img[y1:y2, x1:x2]
    
    if regiao.size == 0:
        return "PRODUTO_DESCONHECIDO"
    
    # Múltiplas tentativas de OCR com diferentes processamentos
    todos_textos = []
    
    # 1. Original
    try:
        texto1 = pytesseract.image_to_string(regiao, lang='por+eng', config='--psm 6')
        todos_textos.append(texto1)
    except:
        pass
    
    # 2. Escala de cinza + contraste alto
    try:
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        contraste = cv2.convertScaleAbs(gray, alpha=3.0, beta=30)
        texto2 = pytesseract.image_to_string(contraste, lang='por+eng', config='--psm 6')
        todos_textos.append(texto2)
    except:
        pass
    
    # 3. Threshold binário
    try:
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        texto3 = pytesseract.image_to_string(threshold, lang='por+eng', config='--psm 8')
        todos_textos.append(texto3)
    except:
        pass
    
    # 4. Erosão para melhorar texto
    try:
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((2,2), np.uint8)
        erosao = cv2.erode(gray, kernel, iterations=1)
        texto4 = pytesseract.image_to_string(erosao, lang='por+eng', config='--psm 7')
        todos_textos.append(texto4)
    except:
        pass
    
    # Combinar todos os textos para análise
    texto_completo = " ".join(todos_textos).upper()
    print(f"    OCR combinado: '{texto_completo[:100]}...'")
    
    # Marcas conhecidas com padrões flexíveis
    marcas_padroes = {
        'DEVASSA': ['DEVASSA', 'DEVAS', 'EVASSA', 'DEVA55A', 'D3VASSA'],
        'HEINEKEN': ['HEINEKEN', 'HEINKEN', 'HEINE', 'HEINEK'],
        'BUDWEISER': ['BUDWEISER', 'BUDWISER', 'BUDWEI', 'BUD'],
        'AMSTEL': ['AMSTEL', 'AMSTE', 'AMSTEI'],
        'STELLA': ['STELLA', 'STELA', 'ARTOIS'],
        'BRAHMA': ['BRAHMA', 'BRAMA', 'BRAHM'],
        'SKOL': ['SKOL', 'SK0L', '5KOL'],
        'ANTARCTICA': ['ANTARCTICA', 'ANTARTIC', 'ANTART'],
        'PEPSI': ['PEPSI', 'P3PSI', 'PEPS'],
        'COCA': ['COCA', 'COLA', 'C0CA']
    }
    
    # Procurar padrões das marcas
    for marca, padroes in marcas_padroes.items():
        for padrao in padroes:
            if padrao in texto_completo:
                print(f"    ✅ Marca identificada: {marca} (padrão: {padrao})")
                return marca
    
    # Análise por proximidade de caracteres
    # Se encontrou "EVAS", provavelmente é DEVASSA
    if 'EVAS' in texto_completo:
        print(f"    ✅ Marca identificada: DEVASSA (aproximação: EVAS)")
        return 'DEVASSA'
    
    # Outros padrões comuns
    padroes_aproximados = {
        'HEINEKEN': ['HEIN', 'NEKEN', 'EINEK'],
        'BUDWEISER': ['BUDW', 'WISER', 'BUWEI'],
        'STELLA': ['STEL', 'TELA', 'ARTOI'],
        'BRAHMA': ['BRAH', 'RAHMA'],
    }
    
    for marca, padroes in padroes_aproximados.items():
        for padrao in padroes:
            if padrao in texto_completo:
                print(f"    ✅ Marca identificada: {marca} (aproximação: {padrao})")
                return marca
    
    # Se não identificou marca específica, criar nome baseado no texto mais limpo
    texto_limpo = limpar_texto_ocr(texto_completo)
    
    if texto_limpo and len(texto_limpo) > 2:
        # Pegar primeira palavra válida
        palavras = texto_limpo.split()
        primeira_palavra = ""
        for palavra in palavras:
            if len(palavra) >= 3 and palavra.isalnum():
                primeira_palavra = palavra
                break
        
        if primeira_palavra:
            return f"PRODUTO_{primeira_palavra[:15]}"
    
    return "PRODUTO_DESCONHECIDO"

def main():
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    print("\n" + "="*80)
    print("🔍 DETECTOR COM OCR - IDENTIFICAÇÃO REAL DE PRODUTOS")
    print("="*80)
    
    # Carregar imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        print("❌ Erro ao carregar imagem")
        return
    
    altura, largura = img.shape[:2]
    print(f"📷 Imagem: {largura}x{altura} pixels")
    
    # Usar modelo YOLOv8 padrão para detectar objetos genéricos
    print("🤖 Carregando YOLOv8...")
    model = YOLO('yolov8n.pt')
    
    # Detectar
    print("🔍 Executando detecção...")
    results = model.predict(
        source=caminho_foto,
        conf=0.25,
        iou=0.45,
        max_det=20,
        save=False,
        verbose=False
    )
    
    boxes = results[0].boxes
    print(f"📦 Objetos detectados: {len(boxes)}")
    
    # Analisar cada detecção
    img_resultado = img.copy()
    produtos_identificados = []
    
    for i, box in enumerate(boxes):
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, xyxy)
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        
        # Nome genérico
        nome_generico = model.names[cls_id] if cls_id in model.names else f"Objeto_{cls_id}"
        
        print(f"\n  🔍 Analisando detecção {i+1}:")
        print(f"     Tipo genérico: {nome_generico} ({conf*100:.1f}%)")
        print(f"     Posição: [{x1},{y1},{x2},{y2}]")
        
        # Identificar produto real com OCR
        produto_real = detectar_marca_por_ocr(img, (x1, y1, x2, y2))
        print(f"     ✅ Produto identificado: {produto_real}")
        
        produtos_identificados.append({
            'nome': produto_real,
            'confiança_detecção': conf,
            'bbox': (x1, y1, x2, y2),
            'tipo_generico': nome_generico
        })
        
        # Desenhar resultado
        cor = (0, 255, 0) if produto_real != "PRODUTO_DESCONHECIDO" else (0, 165, 255)
        
        # Bbox
        cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 3)
        
        # Texto do produto
        texto_produto = produto_real if produto_real != "PRODUTO_DESCONHECIDO" else nome_generico
        cv2.putText(img_resultado, texto_produto, (x1, y1-30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
        
        # Confiança
        texto_conf = f"{conf*100:.1f}%"
        cv2.putText(img_resultado, texto_conf, (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    
    # Salvar resultado
    resultado_path = "resultado_com_ocr.jpg"
    cv2.imwrite(resultado_path, img_resultado)
    
    # Resumo final
    print("\n" + "="*80)
    print("🎯 RESUMO DA IDENTIFICAÇÃO:")
    print("="*80)
    
    if produtos_identificados:
        for i, produto in enumerate(produtos_identificados, 1):
            print(f"  {i}. {produto['nome']}")
            print(f"     Confiança: {produto['confiança_detecção']*100:.1f}%")
            print(f"     Tipo genérico: {produto['tipo_generico']}")
            print()
    else:
        print("  ❌ Nenhum produto identificado")
    
    print(f"💾 Resultado salvo em: {resultado_path}")
    print("="*80)
    
    # Mostrar resultado
    print("\n📺 Mostrando resultado...")
    
    # Redimensionar se necessário
    max_size = 1200
    if largura > max_size or altura > max_size:
        escala = min(max_size/largura, max_size/altura)
        novo_w = int(largura * escala)
        novo_h = int(altura * escala)
        img_resultado = cv2.resize(img_resultado, (novo_w, novo_h))
    
    cv2.imshow("Produtos Identificados com OCR", img_resultado)
    print("⌨️  Pressione qualquer tecla para fechar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()