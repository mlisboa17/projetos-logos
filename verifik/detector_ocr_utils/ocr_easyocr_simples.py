#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR SIMPLES COM EASYOCR
======================
Script para testar OCR com EasyOCR em imagens pré-processadas
Identifica marcas de cervejas e produtos
"""

import cv2
import os
import numpy as np
from datetime import datetime
import json

def carregar_imagem():
    """Carrega a imagem pré-processada mais recente"""
    # Procura pela pasta de processamento mais recente
    pastas = [d for d in os.listdir('.') if d.startswith('processamento_completo_')]
    if not pastas:
        print("❌ Nenhuma pasta de processamento encontrada")
        return None
    
    pasta_recente = sorted(pastas)[-1]
    caminho_imagem = os.path.join(pasta_recente, '01_preprocessamento_final.jpg')
    
    if not os.path.exists(caminho_imagem):
        print(f"❌ Imagem não encontrada: {caminho_imagem}")
        return None
    
    imagem = cv2.imread(caminho_imagem)
    if imagem is None:
        print("❌ Erro ao carregar imagem")
        return None
    
    print(f"✅ Imagem carregada: {imagem.shape}")
    return imagem, caminho_imagem

def configurar_easyocr():
    """Configura EasyOCR"""
    try:
        import easyocr
        print("✅ EasyOCR disponível")
        
        # Inicializa com português e inglês
        reader = easyocr.Reader(['pt', 'en'], gpu=False)
        return reader
    except ImportError:
        print("❌ EasyOCR não encontrado. Instalando...")
        os.system("pip install easyocr")
        try:
            import easyocr
            reader = easyocr.Reader(['pt', 'en'], gpu=False)
            return reader
        except Exception as e:
            print(f"❌ Erro ao configurar EasyOCR: {e}")
            return None

def aplicar_ocr(reader, imagem):
    """Aplica OCR na imagem"""
    try:
        print("\n🔍 Executando OCR...")
        
        # Converte para RGB (EasyOCR espera RGB)
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        
        # Executa OCR
        results = reader.readtext(imagem_rgb)
        
        return results
    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return []

def processar_resultados(results, imagem):
    """Processa os resultados do OCR"""
    print(f"\n📋 Encontrados {len(results)} textos:")
    
    # Lista de marcas conhecidas
    marcas_conhecidas = [
        'CORONA', 'HEINEKEN', 'SKOL', 'BRAHMA', 'ANTARCTICA', 
        'STELLA', 'BUDWEISER', 'EISENBAHN', 'ORIGINAL', 'PILSEN',
        'BEER', 'CERVEJA', 'ML', 'LONG', 'NECK', 'GARRAFA'
    ]
    
    textos_encontrados = []
    marcas_identificadas = []
    
    # Desenha os resultados na imagem
    imagem_resultado = imagem.copy()
    
    for (bbox, text, confidence) in results:
        # Extrai coordenadas
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))
        
        # Filtra textos com confiança mínima
        if confidence > 0.5:
            text_upper = text.upper().strip()
            
            print(f"  📝 '{text}' (confiança: {confidence:.2f})")
            textos_encontrados.append({
                'texto': text,
                'confianca': confidence,
                'bbox': bbox
            })
            
            # Verifica se é uma marca conhecida
            for marca in marcas_conhecidas:
                if marca in text_upper:
                    marcas_identificadas.append({
                        'marca': marca,
                        'texto_original': text,
                        'confianca': confidence,
                        'bbox': bbox
                    })
                    print(f"  🏷️ MARCA IDENTIFICADA: {marca}")
            
            # Desenha retângulo e texto
            cv2.rectangle(imagem_resultado, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(imagem_resultado, f"{text} ({confidence:.2f})", 
                       (top_left[0], top_left[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return textos_encontrados, marcas_identificadas, imagem_resultado

def salvar_resultados(textos, marcas, imagem_resultado, caminho_original):
    """Salva os resultados"""
    # Cria pasta de resultados
    pasta_resultado = "ocr_resultado"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salva imagem com resultados
    nome_imagem = f"ocr_resultado_{timestamp}.jpg"
    caminho_imagem = os.path.join(pasta_resultado, nome_imagem)
    cv2.imwrite(caminho_imagem, imagem_resultado)
    
    # Salva dados JSON
    dados = {
        'timestamp': timestamp,
        'imagem_original': caminho_original,
        'total_textos': len(textos),
        'total_marcas': len(marcas),
        'textos_encontrados': textos,
        'marcas_identificadas': marcas
    }
    
    nome_json = f"ocr_dados_{timestamp}.json"
    caminho_json = os.path.join(pasta_resultado, nome_json)
    
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados salvos:")
    print(f"  📸 Imagem: {caminho_imagem}")
    print(f"  📄 Dados: {caminho_json}")
    
    return dados

def main():
    print("📖 TESTE OCR COM EASYOCR")
    print("=" * 50)
    
    # 1. Carregar imagem
    resultado = carregar_imagem()
    if resultado is None:
        return
    
    imagem, caminho_imagem = resultado
    
    # 2. Configurar EasyOCR
    reader = configurar_easyocr()
    if reader is None:
        return
    
    # 3. Aplicar OCR
    results = aplicar_ocr(reader, imagem)
    
    if not results:
        print("❌ Nenhum texto encontrado")
        return
    
    # 4. Processar resultados
    textos, marcas, imagem_resultado = processar_resultados(results, imagem)
    
    # 5. Salvar resultados
    dados = salvar_resultados(textos, marcas, imagem_resultado, caminho_imagem)
    
    # 6. Resumo
    print(f"\n🎯 RESUMO:")
    print(f"  📊 Total de textos: {len(textos)}")
    print(f"  🏷️ Marcas identificadas: {len(marcas)}")
    
    if marcas:
        print(f"  📋 Marcas encontradas:")
        for marca_info in marcas:
            print(f"    • {marca_info['marca']} ({marca_info['confianca']:.2f})")
    
    print(f"\n✅ Teste OCR concluído!")

if __name__ == "__main__":
    main()