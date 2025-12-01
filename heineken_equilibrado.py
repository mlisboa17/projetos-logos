#!/usr/bin/env python3
"""
HEINEKEN CONFIGURAÇÃO EQUILIBRADA
Ajuste fino para evitar falsos positivos
"""

import cv2
from biblioteca_contagem_produtos import DetectorProdutos

def testar_heineken_equilibrado():
    print("🍺 HEINEKEN - CONFIGURAÇÃO EQUILIBRADA")
    print("=" * 45)
    
    # Carregar imagem
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Heineken (2).jpeg"
    img = cv2.imread(img_path)
    
    print(f"📸 Imagem: {img.shape[1]}x{img.shape[0]}")
    
    # Detector
    detector = DetectorProdutos()
    
    # Cores Heineken mais restritivas
    cores_heineken = {
        'VERDE': {'lower': [40, 50, 50], 'upper': [80, 255, 255]},      # Mais restritivo
        'AZUL': {'lower': [105, 60, 60], 'upper': [125, 255, 255]},     # Mais restritivo
        'BRANCO': {'lower': [0, 0, 180], 'upper': [180, 30, 255]},      # Mais restritivo
    }
    
    detector.definir_cores_produto(cores_heineken)
    
    # TESTE 1: Configuração equilibrada (entre sensível e padrão)
    print(f"\n🔍 TESTE 1: Configuração EQUILIBRADA")
    print("-" * 40)
    
    detector.config['area_minima'] = 6000          # Entre 8000 (padrão) e 2000 (muito sensível)
    detector.config['distancia_minima'] = 80       # Entre 100 (padrão) e 30 (muito sensível)
    detector.config['overlap_threshold'] = 0.4     # Mais restritivo para evitar sobreposições
    
    resultado1 = detector.detectar_produtos(img.copy())
    produtos1, stats1 = resultado1
    print(f"✅ Detectados: {len(produtos1)} produtos")
    print(f"    📊 {stats1['por_tipo']}")
    print(f"    🎯 Confiança média: {stats1['confianca_media']:.2f}")
    
    # TESTE 2: Configuração mais restritiva
    print(f"\n🔍 TESTE 2: Configuração RESTRITIVA")
    print("-" * 40)
    
    detector.config['area_minima'] = 8000          # Área maior
    detector.config['distancia_minima'] = 120      # Distância maior
    detector.config['overlap_threshold'] = 0.2     # Menos tolerante a sobreposições
    
    resultado2 = detector.detectar_produtos(img.copy())
    produtos2, stats2 = resultado2
    print(f"✅ Detectados: {len(produtos2)} produtos")
    print(f"    📊 {stats2['por_tipo']}")
    print(f"    🎯 Confiança média: {stats2['confianca_media']:.2f}")
    
    # TESTE 3: Configuração com confiança alta
    print(f"\n🔍 TESTE 3: Configuração ALTA CONFIANÇA")
    print("-" * 40)
    
    detector.config['area_minima'] = 7000          
    detector.config['distancia_minima'] = 90       
    detector.config['overlap_threshold'] = 0.3     
    
    resultado3 = detector.detectar_produtos(img.copy())
    produtos3, stats3 = resultado3
    
    # Filtrar apenas produtos com confiança alta
    produtos3_filtrados = [p for p in produtos3 if p.get('confianca', 0) > 0.6]
    print(f"✅ Detectados: {len(produtos3)} produtos (total)")
    print(f"✅ Alta confiança: {len(produtos3_filtrados)} produtos (>0.6)")
    print(f"    📊 Tipos totais: {stats3['por_tipo']}")
    print(f"    🎯 Confiança média: {stats3['confianca_media']:.2f}")
    
    # Escolher resultado mais realista (provavelmente 3-4 produtos)
    resultados = [
        (len(produtos1), "Equilibrada", produtos1, stats1),
        (len(produtos2), "Restritiva", produtos2, stats2),
        (len(produtos3_filtrados), "Alta Confiança", produtos3_filtrados, stats3)
    ]
    
    print(f"\n📊 COMPARAÇÃO:")
    for qtd, config, prods, stats in resultados:
        conf_media = stats['confianca_media'] if isinstance(stats['confianca_media'], float) else float(stats['confianca_media'])
        print(f"   🔸 {config}: {qtd} produtos (conf: {conf_media:.2f})")
    
    # Escolher baseado na lógica: nem muito poucos, nem muitos, boa confiança
    if len(produtos3_filtrados) >= 3 and stats3['confianca_media'] > 0.6:
        melhor = (len(produtos3_filtrados), "Alta Confiança", produtos3_filtrados, stats3)
    elif 2 <= len(produtos1) <= 4:
        melhor = (len(produtos1), "Equilibrada", produtos1, stats1)
    else:
        melhor = (len(produtos2), "Restritiva", produtos2, stats2)
    
    melhor_qtd, melhor_config, melhor_produtos, melhor_stats = melhor
    
    print(f"\n🏆 RESULTADO RECOMENDADO: {melhor_config}")
    print(f"    📦 {melhor_qtd} produtos detectados")
    print(f"    🎯 Confiança: {float(melhor_stats['confianca_media']):.2f}")
    
    # Detalhar produtos
    if melhor_produtos:
        print(f"\n📋 PRODUTOS FINAIS:")
        for i, produto in enumerate(melhor_produtos, 1):
            tipo = produto.get('tipo', 'PRODUTO')
            x, y, w, h = produto['bbox']
            area = produto.get('area', w * h)
            confianca = produto.get('confianca', 0)
            cor = produto.get('cor_dominante', 'N/A')
            
            print(f"  {i}. {tipo} ({cor})")
            print(f"     📍 Posição: ({x}, {y}) - {w}x{h}")
            print(f"     📊 Área: {area:,.0f} | Confiança: {confianca:.2f}")
    
    # Salvar resultado
    print(f"\n💾 Salvando resultado equilibrado...")
    img_resultado = img.copy()
    
    cores_desenho = {
        'GARRAFA': (0, 255, 0),    # Verde
        'LATA': (255, 0, 0),       # Azul
        'PRODUTO': (0, 255, 255)   # Amarelo
    }
    
    for i, produto in enumerate(melhor_produtos):
        x, y, w, h = produto['bbox']
        tipo = produto.get('tipo', 'PRODUTO')
        cor = cores_desenho.get(tipo, (128, 128, 128))
        
        # Retângulo mais grosso
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 4)
        
        # Label com confiança
        confianca = produto.get('confianca', 0)
        label = f"{i+1}.{tipo} ({confianca:.2f})"
        cv2.putText(img_resultado, label, (x, y-15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor, 2)
    
    nome_resultado = f"heineken_equilibrado_{melhor_qtd}produtos.jpg"
    cv2.imwrite(nome_resultado, img_resultado)
    print(f"    ✅ Salvo: {nome_resultado}")
    
    print(f"\n🎯 CONFIGURAÇÃO FINAL RECOMENDADA:")
    print(f"   area_minima: {detector.config['area_minima']}")
    print(f"   distancia_minima: {detector.config['distancia_minima']}")
    print(f"   overlap_threshold: {detector.config['overlap_threshold']}")
    
    return melhor_produtos

if __name__ == "__main__":
    try:
        produtos = testar_heineken_equilibrado()
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()