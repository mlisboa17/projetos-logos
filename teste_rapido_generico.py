#!/usr/bin/env python3
"""
TESTE RÁPIDO - DETECTOR GENÉRICO
Teste direto do detector universal para qualquer marca
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Adicionar pasta do projeto
sys.path.append(str(Path(__file__).parent))

def detector_generico_simples(img_path):
    """
    Função simples para testar o detector genérico
    """
    
    # Converter para HSV para detecção de cores
    img = cv2.imread(img_path)
    if img is None:
        print(f"❌ Erro ao carregar: {img_path}")
        return []
    
    print(f"📸 Imagem: {img.shape[1]}x{img.shape[0]}")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # DETECÇÃO POR MÚLTIPLAS CORES (genérico)
    print("🎨 Detectando por cores múltiplas...")
    
    # VERDE: Heineken, Carlsberg
    lower_verde = np.array([35, 30, 30])
    upper_verde = np.array([85, 255, 255])
    mask_verde = cv2.inRange(hsv, lower_verde, upper_verde)
    
    # AZUL: Heineken Silver, Pepsi
    lower_azul = np.array([100, 40, 40])
    upper_azul = np.array([130, 255, 255])
    mask_azul = cv2.inRange(hsv, lower_azul, upper_azul)
    
    # DOURADO: Corona, Brahma
    lower_dourado = np.array([10, 40, 40])
    upper_dourado = np.array([35, 255, 255])
    mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
    
    # BRANCO/CINZA: Latas claras
    lower_claro = np.array([0, 0, 160])
    upper_claro = np.array([180, 40, 255])
    mask_claro = cv2.inRange(hsv, lower_claro, upper_claro)
    
    # VERMELHO: Budweiser, Skol
    lower_vermelho = np.array([0, 50, 50])
    upper_vermelho = np.array([10, 255, 255])
    mask_vermelho = cv2.inRange(hsv, lower_vermelho, upper_vermelho)
    
    # Combinar todas as máscaras
    mask1 = cv2.bitwise_or(mask_verde, mask_azul)
    mask2 = cv2.bitwise_or(mask_dourado, mask_claro)
    mask3 = cv2.bitwise_or(mask1, mask2)
    mask_final = cv2.bitwise_or(mask3, mask_vermelho)
    
    # Limpeza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 6))
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_OPEN, kernel)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    altura_img, largura_img = img.shape[:2]
    
    for contorno in contours:
        area = cv2.contourArea(contorno)
        
        # Filtrar por área
        area_min = altura_img * largura_img * 0.003
        area_max = altura_img * largura_img * 0.5
        
        if area_min < area < area_max:
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / h if h > 0 else 0
            
            # Filtrar formas muito estranhas
            if 0.1 < aspect_ratio < 5.0:
                # Classificar por forma
                if aspect_ratio < 0.7:
                    tipo = "GARRAFA"
                elif 0.7 <= aspect_ratio <= 2.0:
                    tipo = "LATA"
                else:
                    tipo = "PRODUTO"
                
                produtos.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'tipo': tipo,
                    'ratio': round(aspect_ratio, 2)
                })
    
    # Remover sobreposições
    produtos.sort(key=lambda x: x['area'], reverse=True)
    produtos_final = []
    
    for prod in produtos:
        x1, y1, w1, h1 = prod['bbox']
        centro1 = (x1 + w1//2, y1 + h1//2)
        
        muito_proximo = False
        for aceito in produtos_final:
            x2, y2, w2, h2 = aceito['bbox']
            centro2 = (x2 + w2//2, y2 + h2//2)
            
            distancia = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            # Para produtos próximos (Heineken)
            if distancia < 60:
                muito_proximo = True
                break
        
        if not muito_proximo:
            produtos_final.append(prod)
    
    print(f"✅ Encontrados: {len(produtos_final)} produtos")
    
    # Desenhar resultado
    img_resultado = img.copy()
    cores = {
        'GARRAFA': (0, 255, 0),    # Verde
        'LATA': (255, 0, 0),       # Azul  
        'PRODUTO': (0, 255, 255)   # Amarelo
    }
    
    for i, prod in enumerate(produtos_final):
        x, y, w, h = prod['bbox']
        tipo = prod['tipo']
        cor = cores.get(tipo, (128, 128, 128))
        
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 3)
        cv2.putText(img_resultado, f"{i+1}.{tipo}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
    
    # Salvar
    nome_arquivo = Path(img_path).stem
    resultado_path = f"{nome_arquivo}_generico_{len(produtos_final)}produtos.jpg"
    cv2.imwrite(resultado_path, img_resultado)
    
    print(f"💾 Resultado salvo: {resultado_path}")
    
    return produtos_final

if __name__ == "__main__":
    print("🔍 DETECTOR GENÉRICO UNIVERSAL")
    print("=" * 40)
    
    # Testar com qualquer imagem
    caminho = input("📁 Caminho da imagem: ").strip().strip('"')
    
    if Path(caminho).exists():
        produtos = detector_generico_simples(caminho)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   🔸 Total: {len(produtos)} produtos")
        
        for i, p in enumerate(produtos, 1):
            print(f"   {i}. {p['tipo']} (área: {p['area']:,.0f}, ratio: {p['ratio']})")
    else:
        print(f"❌ Arquivo não existe: {caminho}")