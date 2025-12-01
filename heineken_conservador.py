#!/usr/bin/env python3
"""
HEINEKEN CONFIGURAÇÃO CONSERVADORA
Detectar apenas produtos claros e bem definidos
"""

import cv2
from biblioteca_contagem_produtos import DetectorProdutos

def testar_heineken_conservador():
    print("🍺 HEINEKEN - CONFIGURAÇÃO CONSERVADORA")
    print("=" * 45)
    
    # Carregar imagem
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Heineken (2).jpeg"
    img = cv2.imread(img_path)
    
    print(f"📸 Imagem: {img.shape[1]}x{img.shape[0]}")
    
    # Detector
    detector = DetectorProdutos()
    
    # Cores mais específicas para Heineken (apenas tons principais)
    cores_heineken = {
        'VERDE_HEINEKEN': {'lower': [45, 80, 80], 'upper': [75, 255, 255]},    # Verde bem específico
        'BRANCO_LATA': {'lower': [0, 0, 200], 'upper': [180, 20, 255]},        # Branco bem puro
    }
    
    detector.definir_cores_produto(cores_heineken)
    
    # CONFIGURAÇÃO MUITO CONSERVADORA
    print(f"\n🔍 CONFIGURAÇÃO CONSERVADORA")
    print("-" * 40)
    
    detector.config['area_minima'] = 15000         # Área bem grande (produtos principais)
    detector.config['distancia_minima'] = 150      # Distância bem grande
    detector.config['overlap_threshold'] = 0.15    # Quase zero sobreposição
    detector.config['area_maxima_pct'] = 0.25      # Máximo 25% da imagem
    
    resultado = detector.detectar_produtos(img.copy())
    produtos, stats = resultado
    
    # Filtrar apenas produtos com alta confiança E boa proporção
    produtos_filtrados = []
    for produto in produtos:
        confianca = produto.get('confianca', 0)
        area = produto.get('area', 0)
        x, y, w, h = produto['bbox']
        aspect_ratio = w / h if h > 0 else 0
        
        # Critérios rigorosos
        if (confianca > 0.7 and                    # Alta confiança
            area > 20000 and                       # Área significativa
            0.2 < aspect_ratio < 3.0):             # Proporção razoável
            produtos_filtrados.append(produto)
    
    print(f"✅ Detectados: {len(produtos)} produtos (total)")
    print(f"✅ Filtrados: {len(produtos_filtrados)} produtos (alta qualidade)")
    print(f"    📊 Stats originais: {stats['por_tipo']}")
    print(f"    🎯 Confiança média: {float(stats['confianca_media']):.2f}")
    
    # Contar tipos filtrados
    tipos_filtrados = {}
    for p in produtos_filtrados:
        tipo = p.get('tipo', 'PRODUTO')
        tipos_filtrados[tipo] = tipos_filtrados.get(tipo, 0) + 1
    
    print(f"    📊 Tipos filtrados: {tipos_filtrados}")
    
    # Se ainda tem muitos, aplicar filtro por tamanho
    if len(produtos_filtrados) > 4:
        print(f"\n🔧 APLICANDO FILTRO ADICIONAL POR TAMANHO...")
        # Pegar apenas os 4 maiores produtos
        produtos_filtrados.sort(key=lambda x: x.get('area', 0), reverse=True)
        produtos_filtrados = produtos_filtrados[:4]
        print(f"✅ Mantendo apenas os 4 maiores produtos")
    
    print(f"\n🏆 RESULTADO FINAL CONSERVADOR")
    print(f"    📦 {len(produtos_filtrados)} produtos detectados")
    
    # Detalhar produtos finais
    if produtos_filtrados:
        print(f"\n📋 PRODUTOS FINAIS (CONSERVADOR):")
        for i, produto in enumerate(produtos_filtrados, 1):
            tipo = produto.get('tipo', 'PRODUTO')
            x, y, w, h = produto['bbox']
            area = produto.get('area', w * h)
            confianca = produto.get('confianca', 0)
            cor = produto.get('cor_dominante', 'N/A')
            aspect_ratio = w / h if h > 0 else 0
            
            print(f"  {i}. {tipo} ({cor})")
            print(f"     📍 Centro: ({x + w//2}, {y + h//2})")
            print(f"     📏 {w}x{h} (ratio: {aspect_ratio:.2f})")
            print(f"     📊 Área: {area:,.0f} | Conf: {confianca:.2f}")
    
    # Salvar resultado
    print(f"\n💾 Salvando resultado conservador...")
    img_resultado = img.copy()
    
    cores_desenho = {
        'GARRAFA': (0, 255, 0),      # Verde brilhante
        'LATA': (0, 0, 255),         # Vermelho  
        'OUTRO': (255, 255, 0)       # Ciano
    }
    
    for i, produto in enumerate(produtos_filtrados):
        x, y, w, h = produto['bbox']
        tipo = produto.get('tipo', 'PRODUTO')
        cor = cores_desenho.get(tipo, (128, 128, 128))
        confianca = produto.get('confianca', 0)
        
        # Retângulo bem visível
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 5)
        
        # Label detalhado
        label = f"{i+1}.{tipo}"
        cv2.putText(img_resultado, label, (x, y-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, cor, 3)
        
        # Confiança
        conf_label = f"{confianca:.2f}"
        cv2.putText(img_resultado, conf_label, (x, y+h+25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
        
        # Centro
        centro_x = x + w // 2
        centro_y = y + h // 2
        cv2.circle(img_resultado, (centro_x, centro_y), 8, cor, -1)
    
    nome_resultado = f"heineken_conservador_{len(produtos_filtrados)}produtos.jpg"
    cv2.imwrite(nome_resultado, img_resultado)
    print(f"    ✅ Salvo: {nome_resultado}")
    
    print(f"\n⚙️ PARÂMETROS FINAIS CONSERVADORES:")
    print(f"   - area_minima: {detector.config['area_minima']}")
    print(f"   - distancia_minima: {detector.config['distancia_minima']}")
    print(f"   - confianca_minima: 0.7")
    print(f"   - apenas_4_maiores: {len(produtos_filtrados) <= 4}")
    
    print(f"\n🎯 ANÁLISE: {len(produtos_filtrados)} produtos Heineken detectados")
    print(f"   Configuração muito conservadora aplicada!")
    
    return produtos_filtrados

if __name__ == "__main__":
    try:
        produtos = testar_heineken_conservador()
        print(f"\n✅ Sucesso! {len(produtos)} produtos finais.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()