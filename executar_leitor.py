#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXECUTAR LEITOR DE NOMES - Simples e direto
"""

def main():
    print("🔤 EXECUTANDO LEITOR DE NOMES...")
    
    try:
        from leitor_de_nomes import LeitorDeNomes
        
        # Caminho da imagem
        imagem = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
        
        # Criar leitor e processar
        leitor = LeitorDeNomes()
        resultado = leitor.processar_imagem(imagem)
        
        if resultado:
            print("\n🎯 NOMES ENCONTRADOS:")
            for i, res in enumerate(resultado['resultados'], 1):
                nome = res['nome_encontrado']
                conf = res['confianca']
                print(f"   {i}. {nome} ({conf:.0f}%)")
            
            # Abrir resultado
            import os
            if os.path.exists("resultado_leitura_nomes.jpg"):
                os.startfile("resultado_leitura_nomes.jpg")
        
        print("✅ CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()