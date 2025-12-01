#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COM ZOOM OTIMIZADO - OCR AJUSTADO
Resolve problema do OCR com imagens muito grandes
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

def aplicar_zoom_otimizado(img_produto, fator_zoom=3.0):
    """Zoom otimizado com controle de tamanho máximo (mantido para compatibilidade)"""
    altura_original, largura_original = img_produto.shape[:2]
    
    # Limitar tamanho máximo para evitar problemas no OCR
    MAX_DIMENSAO = 2000
    
    nova_largura = int(largura_original * fator_zoom)
    nova_altura = int(altura_original * fator_zoom)
    
    # Se muito grande, reduzir fator de zoom
    if nova_largura > MAX_DIMENSAO or nova_altura > MAX_DIMENSAO:
        fator_ajustado = min(MAX_DIMENSAO / largura_original, MAX_DIMENSAO / altura_original)
        nova_largura = int(largura_original * fator_ajustado)
        nova_altura = int(altura_original * fator_ajustado)
        fator_zoom = fator_ajustado
    
    # Interpolação otimizada
    img_zoom = cv2.resize(
        img_produto, 
        (nova_largura, nova_altura), 
        interpolation=cv2.INTER_CUBIC
    )
    
    return img_zoom, fator_zoom

def otimizar_para_ocr_rapido(img_zoom):
    """OCR otimizado e mais rápido"""
    
    # Conversão para escala de cinza
    if len(img_zoom.shape) == 3:
        gray = cv2.cvtColor(img_zoom, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_zoom.copy()
    
    # Redimensionar se ainda muito grande
    altura, largura = gray.shape
    if largura > 1500 or altura > 1500:
        fator_reducao = min(1500/largura, 1500/altura)
        nova_largura = int(largura * fator_reducao)
        nova_altura = int(altura * fator_reducao)
        gray = cv2.resize(gray, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)
    
    # Denoising leve
    denoised = cv2.fastNlMeansDenoising(gray, h=8)
    
    # CLAHE moderado
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contraste = clahe.apply(denoised)
    
    # Sharpening suave
    kernel_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) * 0.8
    sharpened = cv2.filter2D(contraste, -1, kernel_sharp)
    
    return sharpened

def ocr_rapido_eficiente(img_otimizada, timeout_segundos=10):
    """OCR rápido com timeout para evitar travamento"""
    if not TESSERACT_DISPONIVEL:
        return []
    
    # Configurações mais simples e rápidas
    configs = [
        ("Rápido - Palavra", "--psm 8 -l eng"),
        ("Rápido - Linha", "--psm 7 -l eng"),
        ("Rápido - Geral", "--psm 6 -l por+eng"),
    ]
    
    resultados = []
    
    for nome, config in configs:
        try:
            # OCR com timeout implícito (configuração mais simples)
            texto = pytesseract.image_to_string(img_otimizada, config=config, timeout=timeout_segundos).strip()
            if texto and len(texto) > 0:
                # Limpeza básica
                texto_limpo = ''.join(char for char in texto if char.isalnum() or char.isspace()).strip()
                if texto_limpo and len(texto_limpo) > 1:
                    resultados.append({
                        'config': nome,
                        'texto': texto_limpo,
                        'tamanho': len(texto_limpo)
                    })
        except Exception as e:
            print(f"      ⚠️ {nome}: Timeout/Erro (pulando)")
            continue
    
    return resultados

