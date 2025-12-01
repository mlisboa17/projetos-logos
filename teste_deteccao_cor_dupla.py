#!/usr/bin/env python3
"""
MÉTODO APRIMORADO: DETECÇÃO POR COR DUPLA
- Garrafas douradas/amarelas (Corona líquido)
- Latas brancas (Corona lata)
"""

import cv2
import numpy as np
import os
from datetime import datetime

def metodo_melhorado_cor_dupla(img, pasta_resultado):
    """MÉTODO MELHORADO: Detecta garrafas douradas E latas brancas"""
    print("\n🔍 MÉTODO MELHORADO: COR DUPLA (DOURADO + BRANCO)")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_debug = img.copy()
    
    # ===== DETECÇÃO 1: GARRAFAS DOURADAS/AMARELAS =====
    print("   🍺 Detectando garrafas douradas...")
    lower_dourado = np.array([10, 50, 50])
    upper_dourado = np.array([35, 255, 255])
    mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
    
    # Limpar máscara dourada
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_OPEN, kernel)
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_CLOSE, kernel)
    
    # ===== DETECÇÃO 2: LATAS BRANCAS =====
    print("   🥤 Detectando latas brancas...")
    # Branco: baixa saturação, alto valor
    lower_branco = np.array([0, 0, 180])    # H qualquer, S baixo, V alto
    upper_branco = np.array([180, 30, 255]) # H qualquer, S baixo, V alto
    mask_branco = cv2.inRange(hsv, lower_branco, upper_branco)
    
    # Limpar máscara branca
    mask_branco = cv2.morphologyEx(mask_branco, cv2.MORPH_OPEN, kernel)
    mask_branco = cv2.morphologyEx(mask_branco, cv2.MORPH_CLOSE, kernel)
    
    # ===== COMBINAR MÁSCARAS =====
    mask_combinada = cv2.bitwise_or(mask_dourado, mask_branco)
    
    # Salvar máscaras para análise
    cv2.imwrite(os.path.join(pasta_resultado, "mask_dourado.jpg"), mask_dourado)
    cv2.imwrite(os.path.join(pasta_resultado, "mask_branco.jpg"), mask_branco)
    cv2.imwrite(os.path.join(pasta_resultado, "mask_combinada.jpg"), mask_combinada)
    
    # ===== ENCONTRAR CONTORNOS NA MÁSCARA COMBINADA =====
    contornos, _ = cv2.findContours(mask_combinada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        if area > 8000:  # Área mínima para produto
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Determinar tipo baseado na forma e posição na máscara
            centro_x, centro_y = x + w//2, y + h//2
            
            # Verificar qual máscara tem mais pixels nesta região
            roi_dourado = mask_dourado[y:y+h, x:x+w]
            roi_branco = mask_branco[y:y+h, x:x+w]
            
            pixels_dourado = np.sum(roi_dourado > 0)
            pixels_branco = np.sum(roi_branco > 0)
            
            if pixels_dourado > pixels_branco:
                tipo = "GARRAFA_DOURADA"
                cor = (0, 165, 255)  # Laranja
                # Garrafas são mais altas
                if 0.2 < aspect_ratio < 1.2 and h > w * 1.5:
                    produtos.append({
                        'id': i,
                        'tipo': tipo,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'bbox': (x, y, w, h),
                        'pixels_dominantes': pixels_dourado
                    })
            else:
                tipo = "LATA_BRANCA"
                cor = (255, 255, 255)  # Branco
                # Latas podem ser mais largas
                if 0.3 < aspect_ratio < 2.0:
                    produtos.append({
                        'id': i,
                        'tipo': tipo,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'bbox': (x, y, w, h),
                        'pixels_dominantes': pixels_branco
                    })
            
            # Desenhar detecção
            if len(produtos) > 0 and produtos[-1]['id'] == i:
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor, 3)
                cv2.putText(img_debug, f"{tipo[:6]}{i}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
                print(f"      ✅ {tipo}: {area:.0f} pixels, ratio {aspect_ratio:.2f}")
    
    cv2.imwrite(os.path.join(pasta_resultado, "deteccao_cor_dupla.jpg"), img_debug)
    
    print(f"   ✓ {len(produtos)} produtos detectados (garrafas + latas)")
    
    # Estatísticas
    garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA_DOURADA']
    latas = [p for p in produtos if p['tipo'] == 'LATA_BRANCA']
    
    print(f"      🍺 Garrafas douradas: {len(garrafas)}")
    print(f"      🥤 Latas brancas: {len(latas)}")
    
    return produtos

def testar_refinamento_cores(img, pasta_resultado):
    """Teste diferentes faixas de cor para otimização"""
    print("\n🎨 TESTANDO DIFERENTES FAIXAS DE COR")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Diferentes configurações de branco
    configs_branco = [
        {"nome": "BRANCO_RESTRITO", "lower": [0, 0, 200], "upper": [180, 20, 255]},
        {"nome": "BRANCO_MEDIO", "lower": [0, 0, 180], "upper": [180, 30, 255]},
        {"nome": "BRANCO_AMPLO", "lower": [0, 0, 160], "upper": [180, 40, 255]},
    ]
    
    # Diferentes configurações de dourado
    configs_dourado = [
        {"nome": "DOURADO_RESTRITO", "lower": [15, 80, 80], "upper": [30, 255, 255]},
        {"nome": "DOURADO_MEDIO", "lower": [10, 50, 50], "upper": [35, 255, 255]},
        {"nome": "DOURADO_AMPLO", "lower": [5, 30, 30], "upper": [40, 255, 255]},
    ]
    
    for config in configs_branco:
        lower = np.array(config["lower"])
        upper = np.array(config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Contar contornos
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contornos_grandes = [c for c in contornos if cv2.contourArea(c) > 8000]
        
        print(f"   {config['nome']}: {len(contornos_grandes)} objetos")
        cv2.imwrite(os.path.join(pasta_resultado, f"teste_{config['nome'].lower()}.jpg"), mask)
    
    for config in configs_dourado:
        lower = np.array(config["lower"])
        upper = np.array(config["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Contar contornos
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contornos_grandes = [c for c in contornos if cv2.contourArea(c) > 8000]
        
        print(f"   {config['nome']}: {len(contornos_grandes)} objetos")
        cv2.imwrite(os.path.join(pasta_resultado, f"teste_{config['nome'].lower()}.jpg"), mask)

def main():
    """Teste do método melhorado"""
    print("=" * 70)
    print("🎯 MÉTODO MELHORADO: DETECÇÃO COR DUPLA")
    print("🍺 Garrafas douradas + 🥤 Latas brancas = 4 produtos Corona")
    print("=" * 70)
    
    # Caminho da imagem Corona
    imagem_path = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de teste
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"teste_cor_dupla_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta de teste: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    if not os.path.exists(imagem_path):
        print(f"❌ Imagem não encontrada: {imagem_path}")
        return
    
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Testar método melhorado
    produtos = metodo_melhorado_cor_dupla(img, pasta_resultado)
    
    # Testar diferentes configurações
    testar_refinamento_cores(img, pasta_resultado)
    
    # Resultado final
    print(f"\n🎉 RESULTADO FINAL:")
    print(f"   🎯 Meta: 4 produtos Corona")
    print(f"   ✅ Detectado: {len(produtos)} produtos")
    
    if len(produtos) == 4:
        print(f"   🏆 PERFEITO! Detectou exatamente 4 produtos!")
    elif len(produtos) == 3:
        print(f"   ⚠️ QUASE! Faltou 1 produto (provavelmente a lata branca)")
    else:
        print(f"   🔧 PRECISA AJUSTAR: diferença de {abs(4 - len(produtos))} produtos")
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_cor_dupla.txt"), 'w', encoding='utf-8') as f:
        f.write("TESTE: DETECÇÃO COR DUPLA\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Objetivo: Detectar 4 produtos Corona\n")
        f.write(f"Resultado: {len(produtos)} produtos detectados\n\n")
        
        f.write("PRODUTOS ENCONTRADOS:\n")
        for i, produto in enumerate(produtos, 1):
            f.write(f"{i}. {produto['tipo']} - Área: {produto['area']:.0f}\n")
        
        garrafas = len([p for p in produtos if p['tipo'] == 'GARRAFA_DOURADA'])
        latas = len([p for p in produtos if p['tipo'] == 'LATA_BRANCA'])
        
        f.write(f"\nResumo:\n")
        f.write(f"- Garrafas douradas: {garrafas}\n")
        f.write(f"- Latas brancas: {latas}\n")
        f.write(f"- Total: {len(produtos)}\n")
    
    print(f"\n📄 Relatório: relatorio_cor_dupla.txt")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()