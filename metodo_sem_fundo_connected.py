#!/usr/bin/env python3
"""
MÉTODO MELHORADO: REMOÇÃO DE FUNDO + CONNECTED COMPONENTS
Primeiro remove o fundo automaticamente, depois aplica Connected Components
"""

import cv2
import numpy as np
import os
from datetime import datetime

def remover_fundo_automatico(img):
    """Remove fundo automaticamente usando múltiplas técnicas"""
    print("   🎭 Removendo fundo automaticamente...")
    
    # ===== TÉCNICA 1: GrabCut (fundo/foreground) =====
    height, width = img.shape[:2]
    
    # Criar máscara inicial (interior como provável foreground)
    mask = np.zeros((height, width), np.uint8)
    
    # Definir retângulo central como provável foreground
    rect = (width//8, height//8, 6*width//8, 6*height//8)
    
    # Aplicar GrabCut
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    try:
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Converter máscara
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        img_sem_fundo = img * mask2[:, :, np.newaxis]
        
        print("      ✅ GrabCut aplicado")
        return img_sem_fundo, mask2
        
    except Exception as e:
        print(f"      ❌ GrabCut falhou: {e}")
        return None, None

def remover_fundo_por_cor(img):
    """Remove fundo baseado na cor dominante das bordas"""
    print("   🎨 Removendo fundo por análise de cor...")
    
    height, width = img.shape[:2]
    
    # Coletar pixels das bordas (provável fundo)
    borda_pixels = []
    
    # Borda superior e inferior
    borda_pixels.extend(img[0:10, :].reshape(-1, 3))
    borda_pixels.extend(img[-10:, :].reshape(-1, 3))
    
    # Borda esquerda e direita
    borda_pixels.extend(img[:, 0:10].reshape(-1, 3))
    borda_pixels.extend(img[:, -10:].reshape(-1, 3))
    
    borda_pixels = np.array(borda_pixels)
    
    # Encontrar cor dominante do fundo (média das bordas)
    cor_fundo = np.mean(borda_pixels, axis=0)
    
    print(f"      📊 Cor do fundo detectada: BGR({cor_fundo[0]:.0f}, {cor_fundo[1]:.0f}, {cor_fundo[2]:.0f})")
    
    # Criar máscara baseada na distância da cor do fundo
    diff = np.sqrt(np.sum((img - cor_fundo)**2, axis=2))
    
    # Threshold adaptativo baseado na variação
    threshold = np.std(diff) * 1.5
    mask = (diff > threshold).astype(np.uint8)
    
    # Limpeza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Aplicar máscara
    img_sem_fundo = img * mask[:, :, np.newaxis]
    
    print(f"      ✅ Threshold usado: {threshold:.1f}")
    return img_sem_fundo, mask

def metodo_connected_components_melhorado(img, pasta_resultado):
    """Connected Components após remoção automática de fundo"""
    print("\n🔬 MÉTODO MELHORADO: REMOÇÃO DE FUNDO + CONNECTED COMPONENTS")
    
    # ===== PASSO 1: TENTAR REMOVER FUNDO =====
    img_sem_fundo = None
    mask_fundo = None
    
    # Tentar GrabCut primeiro
    img_grabcut, mask_grabcut = remover_fundo_automatico(img)
    if img_grabcut is not None:
        img_sem_fundo = img_grabcut
        mask_fundo = mask_grabcut
        cv2.imwrite(os.path.join(pasta_resultado, "01_grabcut_result.jpg"), img_sem_fundo)
        print("   ✅ Usando resultado do GrabCut")
    
    # Se GrabCut falhou, usar remoção por cor
    if img_sem_fundo is None:
        img_sem_fundo, mask_fundo = remover_fundo_por_cor(img)
        cv2.imwrite(os.path.join(pasta_resultado, "01_cor_result.jpg"), img_sem_fundo)
        print("   ✅ Usando remoção por cor")
    
    cv2.imwrite(os.path.join(pasta_resultado, "01_mask_fundo.jpg"), mask_fundo * 255)
    
    # ===== PASSO 2: CONVERTER PARA ESCALA DE CINZA =====
    if len(img_sem_fundo.shape) == 3:
        gray = cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_sem_fundo.copy()
    
    cv2.imwrite(os.path.join(pasta_resultado, "02_gray_sem_fundo.jpg"), gray)
    
    # ===== PASSO 3: BINARIZAÇÃO (PIXELS NÃO-ZERO = PRODUTO) =====
    print("   🔲 Criando máscara binária...")
    
    # Qualquer pixel não-preto é produto
    mask_produtos = (gray > 10).astype(np.uint8) * 255
    
    # Limpeza morfológica agressiva
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_OPEN, kernel)
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_CLOSE, kernel)
    
    cv2.imwrite(os.path.join(pasta_resultado, "03_mask_produtos.jpg"), mask_produtos)
    
    # ===== PASSO 4: CONNECTED COMPONENTS =====
    print("   🔍 Aplicando Connected Components...")
    
    num_labels, labels = cv2.connectedComponents(mask_produtos)
    total_componentes = num_labels - 1
    
    print(f"      📊 Componentes encontrados: {total_componentes}")
    
    # ===== PASSO 5: ANÁLISE E FILTRAGEM =====
    print("   📋 Analisando componentes...")
    
    img_debug = img.copy()
    produtos = []
    cores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
             (255, 0, 255), (0, 255, 255), (128, 128, 128)]
    
    for label in range(1, num_labels):
        # Calcular área
        area = np.sum(labels == label)
        
        # Filtrar componentes pequenos (ruído)
        if area < 8000:  # Threshold para produtos reais
            print(f"      ❌ Componente {label}: {area} pixels (muito pequeno)")
            continue
        
        # Encontrar bounding box
        component_mask = (labels == label).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(main_contour)
            
            # Calcular características
            aspect_ratio = w / float(h)
            
            # Classificar por forma
            if aspect_ratio < 0.7:
                tipo = "GARRAFA"
            elif 0.7 <= aspect_ratio <= 1.8:
                tipo = "LATA"
            else:
                tipo = "OUTRO"
            
            produto = {
                'id': label,
                'tipo': tipo,
                'area': area,
                'bbox': (x, y, w, h),
                'aspect_ratio': aspect_ratio,
                'centro': (x + w//2, y + h//2)
            }
            
            produtos.append(produto)
            
            # Desenhar detecção
            cor = cores[label % len(cores)]
            cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor, 4)
            cv2.putText(img_debug, f"{tipo[:4]}{label}", (x, y-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
            
            print(f"      ✅ {tipo} {label}: {area} pixels, ratio {aspect_ratio:.2f}, bbox {w}x{h}")
    
    cv2.imwrite(os.path.join(pasta_resultado, "04_deteccoes_finais.jpg"), img_debug)
    
    # ===== ESTATÍSTICAS =====
    garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA']
    latas = [p for p in produtos if p['tipo'] == 'LATA']
    outros = [p for p in produtos if p['tipo'] == 'OUTRO']
    
    print(f"   ✅ RESULTADO: {len(produtos)} produtos")
    print(f"      🍺 Garrafas: {len(garrafas)}")
    print(f"      🥤 Latas: {len(latas)}")
    print(f"      ❓ Outros: {len(outros)}")
    
    return produtos, garrafas, latas, outros

def main():
    """Teste do método melhorado"""
    print("=" * 80)
    print("🎭 MÉTODO MELHORADO: REMOÇÃO AUTOMÁTICA DE FUNDO + CONNECTED COMPONENTS")
    print("💡 Baseado na sua observação: 'quando tira o fundo, facilita'")
    print("🎯 Objetivo: 4 produtos Corona (3 garrafas + 1 lata)")
    print("=" * 80)
    
    # Procurar imagem
    possible_paths = [
        "imagens_teste/corona_produtos.jpeg",
        "corona_produtos.jpeg",
        "produtos_corona.jpg",
        "anotada_104_1.jpeg.jpg"
    ]
    
    imagem_path = None
    for path in possible_paths:
        if os.path.exists(path):
            imagem_path = path
            print(f"✅ Usando imagem: {path}")
            break
    
    if imagem_path is None:
        print("❌ Nenhuma imagem encontrada")
        return
    
    # Criar pasta de resultado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"sem_fundo_connected_components_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Aplicar método melhorado
    produtos, garrafas, latas, outros = metodo_connected_components_melhorado(img, pasta_resultado)
    
    # ===== RESULTADO FINAL =====
    print(f"\n" + "="*60)
    print("🎉 RESULTADO FINAL")
    print(f"="*60)
    print(f"🎯 Meta: 4 produtos Corona")
    print(f"✅ Detectado: {len(produtos)} produtos")
    print(f"   🍺 Garrafas: {len(garrafas)}")
    print(f"   🥤 Latas: {len(latas)}")
    print(f"   ❓ Outros: {len(outros)}")
    
    # Avaliar
    if len(produtos) == 4:
        if len(garrafas) == 3 and len(latas) == 1:
            print("🏆 PERFEITO! 3 garrafas + 1 lata = 4 produtos Corona!")
            status = "PERFEITO"
        else:
            print(f"🎯 4 produtos, mas proporção: {len(garrafas)}G + {len(latas)}L + {len(outros)}O")
            status = "BOM"
    else:
        print(f"🔧 Detectou {len(produtos)} produtos (esperado: 4)")
        status = "AJUSTAR"
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_sem_fundo.txt"), 'w', encoding='utf-8') as f:
        f.write("MÉTODO: REMOÇÃO DE FUNDO + CONNECTED COMPONENTS\n")
        f.write("=" * 50 + "\n\n")
        f.write("TÉCNICA:\n")
        f.write("1. Remoção automática de fundo (GrabCut ou cor)\n")
        f.write("2. Conversão para escala de cinza\n")
        f.write("3. Binarização (pixel ≠ 0 = produto)\n")
        f.write("4. Connected Components\n")
        f.write("5. Filtragem e classificação por forma\n\n")
        
        f.write(f"RESULTADO:\n")
        f.write(f"Total: {len(produtos)} produtos\n")
        f.write(f"Garrafas: {len(garrafas)}\n")
        f.write(f"Latas: {len(latas)}\n")
        f.write(f"Outros: {len(outros)}\n")
        f.write(f"Status: {status}\n\n")
        
        f.write("PRODUTOS DETECTADOS:\n")
        for produto in produtos:
            f.write(f"ID {produto['id']} - {produto['tipo']}:\n")
            f.write(f"  Área: {produto['area']} pixels\n")
            f.write(f"  Proporção: {produto['aspect_ratio']:.2f}\n")
            f.write(f"  Posição: {produto['centro']}\n\n")
    
    print(f"\n📄 Relatório: relatorio_sem_fundo.txt")
    print("🖼️  Etapas visuais geradas:")
    print("   - 01_*_result.jpg (fundo removido)")
    print("   - 02_gray_sem_fundo.jpg (escala de cinza)")
    print("   - 03_mask_produtos.jpg (máscara de produtos)")
    print("   - 04_deteccoes_finais.jpg (detecções finais)")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()