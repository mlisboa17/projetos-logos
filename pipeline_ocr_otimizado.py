#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de OCR otimizado seguindo especificações:
1. Carregar imagem
2. Pré-processar (cinza, binarização, remoção de ruído, correção de perspectiva)
3. Rodar OCR (EasyOCR ou Tesseract)
4. Exibir resultado
"""

import cv2
import numpy as np
import os
from datetime import datetime
import sys
from pathlib import Path

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

# Configuração do EasyOCR
try:
    import easyocr
    EASYOCR_DISPONIVEL = True
except ImportError:
    EASYOCR_DISPONIVEL = False

def main():
    """Função principal do pipeline OCR"""
    print("=" * 60)
    print("🚀 PIPELINE OCR OTIMIZADO")
    print("=" * 60)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_ocr_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # ====================================
    # ETAPA 1: CARREGAR IMAGEM
    # ====================================
    print("\n📥 ETAPA 1: CARREGAMENTO")
    
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    # Carregar imagem
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"✓ Imagem carregada: {largura}x{altura}")
    
    # ====================================
    # ETAPA 2: PRÉ-PROCESSAR
    # ====================================
    print("\n🎭 ETAPA 2: PRÉ-PROCESSAMENTO")
    
    # 2.1 Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print("✓ Convertido para escala de cinza")
    
    # Salvar versão em cinza
    caminho_gray = os.path.join(pasta_resultado, "1_escala_cinza.jpg")
    cv2.imwrite(caminho_gray, gray)
    
    # 2.2 Binarização adaptativa
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    print("✓ Binarização adaptativa aplicada")
    
    # Salvar versão binarizada
    caminho_thresh = os.path.join(pasta_resultado, "2_binarizada.jpg")
    cv2.imwrite(caminho_thresh, thresh)
    
    # 2.3 Remoção de ruído
    blur = cv2.medianBlur(thresh, 3)
    print("✓ Ruído removido com median blur")
    
    # Salvar versão sem ruído
    caminho_blur = os.path.join(pasta_resultado, "3_sem_ruido.jpg")
    cv2.imwrite(caminho_blur, blur)
    
    # 2.4 Correção de perspectiva (opcional - aplicar se necessário)
    # Para esta imagem, vamos pular a correção de perspectiva
    # mas deixar preparado para futuras implementações
    img_preprocessada = blur.copy()
    print("✓ Pré-processamento concluído")
    
    # Salvar imagem final pré-processada
    caminho_final = os.path.join(pasta_resultado, "4_preprocessada_final.jpg")
    cv2.imwrite(caminho_final, img_preprocessada)
    
    # ====================================
    # ETAPA 3: RODAR OCR
    # ====================================
    print("\n📖 ETAPA 3: OCR - RECONHECIMENTO DE TEXTO")
    
    textos_encontrados = []
    
    # 3a. OCR com EasyOCR
    if EASYOCR_DISPONIVEL:
        try:
            print("🔍 Executando EasyOCR...")
            reader = easyocr.Reader(['pt', 'en'])
            results_easy = reader.readtext(img_preprocessada)
            
            print("\n📋 Resultados EasyOCR:")
            if results_easy:
                for i, (bbox, text, prob) in enumerate(results_easy):
                    print(f"  {i+1}. {text} (confiança: {prob:.2f})")
                    textos_encontrados.append(f"EasyOCR: {text} (conf: {prob:.2f})")
            else:
                print("  ❌ Nenhum texto detectado com EasyOCR")
                
        except Exception as e:
            print(f"❌ Erro no EasyOCR: {e}")
    else:
        print("❌ EasyOCR não disponível")
    
    # 3b. OCR com Tesseract
    if TESSERACT_DISPONIVEL:
        try:
            print("\n🔍 Executando Tesseract...")
            
            # Configurações diferentes para melhor detecção
            configs_tesseract = [
                ("Padrão", ""),
                ("Português", "--oem 3 --psm 6 -l por"),
                ("Inglês", "--oem 3 --psm 6 -l eng"),
                ("Texto livre", "--oem 3 --psm 8"),
                ("Linha única", "--oem 3 --psm 7"),
            ]
            
            print("\n📋 Resultados Tesseract:")
            for nome, config in configs_tesseract:
                try:
                    if config:
                        text_tess = pytesseract.image_to_string(img_preprocessada, config=config).strip()
                    else:
                        text_tess = pytesseract.image_to_string(img_preprocessada, lang="por").strip()
                    
                    if text_tess:
                        print(f"  {nome}: {repr(text_tess)}")
                        textos_encontrados.append(f"Tesseract ({nome}): {text_tess}")
                    else:
                        print(f"  {nome}: (sem texto)")
                        
                except Exception as e:
                    print(f"  {nome}: Erro - {e}")
                    
        except Exception as e:
            print(f"❌ Erro geral no Tesseract: {e}")
    else:
        print("❌ Tesseract não disponível")
    
    # ====================================
    # ETAPA 4: EXIBIR RESULTADO
    # ====================================
    print("\n🎯 ETAPA 4: RESULTADOS FINAIS")
    
    # Verificar marcas conhecidas
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA ARTOIS', 'MEXICO']
    marcas_encontradas = []
    
    texto_completo = ' '.join(textos_encontrados).upper()
    
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            marcas_encontradas.append(marca)
    
    if marcas_encontradas:
        print(f"🍺 Marcas identificadas: {', '.join(set(marcas_encontradas))}")
    else:
        print("📝 Nenhuma marca conhecida identificada")
    
    # Salvar todos os resultados em arquivo
    caminho_resultados = os.path.join(pasta_resultado, "5_resultados_ocr.txt")
    with open(caminho_resultados, 'w', encoding='utf-8') as f:
        f.write("=== RESULTADOS DO PIPELINE OCR ===\n\n")
        f.write(f"Imagem processada: {imagem_original}\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("=== TEXTOS DETECTADOS ===\n")
        for texto in textos_encontrados:
            f.write(f"{texto}\n")
        
        if marcas_encontradas:
            f.write(f"\n=== MARCAS IDENTIFICADAS ===\n")
            for marca in set(marcas_encontradas):
                f.write(f"- {marca}\n")
        
        f.write(f"\n=== ARQUIVOS GERADOS ===\n")
        f.write("1. 1_escala_cinza.jpg - Imagem em escala de cinza\n")
        f.write("2. 2_binarizada.jpg - Após binarização adaptativa\n")
        f.write("3. 3_sem_ruido.jpg - Após remoção de ruído\n")
        f.write("4. 4_preprocessada_final.jpg - Versão final para OCR\n")
        f.write("5. 5_resultados_ocr.txt - Este arquivo de resultados\n")
    
    print(f"\n📁 Todos os arquivos salvos em: {os.path.abspath(pasta_resultado)}")
    
    # Tentar mostrar imagem pré-processada
    print("\n👁️  Mostrando imagem pré-processada...")
    try:
        cv2.imshow("Pré-processada", img_preprocessada)
        print("Pressione qualquer tecla para fechar...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Não foi possível mostrar a imagem: {e}")
    
    # Abrir pasta de resultados
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta de resultados aberta!")
    except:
        pass
    
    print("=" * 60)
    print("🎉 PIPELINE OCR CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()