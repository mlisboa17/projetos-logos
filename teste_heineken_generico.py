#!/usr/bin/env python3
"""
TESTE DETECTOR GENÉRICO - HEINEKEN
Teste do detector universal para produtos próximos
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Adicionar pasta do projeto
sys.path.append(str(Path(__file__).parent))

# Importar pipeline completo
from pipeline_zoom_preprocessamento_completo import (
    preprocessamento_completo_avancado,
    detectar_produtos_precisos_genericos,
    aplicar_zoom_duplo_configuravel
)

def testar_detector_heineken():
    """
    Testa detector genérico com imagem Heineken
    """
    print("🍺 TESTE DETECTOR GENÉRICO - HEINEKEN")
    print("=" * 50)
    
    # Carregar imagem Heineken
    caminho_imagem = input("📁 Cole o caminho da imagem Heineken: ").strip().strip('"')
    
    if not Path(caminho_imagem).exists():
        print(f"❌ Arquivo não encontrado: {caminho_imagem}")
        return
    
    # Carregar imagem
    print(f"📸 Carregando: {Path(caminho_imagem).name}")
    img_original = cv2.imread(caminho_imagem)
    
    if img_original is None:
        print("❌ Erro ao carregar imagem")
        return
    
    print(f"    📏 Resolução: {img_original.shape[1]}x{img_original.shape[0]}")
    
    # 1. TESTE DETECÇÃO DIRETA (sem preprocessamento)
    print("\n🔍 TESTE 1: Detecção direta na imagem original")
    print("-" * 40)
    
    produtos_originais = detectar_produtos_precisos_genericos(img_original.copy())
    
    print(f"✅ Detectados {len(produtos_originais)} produtos na imagem original")
    
    # 2. TESTE COM ZOOM SUAVE (para produtos próximos)
    print("\n🔍 TESTE 2: Detecção com zoom suave (1.3x)")
    print("-" * 40)
    
    versoes_zoom = aplicar_zoom_duplo_configuravel(img_original.copy(), zoom_menor=1.3, zoom_maior=1.3)
    img_zoom = versoes_zoom[0] if versoes_zoom else img_original.copy()
    produtos_zoom = detectar_produtos_precisos_genericos(img_zoom)
    
    print(f"✅ Detectados {len(produtos_zoom)} produtos com zoom 1.3x")
    
    # 3. TESTE COM ZOOM MÉDIO
    print("\n🔍 TESTE 3: Detecção com zoom médio (1.8x)")
    print("-" * 40)
    
    versoes_zoom2 = aplicar_zoom_duplo_configuravel(img_original.copy(), zoom_menor=1.8, zoom_maior=1.8)
    img_zoom2 = versoes_zoom2[0] if versoes_zoom2 else img_original.copy()
    produtos_zoom2 = detectar_produtos_precisos_genericos(img_zoom2)
    
    print(f"✅ Detectados {len(produtos_zoom2)} produtos com zoom 1.8x")
    
    # RESULTADO FINAL
    print("\n" + "="*50)
    print("📊 RESUMO DO TESTE HEINEKEN")
    print("="*50)
    print(f"🔸 Original: {len(produtos_originais)} produtos")
    print(f"🔸 Zoom 1.3x: {len(produtos_zoom)} produtos")
    print(f"🔸 Zoom 1.8x: {len(produtos_zoom2)} produtos")
    
    # Escolher melhor resultado
    resultados = [
        (len(produtos_originais), "Original", produtos_originais),
        (len(produtos_zoom), "Zoom 1.3x", produtos_zoom),
        (len(produtos_zoom2), "Zoom 1.8x", produtos_zoom2)
    ]
    
    # Ordenar por quantidade (assumindo que 4 seria o ideal para Heineken)
    melhor_qtd, melhor_config, melhor_produtos = max(resultados)
    
    print(f"\n🏆 MELHOR RESULTADO: {melhor_config}")
    print(f"    📦 {melhor_qtd} produtos detectados")
    
    # Detalhar produtos encontrados
    if melhor_produtos:
        print(f"\n📋 PRODUTOS DETECTADOS ({melhor_config}):")
        for i, produto in enumerate(melhor_produtos, 1):
            tipo = produto['tipo']
            bbox = produto['bbox']
            area = produto['area']
            ratio = produto.get('aspect_ratio', 0)
            
            print(f"  {i}. {tipo}")
            print(f"     📍 Posição: x={bbox[0]}, y={bbox[1]}")
            print(f"     📏 Tamanho: {bbox[2]}x{bbox[3]} (área: {area:,.0f})")
            print(f"     📊 Proporção: {ratio:.2f}")
    
    # Salvar resultado visual
    print(f"\n💾 Salvando resultado visual...")
    
    # Usar a melhor configuração
    if melhor_config == "Original":
        img_resultado = img_original.copy()
    elif melhor_config == "Zoom 1.3x":
        img_resultado = img_zoom.copy()
    else:
        img_resultado = img_zoom2.copy()
    
    # Desenhar retângulos nos produtos detectados
    for i, produto in enumerate(melhor_produtos):
        x, y, w, h = produto['bbox']
        tipo = produto['tipo']
        
        # Cor baseada no tipo
        cores = {
            'GARRAFA': (0, 255, 0),    # Verde
            'LATA': (255, 0, 0),       # Azul
            'PRODUTO': (0, 255, 255)   # Amarelo
        }
        cor = cores.get(tipo, (128, 128, 128))
        
        # Desenhar retângulo
        cv2.rectangle(img_resultado, (x, y), (x+w, y+h), cor, 3)
        
        # Label
        label = f"{i+1}. {tipo}"
        cv2.putText(img_resultado, label, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
    
    # Salvar
    nome_resultado = f"heineken_generico_{melhor_qtd}produtos.jpg"
    cv2.imwrite(nome_resultado, img_resultado)
    print(f"    ✅ Salvo: {nome_resultado}")
    
    print(f"\n🎯 TESTE CONCLUÍDO!")
    print(f"   Detector genérico detectou {melhor_qtd} produtos Heineken")
    print(f"   Melhor configuração: {melhor_config}")

if __name__ == "__main__":
    try:
        testar_detector_heineken()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()