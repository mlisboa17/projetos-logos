#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COM FOCO NO PRODUTO ANTES DO OCR
1. Remove fundo
2. Detecta regiões de produtos  
3. FOCA em cada produto individualmente
4. OCR otimizado em cada região focada
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

def detectar_produtos_precisos(img):
    """Detecta produtos com maior precisão usando múltiplos métodos"""
    
    # Método 1: Análise por cor (produtos têm cores distintas do fundo)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Máscara para objetos coloridos (não fundo neutro)
    mask_cor = cv2.inRange(hsv, (0, 30, 30), (179, 255, 255))
    
    # Método 2: Detecção de bordas
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Combinar métodos
    mask_combinada = cv2.bitwise_or(mask_cor, edges)
    
    # Operações morfológicas para limpar
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_combinada = cv2.morphologyEx(mask_combinada, cv2.MORPH_CLOSE, kernel)
    mask_combinada = cv2.morphologyEx(mask_combinada, cv2.MORPH_OPEN, kernel)
    
    # Encontrar contornos
    contornos, _ = cv2.findContours(mask_combinada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar por área e aspect ratio (produtos têm formas características)
    produtos = []
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area > 5000:  # Área mínima para produto
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / h
            
            # Produtos geralmente têm aspect ratio entre 0.3 e 3.0
            if 0.3 <= aspect_ratio <= 3.0:
                produtos.append({
                    'contorno': contorno,
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio
                })
    
    return produtos

def focar_produto(img, produto):
    """Foca em um produto específico para OCR otimizado"""
    x, y, w, h = produto['bbox']
    
    # Extrair região do produto com margem
    margem = 20
    x1 = max(0, x - margem)
    y1 = max(0, y - margem)
    x2 = min(img.shape[1], x + w + margem)
    y2 = min(img.shape[0], y + h + margem)
    
    # Recortar região focada
    produto_focado = img[y1:y2, x1:x2]
    
    # Redimensionar se muito pequeno para melhor OCR
    if produto_focado.shape[0] < 200 or produto_focado.shape[1] < 200:
        fator_escala = max(200 / produto_focado.shape[0], 200 / produto_focado.shape[1])
        nova_largura = int(produto_focado.shape[1] * fator_escala)
        nova_altura = int(produto_focado.shape[0] * fator_escala)
        produto_focado = cv2.resize(produto_focado, (nova_largura, nova_altura), interpolation=cv2.INTER_CUBIC)
    
    return produto_focado, (x1, y1, x2, y2)

def otimizar_para_ocr(img_produto):
    """Otimiza imagem do produto para OCR"""
    
    # 1. Conversão para escala de cinza
    if len(img_produto.shape) == 3:
        gray = cv2.cvtColor(img_produto, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_produto.copy()
    
    # 2. Denoising
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # 3. CLAHE para melhorar contraste
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contraste = clahe.apply(denoised)
    
    # 4. Sharpening para texto mais nítido
    kernel_sharp = np.array([[-1,-1,-1],
                            [-1, 9,-1],
                            [-1,-1,-1]])
    sharpened = cv2.filter2D(contraste, -1, kernel_sharp)
    
    # 5. Ajuste de gamma para claridade
    gamma = 1.2
    lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)]).astype("uint8")
    gamma_corrected = cv2.LUT(sharpened, lookup_table)
    
    return gamma_corrected

def ocr_focado(img_otimizada):
    """OCR otimizado para produto focado"""
    if not TESSERACT_DISPONIVEL:
        return []
    
    # Múltiplas configurações para diferentes tipos de texto
    configs = [
        ("Texto geral", "--psm 6 -l por+eng"),
        ("Linha única", "--psm 7 -l eng"),
        ("Palavra única", "--psm 8 -l eng"),
        ("Texto livre", "--psm 3 -l por+eng"),
        ("Caracteres únicos", "--psm 10 -l eng"),
    ]
    
    resultados = []
    
    for nome, config in configs:
        try:
            texto = pytesseract.image_to_string(img_otimizada, config=config).strip()
            if texto and len(texto) > 1:
                # Limpar texto detectado
                texto_limpo = ''.join(char for char in texto if char.isalnum() or char.isspace())
                if texto_limpo:
                    resultados.append({
                        'config': nome,
                        'texto': texto_limpo,
                        'confianca': len(texto_limpo) / len(texto) if texto else 0
                    })
        except Exception as e:
            continue
    
    return resultados

