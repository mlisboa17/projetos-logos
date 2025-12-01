#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Executar detector completo com foto específica
"""

import os
import sys
import django
from detector_simples import DetectorSimples

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'fuel_prices'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

def main():
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    print("="*80)
    print("🔍 DETECTOR COMPLETO - ANOTAÇÃO INTERATIVA")
    print("="*80)
    print(f"📷 Processando: {os.path.basename(caminho_foto)}")
    print()
    print("Como funciona:")
    print("1. 🤖 Sistema detecta produtos automaticamente")
    print("2. 📊 Você confirma quantos produtos existem")
    print("3. ✅ Confirma/corrige cada produto detectado")
    print("4. ➕ Adiciona produtos não detectados")
    print("5. 💾 Salva anotações para treinamento")
    print("="*80)
    
    # Executar detector
    detector = DetectorSimples(caminho_foto)
    detector.executar()
    
    print("\n✅ Processo concluído!")
    print("📁 Verifique a pasta 'dataset_corrigido/' para ver os resultados")

if __name__ == "__main__":
    main()