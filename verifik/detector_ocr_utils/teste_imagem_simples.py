#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste simples da imagem
"""

import os
import cv2
from pathlib import Path

def main():
    # Caminho da foto específica
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    print(f"📷 Testando: {caminho_foto}")
    
    # Verificar se arquivo existe
    if not os.path.exists(caminho_foto):
        print(f"❌ Arquivo não encontrado!")
        return
    
    print(f"✅ Arquivo encontrado: {os.path.getsize(caminho_foto) / 1024:.1f} KB")
    
    # Tentar carregar imagem
    try:
        img = cv2.imread(caminho_foto)
        if img is None:
            print("❌ Erro ao carregar imagem com OpenCV")
            return
        
        altura, largura = img.shape[:2]
        print(f"✅ Imagem carregada: {largura}x{altura} pixels")
        
        # Mostrar imagem por 3 segundos
        print("📺 Mostrando imagem por 3 segundos...")
        cv2.imshow("Teste da Imagem", img)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()
        
        print("✅ Teste da imagem concluído!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()