#!/usr/bin/env python3
"""
TESTE NOVA IMAGEM - BIBLIOTECA GIT
Testando imagem "NaoseiAm.jpeg" com detector configurável
"""

import cv2
from biblioteca_contagem_produtos import DetectorProdutos

def testar_nova_imagem():
    print("🔍 TESTE NOVA IMAGEM - NaoseiAm.jpeg")
    print("=" * 45)
    
    # Carregar imagem nova
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\NaoseiAm.jpeg"
    img = cv2.imread(img_path)
    
    if img is None:
        print(f"❌ Erro ao carregar: {img_path}")
        return
    
    print(f"📸 Imagem carregada: {img.shape[1]}x{img.shape[0]}")
    
    # Detector
    detector = DetectorProdutos()
    
    # Cores universais para qualquer tipo de produto
    cores_universais = {
        'VERDE': {'lower': [30, 20, 20], 'upper': [90, 255, 255]},       # Verde amplo
        'AZUL': {'lower': [90, 20, 20], 'upper': [140, 255, 255]},      # Azul amplo  
        'VERMELHO1': {'lower': [0, 40, 40], 'upper': [10, 255, 255]},   # Vermelho baixo
        'VERMELHO2': {'lower': [170, 40, 40], 'upper': [180, 255, 255]}, # Vermelho alto
        'AMARELO': {'lower': [15, 40, 40], 'upper': [35, 255, 255]},    # Amarelo/dourado
        'BRANCO': {'lower': [0, 0, 150], 'upper': [180, 40, 255]},      # Branco/cinza claro
        'PRETO': {'lower': [0, 0, 0], 'upper': [180, 255, 80]},         # Preto/cinza escuro
    }
    
    detector.definir_cores_produto(cores_universais)
    
    # TESTE 1: Muito sensível (detectar qualquer coisa)
    print(f"\n🔍 TESTE 1: MUITO SENSÍVEL")
    print("-" * 35)
    
    detector.config['area_minima'] = 1000          # Área muito pequena
    detector.config['distancia_minima'] = 20       # Muito próximos OK
    detector.config['overlap_threshold'] = 0.5     # Sobreposições OK
    
    resultado1 = detector.detectar_produtos(img.copy())
    produtos1, stats1 = resultado1
    print(f"✅ Detectados: {len(produtos1)} produtos")
    if produtos1:
        print(f"    📊 {stats1['por_tipo']}")
        print(f"    🎯 Confiança: {float(stats1['confianca_media']):.2f}")
    
    # TESTE 2: Sensível moderado
    print(f"\n🔍 TESTE 2: SENSÍVEL MODERADO")
    print("-" * 35)
    
    detector.config['area_minima'] = 3000          
    detector.config['distancia_minima'] = 50       
    detector.config['overlap_threshold'] = 0.3     
    
    resultado2 = detector.detectar_produtos(img.copy())
    produtos2, stats2 = resultado2
    print(f"✅ Detectados: {len(produtos2)} produtos")
    if produtos2:
        print(f"    📊 {stats2['por_tipo']}")
        print(f"    🎯 Confiança: {float(stats2['confianca_media']):.2f}")
    
    # TESTE 3: Padrão
    print(f"\n🔍 TESTE 3: PADRÃO")
    print("-" * 25)
    
    detector.config['area_minima'] = 8000          
    detector.config['distancia_minima'] = 100      
    detector.config['overlap_threshold'] = 0.3     
    
    resultado3 = detector.detectar_produtos(img.copy())
    produtos3, stats3 = resultado3
    print(f"✅ Detectados: {len(produtos3)} produtos")
    if produtos3:
        print(f"    📊 {stats3['por_tipo']}")
        print(f"    🎯 Confiança: {float(stats3['confianca_media']):.2f}")
    
    # Escolher melhor resultado
    resultados = [
        (len(produtos1), "Muito Sensível", produtos1, stats1),
        (len(produtos2), "Sensível Moderado", produtos2, stats2),
        (len(produtos3), "Padrão", produtos3, stats3)
    ]
    
    # Filtrar resultados válidos
    resultados_validos = [(qtd, config, prods, stats) for qtd, config, prods, stats in resultados if qtd > 0]
    
    if not resultados_validos:
        print(f"\n❌ NENHUM PRODUTO DETECTADO")
        print(f"   A imagem pode não conter produtos de bebida")
        print(f"   Ou as cores não correspondem aos padrões esperados")
        return []
    
    # Escolher resultado com mais produtos (mas não excessivo)
    melhor_qtd, melhor_config, melhor_produtos, melhor_stats = max(resultados_validos, key=lambda x: x[0])
    
    print(f"\n🏆 MELHOR RESULTADO: {melhor_config}")
    print(f"    📦 {melhor_qtd} produtos detectados")
    print(f"    🎯 Confiança: {float(melhor_stats['confianca_media']):.2f}")
    
    # Detalhar produtos encontrados
    if melhor_produtos:
        print(f"\n📋 PRODUTOS DETECTADOS:")
        for i, produto in enumerate(melhor_produtos, 1):
            tipo = produto.get('tipo', 'PRODUTO')
            x, y, w, h = produto['bbox']
            area = produto.get('area', w * h)
            confianca = produto.get('confianca', 0)
            cor = produto.get('cor_dominante', 'N/A')
            
            print(f"  {i}. {tipo} ({cor})")
            print(f"     📍 Posição: ({x}, {y}) - {w}x{h}")
            print(f"     📊 Área: {area:,.0f} | Conf: {confianca:.2f}")
    
    # Salvar resultado visual
    print(f"\n💾 Salvando resultado...")
    img_resultado = img.copy()
    
    cores_desenho = {
        'GARRAFA': (0, 255, 0),    # Verde
        'LATA': (255, 0, 0),       # Azul
        'OUTRO': (0, 255, 255),    # Amarelo
        'PRODUTO': (255, 255, 0)   # Ciano
    }
    
    for i, produto in enumerate(melhor_produtos):
        x, y, w, h = produto['bbox']
        tipo = produto.get('tipo', 'PRODUTO')
        cor = cores_desenho.get(tipo, (128, 128, 128))
        
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 4)
        
        label = f"{i+1}.{tipo}"
        cv2.putText(img_resultado, label, (x, y-15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor, 2)
    
    nome_resultado = f"NaoseiAm_biblioteca_{melhor_qtd}produtos.jpg"
    cv2.imwrite(nome_resultado, img_resultado)
    print(f"    ✅ Salvo: {nome_resultado}")
    
    print(f"\n🎯 ANÁLISE DA NOVA IMAGEM:")
    print(f"   Produtos encontrados: {melhor_qtd}")
    print(f"   Configuração: {melhor_config}")
    print(f"   Qualidade: {float(melhor_stats['confianca_media']):.2f}")
    
    return melhor_produtos

if __name__ == "__main__":
    try:
        produtos = testar_nova_imagem()
        if produtos:
            print(f"\n✅ Sucesso! {len(produtos)} produtos detectados.")
        else:
            print(f"\n⚠️ Nenhum produto detectado nesta imagem.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()