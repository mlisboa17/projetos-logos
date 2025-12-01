#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE CORONA - DETECÇÃO PRECISA + ANÁLISE COMPLETA
- Detecção precisa de exatamente 4 produtos Corona
- Análise completa: Marca + Tipo + Volume + Teor Alcoólico
- Preprocessamento RGB→Cinza + Binarização
- Zoom duplo configurável
"""

import cv2
import numpy as np
import os
from datetime import datetime
import sys
from pathlib import Path
import re
import threading

# Configurações OCR
try:
    import pytesseract
    
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

def detectar_produtos_corona_precisos(img):
    """
    DETECÇÃO PRECISA PARA 4 PRODUTOS CORONA
    Foca em detectar exatamente os produtos visíveis, não fragmentos
    """
    print("    🎯 Detecção precisa para produtos Corona...")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Combinação de técnicas para máxima precisão
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold adaptativo otimizado
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 15, 8
    )
    
    # Limpeza morfológica agressiva
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # CRITÉRIOS ESPECÍFICOS PARA PRODUTOS CORONA
    AREA_MINIMA = 30000     # Produtos significativos (aumentado)
    AREA_MAXIMA = 600000    # Evitar fundo
    HEIGHT_MINIMA = 150     # Altura mínima para produtos visíveis
    WIDTH_MINIMA = 80       # Largura mínima
    ASPECT_MIN = 0.2        # Garrafas podem ser estreitas  
    ASPECT_MAX = 4.0        # Latas podem ser mais largas
    
    print(f"        📏 Área: {AREA_MINIMA} - {AREA_MAXIMA}")
    print(f"        📐 Dimensões: {WIDTH_MINIMA}x{HEIGHT_MINIMA} mín")
    print(f"        📊 Aspect ratio: {ASPECT_MIN} - {ASPECT_MAX}")
    
    produtos_candidatos = []
    
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        
        if AREA_MINIMA <= area <= AREA_MAXIMA:
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            if (w >= WIDTH_MINIMA and h >= HEIGHT_MINIMA and 
                ASPECT_MIN <= aspect_ratio <= ASPECT_MAX):
                
                produtos_candidatos.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'score': area * (1 + (1/aspect_ratio))  # Favor produtos altos
                })
    
    # Ordenar por score e limitar
    produtos_candidatos.sort(key=lambda x: x['score'], reverse=True)
    
    # REMOVER SOBREPOSIÇÕES
    produtos_finais = []
    for produto in produtos_candidatos:
        x1, y1, w1, h1 = produto['bbox']
        
        sobrepoe = False
        for aceito in produtos_finais:
            x2, y2, w2, h2 = aceito['bbox']
            
            # Calcular sobreposição
            overlap_x = max(0, min(x1+w1, x2+w2) - max(x1, x2))
            overlap_y = max(0, min(y1+h1, y2+h2) - max(y1, y2))
            overlap_area = overlap_x * overlap_y
            
            if overlap_area > 0.3 * min(produto['area'], aceito['area']):
                sobrepoe = True
                break
        
        if not sobrepoe:
            produtos_finais.append(produto)
    
    # Limitar a 6 produtos máximo (segurança)
    produtos_finais = produtos_finais[:6]
    
    print(f"        🔍 {len(produtos_candidatos)} candidatos → {len(produtos_finais)} produtos únicos")
    
    return produtos_finais

def preprocessamento_completo_corona(img_produto):
    """
    PREPROCESSAMENTO COMPLETO ESPECÍFICO PARA CORONA
    """
    print(f"      🔧 PREPROCESSAMENTO COMPLETO:")
    
    if img_produto is None or img_produto.size == 0:
        return []
    
    # ETAPA 1: RGB → Cinza
    print(f"         1️⃣ RGB → Cinza (3 canais → 1 canal)")
    if len(img_produto.shape) == 3:
        img_cinza = cv2.cvtColor(img_produto, cv2.COLOR_BGR2GRAY)
    else:
        img_cinza = img_produto.copy()
    
    # ETAPA 2: Normalização de contraste
    print(f"         2️⃣ Normalização de contraste")
    img_normalizada = cv2.equalizeHist(img_cinza)
    
    # ETAPA 3: Múltiplas técnicas de binarização
    versoes_binarizadas = []
    
    # Otsu (melhor para Corona)
    print(f"         3️⃣ Binarização Otsu")
    _, img_otsu = cv2.threshold(img_normalizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    versoes_binarizadas.append({
        'nome': 'OTSU',
        'descricao': 'Threshold automático Otsu',
        'imagem': img_otsu
    })
    
    # Adaptativo Gaussiano
    print(f"         4️⃣ Adaptativo Gaussiano")
    img_adaptativa = cv2.adaptiveThreshold(
        img_normalizada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    versoes_binarizadas.append({
        'nome': 'ADAPTATIVO',
        'descricao': 'Threshold adaptativo',
        'imagem': img_adaptativa
    })
    
    # Manual otimizado para texto
    print(f"         5️⃣ Manual otimizado")
    _, img_manual = cv2.threshold(img_normalizada, 140, 255, cv2.THRESH_BINARY)
    versoes_binarizadas.append({
        'nome': 'MANUAL_140',
        'descricao': 'Threshold manual 140',
        'imagem': img_manual
    })
    
    # Cinza original
    versoes_binarizadas.append({
        'nome': 'CINZA',
        'descricao': 'Cinza sem binarização',
        'imagem': img_normalizada
    })
    
    return versoes_binarizadas

def aplicar_zoom_duplo(img_produto, zoom_menor=1.5, zoom_maior=3.0):
    """Zoom duplo configurável"""
    if img_produto is None or img_produto.size == 0:
        return []
    
    altura_original, largura_original = img_produto.shape[:2]
    MAX_DIMENSAO = 2000
    resultados_zoom = []
    
    zooms = [
        {'nome': 'MENOR', 'fator': zoom_menor, 'descricao': 'conservador'},
        {'nome': 'MAIOR', 'fator': zoom_maior, 'descricao': 'agressivo'}
    ]
    
    for config in zooms:
        fator = config['fator']
        nome = config['nome']
        
        nova_largura = int(largura_original * fator)
        nova_altura = int(altura_original * fator)
        
        # Aplicar limite
        if nova_largura > MAX_DIMENSAO or nova_altura > MAX_DIMENSAO:
            fator_real = min(MAX_DIMENSAO / largura_original, MAX_DIMENSAO / altura_original)
            nova_largura = int(largura_original * fator_real)
            nova_altura = int(altura_original * fator_real)
        else:
            fator_real = fator
        
        img_zoom = cv2.resize(img_produto, (nova_largura, nova_altura), interpolation=cv2.INTER_CUBIC)
        
        resultados_zoom.append({
            'imagem': img_zoom,
            'fator_real': fator_real,
            'tipo': nome,
            'dimensoes': f"{nova_largura}x{nova_altura}"
        })
    
    return resultados_zoom

def ocr_multiplo_windows(versoes_preprocessadas, timeout_segundos=10):
    """OCR em múltiplas versões (Windows compatível)"""
    if not OCR_DISPONIVEL:
        return []
    
    configs_ocr = [
        {'nome': 'Palavra', 'config': '--psm 8'},
        {'nome': 'Linha', 'config': '--psm 7'},  
        {'nome': 'Geral', 'config': '--psm 6'}
    ]
    
    resultados = []
    
    for versao in versoes_preprocessadas:
        nome_versao = versao['nome']
        img_preprocessada = versao['imagem']
        
        print(f"         📖 OCR em {nome_versao}:")
        
        for config in configs_ocr:
            try:
                # OCR com timeout via threading
                resultado_ocr = [None]
                erro_ocr = [None]
                
                def executar_ocr():
                    try:
                        resultado_ocr[0] = pytesseract.image_to_string(
                            img_preprocessada, config=config['config']
                        ).strip()
                    except Exception as e:
                        erro_ocr[0] = e
                
                thread = threading.Thread(target=executar_ocr)
                thread.daemon = True
                thread.start()
                thread.join(timeout=timeout_segundos)
                
                if thread.is_alive():
                    continue
                
                if erro_ocr[0]:
                    continue
                
                texto = resultado_ocr[0]
                if texto and len(texto) > 1:
                    print(f"            ✅ {config['nome']}: {repr(texto)}")
                    resultados.append({
                        'preprocessamento': nome_versao,
                        'config_ocr': config['nome'],
                        'texto': texto
                    })
                    
            except Exception:
                continue
    
    return resultados

def analisar_informacoes_completas_corona(textos_produto):
    """
    ANÁLISE COMPLETA ESPECÍFICA PARA CORONA
    Extrai: Marca, Tipo, Volume, Teor Alcoólico, País
    """
    texto_completo = ' '.join(textos_produto).upper()
    
    info = {
        'marca': 'N/A',
        'tipo': 'N/A', 
        'volume': 'N/A',
        'teor_alcoolico': 'N/A',
        'pais': 'N/A',
        'detalhes': []
    }
    
    # MARCA
    marcas = ['CORONA', 'CORONITA']
    for marca in marcas:
        if marca in texto_completo:
            info['marca'] = marca
            break
    
    # TIPO
    tipos = ['EXTRA', 'CERO', 'ZERO', 'LIGHT', 'PREMIUM']
    for tipo in tipos:
        if tipo in texto_completo:
            info['tipo'] = tipo
            break
    
    # VOLUME
    volumes = re.findall(r'(\d+)\s*ML|(\d+)\s*ml', texto_completo)
    if volumes:
        for match in volumes[0]:
            if match:
                info['volume'] = f"{match}ML"
                break
    
    # TEOR ALCOÓLICO
    teores = re.findall(r'(\d+\.?\d*)\s*%', texto_completo)
    if teores:
        info['teor_alcoolico'] = f"{teores[0]}% vol"
    
    # PAÍS
    if 'MEXICO' in texto_completo or 'MÉXICO' in texto_completo:
        info['pais'] = 'MÉXICO'
    
    # DETALHES ADICIONAIS
    detalhes_importantes = ['CERVEZA', 'BEER', 'IMPORTED', 'MODELO']
    for detalhe in detalhes_importantes:
        if detalhe in texto_completo:
            info['detalhes'].append(detalhe)
    
    return info

def main():
    """Pipeline Corona com detecção precisa e análise completa"""
    print("=" * 80)
    print("🍺 PIPELINE CORONA - DETECÇÃO PRECISA + ANÁLISE COMPLETA")
    print("📋 Marca + Tipo + Volume + Teor Alcoólico + País")
    print("=" * 80)
    
    # CONFIGURAÇÕES
    ZOOM_MENOR = 1.5
    ZOOM_MAIOR = 3.0
    print(f"⚙️ CONFIGURAÇÕES:")
    print(f"   📏 Zoom Menor: {ZOOM_MENOR}x | Zoom Maior: {ZOOM_MAIOR}x")
    print(f"   🎨 Preprocessamento: RGB→Cinza + 4 técnicas de binarização")
    
    # Caminho da imagem Corona
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"corona_analise_completa_{timestamp}"
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
    print(f"\n📥 Imagem Corona: {largura}x{altura}")
    
    # REMOÇÃO DE FUNDO
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
    
    print("✓ Fundo removido")
    cv2.imwrite(os.path.join(pasta_resultado, "1_sem_fundo.jpg"), img_sem_fundo)
    
    # DETECÇÃO PRECISA DE PRODUTOS
    print(f"\n🎯 ETAPA 2: DETECÇÃO PRECISA DE PRODUTOS CORONA")
    produtos = detectar_produtos_corona_precisos(img_sem_fundo)
    print(f"✅ {len(produtos)} produtos Corona detectados")
    
    # ANÁLISE COMPLETA DE CADA PRODUTO
    produtos_analisados = []
    
    for i, produto in enumerate(produtos):
        print(f"\n  🍺 PRODUTO {i+1}:")
        
        # Extrair região do produto
        x, y, w, h = produto['bbox']
        margem = 20
        x1 = max(0, x - margem)
        y1 = max(0, y - margem)
        x2 = min(img_sem_fundo.shape[1], x + w + margem)
        y2 = min(img_sem_fundo.shape[0], y + h + margem)
        
        produto_original = img_sem_fundo[y1:y2, x1:x2]
        
        # ZOOM DUPLO
        print(f"    🔍 Aplicando zoom duplo ({ZOOM_MENOR}x e {ZOOM_MAIOR}x)")
        zooms_testados = aplicar_zoom_duplo(produto_original, ZOOM_MENOR, ZOOM_MAIOR)
        
        melhor_info = None
        max_textos = 0
        todos_textos_produto = []
        
        # TESTAR CADA ZOOM
        for zoom_config in zooms_testados:
            tipo = zoom_config['tipo']
            fator = zoom_config['fator_real']
            produto_zoom = zoom_config['imagem']
            
            print(f"    🔍 ZOOM {tipo}: {fator:.1f}x ({zoom_config['dimensoes']})")
            
            # PREPROCESSAMENTO COMPLETO
            versoes_preprocessadas = preprocessamento_completo_corona(produto_zoom)
            
            # Salvar versões
            for versao in versoes_preprocessadas:
                nome_arquivo = f"produto_{i+1}_{tipo.lower()}_{versao['nome'].lower()}.jpg"
                cv2.imwrite(os.path.join(pasta_resultado, nome_arquivo), versao['imagem'])
            
            # OCR EM MÚLTIPLAS VERSÕES
            resultados_ocr = ocr_multiplo_windows(versoes_preprocessadas, timeout_segundos=8)
            
            if resultados_ocr:
                textos_encontrados = len(resultados_ocr)
                print(f"       ✅ {textos_encontrados} texto(s) encontrado(s)")
                
                # Coletar textos
                textos_zoom = [r['texto'] for r in resultados_ocr]
                todos_textos_produto.extend(textos_zoom)
                
                if textos_encontrados > max_textos:
                    max_textos = textos_encontrados
                    melhor_info = {
                        'zoom': zoom_config,
                        'textos': textos_zoom
                    }
            else:
                print(f"       ❌ Nenhum texto detectado")
        
        # ANÁLISE COMPLETA DAS INFORMAÇÕES
        if todos_textos_produto:
            info_completa = analisar_informacoes_completas_corona(todos_textos_produto)
            
            print(f"    📋 INFORMAÇÕES CORONA IDENTIFICADAS:")
            print(f"       🍺 Marca: {info_completa['marca']}")
            print(f"       🏷️ Tipo: {info_completa['tipo']}")
            print(f"       📏 Volume: {info_completa['volume']}")
            print(f"       🍻 Teor: {info_completa['teor_alcoolico']}")
            print(f"       🌍 País: {info_completa['pais']}")
            if info_completa['detalhes']:
                print(f"       ➕ Detalhes: {', '.join(info_completa['detalhes'])}")
            
            produtos_analisados.append({
                'produto_id': i+1,
                'info_completa': info_completa,
                'textos': todos_textos_produto,
                'melhor_zoom': melhor_info['zoom']['tipo'] if melhor_info else 'N/A'
            })
        else:
            print(f"    ⚠️ Nenhum texto detectado neste produto")
    
    # RELATÓRIO FINAL
    print(f"\n🎉 ANÁLISE FINAL CORONA")
    print(f"📊 Produtos analisados: {len(produtos_analisados)}")
    
    # Resumo dos produtos Corona
    if produtos_analisados:
        print(f"\n🍺 RESUMO DOS PRODUTOS CORONA:")
        for produto in produtos_analisados:
            info = produto['info_completa']
            print(f"  {produto['produto_id']:2d}. {info['marca']} {info['tipo']} - {info['volume']} - {info['teor_alcoolico']} ({info['pais']})")
    
    # Salvar relatório
    with open(os.path.join(pasta_resultado, "relatorio_corona_completo.txt"), 'w', encoding='utf-8') as f:
        f.write("=== ANÁLISE COMPLETA PRODUTOS CORONA ===\n\n")
        f.write(f"Imagem: {imagem_original}\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Produtos detectados: {len(produtos_analisados)}\n\n")
        
        for produto in produtos_analisados:
            info = produto['info_completa']
            f.write(f"PRODUTO {produto['produto_id']}:\n")
            f.write(f"- Marca: {info['marca']}\n")
            f.write(f"- Tipo: {info['tipo']}\n")
            f.write(f"- Volume: {info['volume']}\n")
            f.write(f"- Teor Alcoólico: {info['teor_alcoolico']}\n")
            f.write(f"- País: {info['pais']}\n")
            f.write(f"- Melhor Zoom: {produto['melhor_zoom']}\n")
            if info['detalhes']:
                f.write(f"- Detalhes: {', '.join(info['detalhes'])}\n")
            f.write(f"- Textos detectados: {len(produto['textos'])}\n")
            f.write("\n")
    
    print(f"\n📁 Resultados em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 80)
    print("🎉 ANÁLISE CORONA COMPLETA CONCLUÍDA!")
    print("✅ Detecção precisa + Informações completas extraídas")
    print("=" * 80)

if __name__ == "__main__":
    main()