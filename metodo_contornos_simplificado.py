#!/usr/bin/env python3
"""
MÉTODO SIMPLIFICADO: DETECÇÃO POR CONTORNOS EXTERNOS
Baseado na imagem Corona anexada pelo usuário
"""

import cv2
import numpy as np
import os
from datetime import datetime

def detectar_produtos_corona(img, pasta_resultado):
    """
    Detecta produtos Corona usando contornos externos
    Otimizado para a imagem com fundo complexo (loja)
    """
    print("\n🎯 DETECÇÃO PRODUTOS CORONA")
    print("   📷 Otimizado para imagem com fundo de loja")
    
    altura, largura = img.shape[:2]
    img_debug = img.copy()
    
    # ===== ETAPA 1: PREPROCESSAMENTO =====
    print("   1️⃣ Preprocessamento...")
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.join(pasta_resultado, "01_gray.jpg"), gray)
    
    # Aplicar blur para reduzir ruído
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # ===== ETAPA 2: DETECÇÃO DE BORDAS =====
    print("   2️⃣ Detecção de bordas...")
    
    # Canny edge detection
    edges = cv2.Canny(gray_blur, 50, 150)
    cv2.imwrite(os.path.join(pasta_resultado, "02_edges.jpg"), edges)
    
    # Dilatação para conectar bordas próximas
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges_dilated = cv2.dilate(edges, kernel, iterations=1)
    cv2.imwrite(os.path.join(pasta_resultado, "03_edges_dilated.jpg"), edges_dilated)
    
    # ===== ETAPA 3: ENCONTRAR CONTORNOS =====
    print("   3️⃣ Encontrando contornos...")
    
    contornos, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"      🔍 {len(contornos)} contornos encontrados")
    
    # ===== ETAPA 4: FILTRAR CONTORNOS POR TAMANHO E FORMA =====
    print("   4️⃣ Filtrando contornos...")
    
    produtos = []
    min_area = 15000  # Área mínima para ser considerado produto
    max_area = largura * altura * 0.3  # Máximo 30% da imagem
    
    contornos_validos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        if min_area < area < max_area:
            # Calcular bounding box
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Calcular área do retângulo vs área do contorno (extent)
            rect_area = w * h
            extent = area / rect_area if rect_area > 0 else 0
            
            # Filtros para produtos reais
            if (0.1 < aspect_ratio < 3.0 and  # Não muito estreito nem muito largo
                extent > 0.3 and              # Preenche bem o retângulo
                w > 40 and h > 40):           # Tamanho mínimo razoável
                
                contornos_validos.append({
                    'contorno': contorno,
                    'area': area,
                    'bbox': (x, y, w, h),
                    'aspect_ratio': aspect_ratio,
                    'extent': extent,
                    'centro': (x + w//2, y + h//2)
                })
                
                print(f"      ✅ Contorno {i}: {area:.0f}px, ratio {aspect_ratio:.2f}, extent {extent:.2f}")
    
    # ===== ETAPA 5: ELIMINAR SOBREPOSIÇÕES =====
    print("   5️⃣ Eliminando sobreposições...")
    
    # Ordenar por área (maiores primeiro)
    contornos_validos.sort(key=lambda x: x['area'], reverse=True)
    
    produtos_finais = []
    
    for candidato in contornos_validos:
        x1, y1, w1, h1 = candidato['bbox']
        centro1 = candidato['centro']
        
        # Verificar se não está muito próximo de um produto já aceito
        muito_proximo = False
        
        for produto_aceito in produtos_finais:
            x2, y2, w2, h2 = produto_aceito['bbox']
            centro2 = produto_aceito['centro']
            
            # Calcular distância entre centros
            dist_centros = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            # Calcular sobreposição de retângulos
            overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            overlap_area = overlap_x * overlap_y
            
            # Se há sobreposição significativa ou estão muito próximos
            if (overlap_area > 0.3 * min(candidato['area'], produto_aceito['area']) or 
                dist_centros < 100):
                muito_proximo = True
                break
        
        if not muito_proximo:
            produtos_finais.append(candidato)
            print(f"      ✅ Produto aceito: área {candidato['area']:.0f}, centro {centro1}")
        else:
            print(f"      ❌ Produto rejeitado: muito próximo de outro")
    
    # ===== ETAPA 6: CLASSIFICAR POR FORMA =====
    print("   6️⃣ Classificando produtos...")
    
    garrafas = []
    latas = []
    outros = []
    
    cores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    for i, produto in enumerate(produtos_finais):
        ratio = produto['aspect_ratio']
        x, y, w, h = produto['bbox']
        
        # Classificar por proporção
        if ratio < 0.6:  # Mais alto que largo
            tipo = "GARRAFA"
            garrafas.append(produto)
            cor = (0, 255, 0)  # Verde
        elif 0.6 <= ratio <= 1.4:  # Aproximadamente quadrado
            tipo = "LATA"
            latas.append(produto)
            cor = (255, 0, 0)  # Azul
        else:  # Mais largo que alto
            tipo = "OUTRO"
            outros.append(produto)
            cor = (0, 0, 255)  # Vermelho
        
        produto['tipo'] = tipo
        produto['id'] = i + 1
        
        # Desenhar no debug
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor, 3)
        cv2.putText(img_debug, f"{tipo} {i+1}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
        
        print(f"      📋 Produto {i+1}: {tipo} (ratio {ratio:.2f})")
    
    cv2.imwrite(os.path.join(pasta_resultado, "04_produtos_detectados.jpg"), img_debug)
    
    return produtos_finais, garrafas, latas, outros

def main():
    """Teste do método simplificado"""
    print("=" * 70)
    print("🎯 MÉTODO SIMPLIFICADO: DETECÇÃO POR CONTORNOS")
    print("📷 Otimizado para imagem Corona com fundo de loja")
    print("🏪 Baseado na imagem anexada pelo usuário")
    print("=" * 70)
    
    # Procurar imagem
    possible_paths = [
        "imagens_teste/corona_produtos.jpeg",
        "corona_produtos.jpeg",
        "anotada_104_1.jpeg.jpg"
    ]
    
    imagem_path = None
    for path in possible_paths:
        if os.path.exists(path):
            imagem_path = path
            print(f"✅ Usando: {path}")
            break
    
    if imagem_path is None:
        print("❌ Nenhuma imagem encontrada")
        return
    
    # Criar pasta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"deteccao_contornos_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Detectar produtos
    produtos, garrafas, latas, outros = detectar_produtos_corona(img, pasta_resultado)
    
    # ===== RESULTADO =====
    print(f"\n" + "="*50)
    print("🎉 RESULTADO FINAL")
    print(f"="*50)
    print(f"🎯 Meta: 4 produtos Corona (3 garrafas + 1 lata)")
    print(f"✅ Detectado: {len(produtos)} produtos")
    print(f"   🍺 Garrafas: {len(garrafas)}")
    print(f"   🥤 Latas: {len(latas)}")
    print(f"   ❓ Outros: {len(outros)}")
    
    # Avaliar
    if len(produtos) == 4:
        if len(garrafas) == 3 and len(latas) == 1:
            print("🏆 PERFEITO! 3 garrafas + 1 lata!")
            status = "PERFEITO ✅"
        else:
            print(f"🎯 4 produtos, proporção: {len(garrafas)}G + {len(latas)}L + {len(outros)}O")
            status = "BOM 👍"
    else:
        print(f"🔧 Detectou {len(produtos)} produtos")
        status = "PRECISA AJUSTAR 🔧"
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_contornos.txt"), 'w', encoding='utf-8') as f:
        f.write("DETECÇÃO POR CONTORNOS EXTERNOS\n")
        f.write("=" * 35 + "\n\n")
        f.write("MÉTODO:\n")
        f.write("1. Conversão para escala de cinza\n")
        f.write("2. Detecção de bordas (Canny)\n")
        f.write("3. Encontrar contornos externos\n")
        f.write("4. Filtrar por tamanho e forma\n")
        f.write("5. Eliminar sobreposições\n")
        f.write("6. Classificar por proporção\n\n")
        
        f.write(f"RESULTADO: {status}\n")
        f.write(f"Total: {len(produtos)} produtos\n")
        f.write(f"Garrafas: {len(garrafas)}\n")
        f.write(f"Latas: {len(latas)}\n")
        f.write(f"Outros: {len(outros)}\n\n")
        
        f.write("PRODUTOS DETECTADOS:\n")
        for produto in produtos:
            f.write(f"ID {produto['id']} - {produto['tipo']}:\n")
            f.write(f"  Área: {produto['area']:.0f} pixels\n")
            f.write(f"  Proporção W/H: {produto['aspect_ratio']:.2f}\n")
            f.write(f"  Extent: {produto['extent']:.2f}\n")
            f.write(f"  Centro: {produto['centro']}\n\n")
    
    print(f"\n📄 Relatório: relatorio_contornos.txt")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()