def main():
    """Pipeline principal com foco no produto"""
    print("=" * 70)
    print("🎯 PIPELINE COM FOCO NO PRODUTO ANTES DO OCR")
    print("=" * 70)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_focado_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # ====================================
    # ETAPA 1: CARREGAR E PREPARAR
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
    # ETAPA 2: REMOÇÃO DE FUNDO
    # ====================================
    print("\n🎭 ETAPA 2: REMOÇÃO DE FUNDO")
    
    # Usar método anterior que funcionou bem
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    kernel_limpar = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_limpar)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_limpar)
    
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_grandes = [c for c in contornos if cv2.contourArea(c) > 3000]
    
    # Criar máscara
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for contorno in contornos_grandes:
        cv2.fillPoly(mask, [contorno], 255)
    
    # Expandir máscara
    kernel_expansao = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_expandida = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel_expansao, iterations=3)
    
    # Aplicar máscara
    img_sem_fundo = img.copy()
    img_sem_fundo[mask_expandida == 0] = [255, 255, 255]
    
    print(f"✓ Fundo removido - {len(contornos_grandes)} regiões preservadas")
    
    # Salvar
    cv2.imwrite(os.path.join(pasta_resultado, "1_sem_fundo.jpg"), img_sem_fundo)
    
    # ====================================
    # ETAPA 3: DETECTAR PRODUTOS PRECISOS
    # ====================================
    print("\n🔍 ETAPA 3: DETECÇÃO PRECISA DE PRODUTOS")
    
    produtos = detectar_produtos_precisos(img_sem_fundo)
    print(f"✓ {len(produtos)} produtos detectados com precisão")
    
    # Visualizar detecções
    img_deteccoes = img_sem_fundo.copy()
    for i, produto in enumerate(produtos):
        x, y, w, h = produto['bbox']
        cv2.rectangle(img_deteccoes, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img_deteccoes, f"Produto {i+1}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "2_produtos_detectados.jpg"), img_deteccoes)
    
    # ====================================
    # ETAPA 4: FOCAR EM CADA PRODUTO
    # ====================================
    print("\n🎯 ETAPA 4: FOCO INDIVIDUAL EM CADA PRODUTO")
    
    todos_textos = []
    
    for i, produto in enumerate(produtos):
        print(f"\n  📦 Produto {i+1}:")
        
        # Focar no produto
        produto_focado, coords = focar_produto(img_sem_fundo, produto)
        print(f"    ✓ Região focada: {produto_focado.shape[1]}x{produto_focado.shape[0]}")
        
        # Salvar produto focado
        cv2.imwrite(os.path.join(pasta_resultado, f"3_produto_{i+1}_focado.jpg"), produto_focado)
        
        # Otimizar para OCR
        img_otimizada = otimizar_para_ocr(produto_focado)
        print(f"    ✓ Otimizado para OCR")
        
        # Salvar versão otimizada
        cv2.imwrite(os.path.join(pasta_resultado, f"4_produto_{i+1}_ocr.jpg"), img_otimizada)
        
        # ====================================
        # ETAPA 5: OCR FOCADO
        # ====================================
        print(f"    📖 OCR Focado:")
        
        resultados_ocr = ocr_focado(img_otimizada)
        
        if resultados_ocr:
            for resultado in resultados_ocr:
                print(f"      {resultado['config']}: {repr(resultado['texto'])}")
                todos_textos.append(f"Produto {i+1} - {resultado['config']}: {resultado['texto']}")
        else:
            print(f"      ❌ Nenhum texto detectado")
    
    # ====================================
    # ETAPA 6: ANÁLISE FINAL
    # ====================================
    print("\n🎉 ETAPA 6: ANÁLISE FINAL")
    
    # Verificar marcas conhecidas
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA', 'BEER']
    marcas_encontradas = set()
    
    texto_completo = ' '.join(todos_textos).upper()
    
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            marcas_encontradas.add(marca)
    
    if marcas_encontradas:
        print(f"🍺 Marcas identificadas: {', '.join(marcas_encontradas)}")
    else:
        print("📝 Nenhuma marca específica identificada")
    
    print(f"📊 Total de textos detectados: {len(todos_textos)}")
    
    # Salvar relatório detalhado
    with open(os.path.join(pasta_resultado, "5_relatorio_focado.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE COM FOCO NO PRODUTO ===\n\n")
        f.write(f"Imagem processada: {imagem_original}\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write(f"PRODUTOS DETECTADOS: {len(produtos)}\n")
        for i, produto in enumerate(produtos):
            f.write(f"- Produto {i+1}: Área={produto['area']}, Ratio={produto['aspect_ratio']:.2f}\n")
        
        f.write(f"\nTEXTOS DETECTADOS:\n")
        for texto in todos_textos:
            f.write(f"- {texto}\n")
        
        if marcas_encontradas:
            f.write(f"\nMARCAS IDENTIFICADAS:\n")
            for marca in marcas_encontradas:
                f.write(f"- {marca}\n")
        
        f.write(f"\n=== ARQUIVOS GERADOS ===\n")
        f.write("1_sem_fundo.jpg - Imagem com fundo removido\n")
        f.write("2_produtos_detectados.jpg - Produtos detectados e marcados\n")
        f.write("3_produto_X_focado.jpg - Cada produto focado individualmente\n")
        f.write("4_produto_X_ocr.jpg - Cada produto otimizado para OCR\n")
        f.write("5_relatorio_focado.txt - Este relatório\n")
    
    print(f"\n📁 Resultados completos em: {os.path.abspath(pasta_resultado)}")
    
    # Abrir pasta
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 70)
    print("🎯 PIPELINE COM FOCO CONCLUÍDO!")
    print("✅ Cada produto foi analisado individualmente")
    print("✅ OCR otimizado para cada região")
    print("=" * 70)

if __name__ == "__main__":
    main()