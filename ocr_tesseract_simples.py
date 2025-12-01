#!/usr/bin/env python3
"""
OCR simples usando apenas Tesseract
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
    
    print("📖 TESTE OCR COM TESSERACT")
    print("=" * 50)
    
    # Carregar imagem
    img = cv2.imread(img_path)
    print(f"✅ Imagem carregada: {img.shape}")
    
    try:
        import pytesseract
        print("✅ Tesseract disponível")
        
        # Pré-processar imagem para OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aumentar contraste
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Executar OCR com configuração otimizada
        config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%'
        
        print("\n🔍 Executando OCR...")
        text = pytesseract.image_to_string(enhanced, config=config, lang='por+eng')
        
        # Processar resultado
        lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 1]
        
        print(f"\n🎯 TEXTOS ENCONTRADOS ({len(lines)}):")
        print("-" * 40)
        
        for i, line in enumerate(lines, 1):
            print(f"[{i:2}] {line}")
        
        # Procurar marcas conhecidas
        text_all = ' '.join(lines).lower()
        marcas = ['corona', 'coronita', 'heineken', 'skol', 'brahma', 'antarctica', 'stella', 'budweiser', 'devassa']
        
        marcas_encontradas = []
        for marca in marcas:
            if marca in text_all:
                marcas_encontradas.append(marca.upper())
        
        # Procurar informações de produto
        infos_produto = []
        for line in lines:
            line_lower = line.lower()
            # Procurar ml, %, etc
            if 'ml' in line_lower or '%' in line or 'vol' in line_lower:
                infos_produto.append(line)
        
        print(f"\n🏆 MARCAS IDENTIFICADAS ({len(marcas_encontradas)}):")
        print("-" * 40)
        if marcas_encontradas:
            for marca in marcas_encontradas:
                print(f"   ✅ {marca}")
        else:
            print("   ⚠️  Nenhuma marca conhecida identificada")
        
        if infos_produto:
            print(f"\n📋 INFORMAÇÕES DE PRODUTO ({len(infos_produto)}):")
            print("-" * 40)
            for info in infos_produto:
                print(f"   📊 {info}")
        
        # Salvar resultado processado para análise
        output_dir = Path("ocr_resultado")
        output_dir.mkdir(exist_ok=True)
        
        # Salvar imagem processada para OCR
        cv2.imwrite(str(output_dir / "imagem_ocr_processada.jpg"), enhanced)
        
        # Salvar texto resultado
        with open(output_dir / "texto_detectado.txt", 'w', encoding='utf-8') as f:
            f.write("TEXTO DETECTADO VIA OCR\n")
            f.write("=" * 30 + "\n\n")
            for i, line in enumerate(lines, 1):
                f.write(f"[{i:2}] {line}\n")
            
            if marcas_encontradas:
                f.write(f"\n\nMARCAS IDENTIFICADAS:\n")
                for marca in marcas_encontradas:
                    f.write(f"- {marca}\n")
        
        print(f"\n💾 Resultados salvos em: {output_dir.absolute()}")
        
        # Abrir pasta de resultados
        os.startfile(str(output_dir))
        
    except ImportError:
        print("❌ Tesseract não está disponível")
        print("   Instale com: pip install pytesseract")
        print("   E baixe o Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    
    except Exception as e:
        print(f"❌ Erro no OCR: {str(e)}")
    
    print(f"\n✅ Teste OCR concluído!")

if __name__ == "__main__":
    main()