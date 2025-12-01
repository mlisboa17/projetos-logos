#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO CORONA - Verificar detecção de produtos
"""

import cv2
import numpy as np
import os

def diagnosticar_deteccao_corona():
    """Diagnostica por que não está detectando produtos"""
    
    # Carregar imagem
    imagem = "imagens_teste/corona_produtos.jpeg"
    
    if not os.path.exists(imagem):
        print(f"❌ Imagem não encontrada: {imagem}")
        # Tentar outras possíveis localizações
        alternativas = [
            "corona_produtos.jpeg",
            "imagens_teste/corona.jpg",
            "../imagens_teste/corona_produtos.jpeg"
        ]
        
        for alt in alternativas:
            if os.path.exists(alt):
                print(f"✅ Imagem encontrada em: {alt}")
                imagem = alt
                break
        else:
            print("❌ Nenhuma imagem Corona encontrada!")
            return
    
    img = cv2.imread(imagem)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem}")
        return
        
    altura, largura = img.shape[:2]
    print(f"📥 Imagem: {largura}x{altura}")
    
    # Converter para cinza e analisar
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Diferentes técnicas de threshold
    tecnicas = [
        ("Otsu", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)),
        ("Adaptativo", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("Manual_128", cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)),
        ("Invertido", cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV))
    ]
    
    for nome, resultado in tecnicas:
        if len(resultado) == 2:  # threshold retorna (valor, imagem)
            _, thresh = resultado
        else:
            thresh = resultado
            
        # Encontrar contornos
        contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"\n🔍 {nome}: {len(contornos)} contornos")
        
        # Analisar contornos por tamanho
        areas = [cv2.contourArea(c) for c in contornos]
        areas.sort(reverse=True)
        
        print(f"   📊 Maiores áreas: {areas[:10]}")
        
        # Salvar imagem com contornos
        img_contornos = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(img_contornos, contornos, -1, (0, 255, 0), 2)
        
        nome_arquivo = f"diagnostico_{nome.lower()}.jpg"
        cv2.imwrite(nome_arquivo, img_contornos)
        print(f"   💾 Salvo: {nome_arquivo}")
        
        # Analisar candidatos com diferentes critérios
        candidatos_areas = [
            ("Muito pequenos", 1000, 10000),
            ("Pequenos", 10000, 30000),
            ("Médios", 30000, 100000),
            ("Grandes", 100000, 500000),
            ("Muito grandes", 500000, float('inf'))
        ]
        
        for descricao, area_min, area_max in candidatos_areas:
            candidatos = [c for c in contornos if area_min <= cv2.contourArea(c) < area_max]
            if candidatos:
                print(f"   📦 {descricao} ({area_min}-{area_max}): {len(candidatos)} objetos")
    
    print(f"\n📁 Arquivos de diagnóstico salvos na pasta atual")

if __name__ == "__main__":
    diagnosticar_deteccao_corona()