#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visualiza processamento OCR para debug
"""

import cv2
import numpy as np
import pytesseract
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def processar_e_salvar(img_original, nome_base):
    """
    Aplica diferentes processamentos e salva para comparação
    """
    output_dir = Path("debug_ocr")
    output_dir.mkdir(exist_ok=True)
    
    # Converter para escala de cinza
    cinza = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
    
    processamentos = {}
    
    # 1. Original
    processamentos['01_original'] = img_original
    
    # 2. Escala de cinza
    processamentos['02_cinza'] = cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)
    
    # 3. Brilho + Contraste
    brilhante = cv2.convertScaleAbs(cinza, alpha=1.8, beta=60)
    processamentos['03_brilho_contraste'] = cv2.cvtColor(brilhante, cv2.COLOR_GRAY2BGR)
    
    # 4. CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    equalizado = clahe.apply(cinza)
    processamentos['04_clahe'] = cv2.cvtColor(equalizado, cv2.COLOR_GRAY2BGR)
    
    # 5. Gamma correction
    gamma = 2.0
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    gamma_corrigido = cv2.LUT(cinza, table)
    processamentos['05_gamma'] = cv2.cvtColor(gamma_corrigido, cv2.COLOR_GRAY2BGR)
    
    # 6. Denoising
    denoised = cv2.fastNlMeansDenoising(cinza, None, 10, 7, 21)
    brilhante_denoised = cv2.convertScaleAbs(denoised, alpha=1.8, beta=60)
    processamentos['06_denoising'] = cv2.cvtColor(brilhante_denoised, cv2.COLOR_GRAY2BGR)
    
    # 7. Threshold Otsu
    _, otsu = cv2.threshold(brilhante, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processamentos['07_threshold_otsu'] = cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR)
    
    # 8. Threshold Adaptativo
    adapt = cv2.adaptiveThreshold(brilhante, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    processamentos['08_threshold_adaptativo'] = cv2.cvtColor(adapt, cv2.COLOR_GRAY2BGR)
    
    # 9. Inversão
    invertido = cv2.bitwise_not(brilhante)
    processamentos['09_invertido'] = cv2.cvtColor(invertido, cv2.COLOR_GRAY2BGR)
    
    # 10. Sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(brilhante, -1, kernel)
    processamentos['10_sharpening'] = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
    
    # Salvar todas as versões e executar OCR
    print("\n" + "="*80)
    print("🔍 ANÁLISE OCR - DIFERENTES PROCESSAMENTOS")
    print("="*80 + "\n")
    
    resultados = []
    
    for nome, img_proc in processamentos.items():
        # Salvar imagem
        caminho = output_dir / f"{nome_base}_{nome}.jpg"
        cv2.imwrite(str(caminho), img_proc)
        
        # Executar OCR
        try:
            if len(img_proc.shape) == 3:
                img_ocr = cv2.cvtColor(img_proc, cv2.COLOR_BGR2GRAY)
            else:
                img_ocr = img_proc
            
            texto = pytesseract.image_to_string(img_ocr, lang='por+eng', config='--psm 3 --oem 3')
            texto_limpo = texto.strip().upper()
            
            # Procurar produtos conhecidos
            produtos_encontrados = []
            for produto in ['PEPSI', 'COCA', 'HEINEKEN', 'AMSTEL', 'BUDWEISER', 'STELLA', 
                          'DEVASSA', 'PETRA', 'PILSEN']:
                if produto in texto_limpo:
                    produtos_encontrados.append(produto)
            
            resultados.append({
                'nome': nome,
                'caminho': caminho,
                'texto': texto_limpo,
                'produtos': produtos_encontrados,
                'tamanho_texto': len(texto_limpo)
            })
            
            print(f"📄 {nome}:")
            if produtos_encontrados:
                print(f"   ✅ Produtos: {', '.join(produtos_encontrados)}")
            print(f"   📝 Texto ({len(texto_limpo)} chars): {texto_limpo[:100]}...")
            print()
            
        except Exception as e:
            print(f"   ❌ Erro OCR: {e}\n")
    
    # Resumo
    print("="*80)
    print("📊 RESUMO:")
    print("="*80 + "\n")
    
    melhores = sorted(resultados, key=lambda x: len(x['produtos']), reverse=True)[:3]
    
    print("🏆 Top 3 melhores processamentos:\n")
    for i, res in enumerate(melhores, 1):
        print(f"{i}. {res['nome']}")
        if res['produtos']:
            print(f"   Produtos: {', '.join(res['produtos'])}")
        else:
            print(f"   Nenhum produto identificado")
        print(f"   Texto: {res['tamanho_texto']} caracteres")
        print()
    
    print(f"\n💾 Imagens salvas em: {output_dir.absolute()}")
    print("="*80 + "\n")

def main():
    print("📷 Selecione a foto para análise OCR...")
    
    root = tk.Tk()
    root.withdraw()
    
    caminho_foto = filedialog.askopenfilename(
        title="Selecionar Foto",
        filetypes=[
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("Todos os arquivos", "*.*")
        ]
    )
    
    root.destroy()
    
    if not caminho_foto:
        print("❌ Nenhuma foto selecionada.")
        return
    
    # Carregar imagem
    img = cv2.imread(caminho_foto)
    
    if img is None:
        print(f"❌ Erro ao carregar: {caminho_foto}")
        return
    
    print(f"\n✅ Foto carregada: {caminho_foto}")
    print(f"📐 Dimensões: {img.shape[1]}x{img.shape[0]} pixels\n")
    
    # Processar
    nome_arquivo = Path(caminho_foto).stem
    processar_e_salvar(img, nome_arquivo)

if __name__ == "__main__":
    main()
