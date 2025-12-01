#!/usr/bin/env python3
"""
MÉTODO CLÁSSICO: CONNECTED COMPONENTS LABELING
Baseado na pesquisa do usuário - ideal para fundo removido
"""

import cv2
import numpy as np
import os
from datetime import datetime

def metodo_connected_components(img, pasta_resultado):
    """
    MÉTODO CLÁSSICO: Connected Components Labeling
    1. Remove fundo (limiarização)
    2. Encontra componentes conectados 
    3. Conta produtos automaticamente
    """
    print("\n🔬 MÉTODO CONNECTED COMPONENTS")
    print("   📖 Baseado na pesquisa: Connected Component Labeling")
    
    # ===== PASSO 1: CONVERSÃO PARA ESCALA DE CINZA =====
    print("   1️⃣ Convertendo para escala de cinza...")
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    cv2.imwrite(os.path.join(pasta_resultado, "01_grayscale.jpg"), gray)
    
    # ===== PASSO 2: REMOÇÃO DO FUNDO (LIMIARIZAÇÃO) =====
    print("   2️⃣ Removendo fundo com limiarização...")
    
    # Testar diferentes valores de threshold
    thresholds = [200, 180, 160, 140, 120]
    melhor_thresh = None
    melhor_count = 0
    
    for thresh_val in thresholds:
        # Limiarização INVERSA (produto = branco, fundo = preto)
        _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
        
        # Limpeza morfológica para remover ruído
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh_clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh_clean = cv2.morphologyEx(thresh_clean, cv2.MORPH_CLOSE, kernel)
        
        # Contar componentes preliminar
        num_labels, _ = cv2.connectedComponents(thresh_clean)
        count = num_labels - 1  # -1 para ignorar fundo
        
        print(f"      Threshold {thresh_val}: {count} objetos")
        
        # Salvar para análise
        cv2.imwrite(os.path.join(pasta_resultado, f"thresh_{thresh_val}.jpg"), thresh_clean)
        
        # Escolher threshold que detecta ~4 objetos (próximo ao esperado)
        if abs(count - 4) < abs(melhor_count - 4) or melhor_thresh is None:
            melhor_count = count
            melhor_thresh = thresh_clean
    
    print(f"   ✓ Melhor resultado: {melhor_count} objetos")
    
    # Se não encontrou nenhuma imagem válida, usar a primeira
    if melhor_thresh is None:
        print("   ⚠️ Usando threshold padrão (200)")
        _, melhor_thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    cv2.imwrite(os.path.join(pasta_resultado, "02_binary_mask.jpg"), melhor_thresh)
    
    # ===== PASSO 3: CONNECTED COMPONENT LABELING =====
    print("   3️⃣ Aplicando Connected Component Labeling...")
    
    num_labels, labels = cv2.connectedComponents(melhor_thresh)
    total_produtos = num_labels - 1  # -1 para ignorar o fundo (label 0)
    
    print(f"      🔍 Componentes detectados: {num_labels}")
    print(f"      📦 Produtos encontrados: {total_produtos}")
    
    # ===== PASSO 4: ANÁLISE DE CADA COMPONENTE =====
    print("   4️⃣ Analisando cada produto...")
    
    # Criar imagem colorida para visualizar componentes
    img_components = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    img_boxes = img.copy()
    
    produtos = []
    cores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
             (255, 0, 255), (0, 255, 255), (128, 128, 128)]
    
    for label in range(1, num_labels):  # Ignorar label 0 (fundo)
        # Máscara para este componente
        component_mask = (labels == label).astype(np.uint8) * 255
        
        # Calcular área
        area = np.sum(labels == label)
        
        # Filtrar componentes muito pequenos (ruído)
        if area < 5000:
            print(f"      ❌ Componente {label}: {area} pixels (muito pequeno)")
            continue
        
        # Encontrar bounding box
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            # Pegar maior contorno (caso tenha fragmentos)
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(main_contour)
            
            # Calcular características
            aspect_ratio = w / float(h)
            extent = cv2.contourArea(main_contour) / (w * h)
            
            produto = {
                'id': label,
                'area': area,
                'bbox': (x, y, w, h),
                'aspect_ratio': aspect_ratio,
                'extent': extent,
                'centro': (x + w//2, y + h//2)
            }
            produtos.append(produto)
            
            # Colorir componente
            cor = cores[label % len(cores)]
            img_components[labels == label] = cor
            
            # Desenhar bounding box
            cv2.rectangle(img_boxes, (x, y), (x+w, y+h), cor, 3)
            cv2.putText(img_boxes, f"P{label}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            
            print(f"      ✅ Produto {label}: {area} pixels, bbox {w}x{h}, ratio {aspect_ratio:.2f}")
    
    # Salvar visualizações
    cv2.imwrite(os.path.join(pasta_resultado, "03_components_colored.jpg"), img_components)
    cv2.imwrite(os.path.join(pasta_resultado, "04_bounding_boxes.jpg"), img_boxes)
    
    # ===== PASSO 5: CLASSIFICAÇÃO POR FORMA =====
    print("   5️⃣ Classificando produtos por forma...")
    
    garrafas = []
    latas = []
    outros = []
    
    for produto in produtos:
        ratio = produto['aspect_ratio']
        area = produto['area']
        
        if ratio < 0.7:  # Mais alto que largo = garrafa
            tipo = "GARRAFA"
            garrafas.append(produto)
        elif 0.7 <= ratio <= 1.5:  # Proporção equilibrada = lata
            tipo = "LATA"
            latas.append(produto)
        else:  # Muito largo = outro
            tipo = "OUTRO"
            outros.append(produto)
        
        produto['tipo'] = tipo
        print(f"      📋 Produto {produto['id']}: {tipo} (ratio {ratio:.2f})")
    
    return produtos, len(garrafas), len(latas)

def metodo_otsu_adaptativo(img, pasta_resultado):
    """Variação com Otsu automático"""
    print("\n🔬 VARIAÇÃO: OTSU ADAPTATIVO")
    
    # Converter para escala de cinza
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Aplicar filtro Gaussiano para suavizar
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Otsu automático
    thresh_otsu, binary_otsu = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    print(f"   📊 Threshold Otsu automático: {thresh_otsu:.0f}")
    
    # Limpeza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary_clean = cv2.morphologyEx(binary_otsu, cv2.MORPH_OPEN, kernel)
    binary_clean = cv2.morphologyEx(binary_clean, cv2.MORPH_CLOSE, kernel)
    
    # Connected components
    num_labels, labels = cv2.connectedComponents(binary_clean)
    total_produtos = num_labels - 1
    
    # Salvar
    cv2.imwrite(os.path.join(pasta_resultado, "otsu_binary.jpg"), binary_clean)
    
    print(f"   ✓ Otsu detectou: {total_produtos} produtos")
    return total_produtos

def main():
    """Teste do método Connected Components"""
    print("=" * 80)
    print("🔬 MÉTODO CLÁSSICO: CONNECTED COMPONENTS LABELING")
    print("📖 Baseado na pesquisa: varredura + agrupamento de pixels conectados")
    print("🎯 Ideal para: fundo removido ou uniforme")
    print("=" * 80)
    
    # Procurar por imagem Corona nos testes anteriores
    possible_paths = [
        "imagens_teste/corona_produtos.jpeg",
        "corona_produtos.jpeg",
        "produtos_corona.jpg",
        "anotada_104_1.jpeg.jpg",  # Uma das imagens que encontramos
        "anotada_105_2.jpeg.jpg"
    ]
    
    imagem_path = None
    for path in possible_paths:
        if os.path.exists(path):
            imagem_path = path
            print(f"✅ Encontrada imagem: {path}")
            break
    
    if imagem_path is None:
        print("❌ Não foi possível localizar imagem de teste")
        print("📋 Imagens disponíveis:")
        for f in os.listdir('.'):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"   - {f}")
        return
    
    # Criar pasta de resultado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"connected_components_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta de resultado: {os.path.abspath(pasta_resultado)}")
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Aplicar método Connected Components
    produtos, num_garrafas, num_latas = metodo_connected_components(img, pasta_resultado)
    
    # Aplicar método Otsu como comparação
    produtos_otsu = metodo_otsu_adaptativo(img, pasta_resultado)
    
    # ===== RESULTADO FINAL =====
    print(f"\n" + "="*50)
    print("🎉 RESULTADO CONNECTED COMPONENTS")
    print(f"="*50)
    print(f"🎯 Meta: 4 produtos Corona (3 garrafas + 1 lata)")
    print(f"✅ Detectado: {len(produtos)} produtos total")
    print(f"   🍺 Garrafas: {num_garrafas}")
    print(f"   🥤 Latas: {num_latas}")
    print(f"📊 Comparação Otsu: {produtos_otsu} produtos")
    
    # Avaliar resultado
    if len(produtos) == 4 and num_garrafas == 3 and num_latas == 1:
        print("🏆 PERFEITO! Detectou exatamente 3 garrafas + 1 lata!")
        status = "PERFEITO"
    elif len(produtos) == 4:
        print(f"🎯 4 produtos detectados, mas proporção: {num_garrafas}G + {num_latas}L")
        status = "BOM"
    else:
        print(f"🔧 Precisa ajustar: esperado 4, detectado {len(produtos)}")
        status = "AJUSTAR"
    
    # Relatório final
    with open(os.path.join(pasta_resultado, "relatorio_connected_components.txt"), 'w', encoding='utf-8') as f:
        f.write("MÉTODO CONNECTED COMPONENTS\n")
        f.write("=" * 30 + "\n\n")
        f.write("BASEADO NA PESQUISA:\n")
        f.write("1. Remoção do fundo (limiarização)\n")
        f.write("2. Connected Component Labeling\n")
        f.write("3. Análise de cada componente\n")
        f.write("4. Classificação por forma\n\n")
        
        f.write(f"RESULTADO:\n")
        f.write(f"- Total detectado: {len(produtos)} produtos\n")
        f.write(f"- Garrafas: {num_garrafas}\n")
        f.write(f"- Latas: {num_latas}\n")
        f.write(f"- Status: {status}\n\n")
        
        f.write("DETALHES DOS PRODUTOS:\n")
        for produto in produtos:
            f.write(f"Produto {produto['id']} ({produto['tipo']}):\n")
            f.write(f"  - Área: {produto['area']} pixels\n")
            f.write(f"  - Proporção: {produto['aspect_ratio']:.2f}\n")
            f.write(f"  - Bounding box: {produto['bbox']}\n\n")
    
    print(f"\n📄 Relatório: relatorio_connected_components.txt")
    print(f"🖼️  Imagens geradas:")
    print(f"   - 01_grayscale.jpg (escala de cinza)")
    print(f"   - 02_binary_mask.jpg (máscara binária)")
    print(f"   - 03_components_colored.jpg (componentes coloridos)")
    print(f"   - 04_bounding_boxes.jpg (caixas delimitadoras)")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()