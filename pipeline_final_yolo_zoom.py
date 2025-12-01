#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE FINAL: YOLO + ZOOM SUPER FOCADO
Baseado no método que funcionou bem (pipeline_zoom_20251130_152228)
Combina: YOLO para formas + Zoom extremo em regiões de texto + OCR otimizado
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

def detectar_codigo_barras(img):
    """Detecta códigos de barras na imagem"""
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Gradiente X (códigos de barras têm linhas verticais)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=-1)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=-1)
    
    # Subtrair gradientes
    gradient = cv2.subtract(grad_x, grad_y)
    gradient = cv2.convertScaleAbs(gradient)
    
    # Blur e threshold
    blurred = cv2.blur(gradient, (9, 9))
    (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
    
    # Operações morfológicas para conectar linhas
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Erosão e dilatação
    closed = cv2.erode(closed, None, iterations=4)
    closed = cv2.dilate(closed, None, iterations=4)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    codigos_barras = []
    for contour in contours:
        # Calcular área
        area = cv2.contourArea(contour)
        if area > 500:  # Área mínima para código de barras
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            
            # Código de barras tem aspect ratio alto (mais largo que alto)
            if aspect_ratio > 2.0:
                codigos_barras.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'contorno': contour
                })
    
    return codigos_barras

def detectar_regioes_texto_avancado(img):
    """Detecção avançada de regiões de texto (método que funcionou bem)"""
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # MÉTODO 1: MSER - Maximally Stable Extremal Regions (ótimo para texto)
    mser = cv2.MSER_create(
        _delta=5,
        _min_area=50,
        _max_area=14400,
        _max_variation=0.25,
        _min_diversity=0.2,
        _max_evolution=200,
        _area_threshold=1.01,
        _min_margin=0.003,
        _edge_blur_size=5
    )
    
    regions, _ = mser.detectRegions(gray)
    
    # Criar máscaras das regiões MSER
    mask_mser = np.zeros(gray.shape, dtype=np.uint8)
    for region in regions:
        hull = cv2.convexHull(region.reshape(-1, 1, 2))
        cv2.fillPoly(mask_mser, [hull], 255)
    
    # MÉTODO 2: Gradientes para texto
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_x = cv2.convertScaleAbs(grad_x)
    
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_y = cv2.convertScaleAbs(grad_y)
    
    grad_combinado = cv2.addWeighted(grad_x, 0.5, grad_y, 0.5, 0)
    _, thresh_grad = cv2.threshold(grad_combinado, 30, 255, cv2.THRESH_BINARY)
    
    # MÉTODO 3: Morfologia para conectar texto
    kernel_texto = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    thresh_grad = cv2.morphologyEx(thresh_grad, cv2.MORPH_CLOSE, kernel_texto)
    
    # Combinar métodos
    mask_texto_final = cv2.bitwise_or(mask_mser, thresh_grad)
    
    # Limpeza final
    kernel_limpar = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask_texto_final = cv2.morphologyEx(mask_texto_final, cv2.MORPH_OPEN, kernel_limpar)
    
    return mask_texto_final

