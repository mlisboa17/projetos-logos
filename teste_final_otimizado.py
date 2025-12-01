#!/usr/bin/env python3
"""
MÉTODO FINAL OTIMIZADO: DETECÇÃO COR DUPLA PRECISA
- 3 Garrafas douradas/amarelas (Corona líquido)  
- 1 Lata branca (Corona lata 350ML)
"""

import cv2
import numpy as np
import os
from datetime import datetime

def metodo_final_otimizado(img, pasta_resultado):
    """MÉTODO FINAL: 3 garrafas douradas + 1 lata branca = 4 produtos"""
    print("\n🎯 MÉTODO FINAL OTIMIZADO: COR DUPLA PRECISA")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_debug = img.copy()
    altura, largura = img.shape[:2]
    
    # ===== DETECÇÃO 1: GARRAFAS DOURADAS (mais restrita) =====
    print("   🍺 Detectando garrafas douradas...")
    lower_dourado = np.array([15, 60, 60])  # Mais restrito
    upper_dourado = np.array([30, 255, 255])
    mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
    
    # Limpar máscara dourada
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_OPEN, kernel)
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_CLOSE, kernel)
    
    # ===== DETECÇÃO 2: LATAS BRANCAS (muito mais restrita) =====
    print("   🥤 Detectando latas brancas...")
    # Branco muito específico: saturação MUITO baixa, valor MUITO alto
    lower_branco = np.array([0, 0, 200])    # V >= 200 (muito claro)
    upper_branco = np.array([180, 15, 255]) # S <= 15 (quase sem cor)
    mask_branco = cv2.inRange(hsv, lower_branco, upper_branco)
    
    # Limpar máscara branca com operações mais agressivas
    kernel_branco = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    mask_branco = cv2.morphologyEx(mask_branco, cv2.MORPH_OPEN, kernel_branco)
    mask_branco = cv2.morphologyEx(mask_branco, cv2.MORPH_CLOSE, kernel_branco)
    
    # ===== REMOVER SOBREPOSIÇÕES =====
    # Onde há dourado, não pode haver branco
    mask_branco = cv2.bitwise_and(mask_branco, cv2.bitwise_not(mask_dourado))
    
    # Salvar máscaras
    cv2.imwrite(os.path.join(pasta_resultado, "final_mask_dourado.jpg"), mask_dourado)
    cv2.imwrite(os.path.join(pasta_resultado, "final_mask_branco.jpg"), mask_branco)
    
    produtos = []
    
    # ===== PROCESSAR GARRAFAS DOURADAS =====
    contornos_dourado, _ = cv2.findContours(mask_dourado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for i, contorno in enumerate(contornos_dourado):
        area = cv2.contourArea(contorno)
        
        if area > 15000:  # Área mínima maior para garrafas
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Garrafas: altas e estreitas
            if 0.15 < aspect_ratio < 0.8 and h > w * 1.2:
                produtos.append({
                    'id': len(produtos),
                    'tipo': "GARRAFA_DOURADA",
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'bbox': (x, y, w, h),
                    'confianca': area / 200000  # Baseado na área típica
                })
                
                # Desenhar
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), (0, 165, 255), 3)
                cv2.putText(img_debug, f"GARR{len(produtos)}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                print(f"      ✅ GARRAFA {len(produtos)}: {area:.0f}px, ratio {aspect_ratio:.2f}")
    
    # ===== PROCESSAR LATAS BRANCAS =====
    contornos_branco, _ = cv2.findContours(mask_branco, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Ordenar latas por área (pegar só as maiores)
    contornos_branco_grandes = []
    for contorno in contornos_branco:
        area = cv2.contourArea(contorno)
        if area > 8000:  # Área mínima para latas
            contornos_branco_grandes.append((contorno, area))
    
    # Ordenar por área (maiores primeiro) e pegar só os 2 maiores
    contornos_branco_grandes.sort(key=lambda x: x[1], reverse=True)
    
    for i, (contorno, area) in enumerate(contornos_branco_grandes[:2]):  # Máximo 2 latas
        x, y, w, h = cv2.boundingRect(contorno)
        aspect_ratio = w / float(h)
        
        # Latas: podem ser mais variadas na forma
        if 0.3 < aspect_ratio < 2.5:
            # Verificar se não está muito próxima de uma garrafa (evitar duplicatas)
            muito_proxima = False
            for produto in produtos:
                if produto['tipo'] == 'GARRAFA_DOURADA':
                    px, py, pw, ph = produto['bbox']
                    centro_produto_x = px + pw//2
                    centro_produto_y = py + ph//2
                    centro_lata_x = x + w//2
                    centro_lata_y = y + h//2
                    
                    distancia = np.sqrt((centro_produto_x - centro_lata_x)**2 + 
                                      (centro_produto_y - centro_lata_y)**2)
                    
                    if distancia < 100:  # Se muito próxima, é provavelmente a mesma
                        muito_proxima = True
                        break
            
            if not muito_proxima:
                produtos.append({
                    'id': len(produtos),
                    'tipo': "LATA_BRANCA",
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'bbox': (x, y, w, h),
                    'confianca': min(area / 20000, 1.0)  # Baseado na área típica
                })
                
                # Desenhar
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), (255, 255, 255), 3)
                cv2.putText(img_debug, f"LATA{len(produtos)}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                print(f"      ✅ LATA {len(produtos)}: {area:.0f}px, ratio {aspect_ratio:.2f}")
    
    cv2.imwrite(os.path.join(pasta_resultado, "final_deteccao_otimizada.jpg"), img_debug)
    
    # Estatísticas finais
    garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA_DOURADA']
    latas = [p for p in produtos if p['tipo'] == 'LATA_BRANCA']
    
    print(f"   ✓ TOTAL: {len(produtos)} produtos")
    print(f"      🍺 Garrafas douradas: {len(garrafas)}")
    print(f"      🥤 Latas brancas: {len(latas)}")
    
    return produtos

def analise_hsv_detalhada(img, pasta_resultado):
    """Análise detalhada das cores na imagem"""
    print("\n🔬 ANÁLISE HSV DETALHADA")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Amostrar pixels de diferentes regiões
    altura, largura = img.shape[:2]
    
    # Definir regiões de interesse
    regioes = [
        {"nome": "CENTRO_ESQ", "x": largura//4, "y": altura//2},
        {"nome": "CENTRO_DIR", "x": 3*largura//4, "y": altura//2},
        {"nome": "SUPERIOR", "x": largura//2, "y": altura//4},
        {"nome": "INFERIOR", "x": largura//2, "y": 3*altura//4}
    ]
    
    for regiao in regioes:
        x, y = regiao["x"], regiao["y"]
        
        # Pegar região 50x50 pixels
        roi_hsv = hsv[max(0, y-25):min(altura, y+25), max(0, x-25):min(largura, x+25)]
        
        if roi_hsv.size > 0:
            h_mean = np.mean(roi_hsv[:,:,0])
            s_mean = np.mean(roi_hsv[:,:,1])
            v_mean = np.mean(roi_hsv[:,:,2])
            
            print(f"   {regiao['nome']}: H={h_mean:.1f}, S={s_mean:.1f}, V={v_mean:.1f}")

def main():
    """Teste final otimizado"""
    print("=" * 70)
    print("🏆 MÉTODO FINAL OTIMIZADO")
    print("🎯 Objetivo: 3 garrafas douradas + 1 lata branca = 4 produtos")
    print("=" * 70)
    
    # Caminho da imagem Corona
    imagem_path = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de teste
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"teste_final_otimizado_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
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
    
    # Análise HSV
    analise_hsv_detalhada(img, pasta_resultado)
    
    # Método final otimizado
    produtos = metodo_final_otimizado(img, pasta_resultado)
    
    # Resultado
    print(f"\n🎉 RESULTADO FINAL OTIMIZADO:")
    print(f"   🎯 Meta: 4 produtos (3 garrafas + 1 lata)")
    print(f"   ✅ Detectado: {len(produtos)} produtos")
    
    garrafas = len([p for p in produtos if p['tipo'] == 'GARRAFA_DOURADA'])
    latas = len([p for p in produtos if p['tipo'] == 'LATA_BRANCA'])
    
    if len(produtos) == 4 and garrafas == 3 and latas == 1:
        print(f"   🏆 PERFEITO! 3 garrafas + 1 lata = 4 produtos Corona!")
    elif len(produtos) == 4:
        print(f"   🎯 4 produtos detectados, mas proporção: {garrafas}G + {latas}L")
    else:
        print(f"   🔧 Detectou: {garrafas} garrafas + {latas} latas = {len(produtos)} total")
    
    # Relatório detalhado
    with open(os.path.join(pasta_resultado, "relatorio_final.txt"), 'w', encoding='utf-8') as f:
        f.write("TESTE FINAL OTIMIZADO\n")
        f.write("=" * 25 + "\n\n")
        f.write("OBJETIVO: Detectar exatamente 4 produtos Corona\n")
        f.write("- 3 garrafas douradas (líquido dourado)\n")
        f.write("- 1 lata branca (Corona 350ML)\n\n")
        
        f.write(f"RESULTADO: {len(produtos)} produtos detectados\n")
        f.write(f"- Garrafas douradas: {garrafas}\n")
        f.write(f"- Latas brancas: {latas}\n\n")
        
        f.write("DETALHES DOS PRODUTOS:\n")
        for i, produto in enumerate(produtos, 1):
            f.write(f"{i}. {produto['tipo']}\n")
            f.write(f"   Área: {produto['area']:.0f} pixels\n")
            f.write(f"   Proporção W/H: {produto['aspect_ratio']:.2f}\n")
            f.write(f"   Confiança: {produto['confianca']:.2f}\n\n")
        
        if len(produtos) == 4 and garrafas == 3 and latas == 1:
            f.write("✅ STATUS: PERFEITO!\n")
            f.write("Detectou exatamente 3 garrafas + 1 lata = 4 produtos Corona\n")
        else:
            f.write("⚠️ STATUS: PRECISA AJUSTE\n")
            f.write("Não detectou a combinação exata de 3 garrafas + 1 lata\n")
    
    print(f"\n📄 Relatório completo: relatorio_final.txt")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()