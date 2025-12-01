#!/usr/bin/env python

import os
import sys
import django
import cv2
import numpy as np
import pytesseract
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

# Configurar Tesseract  
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def main():
    print("=== DETECTOR DE MARCA NO RÓTULO ===")
    
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    # Verificar arquivo
    if not os.path.exists(caminho_foto):
        print(f"❌ Arquivo não encontrado: {caminho_foto}")
        return
    
    print(f"✅ Processando: {Path(caminho_foto).name}")
    
    # Carregar imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        print("❌ Erro ao carregar imagem")
        return
    
    print(f"📷 Dimensões: {img.shape[1]}x{img.shape[0]}")
    
    # Usar bbox conhecida da detecção anterior
    x1, y1, x2, y2 = 217, 55, 696, 1029
    
    # Extrair produto completo
    produto = img[y1:y2, x1:x2]
    cv2.imwrite("debug_produto.jpg", produto)
    
    # Focar na região do rótulo (onde fica a marca)
    altura_p = y2 - y1
    largura_p = x2 - x1
    
    # Coordenadas do rótulo (região central-superior)
    rx1 = int(largura_p * 0.2)   # 20% da esquerda
    ry1 = int(altura_p * 0.1)    # 10% do topo
    rx2 = int(largura_p * 0.8)   # 80% da largura
    ry2 = int(altura_p * 0.5)    # 50% da altura
    
    rotulo = produto[ry1:ry2, rx1:rx2]
    cv2.imwrite("debug_rotulo.jpg", rotulo)
    
    print(f"🏷️  Região do rótulo extraída: {rotulo.shape}")
    
    # Processamento para OCR
    gray = cv2.cvtColor(rotulo, cv2.COLOR_BGR2GRAY)
    
    # Aumentar contraste
    contraste = cv2.convertScaleAbs(gray, alpha=2.5, beta=20)
    cv2.imwrite("debug_contraste.jpg", contraste)
    
    # Threshold
    _, thresh = cv2.threshold(contraste, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite("debug_threshold.jpg", thresh)
    
    print("💾 Arquivos debug salvos")
    
    # Tentar OCR com diferentes configurações
    configs_ocr = [
        '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ', 
        '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        '--psm 6',
        '--psm 7',
        '--psm 13'
    ]
    
    print("\n🔤 Tentativas de OCR:")
    textos_encontrados = []
    
    for i, config in enumerate(configs_ocr):
        try:
            texto = pytesseract.image_to_string(thresh, lang='eng+por', config=config)
            texto_limpo = ''.join(c for c in texto.upper() if c.isalnum() or c.isspace()).strip()
            
            if texto_limpo and len(texto_limpo) > 2:
                textos_encontrados.append(texto_limpo)
                print(f"  Config {i+1}: '{texto_limpo}'")
            else:
                print(f"  Config {i+1}: (vazio)")
                
        except Exception as e:
            print(f"  Config {i+1}: Erro - {str(e)[:50]}")
    
    # Análise dos textos encontrados
    marcas_conhecidas = ['HEINEKEN', 'DEVASSA', 'BUDWEISER', 'AMSTEL', 'STELLA', 'BRAHMA', 'SKOL', 'ANTARCTICA', 'PEPSI', 'COCA']
    
    marca_detectada = None
    for texto in textos_encontrados:
        for marca in marcas_conhecidas:
            if marca in texto or any(part in texto for part in [marca[:4], marca[:5]] if len(marca) > 4):
                marca_detectada = marca
                print(f"\n✅ MARCA IDENTIFICADA: {marca} (encontrada em '{texto}')")
                break
        if marca_detectada:
            break
    
    if not marca_detectada:
        print(f"\n❓ Marca não identificada nos textos: {textos_encontrados}")
    
    # Resultado visual
    img_resultado = img.copy()
    
    # Bbox do produto
    cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 3)
    
    # Bbox do rótulo
    cv2.rectangle(img_resultado, (x1+rx1, y1+ry1), (x1+rx2, y1+ry2), (255, 255, 0), 2)
    
    # Texto
    texto_final = marca_detectada if marca_detectada else "MARCA_NAO_IDENTIFICADA"
    cv2.putText(img_resultado, texto_final, (x1, y1-40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(img_resultado, "ROTULO", (x1+rx1, y1+ry1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    
    cv2.imwrite("resultado_marca_final.jpg", img_resultado)
    
    print(f"\n🎯 RESULTADO FINAL: {texto_final}")
    print("💾 Arquivos gerados:")
    print("  - debug_produto.jpg (produto completo)")
    print("  - debug_rotulo.jpg (região do rótulo)")
    print("  - debug_contraste.jpg (processado)")
    print("  - debug_threshold.jpg (binarizado)")
    print("  - resultado_marca_final.jpg (resultado)")

if __name__ == "__main__":
    main()