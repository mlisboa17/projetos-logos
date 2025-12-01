#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline OCR RÁPIDO - Apenas Tesseract
Etapas: 
1. Carregar imagem
2. Pré-processar (cinza, binarização, remoção de ruído)
3. OCR com Tesseract
4. Exibir resultado
"""

import cv2
import numpy as np
import os
from datetime import datetime

# Configuração do Tesseract
try:
    import pytesseract
    
    # Possíveis caminhos do Tesseract no Windows
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

def main():
    """Pipeline OCR rápido apenas com Tesseract"""
    print("=" * 60)
    print("⚡ PIPELINE OCR RÁPIDO - TESSERACT")
    print("=" * 60)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_rapido_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # ====================================
    # 1. CARREGAR IMAGEM
    # ====================================
    print("\n📥 1. CARREGAMENTO")
    
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"✓ Imagem carregada: {largura}x{altura}")
    
    # ====================================
    # 2. PRÉ-PROCESSAR
    # ====================================
    print("\n🎭 2. PRÉ-PROCESSAMENTO")
    
    # Escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print("✓ Escala de cinza")
    
    # Binarização adaptativa (seguindo sua especificação exata)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    print("✓ Binarização adaptativa")
    
    # Remoção de ruído (seguindo sua especificação exata)
    blur = cv2.medianBlur(thresh, 3)
    print("✓ Remoção de ruído")
    
    # Salvar etapas
    cv2.imwrite(os.path.join(pasta_resultado, "1_cinza.jpg"), gray)
    cv2.imwrite(os.path.join(pasta_resultado, "2_binarizada.jpg"), thresh)
    cv2.imwrite(os.path.join(pasta_resultado, "3_preprocessada.jpg"), blur)
    
    # ====================================
    # 3. OCR COM TESSERACT
    # ====================================
    print("\n📖 3. OCR")
    
    if not TESSERACT_DISPONIVEL:
        print("❌ Tesseract não disponível")
        return
    
    print("🔍 Executando Tesseract...")
    
    # Múltiplas configurações como na sua especificação
    configs = [
        ("Português", "por"),
        ("Inglês", "eng"), 
        ("Linha única", "--psm 7 -l eng"),
        ("Palavra única", "--psm 8 -l eng"),
        ("Texto livre", "--psm 6 -l por"),
    ]
    
    textos_encontrados = []
    
    print("\n📋 Resultados Tesseract:")
    for nome, config in configs:
        try:
            if "--psm" in config:
                text_tess = pytesseract.image_to_string(blur, config=config)
            else:
                text_tess = pytesseract.image_to_string(blur, lang=config)
            
            text_tess = text_tess.strip()
            
            if text_tess:
                print(f"  {nome}: {repr(text_tess)}")
                textos_encontrados.append(f"{nome}: {text_tess}")
            else:
                print(f"  {nome}: (sem texto)")
                
        except Exception as e:
            print(f"  {nome}: Erro - {e}")
    
    # ====================================
    # 4. EXIBIR RESULTADO
    # ====================================
    print("\n🎯 4. RESULTADO FINAL")
    
    # Verificar marcas
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO']
    marcas_encontradas = []
    
    todo_texto = ' '.join(textos_encontrados).upper()
    
    for marca in marcas_conhecidas:
        if marca in todo_texto:
            marcas_encontradas.append(marca)
    
    if marcas_encontradas:
        print(f"🍺 Marcas identificadas: {', '.join(set(marcas_encontradas))}")
    else:
        print("📝 Nenhuma marca conhecida")
    
    # Salvar resultados
    with open(os.path.join(pasta_resultado, "resultados.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE OCR RÁPIDO ===\n\n")
        for texto in textos_encontrados:
            f.write(f"{texto}\n")
        if marcas_encontradas:
            f.write(f"\nMarcas: {', '.join(set(marcas_encontradas))}\n")
    
    # Mostrar imagem pré-processada (seguindo sua especificação)
    print("\n👁️ Mostrando imagem pré-processada...")
    try:
        cv2.imshow("Pré-processada", blur)
        print("Pressione qualquer tecla para fechar...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("Não foi possível mostrar a imagem")
    
    # Abrir pasta
    try:
        os.startfile(os.path.abspath(pasta_resultado))
    except:
        pass
    
    print("\n🎉 PIPELINE CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()