#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script avançado para diagnóstico de detecção
Testa múltiplas configurações para encontrar melhor resultado
"""

import os
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
import cv2
import numpy as np


def testar_multiplas_configuracoes(caminho_foto, caminho_modelo=None):
    """
    Testa foto com diferentes configurações para maximizar detecções
    """
    
    print("=" * 80)
    print("🔬 DIAGNÓSTICO AVANÇADO DE DETECÇÃO")
    print("=" * 80)
    print()
    
    # Verificar foto
    if not os.path.exists(caminho_foto):
        print(f"❌ Erro: Foto não encontrada: {caminho_foto}")
        return
    
    print(f"📷 Foto: {caminho_foto}")
    img = Image.open(caminho_foto)
    print(f"📐 Dimensões: {img.size[0]}x{img.size[1]} pixels")
    print(f"🎨 Modo: {img.mode}")
    print()
    
    # Encontrar modelo
    if caminho_modelo is None:
        localizacoes = [
            r"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\runs\treino_continuado\weights\best.pt",
            r"verifik\runs\treino_continuado\weights\best.pt",
            r"fuel_prices\runs\detect\heineken_330ml\weights\best.pt",
        ]
        
        for loc in localizacoes:
            if os.path.exists(loc):
                caminho_modelo = loc
                break
    
    if caminho_modelo is None:
        print("❌ Modelo não encontrado!")
        return
    
    print(f"🤖 Modelo: {caminho_modelo}")
    model = YOLO(caminho_modelo)
    print(f"✓ Classes disponíveis: {len(model.names)}")
    print()
    
    # Configurações para testar
    configuracoes = [
        {"nome": "Padrão", "conf": 0.25, "iou": 0.7, "max_det": 300},
        {"nome": "Baixa confiança", "conf": 0.10, "iou": 0.7, "max_det": 300},
        {"nome": "Confiança muito baixa", "conf": 0.05, "iou": 0.7, "max_det": 300},
        {"nome": "IoU relaxado", "conf": 0.25, "iou": 0.5, "max_det": 300},
        {"nome": "IoU muito relaxado", "conf": 0.25, "iou": 0.3, "max_det": 300},
        {"nome": "Máx detecções", "conf": 0.25, "iou": 0.7, "max_det": 1000},
        {"nome": "Agressivo", "conf": 0.05, "iou": 0.3, "max_det": 1000},
    ]
    
    melhor_resultado = None
    melhor_qtd = 0
    
    print("🔍 TESTANDO CONFIGURAÇÕES:")
    print("-" * 80)
    
    resultados_completos = []
    
    for i, config in enumerate(configuracoes, 1):
        print(f"\n{i}. {config['nome']}:")
        print(f"   Conf: {config['conf']}, IoU: {config['iou']}, Max_det: {config['max_det']}")
        
        try:
            results = model.predict(
                source=caminho_foto,
                conf=config['conf'],
                iou=config['iou'],
                max_det=config['max_det'],
                save=False,
                verbose=False
            )
            
            result = results[0]
            boxes = result.boxes
            
            # Contar por classe
            deteccoes = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                nome_classe = model.names[cls_id]
                
                if nome_classe not in deteccoes:
                    deteccoes[nome_classe] = []
                deteccoes[nome_classe].append(conf)
            
            qtd_total = len(boxes)
            qtd_classes = len(deteccoes)
            
            print(f"   ✓ {qtd_total} detecções, {qtd_classes} produtos diferentes")
            
            for produto, confidencias in sorted(deteccoes.items()):
                conf_max = max(confidencias)
                print(f"     • {produto}: {len(confidencias)}x (máx: {conf_max*100:.1f}%)")
            
            resultados_completos.append({
                'config': config,
                'qtd': qtd_total,
                'deteccoes': deteccoes,
                'result': result
            })
            
            if qtd_total > melhor_qtd:
                melhor_qtd = qtd_total
                melhor_resultado = {
                    'config': config,
                    'result': result,
                    'deteccoes': deteccoes
                }
        
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print()
    print("=" * 80)
    print("🏆 MELHOR RESULTADO:")
    print("=" * 80)
    
    if melhor_resultado:
        config = melhor_resultado['config']
        deteccoes = melhor_resultado['deteccoes']
        
        print(f"Configuração: {config['nome']}")
        print(f"  └─ Conf: {config['conf']}, IoU: {config['iou']}, Max_det: {config['max_det']}")
        print()
        print(f"Total: {melhor_qtd} detecções")
        print()
        
        for produto, confidencias in sorted(deteccoes.items()):
            qtd = len(confidencias)
            conf_media = sum(confidencias) / qtd
            conf_max = max(confidencias)
            conf_min = min(confidencias)
            
            print(f"  📦 {produto}:")
            print(f"     └─ Quantidade: {qtd}")
            print(f"     └─ Confiança: {conf_min*100:.1f}% ~ {conf_max*100:.1f}% (média: {conf_media*100:.1f}%)")
        
        # Salvar imagem com melhor resultado
        img_resultado = melhor_resultado['result'].plot()
        output_path = Path("resultados_deteccao") / "melhor_resultado.jpg"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(output_path), img_resultado)
        print()
        print(f"💾 Imagem salva: {output_path}")
        
        # Também salvar todas as versões
        print()
        print("💾 Salvando todas as variações...")
        for i, res in enumerate(resultados_completos, 1):
            img_var = res['result'].plot()
            var_path = Path("resultados_deteccao") / f"config_{i}_{res['config']['nome'].replace(' ', '_')}.jpg"
            cv2.imwrite(str(var_path), img_var)
            print(f"   {i}. {var_path.name} ({res['qtd']} detecções)")
    
    print()
    print("=" * 80)
    print("💡 ANÁLISE E RECOMENDAÇÕES:")
    print("=" * 80)
    
    if melhor_qtd < 3:
        print()
        print("⚠️  Detectou menos de 3 produtos. Possíveis causas:")
        print()
        print("1. PRODUTOS NÃO TREINADOS:")
        print("   Produtos na foto podem não estar no dataset de treino")
        print(f"   Classes treinadas: {', '.join(model.names.values())}")
        print()
        print("2. OCLUSÃO/SOBREPOSIÇÃO:")
        print("   Produtos muito juntos ou sobrepostos podem ser difíceis de detectar")
        print("   Solução: Tire foto com produtos mais separados")
        print()
        print("3. QUALIDADE DA FOTO:")
        print("   - Foto muito escura ou clara")
        print("   - Produtos muito pequenos na imagem")
        print("   - Ângulo muito diferente das fotos de treino")
        print()
        print("4. BBOX GENÉRICA NO TREINO:")
        print("   O treino usou bbox genérica (0.5, 0.5, 0.9, 0.9)")
        print("   Isso pode afetar a precisão de localização")
        print()
        print("🔧 SOLUÇÕES:")
        print("   a) Retomar foto com melhor iluminação e produtos separados")
        print("   b) Treinar com bboxes reais usando a interface de anotação")
        print("   c) Adicionar mais fotos dos produtos não detectados")
    
    elif melhor_qtd == 3:
        print()
        print("✅ Detectou 3 produtos corretamente!")
        print()
        config_usada = melhor_resultado['config']
        if config_usada['nome'] != "Padrão":
            print(f"💡 Use esta configuração na interface:")
            print(f"   Confiança: {config_usada['conf']}")
            print(f"   IoU: {config_usada['iou']}")
    
    else:
        print()
        print(f"⚠️  Detectou {melhor_qtd} produtos (mais de 3 esperados)")
        print()
        print("Possíveis causas:")
        print("  - Detecções duplicadas do mesmo produto")
        print("  - Reflexos ou embalagens no fundo sendo detectados")
        print()
        print("Solução: Aumente a confiança mínima ou IoU")
    
    print()
    print("=" * 80)


def main():
    import argparse
    import tkinter as tk
    from tkinter import filedialog
    
    parser = argparse.ArgumentParser(description='Diagnóstico avançado de detecção')
    parser.add_argument('foto', nargs='?', help='Caminho para a foto de teste (opcional)')
    parser.add_argument('--modelo', '-m', help='Caminho para o modelo .pt (opcional)')
    
    args = parser.parse_args()
    
    # Se não passou foto por argumento, abrir dialog
    caminho_foto = args.foto
    
    if caminho_foto is None:
        print("📷 Selecione a foto para análise...")
        root = tk.Tk()
        root.withdraw()  # Esconder janela principal
        
        caminho_foto = filedialog.askopenfilename(
            title="Selecionar Foto para Diagnóstico",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        root.destroy()
        
        if not caminho_foto:
            print("❌ Nenhuma foto selecionada. Encerrando.")
            return
    
    testar_multiplas_configuracoes(
        caminho_foto=caminho_foto,
        caminho_modelo=args.modelo
    )


if __name__ == "__main__":
    main()
