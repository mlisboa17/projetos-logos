#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detector simples focado no rótulo
"""

import os
import cv2
import numpy as np
import pytesseract

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def main():
    try:
        print("🔍 Iniciando detector de rótulo...")
        
        caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
        
        # Verificar arquivo
        if not os.path.exists(caminho_foto):
            print(f"❌ Arquivo não encontrado: {caminho_foto}")
            return
        
        print(f"✅ Arquivo encontrado: {os.path.getsize(caminho_foto)} bytes")
        
        # Carregar imagem
        print("📷 Carregando imagem...")
        img = cv2.imread(caminho_foto)
        
        if img is None:
            print("❌ Erro ao carregar imagem com OpenCV")
            return
        
        altura, largura = img.shape[:2]
        print(f"✅ Imagem carregada: {largura}x{altura} pixels")
        
        # Simular bbox da detecção anterior (produto detectado)
        # Baseado na detecção: [217,55,696,1029]
        x1, y1, x2, y2 = 217, 55, 696, 1029
        print(f"📦 Analisando produto em: [{x1},{y1},{x2},{y2}]")
        
        # Focar na região do rótulo (parte central-superior)
        altura_produto = y2 - y1
        largura_produto = x2 - x1
        
        # Região do rótulo: parte superior/central onde fica a marca
        x1_rotulo = x1 + int(largura_produto * 0.1)  # 10% da lateral esquerda
        y1_rotulo = y1 + int(altura_produto * 0.1)   # 10% do topo
        x2_rotulo = x2 - int(largura_produto * 0.1)  # 10% da lateral direita  
        y2_rotulo = y1 + int(altura_produto * 0.5)   # Só metade superior
        
        print(f"🏷️  Região do rótulo: [{x1_rotulo},{y1_rotulo},{x2_rotulo},{y2_rotulo}]")
        
        # Extrair região do rótulo
        regiao_rotulo = img[y1_rotulo:y2_rotulo, x1_rotulo:x2_rotulo]
        
        if regiao_rotulo.size == 0:
            print("❌ Região do rótulo vazia")
            return
        
        print(f"✅ Região extraída: {regiao_rotulo.shape}")
        
        # Salvar região para debug
        cv2.imwrite("debug_regiao_rotulo.jpg", regiao_rotulo)
        print("💾 Região salva em: debug_regiao_rotulo.jpg")
        
        # Melhorar contraste da região
        gray = cv2.cvtColor(regiao_rotulo, cv2.COLOR_BGR2GRAY)
        contraste = cv2.convertScaleAbs(gray, alpha=2.0, beta=30)
        
        # Salvar versão com contraste
        cv2.imwrite("debug_contraste.jpg", contraste)
        print("💾 Versão com contraste salva em: debug_contraste.jpg")
        
        # Tentar OCR
        print("\n🔤 Tentando OCR...")
        
        configs = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 6',
            '--psm 7'
        ]
        
        for i, config in enumerate(configs):
            try:
                texto = pytesseract.image_to_string(contraste, lang='eng+por', config=config)
                texto_limpo = ''.join(c for c in texto.upper() if c.isalnum() or c.isspace()).strip()
                
                if texto_limpo:
                    print(f"  Config {i+1}: '{texto_limpo}'")
                else:
                    print(f"  Config {i+1}: (vazio)")
                    
            except Exception as e:
                print(f"  Config {i+1}: Erro - {e}")
        
        # Mostrar resultado visual
        img_resultado = img.copy()
        
        # Desenhar bbox do produto
        cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        # Desenhar região do rótulo
        cv2.rectangle(img_resultado, (x1_rotulo, y1_rotulo), (x2_rotulo, y2_rotulo), (255, 255, 0), 2)
        
        # Texto
        cv2.putText(img_resultado, "PRODUTO DETECTADO", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(img_resultado, "REGIÃO DO RÓTULO", (x1_rotulo, y1_rotulo-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Salvar resultado
        cv2.imwrite("debug_resultado_completo.jpg", img_resultado)
        print("\n💾 Resultado completo salvo em: debug_resultado_completo.jpg")
        
        print("\n✅ Análise concluída!")
        print("📁 Arquivos gerados:")
        print("   - debug_regiao_rotulo.jpg (região extraída)")
        print("   - debug_contraste.jpg (versão com contraste)")
        print("   - debug_resultado_completo.jpg (visualização)")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()