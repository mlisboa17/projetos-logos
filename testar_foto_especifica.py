#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testar detector com foto específica
"""

import os
import sys
import shutil
import cv2
import numpy as np
import django
import pytesseract
import tkinter as tk
from pathlib import Path
from ultralytics import YOLO
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, simpledialog

# Configurar Django para acessar produtos_mae
sys.path.append(os.path.join(os.path.dirname(__file__), 'fuel_prices'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
try:
    django.setup()
    from verifik.models import ProdutoMae
    USAR_PRODUTOS_MAE = True
except:
    USAR_PRODUTOS_MAE = False
    print("⚠️  Não foi possível carregar produtos_mae, usando lista fixa")

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Importar a classe DetectorSimples
from detector_simples import DetectorSimples

def main():
    # Caminho da foto específica
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    # Verificar se arquivo existe
    if not os.path.exists(caminho_foto):
        print(f"❌ Arquivo não encontrado: {caminho_foto}")
        return
    
    print(f"📷 Processando: {caminho_foto}")
    print(f"📁 Arquivo existe: {os.path.getsize(caminho_foto) / 1024:.1f} KB")
    
    # Executar detector
    detector = DetectorSimples(caminho_foto)
    detector.executar()

if __name__ == "__main__":
    main()