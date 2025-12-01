#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXECUTOR SIMPLES - Sistema de Detecção Organizado
"""

import os
import sys
from detector_organizado import DetectorOrganizado

def main():
    print("🚀 INICIANDO SISTEMA DE DETECÇÃO ORGANIZADO")
    print("="*50)
    
    # Caminho da imagem
    imagem_path = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    # Verificar se arquivo existe
    if not os.path.exists(imagem_path):
        print(f"❌ Arquivo não encontrado: {imagem_path}")
        print("📁 Verifique se o caminho está correto")
        return
    
    print(f"✅ Arquivo encontrado: {os.path.basename(imagem_path)}")
    print(f"📏 Tamanho: {os.path.getsize(imagem_path) / 1024:.1f} KB")
    
    try:
        # Inicializar detector
        print("\n🤖 Inicializando detector...")
        detector = DetectorOrganizado(debug_mode=True)
        
        # Executar pipeline completo
        print("🔄 Executando pipeline de detecção...")
        
        # Etapa 1: Detectar produtos
        img, deteccoes = detector.detectar_produtos(imagem_path)
        
        if not deteccoes:
            print("⚠️  Nenhum produto detectado na imagem")
            return
        
        # Etapa 2: Analisar rótulos  
        detector.analisar_rotulos(img, deteccoes)
        
        # Etapa 3: Gerar resultado
        img_resultado, relatorio = detector.gerar_resultado_final(img, deteccoes)
        
        # Mostrar resumo final
        print(f"\n🎯 RESUMO FINAL:")
        print(f"   📦 Produtos detectados: {relatorio['total_produtos']}")
        
        for marca, qtd in relatorio['marcas_encontradas'].items():
            emoji = "🍺" if marca in ["HEINEKEN", "DEVASSA", "BUDWEISER", "AMSTEL", "STELLA", "BRAHMA"] else "🥤"
            print(f"   {emoji} {marca}: {qtd}")
        
        print(f"\n📁 Arquivos salvos em: {detector.pasta_resultados}")
        
        # Abrir resultado final
        resultado_path = detector.pasta_resultados / "resultado_final.jpg"
        if resultado_path.exists():
            print(f"\n📺 Abrindo resultado: {resultado_path}")
            os.startfile(str(resultado_path))
        
        print("\n✅ DETECÇÃO CONCLUÍDA!")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()