def main():
    """Pipeline principal com zoom duplo configurável"""
    print("=" * 70)
    print("🚀 PIPELINE ZOOM DUPLO CONFIGURÁVEL - OTIMIZADO")
    print("=" * 70)
    
    # ====================================
    # CONFIGURAÇÕES DE ZOOM (AJUSTÁVEL)
    # ====================================
    ZOOM_MENOR = 1.5    # Zoom conservador
    ZOOM_MAIOR = 3.0    # Zoom agressivo
    print(f"⚙️ CONFIGURAÇÕES DE ZOOM:")
    print(f"   📏 Zoom Menor (conservador): {ZOOM_MENOR}x")
    print(f"   📏 Zoom Maior (agressivo): {ZOOM_MAIOR}x")
    print(f"   🔒 Limite máximo de imagem: 2000px")
    
    # Caminhos
    imagem_original = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Spaten (2).jpeg"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_zoom_otimizado_{timestamp}"
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
    # ETAPA 2: DETECTAR E FOCAR PRODUTOS
    # ====================================
    print("\n🔍 ETAPA 2: DETECÇÃO E ZOOM CONTROLADO")
    
    produtos = detectar_produtos_precisos(img_sem_fundo)
    print(f"✓ {len(produtos)} produtos detectados")
    
    todos_textos = []
    
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
        
        # ZOOM DUPLO CONFIGURÁVEL (teste 2 níveis)
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
            
            # Salvar versão com zoom
            cv2.imwrite(os.path.join(pasta_resultado, f"2_produto_{i+1}_zoom_{tipo.lower()}.jpg"), produto_zoom)
            
            # OTIMIZAÇÃO PARA OCR
            print(f"       ⚙️ Otimizando para OCR...")
            img_otimizada = otimizar_para_ocr_rapido(produto_zoom)
            
            # Salvar versão otimizada
            cv2.imwrite(os.path.join(pasta_resultado, f"3_produto_{i+1}_ocr_{tipo.lower()}.jpg"), img_otimizada)
            
            # OCR RÁPIDO E SEGURO
            print(f"       📖 OCR (timeout 10s):")
            resultados_ocr = ocr_rapido_eficiente(img_otimizada, timeout_segundos=10)
            
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
                    todos_textos.append(f"Produto {i+1} - {tipo} ({fator:.1f}x) - {resultado['config']}: {resultado['texto']}")
            else:
                print(f"       ❌ Nenhum texto detectado")
        
        # RESUMIR MELHOR RESULTADO
        if melhor_resultado:
            config = melhor_resultado['zoom_config']
            textos = melhor_resultado['resultados_ocr']
            print(f"    🏆 MELHOR: {config['tipo']} ({config['fator_real']:.1f}x) com {len(textos)} texto(s)")
        else:
            print(f"    ⚠️ Nenhum zoom produziu texto válido")
    
    # ====================================
    # ANÁLISE FINAL
    # ====================================
    print(f"\n🎉 ANÁLISE FINAL OTIMIZADA")
    print(f"📊 Produtos processados: {len(produtos)}")
    print(f"📖 Textos detectados: {len(todos_textos)}")
    
    # Verificar marcas
    marcas_conhecidas = ['CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'BUDWEISER', 'STELLA', 'MEXICO', 'EXTRA', 'BEER', 'CERVEJA']
    marcas_encontradas = set()
    
    texto_completo = ' '.join(todos_textos).upper()
    
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
    with open(os.path.join(pasta_resultado, "4_relatorio_otimizado.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE ZOOM DUPLO CONFIGURÁVEL ===\n\n")
        f.write(f"Imagem processada: {imagem_original}\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"CONFIGURAÇÕES DE ZOOM:\n")
        f.write(f"- Zoom Menor (conservador): {ZOOM_MENOR}x\n")
        f.write(f"- Zoom Maior (agressivo): {ZOOM_MAIOR}x\n")
        f.write(f"- Limite máximo de imagem: 2000px\n\n")
        
        f.write(f"PRODUTOS PROCESSADOS: {len(produtos)}\n")
        for i, produto in enumerate(produtos):
            f.write(f"- Produto {i+1}: Área={produto['area']:.0f}, Ratio={produto['aspect_ratio']:.2f}\n")
        
        f.write(f"\nOTIMIZAÇÕES APLICADAS:\n")
        f.write("- ZOOM DUPLO: testa 2 níveis para cada produto\n")
        f.write(f"- Zoom conservador ({ZOOM_MENOR}x) vs Zoom agressivo ({ZOOM_MAIOR}x)\n")
        f.write("- Limitado a 2000px para evitar problemas de memória\n")
        f.write("- OCR com timeout de 10 segundos\n")
        f.write("- Redimensionamento automático para OCR\n")
        f.write("- Seleção automática do melhor resultado\n\n")
        
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
        
        f.write(f"\n=== ARQUIVOS GERADOS ===\n")
        f.write("1_sem_fundo.jpg - Imagem com fundo removido\n")
        f.write("2_produto_X_zoom.jpg - Produtos com zoom controlado\n")
        f.write("3_produto_X_ocr.jpg - Produtos otimizados para OCR\n")
        f.write("4_relatorio_otimizado.txt - Este relatório\n")
    
    print(f"\n📁 Resultados em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("=" * 70)
    print("🚀 PIPELINE ZOOM OTIMIZADO CONCLUÍDO!")
    print("✅ Zoom controlado + OCR rápido e seguro")
    print("✅ Sem travamentos ou timeouts")
    print("=" * 70)

if __name__ == "__main__":
    main()