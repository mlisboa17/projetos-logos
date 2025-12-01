#!/usr/bin/env python3
"""
Script OCR simples para testar reconhecimento de texto nas imagens processadas
"""

import cv2
import numpy as np
import os
from pathlib import Path

def main():
    # Caminho da imagem pré-processada
    img_path = "processamento_completo_20251130_143852/01_preprocessamento_final.jpg"
    
    if not Path(img_path).exists():
        print(f"❌ Imagem não encontrada: {img_path}")
        return
    
    print("🔍 TESTE OCR SIMPLES")
    print("=" * 50)
    
    # Carregar imagem
    img = cv2.imread(img_path)
    print(f"✅ Imagem carregada: {img.shape}")
    
    # Tentar EasyOCR primeiro
    try:
        import easyocr
        print("📖 Usando EasyOCR...")
        
        reader = easyocr.Reader(['pt', 'en'])
        results = reader.readtext(img)
        
        print(f"\n🎯 TEXTOS ENCONTRADOS ({len(results)}):")
        print("-" * 40)
        
        textos_importantes = []
        
        for i, (bbox, text, confidence) in enumerate(results, 1):
            text_clean = text.strip()
            
            if confidence > 0.3 and len(text_clean) > 1:
                print(f"[{i:2}] {text_clean:20} | Conf: {confidence:.2f}")
                
                # Verificar se é uma marca conhecida
                text_lower = text_clean.lower()
                marcas = ['corona', 'heineken', 'skol', 'brahma', 'antarctica', 'stella']
                
                for marca in marcas:
                    if marca in text_lower:
                        textos_importantes.append({
                            'marca': marca.upper(),
                            'texto': text_clean,
                            'confianca': confidence
                        })
                        print(f"     🏷️  MARCA IDENTIFICADA: {marca.upper()}")
                        break
        
        if textos_importantes:
            print(f"\n🏆 PRODUTOS IDENTIFICADOS:")
            print("-" * 40)
            for produto in textos_importantes:
                print(f"   {produto['marca']}: \"{produto['texto']}\" ({produto['confianca']:.2f})")
        else:
            print("\n⚠️  Nenhuma marca conhecida identificada via OCR")
            
    except ImportError:
        print("⚠️  EasyOCR não disponível")
        
        # Fallback para Tesseract
        try:
            import pytesseract
            print("📖 Usando Tesseract...")
            
            # Configuração para produtos
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, config=config, lang='por+eng')
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            print(f"\n🎯 TEXTOS ENCONTRADOS ({len(lines)}):")
            print("-" * 40)
            
            for i, line in enumerate(lines, 1):
                if len(line) > 1:
                    print(f"[{i:2}] {line}")
            
            # Procurar marcas
            text_all = ' '.join(lines).lower()
            marcas = ['corona', 'heineken', 'skol', 'brahma', 'antarctica', 'stella']
            
            marcas_encontradas = []
            for marca in marcas:
                if marca in text_all:
                    marcas_encontradas.append(marca.upper())
            
            if marcas_encontradas:
                print(f"\n🏆 MARCAS IDENTIFICADAS:")
                print("-" * 40)
                for marca in marcas_encontradas:
                    print(f"   {marca}")
            else:
                print("\n⚠️  Nenhuma marca conhecida identificada via OCR")
                
        except ImportError:
            print("❌ Nenhum OCR disponível (nem EasyOCR nem Tesseract)")
    
    print(f"\n✅ Teste OCR concluído!")

if __name__ == "__main__":
    main()