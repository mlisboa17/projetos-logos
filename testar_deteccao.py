#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar detecção de produtos em fotos
"""

import os
from pathlib import Path
from ultralytics import YOLO
from PIL import Image

def testar_foto(caminho_foto, caminho_modelo=None, confianca=0.25, salvar=True):
    """
    Testa o modelo YOLO em uma foto
    
    Args:
        caminho_foto: Caminho para a imagem de teste
        caminho_modelo: Caminho para o modelo .pt (opcional)
        confianca: Threshold de confiança (0-1)
        salvar: Se deve salvar imagem com detecções
    """
    
    print("=" * 70)
    print("🔍 TESTE DE DETECÇÃO DE PRODUTOS")
    print("=" * 70)
    print()
    
    # Verificar se foto existe
    if not os.path.exists(caminho_foto):
        print(f"❌ Erro: Foto não encontrada: {caminho_foto}")
        return None
    
    print(f"📷 Foto: {caminho_foto}")
    
    # Carregar imagem para ver dimensões
    try:
        img = Image.open(caminho_foto)
        print(f"📐 Dimensões: {img.size[0]}x{img.size[1]} pixels")
        print(f"🎨 Modo: {img.mode}")
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível ler metadados da imagem: {e}")
    
    print()
    
    # Encontrar modelo
    if caminho_modelo is None:
        # Procurar em localizações padrão
        localizacoes = [
            r"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\runs\treino_continuado\weights\best.pt",
            r"verifik\runs\treino_continuado\weights\best.pt",
            r"fuel_prices\runs\detect\heineken_330ml\weights\best.pt",
            r"runs\detect\heineken_330ml\weights\best.pt",
        ]
        
        for loc in localizacoes:
            if os.path.exists(loc):
                caminho_modelo = loc
                break
        
        if caminho_modelo is None:
            print("❌ Erro: Modelo não encontrado!")
            print("Localizações procuradas:")
            for loc in localizacoes:
                print(f"  - {loc}")
            return None
    
    print(f"🤖 Modelo: {caminho_modelo}")
    print()
    
    # Carregar modelo
    print("📦 Carregando modelo YOLO...")
    try:
        model = YOLO(caminho_modelo)
        print(f"✓ Modelo carregado com sucesso")
        print(f"  └─ Classes: {len(model.names)}")
        print(f"  └─ Parâmetros: {sum(p.numel() for p in model.model.parameters()):,}")
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        return None
    
    print()
    
    # Fazer predição
    print(f"🔍 Detectando produtos (confiança mínima: {confianca*100}%)...")
    try:
        results = model.predict(
            source=caminho_foto,
            conf=confianca,
            save=salvar,
            save_txt=False,
            save_conf=True,
            project="resultados_deteccao",
            name="teste",
            exist_ok=True,
            verbose=False
        )
    except Exception as e:
        print(f"❌ Erro ao fazer predição: {e}")
        return None
    
    print()
    
    # Analisar resultados
    result = results[0]
    boxes = result.boxes
    
    if len(boxes) == 0:
        print("⚠️  Nenhum produto detectado!")
        print()
        print("💡 Dicas:")
        print("  - Tente reduzir a confiança: --confianca 0.1")
        print("  - Verifique se a foto contém produtos treinados")
        print("  - Certifique-se que os produtos estão visíveis")
        return None
    
    print(f"✅ {len(boxes)} produto(s) detectado(s)!")
    print()
    print("-" * 70)
    
    # Contar detecções por classe
    deteccoes = {}
    
    for i, box in enumerate(boxes):
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        nome_classe = model.names[cls_id]
        xyxy = box.xyxy[0].tolist()
        
        # Contar
        if nome_classe not in deteccoes:
            deteccoes[nome_classe] = []
        deteccoes[nome_classe].append(conf)
        
        # Mostrar detalhes
        print(f"Detecção #{i+1}:")
        print(f"  📦 Produto: {nome_classe}")
        print(f"  ✓ Confiança: {conf*100:.1f}%")
        print(f"  📍 BBox: x1={xyxy[0]:.0f}, y1={xyxy[1]:.0f}, x2={xyxy[2]:.0f}, y2={xyxy[3]:.0f}")
        print()
    
    print("-" * 70)
    print("📊 RESUMO:")
    print()
    
    for produto, confidencias in sorted(deteccoes.items()):
        qtd = len(confidencias)
        conf_media = sum(confidencias) / qtd
        conf_max = max(confidencias)
        conf_min = min(confidencias)
        
        print(f"  {produto}:")
        print(f"    └─ Quantidade: {qtd}")
        print(f"    └─ Confiança média: {conf_media*100:.1f}%")
        print(f"    └─ Confiança min/max: {conf_min*100:.1f}% / {conf_max*100:.1f}%")
        print()
    
    if salvar:
        resultado_path = Path("resultados_deteccao/teste") / Path(caminho_foto).name
        print(f"💾 Imagem com detecções salva em:")
        print(f"   {resultado_path}")
    
    print()
    print("=" * 70)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Testar detecção de produtos em foto')
    parser.add_argument('foto', help='Caminho para a foto de teste')
    parser.add_argument('--modelo', '-m', help='Caminho para o modelo .pt (opcional)')
    parser.add_argument('--confianca', '-c', type=float, default=0.25, 
                       help='Confiança mínima (0-1). Padrão: 0.25')
    parser.add_argument('--nao-salvar', action='store_true',
                       help='Não salvar imagem com detecções')
    
    args = parser.parse_args()
    
    testar_foto(
        caminho_foto=args.foto,
        caminho_modelo=args.modelo,
        confianca=args.confianca,
        salvar=not args.nao_salvar
    )


if __name__ == "__main__":
    main()
