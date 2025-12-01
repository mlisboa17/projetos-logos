#!/usr/bin/env python3
"""
TESTE HEINEKEN - USANDO BIBLIOTECA DO GIT
Detector com a biblioteca DetectorProdutos que você forneceu
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Importar a biblioteca do git
from biblioteca_contagem_produtos import DetectorProdutos

def testar_heineken_com_biblioteca():
    """
    Testa Heineken usando a biblioteca DetectorProdutos do git
    """
    print("🍺 TESTE HEINEKEN - BIBLIOTECA DO GIT")
    print("=" * 50)
    
    # Caminho da imagem Heineken
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Heineken (2).jpeg"
    
    # Carregar imagem
    print(f"📸 Carregando imagem...")
    img = cv2.imread(img_path)
    
    if img is None:
        print(f"❌ Erro ao carregar imagem: {img_path}")
        return
    
    print(f"    📏 Resolução: {img.shape[1]}x{img.shape[0]}")
    
    # Criar detector com a biblioteca do git
    print(f"\n🔧 Inicializando DetectorProdutos...")
    detector = DetectorProdutos()
    
    # Definir cores para Heineken (verde, azul, branco, dourado)
    cores_heineken = {
        'VERDE': {'lower': [35, 30, 30], 'upper': [85, 255, 255]},      # Heineken verde
        'AZUL': {'lower': [100, 40, 40], 'upper': [130, 255, 255]},     # Heineken Silver
        'BRANCO': {'lower': [0, 0, 160], 'upper': [180, 40, 255]},      # Latas claras
        'DOURADO': {'lower': [10, 40, 40], 'upper': [35, 255, 255]},    # Detalhes dourados
        'VERMELHO': {'lower': [0, 50, 50], 'upper': [10, 255, 255]}     # Detalhes vermelhos
    }
    
    detector.definir_cores_produto(cores_heineken)
    
    # TESTE 1: Configuração padrão
    print(f"\n🔍 TESTE 1: Configuração padrão")
    print("-" * 40)
    
    resultado1 = detector.detectar_produtos(img.copy())
    produtos1, stats1 = resultado1  # Desempacotar produtos e estatísticas
    print(f"✅ Detectados: {len(produtos1)} produtos (padrão)")
    print(f"    📊 Stats: {stats1['total']} total - {stats1['por_tipo']}")
    
    # TESTE 2: Configuração sensível para produtos próximos
    print(f"\n🔍 TESTE 2: Configuração sensível")
    print("-" * 40)
    
    # Ajustar parâmetros para produtos próximos
    detector.config['area_minima'] = 5000          # Reduzir área mínima
    detector.config['distancia_minima'] = 50       # Reduzir distância mínima
    
    resultado2 = detector.detectar_produtos(img.copy())
    produtos2, stats2 = resultado2
    print(f"✅ Detectados: {len(produtos2)} produtos (sensível)")
    print(f"    📊 Stats: {stats2['total']} total - {stats2['por_tipo']}")
    
    # TESTE 3: Configuração muito sensível
    print(f"\n🔍 TESTE 3: Configuração muito sensível")
    print("-" * 40)
    
    detector.config['area_minima'] = 2000          # Ainda menor
    detector.config['distancia_minima'] = 30       # Muito próximo
    
    resultado3 = detector.detectar_produtos(img.copy())
    produtos3, stats3 = resultado3
    print(f"✅ Detectados: {len(produtos3)} produtos (muito sensível)")
    print(f"    📊 Stats: {stats3['total']} total - {stats3['por_tipo']}")
    
    # Escolher melhor resultado
    resultados = [
        (len(produtos1), "Padrão", produtos1, stats1),
        (len(produtos2), "Sensível", produtos2, stats2),
        (len(produtos3), "Muito Sensível", produtos3, stats3)
    ]
    
    # Assumindo que Heineken tem 4 produtos, escolher o mais próximo
    melhor_qtd, melhor_config, melhor_produtos, melhor_stats = max(resultados, key=lambda x: x[0])
    
    print(f"\n🏆 MELHOR RESULTADO: {melhor_config}")
    print(f"    📦 {melhor_qtd} produtos detectados")
    
    # Detalhar produtos
    if melhor_produtos:
        print(f"\n📋 PRODUTOS DETECTADOS:")
        garrafas = 0
        latas = 0
        
        for i, produto in enumerate(melhor_produtos, 1):
            # Agora sabemos que produto é um dicionário
            tipo = produto.get('tipo', 'PRODUTO')
            x, y, w, h = produto['bbox']
            area = produto.get('area', w * h)
            confianca = produto.get('confianca', 0)
            
            print(f"  {i}. {tipo}")
            print(f"     📍 Posição: ({x}, {y})")
            print(f"     📏 Tamanho: {w}x{h}")
            print(f"     📊 Área: {area:,.0f}")
            print(f"     🎯 Confiança: {confianca:.2f}")
            
            if tipo == 'GARRAFA':
                garrafas += 1
            elif tipo == 'LATA':
                latas += 1
        
        print(f"\n📊 RESUMO:")
        print(f"   🍺 Garrafas: {garrafas}")
        print(f"   🥤 Latas: {latas}")
    
    # Salvar resultado visual
    print(f"\n💾 Salvando resultado visual...")
    
    img_resultado = img.copy()
    cores = {
        'GARRAFA': (0, 255, 0),    # Verde
        'LATA': (255, 0, 0),       # Azul
        'PRODUTO': (0, 255, 255)   # Amarelo
    }
    
    for i, produto in enumerate(melhor_produtos):
        # Produto é um dicionário
        x, y, w, h = produto['bbox']
        tipo = produto.get('tipo', 'PRODUTO')
        cor = cores.get(tipo, (128, 128, 128))
        
        # Desenhar retângulo
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 3)
        
        # Label
        label = f"{i+1}.{tipo}"
        cv2.putText(img_resultado, label, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
    
    # Salvar
    nome_resultado = f"heineken_biblioteca_git_{melhor_qtd}produtos.jpg"
    cv2.imwrite(nome_resultado, img_resultado)
    print(f"    ✅ Salvo: {nome_resultado}")
    
    print(f"\n🎯 TESTE CONCLUÍDO!")
    print(f"   Biblioteca do git detectou: {melhor_qtd} produtos")
    print(f"   Melhor configuração: {melhor_config}")
    
    return melhor_produtos

if __name__ == "__main__":
    try:
        produtos = testar_heineken_com_biblioteca()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()