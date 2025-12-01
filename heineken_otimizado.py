#!/usr/bin/env python3
"""
DETECTOR HEINEKEN OTIMIZADO - Para produtos muito próximos
"""

import cv2
import numpy as np
from pathlib import Path

def detector_heineken_otimizado(img_path):
    """
    Detector específico para produtos Heineken muito próximos
    """
    
    img = cv2.imread(img_path)
    if img is None:
        print(f"❌ Erro ao carregar: {img_path}")
        return []
    
    print(f"📸 Imagem Heineken: {img.shape[1]}x{img.shape[0]}")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # DETECÇÃO ESPECÍFICA HEINEKEN (mais sensível)
    print("🍺 Detectando produtos Heineken próximos...")
    
    # VERDE Heineken (mais amplo)
    lower_verde = np.array([30, 20, 20])
    upper_verde = np.array([90, 255, 255])
    mask_verde = cv2.inRange(hsv, lower_verde, upper_verde)
    
    # AZUL Heineken Silver (mais amplo)
    lower_azul = np.array([90, 30, 30])
    upper_azul = np.array([140, 255, 255])
    mask_azul = cv2.inRange(hsv, lower_azul, upper_azul)
    
    # BRANCO/PRATA (latas claras)
    lower_claro = np.array([0, 0, 150])
    upper_claro = np.array([180, 50, 255])
    mask_claro = cv2.inRange(hsv, lower_claro, upper_claro)
    
    # PRETO/ESCURO (textos e detalhes)
    lower_escuro = np.array([0, 0, 0])
    upper_escuro = np.array([180, 255, 80])
    mask_escuro = cv2.inRange(hsv, lower_escuro, upper_escuro)
    
    # Combinar máscaras
    mask1 = cv2.bitwise_or(mask_verde, mask_azul)
    mask2 = cv2.bitwise_or(mask_claro, mask_escuro)
    mask_final = cv2.bitwise_or(mask1, mask2)
    
    # Limpeza morfológica SUAVE
    kernel_pequeno = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_OPEN, kernel_pequeno)
    
    kernel_medio = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel_medio)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    altura_img, largura_img = img.shape[:2]
    
    print(f"   📊 Analisando {len(contours)} contornos...")
    
    for i, contorno in enumerate(contours):
        area = cv2.contourArea(contorno)
        
        # Área mais permissiva
        area_min = altura_img * largura_img * 0.001
        area_max = altura_img * largura_img * 0.6
        
        if area_min < area < area_max:
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / h if h > 0 else 0
            
            if 0.05 < aspect_ratio < 8.0:
                
                if aspect_ratio < 0.6:
                    tipo = "GARRAFA"
                elif 0.6 <= aspect_ratio <= 2.5:
                    tipo = "LATA"
                else:
                    tipo = "PRODUTO"
                
                produtos.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'tipo': tipo,
                    'ratio': round(aspect_ratio, 2),
                    'centro': (x + w//2, y + h//2)
                })
    
    print(f"   🔍 Candidatos: {len(produtos)}")
    
    # Remover sobreposições com tolerância baixa
    produtos.sort(key=lambda x: x['area'], reverse=True)
    produtos_final = []
    
    for prod in produtos:
        centro1 = prod['centro']
        
        muito_proximo = False
        for aceito in produtos_final:
            centro2 = aceito['centro']
            distancia = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            if distancia < 30:
                muito_proximo = True
                break
        
        if not muito_proximo:
            produtos_final.append(prod)
    
    print(f"✅ FINAL: {len(produtos_final)} produtos únicos")
    
    # Desenhar resultado
    img_resultado = img.copy()
    cores = {
        'GARRAFA': (0, 255, 0),
        'LATA': (255, 0, 0),
        'PRODUTO': (0, 255, 255)
    }
    
    for i, prod in enumerate(produtos_final):
        x, y, w, h = prod['bbox']
        tipo = prod['tipo']
        cor = cores.get(tipo, (128, 128, 128))
        
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 3)
        
        label = f"{i+1}.{tipo}"
        cv2.putText(img_resultado, label, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
        
        centro = prod['centro']
        cv2.circle(img_resultado, centro, 5, cor, -1)
    
    # Salvar
    nome_arquivo = Path(img_path).stem
    resultado_path = f"{nome_arquivo}_heineken_otimizado_{len(produtos_final)}produtos.jpg"
    cv2.imwrite(resultado_path, img_resultado)
    
    print(f"💾 Salvo: {resultado_path}")
    
    return produtos_final

if __name__ == "__main__":
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Heineken (2).jpeg"
    
    print("🍺 DETECTOR HEINEKEN OTIMIZADO")
    print("=" * 40)
    
    if Path(img_path).exists():
        produtos = detector_heineken_otimizado(img_path)
        
        print(f"\n🎯 RESULTADO OTIMIZADO:")
        print(f"   📦 Total: {len(produtos)} produtos")
        
        garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA']
        latas = [p for p in produtos if p['tipo'] == 'LATA'] 
        outros = [p for p in produtos if p['tipo'] == 'PRODUTO']
        
        print(f"   🍺 Garrafas: {len(garrafas)}")
        print(f"   🥤 Latas: {len(latas)}")
        if outros:
            print(f"   📦 Outros: {len(outros)}")
            
        print(f"\n📋 DETALHES:")
        for i, p in enumerate(produtos, 1):
            centro = p['centro']
            print(f"   {i}. {p['tipo']} - área: {p['area']:,.0f}, ratio: {p['ratio']}, centro: {centro}")
    else:
        print(f"❌ Arquivo não existe")