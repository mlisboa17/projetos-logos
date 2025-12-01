#!/usr/bin/env python3
"""
DETECTOR PRECISO - SEM FALSOS POSITIVOS
Configuração para detectar apenas produtos reais
"""

import cv2
from biblioteca_contagem_produtos import DetectorProdutos

def testar_precisao_maxima():
    print("🎯 DETECTOR PRECISO - SEM FALSOS POSITIVOS")
    print("=" * 50)
    
    # Carregar imagem
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\NaoseiAm.jpeg"
    img = cv2.imread(img_path)
    
    print(f"📸 Imagem: {img.shape[1]}x{img.shape[0]}")
    
    # Detector com configuração muito restritiva
    detector = DetectorProdutos()
    
    # Cores muito específicas (reduzir falsos positivos)
    cores_especificas = {
        'VERDE_PRODUTO': {'lower': [40, 80, 100], 'upper': [75, 255, 255]},    # Verde bem definido
        'AZUL_PRODUTO': {'lower': [100, 80, 100], 'upper': [130, 255, 255]},   # Azul bem definido
        'BRANCO_PRODUTO': {'lower': [0, 0, 200], 'upper': [180, 25, 255]},     # Branco muito puro
    }
    
    detector.definir_cores_produto(cores_especificas)
    
    # Configuração ULTRA RESTRITIVA
    detector.config['area_minima'] = 20000         # Área muito grande
    detector.config['distancia_minima'] = 200      # Muito separados
    detector.config['overlap_threshold'] = 0.1     # Quase zero sobreposição
    detector.config['area_maxima_pct'] = 0.2       # Máximo 20% da imagem
    
    print(f"\n🔧 CONFIGURAÇÃO ULTRA RESTRITIVA:")
    print(f"   - Área mínima: {detector.config['area_minima']:,}")
    print(f"   - Distância mínima: {detector.config['distancia_minima']}")
    print(f"   - Apenas cores bem definidas")
    
    resultado = detector.detectar_produtos(img.copy())
    produtos, stats = resultado
    
    # Filtrar com critérios ainda mais rigorosos
    produtos_validos = []
    for produto in produtos:
        confianca = produto.get('confianca', 0)
        area = produto.get('area', 0)
        x, y, w, h = produto['bbox']
        aspect_ratio = w / h if h > 0 else 0
        
        # Critérios MUITO rigorosos
        if (confianca > 0.8 and                    # Confiança muito alta
            area > 25000 and                       # Área bem grande
            0.3 < aspect_ratio < 2.5 and          # Proporção de produto
            w > 50 and h > 50):                   # Tamanho mínimo
            produtos_validos.append(produto)
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Candidatos detectados: {len(produtos)}")
    print(f"   Produtos válidos: {len(produtos_validos)}")
    
    if len(produtos_validos) == 0:
        print(f"\n⚠️ NENHUM PRODUTO VÁLIDO ENCONTRADO")
        print(f"   Tentando configuração menos restritiva...")
        
        # Configuração um pouco menos restritiva
        detector.config['area_minima'] = 15000
        detector.config['distancia_minima'] = 150
        
        resultado2 = detector.detectar_produtos(img.copy())
        produtos2, stats2 = resultado2
        
        produtos_validos = []
        for produto in produtos2:
            confianca = produto.get('confianca', 0)
            area = produto.get('area', 0)
            
            if confianca > 0.7 and area > 18000:
                produtos_validos.append(produto)
        
        print(f"   Segunda tentativa: {len(produtos_validos)} produtos")
    
    if produtos_validos:
        # Se ainda tem muitos, pegar apenas os melhores
        if len(produtos_validos) > 4:
            produtos_validos.sort(key=lambda x: (x.get('confianca', 0) + x.get('area', 0)/50000), reverse=True)
            produtos_validos = produtos_validos[:3]  # Máximo 3 produtos
            print(f"   Limitado aos 3 melhores produtos")
        
        print(f"\n✅ PRODUTOS FINAIS: {len(produtos_validos)}")
        
        for i, produto in enumerate(produtos_validos, 1):
            tipo = produto.get('tipo', 'PRODUTO')
            x, y, w, h = produto['bbox']
            area = produto.get('area', w * h)
            confianca = produto.get('confianca', 0)
            cor = produto.get('cor_dominante', 'N/A')
            
            print(f"  {i}. {tipo} ({cor})")
            print(f"     📍 Centro: ({x + w//2}, {y + h//2})")
            print(f"     📏 {w}x{h} pixels")
            print(f"     📊 Área: {area:,.0f} | Conf: {confianca:.2f}")
        
        # Salvar resultado
        img_resultado = img.copy()
        
        cores_desenho = {
            'GARRAFA': (0, 255, 0),
            'LATA': (0, 0, 255),
            'PRODUTO': (255, 255, 0)
        }
        
        for i, produto in enumerate(produtos_validos):
            x, y, w, h = produto['bbox']
            tipo = produto.get('tipo', 'PRODUTO')
            cor = cores_desenho.get(tipo, (128, 128, 128))
            
            # Retângulo bem visível
            cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 6)
            
            # Label grande
            label = f"{i+1}.{tipo}"
            cv2.putText(img_resultado, label, (x, y-25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, cor, 3)
        
        nome_arquivo = f"NaoseiAm_preciso_{len(produtos_validos)}produtos.jpg"
        cv2.imwrite(nome_arquivo, img_resultado)
        print(f"\n💾 Salvo: {nome_arquivo}")
    else:
        print(f"\n❌ NENHUM PRODUTO REAL DETECTADO")
        print(f"   A imagem pode não conter produtos de bebida claros")
    
    print(f"\n🎯 RESULTADO FINAL: {len(produtos_validos)} produtos reais")
    return produtos_validos

if __name__ == "__main__":
    produtos = testar_precisao_maxima()