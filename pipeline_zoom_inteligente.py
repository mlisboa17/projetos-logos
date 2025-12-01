#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COM ZOOM/AUMENTO INTELIGENTE
Aplica zoom nas regiões dos produtos para melhorar OCR
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

def detectar_produtos_precisos(img):
    """Detecta produtos com maior precisão"""
    
    # Método combinado: cor + bordas
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_cor = cv2.inRange(hsv, (0, 30, 30), (179, 255, 255))
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    mask_combinada = cv2.bitwise_or(mask_cor, edges)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_combinada = cv2.morphologyEx(mask_combinada, cv2.MORPH_CLOSE, kernel)
    mask_combinada = cv2.morphologyEx(mask_combinada, cv2.MORPH_OPEN, kernel)
    
    contornos, _ = cv2.findContours(mask_combinada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area > 5000:
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / h
            
            if 0.3 <= aspect_ratio <= 3.0:
                produtos.append({
                    'contorno': contorno,
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio
                })
    
    return produtos

def aplicar_zoom_inteligente(img_produto, fator_zoom=3.0):
    """
    Aplica zoom inteligente na imagem do produto
    fator_zoom: 2.0 = 2x, 3.0 = 3x, 4.0 = 4x etc.
    """
    altura_original, largura_original = img_produto.shape[:2]
    
    # Calcular novas dimensões
    nova_largura = int(largura_original * fator_zoom)
    nova_altura = int(altura_original * fator_zoom)
    
    # MÉTODO 1: Interpolação cúbica (melhor qualidade)
    img_zoom_cubica = cv2.resize(
        img_produto, 
        (nova_largura, nova_altura), 
        interpolation=cv2.INTER_CUBIC
    )
    
    # MÉTODO 2: Super-resolução com filtros
    # Aplicar filtro gaussiano antes do zoom para suavizar
    img_suavizada = cv2.GaussianBlur(img_produto, (3, 3), 0)
    img_zoom_suave = cv2.resize(
        img_suavizada,
        (nova_largura, nova_altura),
        interpolation=cv2.INTER_LANCZOS4
    )
    
    # MÉTODO 3: Combinar ambos os métodos
    img_zoom_final = cv2.addWeighted(img_zoom_cubica, 0.7, img_zoom_suave, 0.3, 0)
    
    return img_zoom_final, fator_zoom

def detectar_regioes_texto(img):
    """Detecta especificamente regiões que podem conter texto"""
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # MÉTODO 1: Detecção de regiões de texto usando gradientes
    # Gradiente horizontal (texto geralmente tem mudanças horizontais)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_x = cv2.convertScaleAbs(grad_x)
    
    # Gradiente vertical
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_y = cv2.convertScaleAbs(grad_y)
    
    # Combinar gradientes
    grad_combinado = cv2.addWeighted(grad_x, 0.5, grad_y, 0.5, 0)
    
    # Threshold para destacar regiões com gradientes fortes
    _, thresh_grad = cv2.threshold(grad_combinado, 50, 255, cv2.THRESH_BINARY)
    
    # MÉTODO 2: MSER (Maximally Stable Extremal Regions) - ótimo para texto
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)
    
    # Criar máscara das regiões MSER
    mask_mser = np.zeros(gray.shape, dtype=np.uint8)
    for region in regions:
        hull = cv2.convexHull(region.reshape(-1, 1, 2))
        cv2.fillPoly(mask_mser, [hull], 255)
    
    # Combinar métodos
    mask_texto = cv2.bitwise_or(thresh_grad, mask_mser)
    
    # Limpeza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask_texto = cv2.morphologyEx(mask_texto, cv2.MORPH_CLOSE, kernel)
    
    return mask_texto