def aplicar_zoom_super_focado(img_produto, regioes_texto, fator_zoom=5.0):
    """Zoom super focado nas regiões de texto (método que funcionou)"""
    
    # Encontrar contornos das regiões de texto
    contornos_texto, _ = cv2.findContours(regioes_texto, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regioes_zoom = []
    
    for i, contorno in enumerate(contornos_texto):
        area = cv2.contourArea(contorno)
        if area > 80:  # Área mínima para região de texto
            x, y, w, h = cv2.boundingRect(contorno)
            
            # Filtrar por aspecto (evitar ruídos)
            aspect_ratio = w / max(h, 1)
            if 0.1 <= aspect_ratio <= 10.0:  # Texto pode ser horizontal ou vertical
                
                # Adicionar margem generosa
                margem = 15
                x1 = max(0, x - margem)
                y1 = max(0, y - margem)
                x2 = min(img_produto.shape[1], x + w + margem)
                y2 = min(img_produto.shape[0], y + h + margem)
                
                # Extrair região
                regiao_texto = img_produto[y1:y2, x1:x2]
                
                if regiao_texto.size > 0 and regiao_texto.shape[0] > 5 and regiao_texto.shape[1] > 5:
                    # SUPER ZOOM na região de texto
                    nova_largura = int(regiao_texto.shape[1] * fator_zoom)
                    nova_altura = int(regiao_texto.shape[0] * fator_zoom)
                    
                    # Limitar tamanho máximo
                    if nova_largura > 3000:
                        fator_ajustado = 3000 / regiao_texto.shape[1]
                        nova_largura = 3000
                        nova_altura = int(regiao_texto.shape[0] * fator_ajustado)
                        fator_zoom_real = fator_ajustado
                    else:
                        fator_zoom_real = fator_zoom
                    
                    # Criar cópia dedicada antes do resize para evitar conflitos
                    regiao_texto_copia = regiao_texto.copy()
                    regiao_zoom = cv2.resize(
                        regiao_texto_copia, 
                        (nova_largura, nova_altura), 
                        interpolation=cv2.INTER_CUBIC
                    )
                    
                    regioes_zoom.append({
                        'indice': i,
                        'coordenadas': (x1, y1, x2, y2),
                        'imagem_original': regiao_texto,
                        'imagem_zoom': regiao_zoom,
                        'fator_zoom': fator_zoom_real,
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
    
    return regioes_zoom

def otimizar_para_ocr_super_focado(img_zoom):
    """Otimização para OCR em imagens super focadas"""
    
    # Conversão para escala de cinza
    gray = cv2.cvtColor(img_zoom, cv2.COLOR_BGR2GRAY) if len(img_zoom.shape) == 3 else img_zoom
    
    # Denoising leve
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    # CLAHE para contraste
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    contraste = clahe.apply(denoised)
    
    # Sharpening suave
    kernel_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(contraste, -1, kernel_sharp)
    
    # Binarização adaptativa
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return binary

def ocr_super_focado(img_otimizada, timeout=8):
    """OCR otimizado para regiões super focadas"""
    if not TESSERACT_DISPONIVEL:
        return []
    
    # Configurações específicas para texto ampliado
    configs = [
        ("Super Zoom - Palavra", "--psm 8 -l eng --dpi 300"),
        ("Super Zoom - Linha", "--psm 7 -l eng --dpi 300"),
        ("Super Zoom - Caractere", "--psm 10 -l eng --dpi 300"),
        ("Super Zoom - Geral", "--psm 6 -l por+eng --dpi 300"),
    ]
    
    resultados = []
    
    for nome, config in configs:
        try:
            texto = pytesseract.image_to_string(img_otimizada, config=config, timeout=timeout).strip()
            if texto and len(texto) > 0:
                # Limpeza focada
                texto_limpo = ''.join(char for char in texto if char.isalnum() or char.isspace()).strip()
                if texto_limpo and len(texto_limpo) >= 1:
                    resultados.append({
                        'config': nome,
                        'texto': texto_limpo,
                        'tamanho': len(texto_limpo),
                        'confianca': len(texto_limpo) / max(len(texto), 1)
                    })
        except Exception as e:
            continue
    
    return resultados

def main():
    """Pipeline final YOLO + Zoom super focado"""
    print("=" * 80)
    print("🚀 PIPELINE FINAL: YOLO + ZOOM SUPER FOCADO")
    print("🎯 Baseado no método que funcionou bem")
    print("=" * 80)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    modelo_yolo = r"C:\dataset_yolo_verifik\yolo_embalagens_best.pt"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_final_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"\n📥 Imagem: {largura}x{altura}")
    
    # ====================================
    # ETAPA 1: REMOÇÃO DE FUNDO
    # ====================================
    print("\n🎭 ETAPA 1: REMOÇÃO DE FUNDO")
    
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
    
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for contorno in contornos_grandes:
        cv2.fillPoly(mask, [contorno], 255)
    
    kernel_expansao = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_expandida = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel_expansao, iterations=3)
    
    img_sem_fundo = img.copy()
    img_sem_fundo[mask_expandida == 0] = [255, 255, 255]
    
    print(f"✓ Fundo removido")
    cv2.imwrite(os.path.join(pasta_resultado, "1_sem_fundo.jpg"), img_sem_fundo)
    
    # ====================================
    # ETAPA 2: YOLO PARA DETECTAR FORMAS (NA IMAGEM ORIGINAL)
    # ====================================
    print("\n🎯 ETAPA 2: DETECÇÃO YOLO DE FORMAS (IMAGEM ORIGINAL COM CONTEXTO)")
    
    deteccoes_yolo = []
    
    if YOLO_DISPONIVEL and os.path.exists(modelo_yolo):
        try:
            model = YOLO(modelo_yolo)
            print("✓ Modelo YOLO carregado")
            
            # Criar CÓPIA DEDICADA para YOLO (evitar conflito de acesso com OCR)
            img_yolo = img.copy()
            print("🎨 Rodando YOLO na cópia dedicada da imagem original (com cores e fundo para contexto)")
            resultados = model(img_yolo, verbose=False)
            
            img_com_yolo = img_yolo.copy()  # Visualização na cópia YOLO
            
            # DEBUG: Verificar todas as detecções encontradas
            total_deteccoes = 0
            deteccoes_rejeitadas = 0
            
            for resultado in resultados:
                boxes = resultado.boxes
                if boxes is not None:
                    total_deteccoes += len(boxes)
                    print(f"    🔍 YOLO encontrou {len(boxes)} detecções brutas")
                    
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confianca = float(box.conf[0])
                        classe_id = int(box.cls[0])
                        
                        nomes_classes = ['LATA_350ML', 'LATA_473ML', 'GARRAFA_LONG_NECK', 'GARRAFA_600ML', 'OUTROS']
                        classe_nome = nomes_classes[classe_id] if classe_id < len(nomes_classes) else f"CLASSE_{classe_id}"
                        
                        print(f"      📊 Detecção {i+1}: {classe_nome} - Confiança: {confianca:.3f}")
                        
                        # LIMIAR REDUZIDO DE 0.3 PARA 0.1
                        if confianca > 0.1:
                            # Desenhar bounding box na imagem original
                            cv2.rectangle(img_com_yolo, (x1, y1), (x2, y2), (0, 255, 0), 3)
                            cv2.putText(img_com_yolo, f"{classe_nome} {confianca:.2f}", 
                                      (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
                            deteccoes_yolo.append({
                                'classe': classe_nome,
                                'confianca': confianca,
                                'bbox': (x1, y1, x2, y2),
                                'area': (x2-x1) * (y2-y1)
                            })
                        else:
                            deteccoes_rejeitadas += 1
                            print(f"        ❌ REJEITADA - Confiança {confianca:.3f} < 0.1")
            
            # RELATÓRIO DE DEBUG
            print(f"    📊 RELATÓRIO YOLO:")
            print(f"      🔍 Total detectado: {total_deteccoes}")
            print(f"      ✅ Aceitas (>0.1): {len(deteccoes_yolo)}")
            print(f"      ❌ Rejeitadas (<0.1): {deteccoes_rejeitadas}")
            print(f"    ✓ {len(deteccoes_yolo)} produtos finais detectados pelo YOLO")
            cv2.imwrite(os.path.join(pasta_resultado, "2_deteccoes_yolo.jpg"), img_com_yolo)
            
        except Exception as e:
            print(f"❌ Erro no YOLO: {e}")
    else:
        print("❌ YOLO não disponível - usando detecção por contornos")
        
        # Fallback: usar contornos como "produtos"
        for i, contorno in enumerate(contornos_grandes):
            x, y, w, h = cv2.boundingRect(contorno)
            area = cv2.contourArea(contorno)
            aspect_ratio = w / h
            
            # Classificar por aspect ratio
            if aspect_ratio > 1.5:
                classe_estimada = "GARRAFA_LONG_NECK"
            elif aspect_ratio < 0.7:
                classe_estimada = "LATA_350ML"
            else:
                classe_estimada = "OUTROS"
            
            deteccoes_yolo.append({
                'classe': classe_estimada,
                'confianca': 0.8,
                'bbox': (x, y, x+w, y+h),
                'area': area
            })
        
        print(f"✓ {len(deteccoes_yolo)} produtos estimados por contornos")
    
    # ====================================
    # ETAPA 3: ZOOM SUPER FOCADO EM CADA PRODUTO YOLO
    # ====================================
    print("\n🔍 ETAPA 3: ZOOM SUPER FOCADO NOS PRODUTOS YOLO")
    
    todos_textos = []
    total_regioes_texto = 0
    
    for i, deteccao in enumerate(deteccoes_yolo):
        x1, y1, x2, y2 = deteccao['bbox']
        classe = deteccao['classe']
        confianca = deteccao['confianca']
        
        print(f"\n  📦 Produto {i+1}: {classe} (conf: {confianca:.2f})")
        
        # Criar CÓPIAS DEDICADAS para OCR (evitar conflito com YOLO)
        img_sem_fundo_copia = img_sem_fundo.copy()
        img_original_copia = img.copy()
        
        # Extrair região do produto YOLO da CÓPIA da imagem sem fundo (para OCR limpo)
        produto_yolo = img_sem_fundo_copia[y1:y2, x1:x2].copy()
        
        # Também salvar região original (com cores) para referência
        produto_original = img_original_copia[y1:y2, x1:x2].copy()
        cv2.imwrite(os.path.join(pasta_resultado, f"3a_yolo_produto_{i+1}_{classe}_original.jpg"), produto_original)
        
        # Salvar produto detectado pelo YOLO (sem fundo para OCR)
        cv2.imwrite(os.path.join(pasta_resultado, f"3b_yolo_produto_{i+1}_{classe}_sem_fundo.jpg"), produto_yolo)
        
        # ZOOM 3x no produto primeiro - CÓPIA DEDICADA
        produto_yolo_copia = produto_yolo.copy()
        produto_zoom = cv2.resize(produto_yolo_copia, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(os.path.join(pasta_resultado, f"4_produto_{i+1}_zoom_3x.jpg"), produto_zoom)
        
        print(f"    🔍 Produto ampliado 3x: {produto_zoom.shape[1]}x{produto_zoom.shape[0]}")
        
        # DETECTAR CÓDIGOS DE BARRAS
        codigos_barras = detectar_codigo_barras(produto_zoom)
        if codigos_barras:
            print(f"    📊 {len(codigos_barras)} códigos de barras detectados")
            for k, codigo in enumerate(codigos_barras):
                x, y, w, h = codigo['bbox']
                area = codigo['area']
                ratio = codigo['aspect_ratio']
                
                # Extrair região do código de barras com margem
                margem = 10
                x1 = max(0, x - margem)
                y1 = max(0, y - margem)  
                x2 = min(produto_zoom.shape[1], x + w + margem)
                y2 = min(produto_zoom.shape[0], y + h + margem)
                
                codigo_regiao = produto_zoom[y1:y2, x1:x2].copy()
                
                if codigo_regiao.size > 0:
                    # ZOOM EXTRA no código de barras (6x para números pequenos) - CÓPIA DEDICADA
                    codigo_regiao_copia = codigo_regiao.copy()
                    codigo_zoom = cv2.resize(codigo_regiao_copia, None, fx=6.0, fy=6.0, interpolation=cv2.INTER_CUBIC)
                    
                    # Salvar código de barras ampliado
                    cv2.imwrite(os.path.join(pasta_resultado, f"BARCODE_{classe}_produto_{i+1}_codigo_{k+1}_zoom_6x.jpg"), codigo_zoom)
                    
                    # OCR específico para códigos (apenas números)
                    codigo_otimizado = otimizar_para_ocr_super_focado(codigo_zoom)
                    cv2.imwrite(os.path.join(pasta_resultado, f"BARCODE_{classe}_produto_{i+1}_codigo_{k+1}_ocr.jpg"), codigo_otimizado)
                    
                    # OCR focado em números
                    try:
                        codigo_texto = pytesseract.image_to_string(codigo_otimizado, config="--psm 8 -c tessedit_char_whitelist=0123456789").strip()
                        if codigo_texto and len(codigo_texto) > 8:  # Códigos de barras têm pelo menos 8 dígitos
                            print(f"        📊 Código {k+1}: {codigo_texto}")
                            todos_textos.append({
                                'produto': i+1,
                                'classe_yolo': classe,
                                'regiao': f'BARCODE_{k+1}',
                                'config': 'Código de Barras',
                                'texto': codigo_texto,
                                'tamanho': len(codigo_texto)
                            })
                    except:
                        print(f"        ❌ Erro OCR código {k+1}")
        
        # DETECTAR REGIÕES DE TEXTO no produto ampliado - CÓPIA DEDICADA
        produto_zoom_copia_texto = produto_zoom.copy()
        regioes_texto = detectar_regioes_texto_avancado(produto_zoom_copia_texto)
        
        # ZOOM SUPER FOCADO nas regiões de texto - CÓPIAS DEDICADAS
        produto_zoom_copia_super = produto_zoom.copy()
        regioes_texto_copia = regioes_texto.copy()
        regioes_super_zoom = aplicar_zoom_super_focado(produto_zoom_copia_super, regioes_texto_copia, fator_zoom=5.0)
        
        print(f"    🎯 {len(regioes_super_zoom)} regiões de texto encontradas")
        total_regioes_texto += len(regioes_super_zoom)
        
        # OCR em cada região com super zoom
        for j, regiao in enumerate(regioes_super_zoom):
            img_texto_zoom = regiao['imagem_zoom']
            fator_zoom = regiao['fator_zoom']
            area_regiao = regiao['area']
            
            print(f"      🔍 Região {j+1}: {fator_zoom:.1f}x, área={area_regiao:.0f}")
            
            # Salvar região com super zoom
            cv2.imwrite(os.path.join(pasta_resultado, f"5_{classe}_produto_{i+1}_texto_{j+1}_zoom_{fator_zoom:.1f}x.jpg"), img_texto_zoom)
            
            # Otimizar para OCR
            img_otimizada = otimizar_para_ocr_super_focado(img_texto_zoom)
            cv2.imwrite(os.path.join(pasta_resultado, f"6_{classe}_produto_{i+1}_texto_{j+1}_ocr.jpg"), img_otimizada)
            
            # OCR super focado
            resultados_ocr = ocr_super_focado(img_otimizada, timeout=8)
            
            if resultados_ocr:
                for resultado in resultados_ocr:
                    print(f"        📖 {resultado['config']}: {repr(resultado['texto'])}")
                    todos_textos.append({
                        'produto': i+1,
                        'classe_yolo': classe,
                        'regiao': j+1,
                        'config': resultado['config'],
                        'texto': resultado['texto'],
                        'tamanho': resultado['tamanho']
                    })
            else:
                print(f"        ❌ Nenhum texto detectado")
    
    # ====================================
    # ANÁLISE INTELIGENTE - YOLO AGUARDA OCR PARA CONFIRMAÇÃO
    # ====================================
    print(f"\n🧠 ANÁLISE INTELIGENTE - YOLO + OCR COMPLEMENTARES")
    print(f"📊 Produtos YOLO: {len(deteccoes_yolo)}")
    print(f"🔍 Regiões de texto: {total_regioes_texto}")
    print(f"📖 Textos detectados: {len(todos_textos)}")
    
    # COMBINAÇÃO INTELIGENTE YOLO + OCR
    resultados_inteligentes = []
    
    # Agrupar textos por produto
    produtos_com_texto = {}
    for texto_info in todos_textos:
        produto_id = texto_info['produto']
        if produto_id not in produtos_com_texto:
            produtos_com_texto[produto_id] = {
                'classe_yolo': texto_info['classe_yolo'],
                'textos': [],
                'codigos_barras': [],
                'marcas': [],
                'volumes': []
            }
        
        texto = texto_info['texto'].upper()
        
        # Categorizar texto detectado
        if 'BARCODE' in texto_info.get('regiao', ''):
            produtos_com_texto[produto_id]['codigos_barras'].append(texto)
        elif any(marca in texto for marca in ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA']):
            produtos_com_texto[produto_id]['marcas'].append(texto)
        elif any(vol in texto for vol in ['350', '473', '600', 'ML']):
            produtos_com_texto[produto_id]['volumes'].append(texto)
        else:
            produtos_com_texto[produto_id]['textos'].append(texto)
    
    # ANÁLISE INTELIGENTE PRODUTO POR PRODUTO
    print(f"\n🔍 ANÁLISE DETALHADA POR PRODUTO:")
    
    for produto_id, info in produtos_com_texto.items():
        classe_yolo = info['classe_yolo']
        marcas = info['marcas']
        volumes = info['volumes']
        codigos = info['codigos_barras']
        outros_textos = info['textos']
        
        print(f"\n  📦 PRODUTO {produto_id}:")
        print(f"    🤖 YOLO detectou: {classe_yolo}")
        
        # CONFIRMAÇÃO INTELIGENTE
        confirmacao = "PENDENTE"
        volume_confirmado = ""
        marca_confirmada = ""
        codigo_confirmado = ""
        
        # Verificar se OCR confirma o volume detectado pelo YOLO
        if classe_yolo == 'LATA_350ML':
            if any('350' in vol for vol in volumes):
                confirmacao = "CONFIRMADO"
                volume_confirmado = "350ML"
                print(f"    ✅ OCR CONFIRMOU: Encontrou '350' no texto")
            else:
                print(f"    ⚠️ OCR NÃO CONFIRMOU: Não encontrou '350' nos textos")
        
        elif classe_yolo == 'LATA_473ML':
            if any('473' in vol for vol in volumes):
                confirmacao = "CONFIRMADO"  
                volume_confirmado = "473ML"
                print(f"    ✅ OCR CONFIRMOU: Encontrou '473' no texto")
            else:
                print(f"    ⚠️ OCR NÃO CONFIRMOU: Não encontrou '473' nos textos")
        
        elif classe_yolo == 'GARRAFA_600ML':
            if any('600' in vol for vol in volumes):
                confirmacao = "CONFIRMADO"
                volume_confirmado = "600ML"
                print(f"    ✅ OCR CONFIRMOU: Encontrou '600' no texto")
            else:
                print(f"    ⚠️ OCR NÃO CONFIRMOU: Não encontrou '600' nos textos")
        
        elif classe_yolo == 'GARRAFA_LONG_NECK':
            # Para Long Neck, aceitar vários volumes ou marca típica
            if volumes or any('CORONA' in marca or 'HEINEKEN' in marca for marca in marcas):
                confirmacao = "CONFIRMADO"
                volume_confirmado = "LONG NECK"
                print(f"    ✅ OCR CONFIRMOU: Long Neck com marca/volume detectado")
            else:
                print(f"    ⚠️ OCR AGUARDANDO: Long Neck precisa confirmar marca")
        
        # Extrair melhor marca
        if marcas:
            # Priorizar marcas conhecidas
            for marca_texto in marcas:
                for marca_conhecida in ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA']:
                    if marca_conhecida in marca_texto:
                        marca_confirmada = marca_conhecida
                        break
                if marca_confirmada:
                    break
        
        # Extrair melhor código
        if codigos:
            codigo_confirmado = codigos[0]  # Pegar primeiro código válido
        
        print(f"    📝 Marca detectada: {marca_confirmada or 'NÃO IDENTIFICADA'}")
        print(f"    📏 Volume: {volume_confirmado or 'NÃO CONFIRMADO'}")
        print(f"    📊 Código: {codigo_confirmado or 'NÃO DETECTADO'}")
        
        # RESULTADO FINAL INTELIGENTE
        if confirmacao == "CONFIRMADO":
            resultado_final = f"✅ {classe_yolo}"
            if marca_confirmada:
                resultado_final += f" - {marca_confirmada}"
            if volume_confirmado:
                resultado_final += f" - {volume_confirmado}"
            if codigo_confirmado:
                resultado_final += f" - {codigo_confirmado}"
            
            print(f"    🎯 RESULTADO FINAL: {resultado_final}")
            resultados_inteligentes.append(resultado_final)
            
        else:
            resultado_parcial = f"⚠️ {classe_yolo} (OCR não confirmou)"
            if marca_confirmada:
                resultado_parcial += f" - {marca_confirmada}"
            if outros_textos:
                resultado_parcial += f" - Textos: {', '.join(outros_textos[:2])}"
            
            print(f"    ⏳ RESULTADO PARCIAL: {resultado_parcial}")
            resultados_inteligentes.append(resultado_parcial)
    
    # PRODUTOS SEM TEXTO (apenas YOLO)
    produtos_com_texto_ids = set(produtos_com_texto.keys())
    for i, deteccao in enumerate(deteccoes_yolo, 1):
        if i not in produtos_com_texto_ids:
            classe = deteccao['classe']
            confianca = deteccao['confianca']
            resultado_yolo_only = f"🤖 {classe} (conf: {confianca:.2f}) - AGUARDANDO OCR"
            resultados_inteligentes.append(resultado_yolo_only)
            print(f"\n  📦 PRODUTO {i}: {resultado_yolo_only}")
    
    # Combinar também resultados simples para compatibilidade
    resultados_combinados = []
    for texto_info in todos_textos:
        resultado_combinado = f"{texto_info['classe_yolo']} - {texto_info['texto']}"
        resultados_combinados.append(resultado_combinado)
    
    # Verificar marcas e volumes
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA']
    volumes_conhecidos = ['350', '473', '600', 'ML']
    
    marcas_encontradas = set()
    volumes_encontrados = set()
    
    texto_completo = ' '.join([t['texto'] for t in todos_textos]).upper()
    
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            marcas_encontradas.add(marca)
    
    for volume in volumes_conhecidos:
        if volume in texto_completo:
            volumes_encontrados.add(volume)
    
    if marcas_encontradas:
        print(f"🍺 MARCAS: {', '.join(marcas_encontradas)}")
    
    if volumes_encontrados:
        print(f"📏 VOLUMES: {', '.join(volumes_encontrados)}")
    
    # RESULTADOS FINAIS INTELIGENTES
    print(f"\n🎯 RESULTADOS FINAIS INTELIGENTES:")
    for i, resultado in enumerate(resultados_inteligentes, 1):
        print(f"  {i:2d}. {resultado}")
    
    print(f"\n📋 RESULTADOS COMBINADOS TRADICIONAIS:")
    for i, resultado in enumerate(resultados_combinados, 1):
        print(f"  {i:2d}. {resultado}")
    
    # Salvar relatório final
    with open(os.path.join(pasta_resultado, "7_relatorio_final_yolo_zoom.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE FINAL: YOLO + ZOOM SUPER FOCADO ===\n\n")
        f.write(f"Imagem: {imagem_original}\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("DETECÇÕES YOLO:\n")
        for i, det in enumerate(deteccoes_yolo):
            f.write(f"- Produto {i+1}: {det['classe']} (conf: {det['confianca']:.2f})\n")
        
        f.write(f"\nTOTAL DE REGIÕES DE TEXTO: {total_regioes_texto}\n\n")
        
        f.write("RESULTADOS INTELIGENTES (YOLO AGUARDA OCR):\n")
        for resultado in resultados_inteligentes:
            f.write(f"- {resultado}\n")
        
        f.write(f"\nRESULTADOS COMBINADOS TRADICIONAIS:\n")
        for resultado in resultados_combinados:
            f.write(f"- {resultado}\n")
        
        if marcas_encontradas:
            f.write(f"\nMARCAS IDENTIFICADAS: {', '.join(marcas_encontradas)}\n")
        
        if volumes_encontrados:
            f.write(f"VOLUMES IDENTIFICADOS: {', '.join(volumes_encontrados)}\n")
    
    print(f"\n📁 Resultados em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 80)
    print("🎉 PIPELINE FINAL CONCLUÍDO!")
    print("✅ YOLO detectou formas + Zoom super focado + OCR otimizado")
    print("✅ Combinação perfeita de classificação + texto")
    print("=" * 80)

if __name__ == "__main__":
    main()