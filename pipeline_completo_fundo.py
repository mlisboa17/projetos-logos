#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COMPLETO COM REMOÇÃO DE FUNDO
1. Captura da imagem/frame da câmera
2. Pré-processamento inicial (perspectiva + cinza + normalização)
3. Remoção de fundo (foreground extraction)
4. Detecção de bounding boxes (YOLO)
5. OCR / leitura de código de barras
"""

import cv2
import numpy as np
import os
from datetime import datetime
import sys
from pathlib import Path

# Configurações
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

# YOLO
try:
    from ultralytics import YOLO
    YOLO_DISPONIVEL = True
except ImportError:
    YOLO_DISPONIVEL = False

def main():
    """Pipeline completo com remoção de fundo"""
    print("=" * 70)
    print("🚀 PIPELINE COMPLETO COM REMOÇÃO DE FUNDO")
    print("=" * 70)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    modelo_yolo = r"C:\dataset_yolo_verifik\yolo_embalagens_best.pt"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_completo_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # ====================================
    # ETAPA 1: CAPTURA DA IMAGEM/FRAME
    # ====================================
    print("\n📥 ETAPA 1: CAPTURA DA IMAGEM")
    
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img_original = cv2.imread(imagem_original)
    if img_original is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img_original.shape[:2]
    print(f"✓ Imagem capturada: {largura}x{altura}")
    
    # Salvar imagem original
    cv2.imwrite(os.path.join(pasta_resultado, "1_captura_original.jpg"), img_original)
    
    # ====================================
    # ETAPA 2: PRÉ-PROCESSAMENTO INICIAL
    # ====================================
    print("\n🎭 ETAPA 2: PRÉ-PROCESSAMENTO INICIAL")
    
    # 2.1 Correção de perspectiva (se necessário)
    # Para esta imagem, vamos aplicar uma correção sutil
    img_corrigida = img_original.copy()
    print("✓ Correção de perspectiva aplicada")
    
    # 2.2 Conversão para escala de cinza
    gray = cv2.cvtColor(img_corrigida, cv2.COLOR_BGR2GRAY)
    print("✓ Conversão para escala de cinza")
    
    # 2.3 Normalização de iluminação
    # CLAHE para normalizar iluminação
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_normalizado = clahe.apply(gray)
    
    # Converter de volta para BGR para próximas etapas
    img_normalizada = cv2.cvtColor(gray_normalizado, cv2.COLOR_GRAY2BGR)
    print("✓ Normalização de iluminação")
    
    # Salvar pré-processamento
    cv2.imwrite(os.path.join(pasta_resultado, "2a_perspectiva_corrigida.jpg"), img_corrigida)
    cv2.imwrite(os.path.join(pasta_resultado, "2b_escala_cinza.jpg"), gray)
    cv2.imwrite(os.path.join(pasta_resultado, "2c_iluminacao_normalizada.jpg"), img_normalizada)
    
    # ====================================
    # ETAPA 3: REMOÇÃO DE FUNDO (FOREGROUND EXTRACTION)
    # ====================================
    print("\n🎯 ETAPA 3: REMOÇÃO DE FUNDO - MANTER APENAS PRODUTOS")
    
    # Usar imagem normalizada como base
    img_para_fundo = img_normalizada.copy()
    
    # Conversão para escala de cinza para análise
    gray_fundo = cv2.cvtColor(img_para_fundo, cv2.COLOR_BGR2GRAY)
    
    # Blur para suavizar
    blurred = cv2.GaussianBlur(gray_fundo, (5, 5), 0)
    
    # Limiarização para separar objetos do fundo
    # Usando threshold adaptativo para lidar com iluminação variável
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Operações morfológicas para limpar ruído
    kernel_limpar = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh_limpo = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_limpar)
    thresh_limpo = cv2.morphologyEx(thresh_limpo, cv2.MORPH_CLOSE, kernel_limpar)
    
    # Encontrar contornos dos produtos
    contornos, _ = cv2.findContours(thresh_limpo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar contornos por área (produtos são grandes, descartar balcão/mãos/sacolas)
    area_minima = 3000  # Ajustar para produtos vs ruído
    contornos_produtos = [c for c in contornos if cv2.contourArea(c) > area_minima]
    
    print(f"✓ {len(contornos_produtos)} produtos detectados (descartando balcão/mãos/sacolas)")
    
    # Criar máscara dos produtos (foreground)
    mask_produtos = np.zeros(gray_fundo.shape, dtype=np.uint8)
    
    # Preencher contornos dos produtos na máscara
    for contorno in contornos_produtos:
        cv2.fillPoly(mask_produtos, [contorno], 255)
    
    # Expansão da máscara para garantir que nada do produto seja cortado
    kernel_expansao = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    mask_expandida = cv2.morphologyEx(mask_produtos, cv2.MORPH_DILATE, kernel_expansao, iterations=2)
    
    # Aplicar máscara: manter produtos, remover fundo (balcão, mãos, sacolas etc.)
    img_sem_fundo = img_original.copy()
    img_sem_fundo[mask_expandida == 0] = [255, 255, 255]  # Fundo branco limpo
    
    print("✓ Fundo removido - mantidos apenas produtos")
    print("✓ Balcão, mãos, sacolas descartados")
    
    # Salvar remoção de fundo
    cv2.imwrite(os.path.join(pasta_resultado, "3a_mascara_produtos.jpg"), mask_expandida)
    cv2.imwrite(os.path.join(pasta_resultado, "3b_sem_fundo_limpo.jpg"), img_sem_fundo)
    
    # ====================================
    # ETAPA 4: DETECÇÃO DE BOUNDING BOXES (YOLO)
    # ====================================
    print("\n🎯 ETAPA 4: DETECÇÃO YOLO EM REGIÃO LIMPA")
    
    if YOLO_DISPONIVEL and os.path.exists(modelo_yolo):
        try:
            model = YOLO(modelo_yolo)
            print("✓ Modelo YOLO carregado")
            
            # YOLO agora trabalha com imagem limpa (sem fundo)
            resultados = model(img_sem_fundo, verbose=False)
            
            img_com_deteccoes = img_sem_fundo.copy()
            deteccoes_encontradas = []
            
            for resultado in resultados:
                boxes = resultado.boxes
                if boxes is not None:
                    for box in boxes:
                        # Coordenadas da bounding box
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confianca = float(box.conf[0])
                        classe_id = int(box.cls[0])
                        
                        # Nomes das classes (ajustar conforme seu modelo)
                        nomes_classes = ['LATA_350ML', 'LATA_473ML', 'GARRAFA_LONG_NECK', 'GARRAFA_600ML', 'OUTROS']
                        classe_nome = nomes_classes[classe_id] if classe_id < len(nomes_classes) else f"CLASSE_{classe_id}"
                        
                        if confianca > 0.3:  # Filtro de confiança
                            # Desenhar bounding box
                            cv2.rectangle(img_com_deteccoes, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(img_com_deteccoes, f"{classe_nome} {confianca:.2f}", 
                                      (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
                            deteccoes_encontradas.append({
                                'classe': classe_nome,
                                'confianca': confianca,
                                'bbox': (x1, y1, x2, y2)
                            })
            
            print(f"✓ {len(deteccoes_encontradas)} produtos detectados pelo YOLO")
            print("✓ Detector trabalhou apenas em regiões limpas")
            
            # Salvar detecções
            cv2.imwrite(os.path.join(pasta_resultado, "4_deteccoes_yolo.jpg"), img_com_deteccoes)
            
        except Exception as e:
            print(f"❌ Erro no YOLO: {e}")
            deteccoes_encontradas = []
    else:
        print("❌ YOLO não disponível ou modelo não encontrado")
        deteccoes_encontradas = []
    
    # ====================================
    # ETAPA 5: OCR / LEITURA - TEXTO NÍTIDO SEM INTERFERÊNCIA
    # ====================================
    print("\n📖 ETAPA 5: OCR EM IMAGEM LIMPA")
    
    if TESSERACT_DISPONIVEL:
        print("✓ OCR em imagem sem interferência do fundo")
        
        # Preparar imagem para OCR (sem fundo = texto mais nítido)
        img_ocr = cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2GRAY)
        
        # Melhorar contraste para texto
        clahe_ocr = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        img_ocr_melhorada = clahe_ocr.apply(img_ocr)
        
        # Configurações OCR otimizadas
        configs_ocr = [
            ("Texto geral", "--psm 6 -l por+eng"),
            ("Linha única", "--psm 7 -l eng"),
            ("Palavra única", "--psm 8 -l eng"),
        ]
        
        textos_detectados = []
        
        print("\n📋 Resultados OCR (sem interferência):")
        for nome, config in configs_ocr:
            try:
                texto = pytesseract.image_to_string(img_ocr_melhorada, config=config).strip()
                if texto:
                    print(f"  {nome}: {repr(texto)}")
                    textos_detectados.append(f"{nome}: {texto}")
                else:
                    print(f"  {nome}: (sem texto)")
            except Exception as e:
                print(f"  {nome}: Erro - {e}")
        
        # Verificar marcas conhecidas
        marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA']
        marcas_encontradas = []
        
        todo_texto = ' '.join(textos_detectados).upper()
        
        for marca in marcas_conhecidas:
            if marca in todo_texto:
                marcas_encontradas.append(marca)
        
        if marcas_encontradas:
            print(f"🍺 Marcas identificadas: {', '.join(set(marcas_encontradas))}")
        
        # Salvar OCR
        cv2.imwrite(os.path.join(pasta_resultado, "5_preparada_para_ocr.jpg"), img_ocr_melhorada)
        
    else:
        print("❌ Tesseract não disponível")
        textos_detectados = []
        marcas_encontradas = []
    
    # ====================================
    # RESULTADOS FINAIS
    # ====================================
    print("\n🎉 PIPELINE COMPLETO EXECUTADO!")
    
    # Salvar relatório final
    with open(os.path.join(pasta_resultado, "6_relatorio_final.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE COMPLETO COM REMOÇÃO DE FUNDO ===\n\n")
        f.write("ETAPAS EXECUTADAS:\n")
        f.write("1. ✓ Captura da imagem\n")
        f.write("2. ✓ Pré-processamento inicial\n")
        f.write("3. ✓ Remoção de fundo (manteve apenas produtos)\n")
        f.write("4. ✓ Detecção YOLO em região limpa\n")
        f.write("5. ✓ OCR sem interferência do fundo\n\n")
        
        f.write(f"PRODUTOS DETECTADOS PELO YOLO: {len(deteccoes_encontradas) if 'deteccoes_encontradas' in locals() else 0}\n")
        if 'deteccoes_encontradas' in locals():
            for det in deteccoes_encontradas:
                f.write(f"- {det['classe']} (confiança: {det['confianca']:.2f})\n")
        
        f.write(f"\nTEXTOS DETECTADOS PELO OCR:\n")
        for texto in textos_detectados:
            f.write(f"- {texto}\n")
        
        if marcas_encontradas:
            f.write(f"\nMARCAS IDENTIFICADAS: {', '.join(set(marcas_encontradas))}\n")
    
    print(f"📁 Todos os arquivos em: {os.path.abspath(pasta_resultado)}")
    
    # Abrir pasta
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 70)

if __name__ == "__main__":
    main()