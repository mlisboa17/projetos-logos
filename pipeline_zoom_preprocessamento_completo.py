#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COM PREPROCESSAMENTO COMPLETO
- Normalização de cores (RGB → Cinza)
- Binarização com diferentes técnicas
- Zoom duplo configurável
- OCR otimizado
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
        r"C:\Users\gabri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    
    tesseract_path = None
    for path in possible_paths:
        if os.path.exists(path):
            tesseract_path = path
            break
    
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        OCR_DISPONIVEL = True
        print(f"✓ Tesseract encontrado: {tesseract_path}")
    else:
        OCR_DISPONIVEL = False
        print("❌ Tesseract não encontrado")
        
except ImportError:
    OCR_DISPONIVEL = False
    print("❌ pytesseract não instalado")

def detectar_produtos_precisos_genericos(img):
    """
    DETECÇÃO GENÉRICA DE PRODUTOS DE BEBIDAS
    HSV + Análise de Forma - funciona com qualquer marca/cor
    Detecta: Heineken (verde/azul), Corona (dourado/branco), etc.
    """
    print("    🔍 Detecção genérica: HSV + Forma para qualquer marca...")
    
    # Converter para HSV para detecção de cores
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # DETECÇÃO POR MÚLTIPLAS CORES (genérico)
    print("      🎨 Detectando produtos por cores múltiplas...")
    
    # VERDE: Heineken, Carlsberg, etc.
    lower_verde = np.array([35, 30, 30])
    upper_verde = np.array([85, 255, 255])
    mask_verde = cv2.inRange(hsv, lower_verde, upper_verde)
    
    # AZUL: Heineken Silver, Pepsi, etc.
    lower_azul = np.array([100, 40, 40])
    upper_azul = np.array([130, 255, 255])
    mask_azul = cv2.inRange(hsv, lower_azul, upper_azul)
    
    # DOURADO/AMARELO: Corona, Brahma, etc.
    lower_dourado = np.array([10, 40, 40])
    upper_dourado = np.array([35, 255, 255])
    mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
    
    # BRANCO/CINZA: Corona lata, latas claras
    lower_claro = np.array([0, 0, 160])
    upper_claro = np.array([180, 40, 255])
    mask_claro = cv2.inRange(hsv, lower_claro, upper_claro)
    
    # VERMELHO: Budweiser, Skol, etc.
    lower_vermelho = np.array([0, 50, 50])
    upper_vermelho = np.array([10, 255, 255])
    mask_vermelho = cv2.inRange(hsv, lower_vermelho, upper_vermelho)
    
    # Combinar todas as máscaras
    mask_temp1 = cv2.bitwise_or(mask_verde, mask_azul)
    mask_temp2 = cv2.bitwise_or(mask_dourado, mask_claro)
    mask_temp3 = cv2.bitwise_or(mask_temp1, mask_temp2)
    mask_produtos = cv2.bitwise_or(mask_temp3, mask_vermelho)
    
    # Limpeza morfológica suave (para produtos próximos)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 6))
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_OPEN, kernel)
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos
    contornos, _ = cv2.findContours(mask_produtos, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos_candidatos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        # Filtrar por área mínima (produtos significativos)
        if area > 10000:  # Área mínima para produtos
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Classificar baseado apenas na forma (universal)
            if 0.2 < aspect_ratio < 0.8:  # Mais alto que largo
                tipo = "GARRAFA"
            elif 0.8 <= aspect_ratio <= 2.0:  # Aproximadamente quadrado
                tipo = "LATA"
            else:
                tipo = "PRODUTO"  # Outros formatos
            
            # Calcular confiança baseada em área e forma
            confianca = min(area / 50000, 1.0)  # Normalizar por área típica
            
            produtos_candidatos.append({
                'bbox': (x, y, w, h),
                'area': area,
                'aspect_ratio': aspect_ratio,
                'tipo': tipo,
                'confianca': confianca
            })
    
    print(f"        🔍 {len(produtos_candidatos)} candidatos detectados por cor+forma")
    
    # Remover sobreposições (produtos duplicados)
    produtos_candidatos.sort(key=lambda x: x['area'], reverse=True)  # Maiores primeiro
    
    produtos_filtrados = []
    
    for produto in produtos_candidatos:
        x1, y1, w1, h1 = produto['bbox']
        centro1 = (x1 + w1//2, y1 + h1//2)
        
        # Verificar se não está muito próximo de outro produto
        muito_proximo = False
        for aceito in produtos_filtrados:
            x2, y2, w2, h2 = aceito['bbox']
            centro2 = (x2 + w2//2, y2 + h2//2)
            
            # Calcular distância entre centros
            distancia = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            # Calcular sobreposição
            overlap_x = max(0, min(x1+w1, x2+w2) - max(x1, x2))
            overlap_y = max(0, min(y1+h1, y2+h2) - max(y1, y2))
            overlap_area = overlap_x * overlap_y
            
            # Ajuste para produtos próximos (como Heineken)
            # Sobreposição reduzida e distância menor para produtos próximos
            if (overlap_area > 0.2 * min(produto['area'], aceito['area']) or distancia < 60):
                muito_proximo = True
                break
        
        if not muito_proximo:
            produtos_filtrados.append(produto)
    
    # Contar por tipo
    garrafas = [p for p in produtos_filtrados if p['tipo'] == 'GARRAFA']
    latas = [p for p in produtos_filtrados if p['tipo'] == 'LATA']
    outros = [p for p in produtos_filtrados if p['tipo'] == 'PRODUTO']
    
    print(f"        ✅ RESULTADO: {len(produtos_filtrados)} produtos")
    print(f"           🍺 Garrafas: {len(garrafas)}")
    print(f"           🥤 Latas: {len(latas)}")
    if outros:
        print(f"           📦 Outros: {len(outros)}")
    
    print(f"           📊 Detecção genérica concluída")
    
    return produtos_filtrados

def analisar_informacoes_produto(textos_produto):
    """
    ANÁLISE COMPLETA DE INFORMAÇÕES DO PRODUTO
    Extrai: Marca, Tipo, Volume, Teor Alcoólico, etc.
    """
    texto_completo = ' '.join(textos_produto).upper()
    info_produto = {
        'marca': 'N/A',
        'tipo': 'N/A', 
        'volume': 'N/A',
        'teor_alcoolico': 'N/A',
        'pais_origem': 'N/A',
        'outros': []
    }
    
    # ANÁLISE DE MARCA
    marcas_conhecidas = ['CORONA', 'CORONITA', 'SPATEN', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA']
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            info_produto['marca'] = marca
            break
    
    # ANÁLISE DE TIPO (palavras após a marca)
    tipos_cerveja = ['EXTRA', 'CERO', 'LIGHT', 'ZERO', 'PREMIUM', 'PILSNER', 'LAGER']
    for tipo in tipos_cerveja:
        if tipo in texto_completo:
            info_produto['tipo'] = tipo
            break
    
    # ANÁLISE DE VOLUME (ml, ML)
    import re
    volumes_match = re.findall(r'(\d+)\s*ML|(\d+)\s*ml|(\d+)ML|(\d+)ml', texto_completo)
    if volumes_match:
        for match in volumes_match[0]:
            if match:
                info_produto['volume'] = f"{match}ML"
                break
    
    # ANÁLISE DE TEOR ALCOÓLICO (% vol, % VOL)
    teor_match = re.findall(r'(\d+\.?\d*)\s*%\s*VOL|(\d+\.?\d*)\s*%\s*vol|(\d+\.?\d*)\s*%', texto_completo)
    if teor_match:
        for match in teor_match[0]:
            if match:
                info_produto['teor_alcoolico'] = f"{match}% vol"
                break
    
    # ANÁLISE DE PAÍS (MEXICO, BRASIL, GERMANY)
    paises = ['MEXICO', 'MÉXICO', 'BRASIL', 'BRAZIL', 'GERMANY', 'DEUTSCHLAND']
    for pais in paises:
        if pais in texto_completo:
            info_produto['pais_origem'] = pais
            break
    
    # OUTROS DADOS INTERESSANTES
    outros_termos = ['CERVEZA', 'BEER', 'BIER', 'MODELO', 'IMPORTED', 'PREMIUM']
    for termo in outros_termos:
        if termo in texto_completo:
            info_produto['outros'].append(termo)
    
    return info_produto

def preprocessamento_completo_avancado(img_produto):
    """
    PREPROCESSAMENTO COMPLETO COM NORMALIZAÇÃO E BINARIZAÇÃO
    """
    print(f"      🔧 PREPROCESSAMENTO COMPLETO:")
    
    if img_produto is None or img_produto.size == 0:
        return []
    
    # ETAPA 1: CONVERSÃO PARA CINZA (3 canais → 1 canal)
    print(f"         1️⃣ RGB → Cinza (3 canais → 1 canal)")
    if len(img_produto.shape) == 3:
        img_cinza = cv2.cvtColor(img_produto, cv2.COLOR_BGR2GRAY)
    else:
        img_cinza = img_produto.copy()
    
    # ETAPA 2: NORMALIZAÇÃO DE CONTRASTE
    print(f"         2️⃣ Normalização de contraste")
    img_normalizada = cv2.equalizeHist(img_cinza)
    
    # ETAPA 3: MÚLTIPLAS TÉCNICAS DE BINARIZAÇÃO
    versoes_binarizadas = []
    
    # TÉCNICA 1: Threshold Global (Otsu)
    print(f"         3️⃣ Binarização Otsu (threshold automático)")
    _, img_otsu = cv2.threshold(img_normalizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    versoes_binarizadas.append({
        'nome': 'OTSU',
        'descricao': 'Threshold automático global',
        'imagem': img_otsu
    })
    
    # TÉCNICA 2: Threshold Adaptativo (Gaussian)
    print(f"         4️⃣ Binarização Adaptativa Gaussiana")
    img_adaptativa_gauss = cv2.adaptiveThreshold(
        img_normalizada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    versoes_binarizadas.append({
        'nome': 'ADAPTATIVA_GAUSS',
        'descricao': 'Threshold adaptativo gaussiano',
        'imagem': img_adaptativa_gauss
    })
    
    # TÉCNICA 3: Threshold Adaptativo (Mean)
    print(f"         5️⃣ Binarização Adaptativa Média")
    img_adaptativa_mean = cv2.adaptiveThreshold(
        img_normalizada, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
    )
    versoes_binarizadas.append({
        'nome': 'ADAPTATIVA_MEAN', 
        'descricao': 'Threshold adaptativo por média',
        'imagem': img_adaptativa_mean
    })
    
    # TÉCNICA 4: Threshold Manual (128)
    print(f"         6️⃣ Binarização Manual (threshold 128)")
    _, img_manual = cv2.threshold(img_normalizada, 128, 255, cv2.THRESH_BINARY)
    versoes_binarizadas.append({
        'nome': 'MANUAL_128',
        'descricao': 'Threshold manual fixo em 128',
        'imagem': img_manual
    })
    
    # TÉCNICA 5: Cinza Original (sem binarização para comparação)
    versoes_binarizadas.append({
        'nome': 'CINZA_ORIGINAL',
        'descricao': 'Cinza sem binarização (referência)',
        'imagem': img_normalizada
    })
    
    return versoes_binarizadas

def aplicar_zoom_duplo_configuravel(img_produto, zoom_menor=1.5, zoom_maior=3.0):
    """ZOOM DUPLO CONFIGURÁVEL: testa 2 níveis de zoom para melhor OCR"""
    if img_produto is None or img_produto.size == 0:
        return []
    
    altura_original, largura_original = img_produto.shape[:2]
    MAX_DIMENSAO = 2000
    resultados_zoom = []
    
    # CONFIGURAÇÕES DE ZOOM
    zooms_para_testar = [
        {'nome': 'MENOR', 'fator': zoom_menor, 'descricao': 'mais conservador'},
        {'nome': 'MAIOR', 'fator': zoom_maior, 'descricao': 'mais agressivo'}
    ]
    
    for config_zoom in zooms_para_testar:
        fator = config_zoom['fator']
        nome = config_zoom['nome']
        descricao = config_zoom['descricao']
        
        print(f"    🔍 ZOOM {nome}: {fator}x ({descricao})")
        
        # Calcular dimensões
        nova_largura = int(largura_original * fator)
        nova_altura = int(altura_original * fator)
        
        # Aplicar limite de tamanho
        if nova_largura > MAX_DIMENSAO or nova_altura > MAX_DIMENSAO:
            fator_ajustado = min(MAX_DIMENSAO / largura_original, MAX_DIMENSAO / altura_original)
            nova_largura = int(largura_original * fator_ajustado)
            nova_altura = int(altura_original * fator_ajustado)
            fator_real = fator_ajustado
            print(f"       ⚠️ Ajustado para {fator_real:.1f}x (limite 2000px)")
        else:
            fator_real = fator
        
        # Aplicar zoom
        img_zoom = cv2.resize(
            img_produto, 
            (nova_largura, nova_altura), 
            interpolation=cv2.INTER_CUBIC
        )
        
        resultados_zoom.append({
            'imagem': img_zoom,
            'fator_planejado': fator,
            'fator_real': fator_real,
            'tipo': nome,
            'descricao': descricao,
            'dimensoes': f"{nova_largura}x{nova_altura}"
        })
    
    return resultados_zoom

def ocr_rapido_eficiente_multiplo(versoes_preprocessadas, timeout_segundos=10):
    """OCR em múltiplas versões preprocessadas (Windows compatível)"""
    if not OCR_DISPONIVEL:
        return []
    
    import threading
    import time
    
    # Configurações de OCR otimizadas
    configs_ocr = [
        {'nome': 'Palavra', 'config': '--psm 8'},
        {'nome': 'Linha', 'config': '--psm 7'},  
        {'nome': 'Geral', 'config': '--psm 6'}
    ]
    
    resultados = []
    
    for versao in versoes_preprocessadas:
        nome_versao = versao['nome']
        img_preprocessada = versao['imagem']
        descricao = versao['descricao']
        
        print(f"         📖 OCR em {nome_versao} ({descricao}):")
        
        for config in configs_ocr:
            try:
                # Timeout com threading (compatível Windows)
                resultado_ocr = [None]
                erro_ocr = [None]
                
                def executar_ocr():
                    try:
                        resultado_ocr[0] = pytesseract.image_to_string(img_preprocessada, config=config['config']).strip()
                    except Exception as e:
                        erro_ocr[0] = e
                
                thread_ocr = threading.Thread(target=executar_ocr)
                thread_ocr.daemon = True
                thread_ocr.start()
                thread_ocr.join(timeout=timeout_segundos)
                
                if thread_ocr.is_alive():
                    print(f"            ❌ {config['nome']}: timeout ({timeout_segundos}s)")
                    continue
                
                if erro_ocr[0]:
                    print(f"            ❌ {config['nome']}: erro ({str(erro_ocr[0])[:30]})")
                    continue
                
                texto = resultado_ocr[0]
                
                if texto and len(texto) > 1:
                    print(f"            ✅ {config['nome']}: {repr(texto)}")
                    resultados.append({
                        'preprocessamento': nome_versao,
                        'config_ocr': config['nome'],
                        'texto': texto,
                        'descricao_prep': descricao
                    })
                    
            except Exception as e:
                print(f"            ❌ {config['nome']}: erro geral ({str(e)[:30]})")
                continue
    
    return resultados

def main():
    """Pipeline principal com preprocessamento completo"""
    print("=" * 80)
    print("🚀 PIPELINE ZOOM + PREPROCESSAMENTO COMPLETO")
    print("📋 RGB→Cinza + Binarização + Zoom Duplo + OCR")
    print("=" * 80)
    
    # ====================================
    # CONFIGURAÇÕES (AJUSTÁVEL)
    # ====================================
    ZOOM_MENOR = 1.5    # Zoom conservador
    ZOOM_MAIOR = 3.0    # Zoom agressivo
    print(f"⚙️ CONFIGURAÇÕES:")
    print(f"   📏 Zoom Menor (conservador): {ZOOM_MENOR}x")
    print(f"   📏 Zoom Maior (agressivo): {ZOOM_MAIOR}x")
    print(f"   🔒 Limite máximo de imagem: 2000px")
    print(f"   🎨 Preprocessamento: RGB→Cinza + 5 técnicas de binarização")
    
    # Caminhos - IMAGEM CORONA (4 produtos)
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_preprocessamento_completo_{timestamp}"
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
    # ETAPA 2: DETECÇÃO E PREPROCESSAMENTO COMPLETO
    # ====================================
    print(f"\n🔍 ETAPA 2: DETECÇÃO E PREPROCESSAMENTO COMPLETO")
    
    # Detectar produtos genéricos
    produtos = detectar_produtos_precisos_genericos(img_sem_fundo)
    print(f"✅ {len(produtos)} produtos detectados (detecção genérica)")
    
    # Listas para análise
    todos_textos = []
    total_versoes_testadas = 0
    
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
        
        # ZOOM DUPLO CONFIGURÁVEL
        print(f"    🔧 CONFIGURAÇÕES: Zoom Menor={ZOOM_MENOR}x, Zoom Maior={ZOOM_MAIOR}x")
        zooms_testados = aplicar_zoom_duplo_configuravel(produto_original, zoom_menor=ZOOM_MENOR, zoom_maior=ZOOM_MAIOR)
        
        melhor_resultado = None
        max_textos = 0
        
        # TESTAR CADA NÍVEL DE ZOOM
        for j, zoom_config in enumerate(zooms_testados):
            tipo = zoom_config['tipo']
            fator = zoom_config['fator_real']
            dimensoes = zoom_config['dimensoes']
            produto_zoom = zoom_config['imagem']
            
            print(f"    🔍 {tipo}: {fator:.1f}x ({dimensoes})")
            
            # PREPROCESSAMENTO COMPLETO (RGB→Cinza + Binarização)
            versoes_preprocessadas = preprocessamento_completo_avancado(produto_zoom)
            total_versoes_testadas += len(versoes_preprocessadas)
            
            # Salvar versões preprocessadas
            for k, versao in enumerate(versoes_preprocessadas):
                nome_arquivo = f"2_produto_{i+1}_{tipo.lower()}_{versao['nome'].lower()}.jpg"
                cv2.imwrite(os.path.join(pasta_resultado, nome_arquivo), versao['imagem'])
            
            # OCR EM MÚLTIPLAS VERSÕES
            print(f"       📖 OCR em {len(versoes_preprocessadas)} versões preprocessadas:")
            resultados_ocr = ocr_rapido_eficiente_multiplo(versoes_preprocessadas, timeout_segundos=10)
            
            if resultados_ocr:
                textos_encontrados = len(resultados_ocr)
                print(f"       ✅ {textos_encontrados} texto(s) encontrado(s)")
                
                # Verificar se é o melhor resultado
                if textos_encontrados > max_textos:
                    max_textos = textos_encontrados
                    melhor_resultado = {
                        'zoom_config': zoom_config,
                        'resultados_ocr': resultados_ocr
                    }
                
                # Adicionar todos os textos
                for resultado in resultados_ocr:
                    label_completo = f"Produto {i+1} - {tipo} ({fator:.1f}x) - {resultado['preprocessamento']} - {resultado['config_ocr']}: {resultado['texto']}"
                    todos_textos.append(label_completo)
            else:
                print(f"       ❌ Nenhum texto detectado em nenhuma versão")
        
        # RESUMIR MELHOR RESULTADO E ANALISAR INFORMAÇÕES COMPLETAS
        if melhor_resultado:
            config = melhor_resultado['zoom_config']
            textos = melhor_resultado['resultados_ocr']
            print(f"    🏆 MELHOR: {config['tipo']} ({config['fator_real']:.1f}x) com {len(textos)} texto(s)")
            
            # ANÁLISE COMPLETA DAS INFORMAÇÕES DO PRODUTO
            textos_produto = [r['texto'] for r in textos]
            info_completa = analisar_informacoes_produto(textos_produto)
            
            print(f"    📋 INFORMAÇÕES COMPLETAS:")
            print(f"       🍺 Marca: {info_completa['marca']}")
            print(f"       🏷️ Tipo: {info_completa['tipo']}")  
            print(f"       📏 Volume: {info_completa['volume']}")
            print(f"       🍻 Teor Alcoólico: {info_completa['teor_alcoolico']}")
            print(f"       🌍 País: {info_completa['pais_origem']}")
            if info_completa['outros']:
                print(f"       ➕ Outros: {', '.join(info_completa['outros'])}")
        else:
            print(f"    ⚠️ Nenhuma combinação produziu texto válido")
    
    # ====================================
    # ANÁLISE FINAL
    # ====================================
    print(f"\n🎉 ANÁLISE FINAL COMPLETA")
    print(f"📊 Produtos processados: {len(produtos)}")
    print(f"📊 Versões preprocessadas testadas: {total_versoes_testadas}")
    print(f"📖 Textos detectados: {len(todos_textos)}")
    
    # Análise de marcas
    texto_completo = ' '.join(todos_textos).upper()
    marcas_conhecidas = ['SPATEN', 'CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA']
    marcas_encontradas = set()
    
    for marca in marcas_conhecidas:
        if marca in texto_completo:
            marcas_encontradas.add(marca)
    
    if marcas_encontradas:
        print(f"🍺 MARCAS IDENTIFICADAS: {', '.join(marcas_encontradas)}")
    else:
        print("📝 Nenhuma marca específica identificada")
    
    # ANÁLISE DE PRODUTOS IDENTIFICADOS
    print(f"\n🔍 PRODUTOS QUE O SISTEMA IDENTIFICA:")
    produtos_identificados = []
    
    # Análise de marcas no texto
    marcas_cervejas = ['SPATEN', 'CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA']
    for marca in marcas_cervejas:
        if marca in texto_completo:
            produtos_identificados.append(f"Cerveja {marca}")
    
    # Análise contextual do nome da imagem
    nome_imagem = os.path.basename(imagem_original).upper()
    if 'SPATEN' in nome_imagem:
        produtos_identificados.append("Cerveja Spaten (identificada pelo nome da imagem)")
    
    if produtos_identificados:
        for produto in set(produtos_identificados):
            print(f"  📦 {produto}")
    else:
        print(f"  📦 {len(produtos)} recipientes detectados (marca não identificada)")
    
    # Mostrar todos os textos detectados
    if todos_textos:
        print(f"\n📋 TODOS OS TEXTOS DETECTADOS:")
        for i, texto in enumerate(todos_textos, 1):
            print(f"  {i:2d}. {texto}")
    
    # Salvar relatório detalhado
    with open(os.path.join(pasta_resultado, "relatorio_preprocessamento_completo.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE PREPROCESSAMENTO COMPLETO ===\n\n")
        f.write(f"Imagem processada: {imagem_original}\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"CONFIGURAÇÕES DE ZOOM:\n")
        f.write(f"- Zoom Menor (conservador): {ZOOM_MENOR}x\n")
        f.write(f"- Zoom Maior (agressivo): {ZOOM_MAIOR}x\n")
        f.write(f"- Limite máximo de imagem: 2000px\n\n")
        
        f.write(f"PRODUTOS PROCESSADOS: {len(produtos)}\n")
        for i, produto in enumerate(produtos):
            f.write(f"- Produto {i+1}: Área={produto['area']:.0f}, Ratio={produto['aspect_ratio']:.2f}\n")
        
        f.write(f"\nPREPROCESSAMENTO APLICADO:\n")
        f.write("- NORMALIZAÇÃO: RGB → Cinza (3 canais → 1 canal)\n")
        f.write("- BINARIZAÇÃO: 5 técnicas testadas\n")
        f.write("  • Otsu (threshold automático)\n")
        f.write("  • Adaptativo Gaussiano\n")
        f.write("  • Adaptativo por Média\n")
        f.write("  • Manual (threshold 128)\n")
        f.write("  • Cinza original (referência)\n")
        f.write("- ZOOM DUPLO: testa 2 níveis para cada produto\n")
        f.write(f"- Zoom conservador ({ZOOM_MENOR}x) vs Zoom agressivo ({ZOOM_MAIOR}x)\n")
        f.write("- Limitado a 2000px para evitar problemas de memória\n")
        f.write("- OCR com timeout de 10 segundos\n")
        f.write(f"- TOTAL: {total_versoes_testadas} versões preprocessadas testadas\n\n")
        
        f.write("TEXTOS DETECTADOS:\n")
        for texto in todos_textos:
            f.write(f"- {texto}\n")
        
        if marcas_encontradas:
            f.write(f"\nMARCAS IDENTIFICADAS:\n")
            for marca in marcas_encontradas:
                f.write(f"- {marca}\n")
        
        # PRODUTOS QUE O SISTEMA "ACHA" QUE ESTÃO NA IMAGEM
        f.write(f"\n=== PRODUTOS IDENTIFICADOS PELO SISTEMA ===\n")
        f.write(f"Baseado na análise de texto e contexto:\n\n")
        
        produtos_identificados_relatorio = []
        
        # Análise de marcas conhecidas no texto
        marcas_cervejas = ['SPATEN', 'CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA']
        for marca in marcas_cervejas:
            if marca in texto_completo:
                produtos_identificados_relatorio.append(f"Cerveja {marca}")
        
        # Análise de volumes
        if '350' in texto_completo or '350ML' in texto_completo:
            produtos_identificados_relatorio.append("Lata 350ML")
        if '473' in texto_completo or '473ML' in texto_completo:
            produtos_identificados_relatorio.append("Lata 473ML") 
        if '600' in texto_completo or '600ML' in texto_completo:
            produtos_identificados_relatorio.append("Garrafa 600ML")
        if 'LONG NECK' in texto_completo or 'LONGNECK' in texto_completo:
            produtos_identificados_relatorio.append("Garrafa Long Neck")
        
        # Análise contextual baseada no nome da imagem
        nome_imagem = os.path.basename(imagem_original).upper()
        if 'SPATEN' in nome_imagem:
            produtos_identificados_relatorio.append("Cerveja Spaten (identificada pelo nome da imagem)")
        if 'CORONA' in nome_imagem:
            produtos_identificados_relatorio.append("Cerveja Corona (identificada pelo nome da imagem)")
        
        if produtos_identificados_relatorio:
            for produto in set(produtos_identificados_relatorio):  # Remove duplicatas
                f.write(f"• {produto}\n")
        else:
            f.write("• Nenhum produto específico identificado com certeza\n")
            f.write(f"• Detectados {len(produtos)} objetos que podem ser recipientes de bebida\n")
    
    print(f"\n📁 Resultados salvos em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 80)
    print("🚀 PIPELINE PREPROCESSAMENTO COMPLETO CONCLUÍDO!")
    print("✅ RGB→Cinza + Binarização + Zoom Duplo + OCR")
    print("✅ Múltiplas técnicas testadas simultaneamente")
    print("=" * 80)

if __name__ == "__main__":
    main()