def zoom_super_focado(img_produto, regioes_texto):
    """Aplica zoom extra nas regiões de texto detectadas"""
    
    # Encontrar contornos das regiões de texto
    contornos_texto, _ = cv2.findContours(regioes_texto, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regioes_zoom = []
    
    for i, contorno in enumerate(contornos_texto):
        area = cv2.contourArea(contorno)
        if area > 100:  # Área mínima para região de texto
            x, y, w, h = cv2.boundingRect(contorno)
            
            # Adicionar margem
            margem = 10
            x1 = max(0, x - margem)
            y1 = max(0, y - margem)
            x2 = min(img_produto.shape[1], x + w + margem)
            y2 = min(img_produto.shape[0], y + h + margem)
            
            # Extrair região
            regiao_texto = img_produto[y1:y2, x1:x2]
            
            if regiao_texto.size > 0:
                # SUPER ZOOM na região de texto (5x)
                regiao_zoom, fator = aplicar_zoom_inteligente(regiao_texto, fator_zoom=5.0)
                
                regioes_zoom.append({
                    'indice': i,
                    'coordenadas': (x1, y1, x2, y2),
                    'imagem_original': regiao_texto,
                    'imagem_zoom': regiao_zoom,
                    'fator_zoom': fator
                })
    
    return regioes_zoom

def otimizar_para_ocr_zoom(img_zoom):
    """Otimização específica para imagens com zoom"""
    
    # 1. Conversão para escala de cinza
    gray = cv2.cvtColor(img_zoom, cv2.COLOR_BGR2GRAY) if len(img_zoom.shape) == 3 else img_zoom
    
    # 2. Denoising mais agressivo (imagem com zoom pode ter mais ruído)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    # 3. CLAHE adaptado para zoom
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    contraste = clahe.apply(denoised)
    
    # 4. Sharpening suave (zoom pode deixar borrado)
    kernel_sharp = np.array([[0, -1, 0],
                            [-1, 5, -1],
                            [0, -1, 0]])
    sharpened = cv2.filter2D(contraste, -1, kernel_sharp)
    
    # 5. Binarização adaptativa para texto
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return binary

def ocr_zoom_otimizado(img_otimizada):
    """OCR otimizado para imagens com zoom"""
    if not TESSERACT_DISPONIVEL:
        return []
    
    # Configurações especiais para texto ampliado
    configs = [
        ("Zoom - Texto geral", "--psm 6 -l por+eng --dpi 300"),
        ("Zoom - Linha única", "--psm 7 -l eng --dpi 300"),
        ("Zoom - Palavra única", "--psm 8 -l eng --dpi 300"),
        ("Zoom - Caractere único", "--psm 10 -l eng --dpi 300"),
        ("Zoom - Texto livre", "--psm 3 -l por+eng --dpi 300"),
    ]
    
    resultados = []
    
    for nome, config in configs:
        try:
            # OCR com DPI alto para imagens ampliadas
            texto = pytesseract.image_to_string(img_otimizada, config=config).strip()
            if texto and len(texto) > 0:
                # Limpeza mais rigorosa
                texto_limpo = ''.join(char for char in texto if char.isalnum() or char.isspace())
                if texto_limpo and len(texto_limpo) > 1:
                    resultados.append({
                        'config': nome,
                        'texto': texto_limpo,
                        'confianca': len(texto_limpo) / max(len(texto), 1)
                    })
        except Exception as e:
            continue
    
    return resultados

def main():
    """Pipeline principal com zoom inteligente"""
    print("=" * 70)
    print("🔍 PIPELINE COM ZOOM INTELIGENTE - LENTE DE AUMENTO")
    print("=" * 70)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_zoom_{timestamp}"
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
    # ETAPA 2: DETECTAR PRODUTOS
    # ====================================
    print("\n🔍 ETAPA 2: DETECÇÃO DE PRODUTOS")
    
    produtos = detectar_produtos_precisos(img_sem_fundo)
    print(f"✓ {len(produtos)} produtos detectados")
    
    # ====================================
    # ETAPA 3: ZOOM INTELIGENTE EM CADA PRODUTO
    # ====================================
    print("\n🔍 ETAPA 3: APLICANDO ZOOM INTELIGENTE")
    
    todos_textos = []
    total_regioes_zoom = 0
    
    for i, produto in enumerate(produtos):
        print(f"\n  📦 Produto {i+1}:")
        
        # Extrair produto
        x, y, w, h = produto['bbox']
        margem = 20
        x1 = max(0, x - margem)
        y1 = max(0, y - margem)
        x2 = min(img_sem_fundo.shape[1], x + w + margem)
        y2 = min(img_sem_fundo.shape[0], y + h + margem)
        
        produto_original = img_sem_fundo[y1:y2, x1:x2]
        
        # ZOOM GERAL no produto (3x)
        produto_zoom, fator_geral = aplicar_zoom_inteligente(produto_original, fator_zoom=3.0)
        print(f"    🔍 Zoom geral: {fator_geral}x ({produto_zoom.shape[1]}x{produto_zoom.shape[0]})")
        
        # Salvar produto com zoom geral
        cv2.imwrite(os.path.join(pasta_resultado, f"2_produto_{i+1}_zoom_3x.jpg"), produto_zoom)
        
        # DETECTAR REGIÕES DE TEXTO no produto ampliado
        regioes_texto = detectar_regioes_texto(produto_zoom)
        
        # SUPER ZOOM nas regiões de texto (5x adicional)
        regioes_super_zoom = zoom_super_focado(produto_zoom, regioes_texto)
        
        print(f"    🎯 {len(regioes_super_zoom)} regiões de texto encontradas")
        total_regioes_zoom += len(regioes_super_zoom)
        
        # OCR em cada região com super zoom
        for j, regiao in enumerate(regioes_super_zoom):
            img_texto = regiao['imagem_zoom']
            fator_zoom = regiao['fator_zoom']
            
            print(f"      🔍 Região {j+1}: Super zoom {fator_zoom}x ({img_texto.shape[1]}x{img_texto.shape[0]})")
            
            # Salvar região com super zoom
            cv2.imwrite(os.path.join(pasta_resultado, f"3_produto_{i+1}_texto_{j+1}_zoom_{fator_zoom}x.jpg"), img_texto)
            
            # Otimizar para OCR
            img_otimizada = otimizar_para_ocr_zoom(img_texto)
            cv2.imwrite(os.path.join(pasta_resultado, f"4_produto_{i+1}_texto_{j+1}_ocr.jpg"), img_otimizada)
            
            # OCR otimizado para zoom
            resultados_ocr = ocr_zoom_otimizado(img_otimizada)
            
            if resultados_ocr:
                for resultado in resultados_ocr:
                    print(f"        📖 {resultado['config']}: {repr(resultado['texto'])}")
                    todos_textos.append(f"Produto {i+1} Região {j+1} - {resultado['config']}: {resultado['texto']}")
            else:
                print(f"        ❌ Nenhum texto detectado nesta região")
    
    # ====================================
    # ANÁLISE FINAL
    # ====================================
    print(f"\n🎉 ANÁLISE FINAL COM ZOOM")
    print(f"📊 Total de produtos: {len(produtos)}")
    print(f"🔍 Total de regiões com super zoom: {total_regioes_zoom}")
    print(f"📖 Total de textos detectados: {len(todos_textos)}")
    
    # Verificar marcas
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA', 'BEER', 'CERVEJA']
    marcas_encontradas = set()
    
    texto_completo = ' '.join(todos_textos).upper()
    
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            marcas_encontradas.add(marca)
    
    if marcas_encontradas:
        print(f"🍺 Marcas identificadas: {', '.join(marcas_encontradas)}")
    else:
        print("📝 Nenhuma marca específica identificada")
    
    # Salvar relatório
    with open(os.path.join(pasta_resultado, "5_relatorio_zoom.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE COM ZOOM INTELIGENTE ===\n\n")
        f.write(f"Imagem processada: {imagem_original}\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write(f"PRODUTOS DETECTADOS: {len(produtos)}\n")
        f.write(f"REGIÕES COM SUPER ZOOM: {total_regioes_zoom}\n\n")
        
        f.write("TÉCNICAS DE ZOOM APLICADAS:\n")
        f.write("- Zoom geral nos produtos: 3x\n")
        f.write("- Super zoom nas regiões de texto: 5x\n")
        f.write("- Interpolação cúbica + Lanczos4\n")
        f.write("- OCR com DPI 300 para imagens ampliadas\n\n")
        
        f.write("TEXTOS DETECTADOS:\n")
        for texto in todos_textos:
            f.write(f"- {texto}\n")
        
        if marcas_encontradas:
            f.write(f"\nMARCAS IDENTIFICADAS:\n")
            for marca in marcas_encontradas:
                f.write(f"- {marca}\n")
    
    print(f"\n📁 Resultados em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 70)
    print("🔍 PIPELINE COM ZOOM CONCLUÍDO!")
    print("✅ Zoom 3x nos produtos + Super zoom 5x no texto")
    print("✅ Imagens ampliadas para melhor OCR")
    print("=" * 70)

if __name__ == "__main__":
    main()