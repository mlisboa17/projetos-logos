#!/usr/bin/env python3
"""
TESTE SIMPLES - BIBLIOTECA GIT
Debug do formato de retorno da biblioteca
"""

import cv2
from biblioteca_contagem_produtos import DetectorProdutos

def testar_formato_retorno():
    print("🔍 TESTE DEBUG - FORMATO DE RETORNO")
    print("=" * 40)
    
    # Carregar imagem
    img_path = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\ProdutosParaImportar\Marca_Heineken (2).jpeg"
    img = cv2.imread(img_path)
    
    # Inicializar detector
    detector = DetectorProdutos()
    
    # Definir cores Heineken
    cores = {
        'VERDE': {'lower': [35, 30, 30], 'upper': [85, 255, 255]},
        'AZUL': {'lower': [100, 40, 40], 'upper': [130, 255, 255]},
        'BRANCO': {'lower': [0, 0, 160], 'upper': [180, 40, 255]}
    }
    
    detector.definir_cores_produto(cores)
    
    # Detectar produtos
    print("📍 Detectando produtos...")
    resultado = detector.detectar_produtos(img.copy())
    
    print(f"\n📊 RESULTADO BRUTO:")
    print(f"   Tipo: {type(resultado)}")
    print(f"   Tamanho: {len(resultado)}")
    
    if resultado:
        print(f"\n🔍 PRIMEIRO ITEM:")
        primeiro = resultado[0]
        print(f"   Tipo: {type(primeiro)}")
        print(f"   Conteúdo: {primeiro}")
        
        if len(resultado) > 1:
            print(f"\n🔍 SEGUNDO ITEM:")
            segundo = resultado[1]
            print(f"   Tipo: {type(segundo)}")
            print(f"   Conteúdo: {segundo}")
    
    return resultado

if __name__ == "__main__":
    produtos = testar_formato_retorno()