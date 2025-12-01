#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script final para processamento conservador + OCR
Combina: remoção conservadora de fundo + luminosidade + OCR
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

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 PROCESSAMENTO CONSERVADOR + OCR FINAL")
    print("=" * 60)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"resultado_final_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # ====================================
    # ETAPA 1: CARREGAMENTO
    # ====================================
    print("\n📥 ETAPA 1: CARREGAMENTO")
    
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"✓ Imagem: {largura}x{altura}")
    
    # ====================================
    # ETAPA 2: REMOÇÃO CONSERVADORA
    # ====================================
    print("\n🎭 ETAPA 2: REMOÇÃO DE FUNDO CONSERVADORA")
    
    # Conversão para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Blur para suavizar
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Limiarização adaptativa para detectar objetos
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Operações morfológicas para limpar ruído
    kernel_limpar = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_limpar)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_limpar)
    
    # Encontrar contornos
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar contornos por área (produtos geralmente são grandes)
    area_minima = 5000  # Ajustar conforme necessário
    contornos_produtos = [c for c in contornos if cv2.contourArea(c) > area_minima]
    
    print(f"✓ {len(contornos_produtos)} contornos de produtos encontrados")
    
    # Criar máscara dos produtos
    mask = np.zeros(gray.shape, dtype=np.uint8)
    
    # Preencher contornos na máscara
    for contorno in contornos_produtos:
        cv2.fillPoly(mask, [contorno], 255)
    
    # EXPANSÃO CONSERVADORA da máscara (preservar bordas dos produtos)
    kernel_expansao = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_expandida = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel_expansao, iterations=3)
    
    # Aplicar máscara para remover fundo
    img_sem_fundo = img.copy()
    img_sem_fundo[mask_expandida == 0] = [255, 255, 255]  # Fundo branco
    
    # Salvar imagem sem fundo
    caminho_sem_fundo = os.path.join(pasta_resultado, "1_sem_fundo_conservador.jpg")
    cv2.imwrite(caminho_sem_fundo, img_sem_fundo)
    print("✓ Fundo removido preservando produtos")
    
    # ====================================
    # ETAPA 3: MELHORIA DE QUALIDADE - ÊNFASE EM RÓTULOS E LETRAS
    # ====================================
    print("\n✨ ETAPA 3: MELHORIA DE QUALIDADE - FOCO EM TEXTO")
    
    # MÉTODO 1: Melhorar contraste para texto
    # Converter para escala de cinza para análise de texto
    gray_sem_fundo = cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2GRAY)
    
    # Aplicar CLAHE mais agressivo para realçar texto
    clahe_texto = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    gray_clahe = clahe_texto.apply(gray_sem_fundo)
    
    # MÉTODO 2: Realçar bordas e texto com filtros
    # Filtro bilateral para suavizar preservando bordas
    bilateral = cv2.bilateralFilter(gray_clahe, 9, 75, 75)
    
    # Sharpening para realçar detalhes do texto
    kernel_sharp = np.array([[-1,-1,-1],
                            [-1, 9,-1],
                            [-1,-1,-1]])
    sharpened = cv2.filter2D(bilateral, -1, kernel_sharp)
    
    # MÉTODO 3: Ajuste de gamma para melhor visibilidade do texto
    gamma = 1.2  # Aumentar para clarear texto
    lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)]).astype("uint8")
    gamma_corrected = cv2.LUT(sharpened, lookup_table)
    
    # MÉTODO 4: Converter de volta para BGR e aplicar ajustes finais
    img_melhorada = cv2.cvtColor(gamma_corrected, cv2.COLOR_GRAY2BGR)
    
    # Aumentar saturação para destacar cores dos rótulos
    hsv = cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = cv2.multiply(s, 1.3)  # Aumentar saturação em 30%
    s = np.clip(s, 0, 255).astype(np.uint8)
    hsv_saturated = cv2.merge([h, s, v])
    img_colorida = cv2.cvtColor(hsv_saturated, cv2.COLOR_HSV2BGR)
    
    # Combinar texto realçado com cores dos rótulos
    img_melhorada = cv2.addWeighted(img_melhorada, 0.6, img_colorida, 0.4, 0)
    
    # Salvar imagem melhorada
    caminho_melhorada = os.path.join(pasta_resultado, "2_qualidade_melhorada.jpg")
    cv2.imwrite(caminho_melhorada, img_melhorada)
    
    # Salvar também versão em escala de cinza otimizada para OCR
    caminho_gray_ocr = os.path.join(pasta_resultado, "2b_gray_para_ocr.jpg")
    cv2.imwrite(caminho_gray_ocr, gamma_corrected)
    
    print("✓ Qualidade melhorada com foco em rótulos e letras")
    print("✓ CLAHE agressivo aplicado (clipLimit=3.0)")
    print("✓ Sharpening para realçar texto")
    print("✓ Gamma corrigido para melhor visibilidade")
    print("✓ Saturação aumentada em 30%")
    
    # ====================================
    # ETAPA 4: OCR
    # ====================================
    print("\n📖 ETAPA 4: OCR PARA RECONHECIMENTO")
    
    if not TESSERACT_DISPONIVEL:
        print("❌ Tesseract não disponível")
    else:
        # Verificar se tesseract está configurado
        try:
            # Teste rápido
            pytesseract.get_tesseract_version()
            print("✓ Tesseract disponível")
            
            # MÚLTIPLAS CONFIGURAÇÕES OCR para melhor detecção
            configs_ocr = [
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # Palavra única
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # Linha única
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',  # Bloco uniforme
                '--psm 13',  # Linha crua - modo rápido
            ]
            
            textos_detectados = []
            
            # Tentar OCR na imagem colorida melhorada
            for i, config in enumerate(configs_ocr):
                try:
                    texto = pytesseract.image_to_string(
                        img_melhorada, 
                        config=config,
                        lang='eng'
                    ).strip()
                    if texto:
                        textos_detectados.append(f"Config {i+1}: {texto}")
                except:
                    continue
            
            # Tentar também na versão em escala de cinza otimizada
            for i, config in enumerate(configs_ocr):
                try:
                    texto = pytesseract.image_to_string(
                        gamma_corrected, 
                        config=config,
                        lang='eng'
                    ).strip()
                    if texto:
                        textos_detectados.append(f"Gray Config {i+1}: {texto}")
                except:
                    continue
            
            # Consolidar resultados
            if textos_detectados:
                texto_detectado = '\n'.join(textos_detectados)
            else:
                texto_detectado = ""
            
            if texto_detectado:
                print(f"✓ Texto detectado: {repr(texto_detectado)}")
                
                # Marcas conhecidas para verificar
                marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA ARTOIS']
                marcas_encontradas = []
                
                for marca in marcas_conhecidas:
                    if marca.upper() in texto_detectado.upper():
                        marcas_encontradas.append(marca)
                
                if marcas_encontradas:
                    print(f"🍺 Marcas identificadas: {', '.join(marcas_encontradas)}")
                else:
                    print("📝 Texto detectado mas nenhuma marca conhecida identificada")
                
                # Salvar texto em arquivo
                caminho_texto = os.path.join(pasta_resultado, "3_texto_detectado.txt")
                with open(caminho_texto, 'w', encoding='utf-8') as f:
                    f.write(f"Texto detectado pelo OCR:\n")
                    f.write(f"{texto_detectado}\n\n")
                    if marcas_encontradas:
                        f.write(f"Marcas identificadas: {', '.join(marcas_encontradas)}\n")
                
            else:
                print("❌ Nenhum texto detectado")
                
        except Exception as e:
            print(f"❌ Erro no OCR: {e}")
    
    # ====================================
    # FINALIZAÇÃO
    # ====================================
    print(f"\n🎯 PROCESSAMENTO CONCLUÍDO!")
    print(f"📁 Todos os arquivos em: {os.path.abspath(pasta_resultado)}")
    
    # Tentar abrir pasta no explorador
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("👁️  Resultado aberto!")
    except:
        pass
    
    print("=" * 60)

if __name__ == "__main__":
    main()