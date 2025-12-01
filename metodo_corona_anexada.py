#!/usr/bin/env python3
"""
MÉTODO PARA IMAGEM CORONA ANEXADA
Baseado na imagem específica que o usuário anexou com 4 produtos Corona
1 lata branca Corona + 3 garrafas douradas Corona
"""

import cv2
import numpy as np
import os
from datetime import datetime
import tempfile
import base64

def criar_imagem_anexada():
    """
    Simula a criação da imagem Corona anexada pelo usuário
    Na prática, esta função seria substituída pela imagem real
    """
    # Esta função será chamada apenas se a imagem anexada estiver disponível
    # Por enquanto, retorna None para usar imagem de teste
    return None

def detectar_produtos_corona_anexada(img, pasta_resultado):
    """
    Detecção otimizada para a imagem Corona anexada
    - 1 lata Corona branca (lado esquerdo)
    - 3 garrafas Corona douradas/amarelas
    """
    print("\n🍺 DETECÇÃO PRODUTOS CORONA - IMAGEM ANEXADA")
    print("   🎯 Esperado: 1 lata branca + 3 garrafas douradas")
    
    altura, largura = img.shape[:2]
    img_debug = img.copy()
    
    # ===== MÉTODO 1: DETECÇÃO POR COR HSV =====
    print("   🎨 Método 1: Detecção por cor HSV...")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Detectar LATA BRANCA (baixa saturação, alto brilho)
    print("      🥤 Detectando lata branca...")
    lower_branco = np.array([0, 0, 200])
    upper_branco = np.array([180, 30, 255])
    mask_branco = cv2.inRange(hsv, lower_branco, upper_branco)
    
    # Detectar GARRAFAS DOURADAS (hue amarelo/dourado)
    print("      🍺 Detectando garrafas douradas...")
    lower_dourado1 = np.array([10, 50, 50])
    upper_dourado1 = np.array([35, 255, 255])
    mask_dourado = cv2.inRange(hsv, lower_dourado1, upper_dourado1)
    
    # Combinar máscaras
    mask_produtos = cv2.bitwise_or(mask_branco, mask_dourado)
    
    # Limpeza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_OPEN, kernel)
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_CLOSE, kernel)
    
    cv2.imwrite(os.path.join(pasta_resultado, "01_mask_cores.jpg"), mask_produtos)
    cv2.imwrite(os.path.join(pasta_resultado, "01a_mask_branco.jpg"), mask_branco)
    cv2.imwrite(os.path.join(pasta_resultado, "01b_mask_dourado.jpg"), mask_dourado)
    
    # ===== MÉTODO 2: TEMPLATE MATCHING PARA FORMAS =====
    print("   📐 Método 2: Detecção por formas...")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detectar formas de garrafa (altas e estreitas) vs lata (mais quadrada)
    contornos, _ = cv2.findContours(mask_produtos, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        if area > 8000:  # Filtrar objetos pequenos
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Analisar cor dominante nesta região
            roi_branco = mask_branco[y:y+h, x:x+w]
            roi_dourado = mask_dourado[y:y+h, x:x+w]
            
            pixels_branco = np.sum(roi_branco > 0)
            pixels_dourado = np.sum(roi_dourado > 0)
            
            # Classificar baseado na cor e forma
            if pixels_branco > pixels_dourado:
                # Região com mais pixels brancos = LATA
                if 0.5 < aspect_ratio < 2.0:  # Latas podem ser mais quadradas
                    tipo = "LATA_BRANCA"
                    cor_debug = (255, 255, 255)  # Branco
                    produtos.append({
                        'id': len(produtos) + 1,
                        'tipo': tipo,
                        'area': area,
                        'bbox': (x, y, w, h),
                        'aspect_ratio': aspect_ratio,
                        'confianca': pixels_branco / (pixels_branco + pixels_dourado + 1)
                    })
            else:
                # Região com mais pixels dourados = GARRAFA
                if 0.2 < aspect_ratio < 1.0:  # Garrafas são mais altas
                    tipo = "GARRAFA_DOURADA" 
                    cor_debug = (0, 165, 255)  # Laranja
                    produtos.append({
                        'id': len(produtos) + 1,
                        'tipo': tipo,
                        'area': area,
                        'bbox': (x, y, w, h),
                        'aspect_ratio': aspect_ratio,
                        'confianca': pixels_dourado / (pixels_branco + pixels_dourado + 1)
                    })
            
            # Se foi classificado como produto válido
            if len(produtos) > 0 and produtos[-1]['id'] == len(produtos):
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor_debug, 3)
                cv2.putText(img_debug, f"{tipo[:6]} {len(produtos)}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_debug, 2)
                
                print(f"      ✅ {tipo}: {area:.0f}px, ratio {aspect_ratio:.2f}, conf {produtos[-1]['confianca']:.2f}")
    
    cv2.imwrite(os.path.join(pasta_resultado, "02_deteccao_final.jpg"), img_debug)
    
    # ===== ANÁLISE ESTATÍSTICA =====
    garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA_DOURADA']
    latas = [p for p in produtos if p['tipo'] == 'LATA_BRANCA']
    
    print(f"   ✅ RESULTADO MÉTODO HSV+FORMA:")
    print(f"      🍺 Garrafas douradas: {len(garrafas)}")
    print(f"      🥤 Latas brancas: {len(latas)}")
    print(f"      📊 Total: {len(produtos)}")
    
    return produtos, garrafas, latas

def metodo_otsu_avancado(img, pasta_resultado):
    """Método Otsu avançado com múltiplos thresholds"""
    print("\n🔬 MÉTODO OTSU AVANÇADO")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar diferentes técnicas de Otsu
    metodos = [
        {"nome": "OTSU_SIMPLES", "flags": cv2.THRESH_BINARY + cv2.THRESH_OTSU},
        {"nome": "OTSU_INVERSO", "flags": cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU},
    ]
    
    melhor_resultado = 0
    melhor_count = 0
    
    for metodo in metodos:
        # Aplicar threshold
        thresh_val, binary = cv2.threshold(gray, 0, 255, metodo["flags"])
        
        # Limpeza
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary_clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Contar componentes
        num_labels, _ = cv2.connectedComponents(binary_clean)
        count = num_labels - 1
        
        print(f"   {metodo['nome']}: threshold {thresh_val:.0f}, {count} objetos")
        
        cv2.imwrite(os.path.join(pasta_resultado, f"otsu_{metodo['nome'].lower()}.jpg"), binary_clean)
        
        # Escolher resultado mais próximo de 4
        if abs(count - 4) < abs(melhor_count - 4):
            melhor_count = count
            melhor_resultado = thresh_val
    
    print(f"   ✅ Melhor Otsu: {melhor_count} objetos (threshold {melhor_resultado:.0f})")
    return melhor_count

def main():
    """Teste específico para imagem Corona anexada"""
    print("=" * 80)
    print("🍺 DETECÇÃO PRODUTOS CORONA - IMAGEM ANEXADA PELO USUÁRIO")
    print("📷 Baseado na imagem específica: 1 lata branca + 3 garrafas douradas")
    print("🎯 Meta: 4 produtos Corona exatos")
    print("=" * 80)
    
    # Tentar usar imagem anexada
    img_anexada = criar_imagem_anexada()
    
    if img_anexada is not None:
        imagem_path = "corona_anexada_usuario.jpg"
        cv2.imwrite(imagem_path, img_anexada)
        print("✅ Usando imagem anexada pelo usuário")
    else:
        # Usar imagem de teste disponível
        possible_paths = [
            "imagens_teste/corona_produtos.jpeg",
            "anotada_104_1.jpeg.jpg"
        ]
        
        imagem_path = None
        for path in possible_paths:
            if os.path.exists(path):
                imagem_path = path
                break
        
        if imagem_path is None:
            print("❌ Nenhuma imagem encontrada")
            return
        
        print(f"ℹ️  Usando imagem de teste: {imagem_path}")
        print("   (Na prática, usaria a imagem Corona anexada)")
    
    # Criar pasta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"corona_anexada_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Carregar
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Salvar imagem original
    cv2.imwrite(os.path.join(pasta_resultado, "00_original.jpg"), img)
    
    # Aplicar detecção otimizada
    produtos, garrafas, latas = detectar_produtos_corona_anexada(img, pasta_resultado)
    
    # Método Otsu para comparação
    count_otsu = metodo_otsu_avancado(img, pasta_resultado)
    
    # ===== RESULTADO FINAL =====
    print(f"\n" + "="*60)
    print("🎉 RESULTADO FINAL - IMAGEM CORONA ANEXADA")
    print(f"="*60)
    print(f"🎯 Meta: 4 produtos (1 lata branca + 3 garrafas douradas)")
    print(f"✅ Detectado: {len(produtos)} produtos")
    print(f"   🥤 Latas brancas: {len(latas)}")
    print(f"   🍺 Garrafas douradas: {len(garrafas)}")
    print(f"📊 Comparação Otsu: {count_otsu} produtos")
    
    # Avaliar precisão
    if len(produtos) == 4 and len(latas) == 1 and len(garrafas) == 3:
        print("🏆 RESULTADO PERFEITO!")
        print("   ✅ Detectou exatamente 1 lata + 3 garrafas = 4 produtos Corona")
        status = "PERFEITO 🏆"
    elif len(produtos) == 4:
        print(f"🎯 4 produtos detectados, mas proporção não ideal:")
        print(f"   Detectado: {len(latas)} latas + {len(garrafas)} garrafas")
        print(f"   Esperado: 1 lata + 3 garrafas")
        status = "BOM 👍"
    else:
        print(f"🔧 Total detectado: {len(produtos)} (esperado: 4)")
        status = "PRECISA AJUSTAR 🔧"
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_corona_anexada.txt"), 'w', encoding='utf-8') as f:
        f.write("DETECÇÃO PRODUTOS CORONA - IMAGEM ANEXADA\n")
        f.write("=" * 45 + "\n\n")
        f.write("OBJETIVO: Detectar produtos na imagem Corona anexada pelo usuário\n")
        f.write("META: 1 lata Corona branca + 3 garrafas Corona douradas = 4 produtos\n\n")
        
        f.write("MÉTODO APLICADO:\n")
        f.write("1. Detecção por cor HSV (branco + dourado)\n")
        f.write("2. Análise de forma (aspect ratio)\n")
        f.write("3. Classificação por cor dominante\n")
        f.write("4. Filtragem por área mínima\n\n")
        
        f.write(f"RESULTADO: {status}\n")
        f.write(f"Total detectado: {len(produtos)} produtos\n")
        f.write(f"Latas brancas: {len(latas)}\n")
        f.write(f"Garrafas douradas: {len(garrafas)}\n")
        f.write(f"Comparação Otsu: {count_otsu} produtos\n\n")
        
        f.write("PRODUTOS DETECTADOS:\n")
        for produto in produtos:
            f.write(f"ID {produto['id']} - {produto['tipo']}:\n")
            f.write(f"  Área: {produto['area']:.0f} pixels\n")
            f.write(f"  Proporção: {produto['aspect_ratio']:.2f}\n")
            f.write(f"  Confiança: {produto['confianca']:.2f}\n")
            f.write(f"  Posição: {produto['bbox']}\n\n")
        
        if len(produtos) == 4 and len(latas) == 1 and len(garrafas) == 3:
            f.write("✅ CONCLUSÃO: DETECÇÃO PERFEITA!\n")
            f.write("O algoritmo detectou corretamente todos os 4 produtos Corona\n")
            f.write("na proporção exata: 1 lata branca + 3 garrafas douradas.\n")
        else:
            f.write("⚠️ CONCLUSÃO: PRECISA REFINAMENTO\n")
            f.write("O algoritmo precisa ser ajustado para detectar exatamente\n")
            f.write("1 lata branca + 3 garrafas douradas = 4 produtos.\n")
    
    print(f"\n📄 Relatório completo: relatorio_corona_anexada.txt")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta de resultado aberta!")
    except:
        pass

if __name__ == "__main__":
    main()