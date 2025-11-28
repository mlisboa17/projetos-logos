#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de detecção iterativa - detecta múltiplos produtos mascarando os já encontrados
"""

import os
from pathlib import Path
from ultralytics import YOLO
from PIL import Image, ImageDraw
import cv2
import numpy as np
from collections import Counter


def extrair_cor_dominante(img_cv, bbox):
    """Extrai a cor dominante de uma região da imagem"""
    x1, y1, x2, y2 = bbox
    regiao = img_cv[y1:y2, x1:x2]
    
    # Converter para RGB
    regiao_rgb = cv2.cvtColor(regiao, cv2.COLOR_BGR2RGB)
    
    # Redimensionar para acelerar processamento
    regiao_small = cv2.resize(regiao_rgb, (50, 50))
    
    # Achatar array de pixels
    pixels = regiao_small.reshape(-1, 3)
    
    # Calcular cor média
    cor_media = pixels.mean(axis=0)
    
    return tuple(cor_media.astype(int))


def identificar_cor(rgb):
    """Identifica a cor predominante"""
    r, g, b = rgb
    
    # Verde (Heineken, Stella)
    if g > r and g > b and g > 100:
        return "verde"
    # Vermelho (Budweiser)
    elif r > g and r > b and r > 80:
        return "vermelho"
    # Azul/Ciano (Amstel, Devassa)
    elif b > r and b > g:
        return "azul"
    # Amarelo/Dourado
    elif r > 150 and g > 150 and b < 100:
        return "amarelo"
    # Preto/Escuro
    elif r < 80 and g < 80 and b < 80:
        return "preto"
    else:
        return "indefinido"



def detectar_iterativo(caminho_foto, caminho_modelo=None, max_iteracoes=10, confianca=0.25, iou=0.45):
    """
    Detecta produtos iterativamente, mascarando os já encontrados
    """
    
    print("=" * 80)
    print("🔍 DETECÇÃO ITERATIVA - MÚLTIPLOS PRODUTOS")
    print("=" * 80)
    print()
    
    # Verificar foto
    if not os.path.exists(caminho_foto):
        print(f"❌ Erro: Foto não encontrada: {caminho_foto}")
        return
    
    # Carregar imagem original
    img_original_pil = Image.open(caminho_foto)
    img_original_cv = cv2.imread(caminho_foto)
    img_trabalho = img_original_cv.copy()
    
    print(f"📷 Foto: {caminho_foto}")
    print(f"📐 Dimensões: {img_original_pil.size[0]}x{img_original_pil.size[1]} pixels")
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
    
    # MUDANÇA: Detectar TODOS os produtos de uma vez com max_det alto
    print(f"🔍 Detectando TODOS os produtos simultaneamente...")
    print(f"⚙️  Parâmetros: Confiança={confianca*100:.0f}%, IoU={iou*100:.0f}%")
    print("-" * 80)
    print()
    
    try:
        results = model.predict(
            source=caminho_foto,
            conf=confianca,
            iou=iou,
            max_det=100,  # Permitir até 100 detecções
            save=False,
            verbose=False
        )
        
        result = results[0]
        boxes = result.boxes
        
        if len(boxes) == 0:
            print("⚠️  Nenhum produto detectado!")
            print()
            print("💡 Sugestões:")
            print("   - Reduza a confiança: --confianca 0.05")
            print("   - Reduza o IoU: --iou 0.3")
            return
        
        print(f"✅ Detectados {len(boxes)} produto(s) na primeira passagem")
        print()
        
        # Armazenar todas as detecções
        todas_deteccoes = []
        
        # Filtrar bboxes que cobrem mais de 80% da imagem (bbox genérica do treino)
        img_altura, img_largura = img_original_cv.shape[:2]
        area_total = img_largura * img_altura
        
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            nome_classe = model.names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy()
            
            x1, y1, x2, y2 = map(int, xyxy)
            
            # Calcular área da bbox
            bbox_largura = x2 - x1
            bbox_altura = y2 - y1
            bbox_area = bbox_largura * bbox_altura
            percentual_imagem = (bbox_area / area_total) * 100
            
            print(f"Detecção #{i+1}:")
            print(f"  📦 Produto: {nome_classe}")
            print(f"  ✓ Confiança: {conf*100:.1f}%")
            print(f"  📍 BBox: ({x1}, {y1}) → ({x2}, {y2})")
            print(f"  📏 Tamanho: {bbox_largura}x{bbox_altura} ({percentual_imagem:.1f}% da imagem)")
            
            # Se a bbox cobre mais de 80% da imagem, dividir em grid
            # Caso contrário, adicionar a detecção normalmente
            if percentual_imagem > 80:
                print(f"  ⚠️  BBox muito grande! Dividindo imagem em GRID 3x3...")
                
                # Dividir em GRID 3x3 COM SOBREPOSIÇÃO
                # Horizontal: 5 janelas (3 principais + 2 sobreposições)
                # Vertical: 3 janelas (superior, meio, inferior)
                
                largura_regiao = img_largura // 3
                altura_regiao = img_altura // 3
                overlap_h = largura_regiao // 2  # 50% sobreposição horizontal
                overlap_v = altura_regiao // 2   # 50% sobreposição vertical
                
                # Regiões horizontais
                pos_h = [
                    ("Esq", 0, largura_regiao),
                    ("Esq-Centro", overlap_h, overlap_h + largura_regiao),
                    ("Centro", largura_regiao, 2 * largura_regiao),
                    ("Centro-Dir", largura_regiao + overlap_h, largura_regiao + overlap_h + largura_regiao),
                    ("Dir", 2 * largura_regiao, img_largura)
                ]
                
                # Regiões verticais
                pos_v = [
                    ("Superior", 0, altura_regiao + overlap_v),
                    ("Meio", altura_regiao - overlap_v, 2 * altura_regiao + overlap_v),
                    ("Inferior", 2 * altura_regiao - overlap_v, img_altura)
                ]
                
                # Criar grid completo
                regioes = []
                for nome_v, y_inicio, y_fim in pos_v:
                    for nome_h, x_inicio, x_fim in pos_h:
                        regioes.append((f"{nome_v}-{nome_h}", x_inicio, x_fim, y_inicio, y_fim))
                
                deteccoes_regioes = []
                
                print(f"     Total de {len(regioes)} regiões a analisar...")
                print()
                
                for nome_regiao, x_inicio, x_fim, y_inicio, y_fim in regioes:
                    # Garantir que não ultrapasse os limites
                    x_fim = min(x_fim, img_largura)
                    y_fim = min(y_fim, img_altura)
                    
                    if x_fim <= x_inicio or y_fim <= y_inicio:
                        continue
                    
                    print(f"     🔍 {nome_regiao}: x({x_inicio}-{x_fim}) y({y_inicio}-{y_fim})")
                    
                    # Recortar região
                    regiao = img_original_cv[y_inicio:y_fim, x_inicio:x_fim].copy()
                    temp_path = f"temp_regiao_{nome_regiao.replace('-', '_')}.jpg"
                    cv2.imwrite(temp_path, regiao)
                    
                    # Detectar na região
                    try:
                        results_regiao = model.predict(
                            source=temp_path,
                            conf=confianca * 0.5,  # Reduzir confiança em 50% para pegar mais produtos
                            iou=iou * 0.8,  # IoU mais relaxado
                            max_det=5,
                            save=False,
                            verbose=False
                        )
                        
                        boxes_regiao = results_regiao[0].boxes
                        
                        if len(boxes_regiao) > 0:
                            # Pegar TODAS as detecções (não apenas a melhor)
                            for box_reg in boxes_regiao:
                                cls_id_reg = int(box_reg.cls[0])
                                conf_reg = float(box_reg.conf[0])
                                nome_classe_reg = model.names[cls_id_reg]
                                xyxy_reg = box_reg.xyxy[0].cpu().numpy()
                                
                                # Ajustar coordenadas para imagem completa
                                x1_reg, y1_reg, x2_reg, y2_reg = map(int, xyxy_reg)
                                x1_global = x_inicio + x1_reg
                                x2_global = x_inicio + x2_reg
                                y1_global = y_inicio + y1_reg
                                y2_global = y_inicio + y2_reg
                                
                                # Calcular centro da bbox
                                centro_x = (x1_global + x2_global) // 2
                                centro_y = (y1_global + y2_global) // 2
                                
                                # Calcular área da bbox na região
                                bbox_w = x2_reg - x1_reg
                                bbox_h = y2_reg - y1_reg
                                bbox_area_regiao = bbox_w * bbox_h
                                regiao_area = (x_fim - x_inicio) * (y_fim - y_inicio)
                                percentual_regiao = (bbox_area_regiao / regiao_area) * 100
                                
                                # Ignorar se bbox cobre mais de 90% da região (muito grande)
                                if percentual_regiao > 90:
                                    print(f"        ⚠️  {nome_classe_reg} ({conf_reg*100:.1f}%) - bbox muito grande ({percentual_regiao:.0f}%), ignorando")
                                    continue
                                
                                deteccoes_regioes.append({
                                    'produto': nome_classe_reg,
                                    'confianca': conf_reg,
                                    'bbox': (x1_global, y1_global, x2_global, y2_global),
                                    'cls_id': cls_id_reg,
                                    'regiao': nome_regiao,
                                    'centro': (centro_x, centro_y)
                                })
                                
                                print(f"        ✅ {nome_classe_reg} - {conf_reg*100:.1f}% ({percentual_regiao:.0f}% da região)")
                        # Sem print para regiões vazias (muito output)
                        
                        os.remove(temp_path)
                    
                    except Exception as e:
                        print(f"        ❌ Erro: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                
                # Remover duplicatas (produtos detectados em múltiplas regiões)
                print()
                print(f"     🔄 Processando {len(deteccoes_regioes)} detecções brutas...")
                
                deteccoes_unicas = []
                for det in deteccoes_regioes:
                    # Verificar se já existe detecção próxima (mesma classe, centros próximos)
                    eh_duplicata = False
                    for det_unica in deteccoes_unicas:
                        # Mesmo produto?
                        if det['produto'] == det_unica['produto']:
                            # Centros próximos? (menos de 15% da diagonal)
                            diagonal = np.sqrt(img_largura**2 + img_altura**2)
                            dist = np.sqrt(
                                (det['centro'][0] - det_unica['centro'][0])**2 + 
                                (det['centro'][1] - det_unica['centro'][1])**2
                            )
                            
                            if dist < diagonal * 0.15:  # Centros a menos de 15% da diagonal
                                eh_duplicata = True
                                # Manter o de maior confiança
                                if det['confianca'] > det_unica['confianca']:
                                    deteccoes_unicas.remove(det_unica)
                                    deteccoes_unicas.append(det)
                                break
                    
                    if not eh_duplicata:
                        deteccoes_unicas.append(det)
                
                print(f"     ✅ {len(deteccoes_unicas)} produto(s) único(s) encontrado(s)")
                
                # Verificar sobreposição com a detecção original (bbox genérica)
                print()
                print(f"     🔍 Verificando sobreposição com detecção original...")
                
                bbox_original = (x1, y1, x2, y2)
                tem_sobreposicao = False
                
                for det_unica in deteccoes_unicas:
                    bbox_grid = det_unica['bbox']
                    
                    # Calcular IoU
                    x1_inter = max(bbox_original[0], bbox_grid[0])
                    y1_inter = max(bbox_original[1], bbox_grid[1])
                    x2_inter = min(bbox_original[2], bbox_grid[2])
                    y2_inter = min(bbox_original[3], bbox_grid[3])
                    
                    if x1_inter < x2_inter and y1_inter < y2_inter:
                        area_inter = (x2_inter - x1_inter) * (y2_inter - y1_inter)
                        area_original = bbox_area
                        area_grid = (bbox_grid[2] - bbox_grid[0]) * (bbox_grid[3] - bbox_grid[1])
                        
                        iou_calc = area_inter / (area_original + area_grid - area_inter)
                        
                        # Se IoU > 30%, considerar sobreposição
                        if iou_calc > 0.3:
                            tem_sobreposicao = True
                            print(f"        ⚠️  Sobreposição com {det_unica['produto']} (IoU: {iou_calc*100:.1f}%)")
                
                if tem_sobreposicao:
                    print(f"     ❌ IGNORANDO detecção original (bbox genérica) - usando apenas grid")
                else:
                    print(f"     ✅ Sem sobreposição - mantendo detecção original também")
                    # Adicionar a detecção original
                    todas_deteccoes.append({
                        'produto': nome_classe,
                        'confianca': conf,
                        'bbox': (x1, y1, x2, y2),
                        'cls_id': cls_id,
                        'regiao': 'detecção_completa'
                    })
                
                # Adicionar detecções únicas
                for det in deteccoes_unicas:
                    todas_deteccoes.append(det)
                    print(f"        📦 {det['produto']} na região {det['regiao']}")
                
                print()
            
            else:
                # BBox normal, adicionar direto
                print(f"  ✅ BBox válida")
                todas_deteccoes.append({
                    'produto': nome_classe,
                    'confianca': conf,
                    'bbox': (x1, y1, x2, y2),
                    'cls_id': cls_id,
                    'regiao': 'completa'
                })
                print()
    
    except Exception as e:
        print(f"❌ Erro na detecção: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 80)
    print("📊 RESUMO FINAL:")
    print("=" * 80)
    print()
    
    if len(todas_deteccoes) == 0:
        print("⚠️  Nenhum produto detectado em nenhuma iteração!")
        print()
        print("💡 Sugestões:")
        print("   - Reduza a confiança: --confianca 0.05")
        print("   - Reduza o IoU: --iou 0.3")
        print("   - Verifique se os produtos estão no dataset de treino")
        return
    
    print(f"✅ Total de produtos detectados: {len(todas_deteccoes)}")
    print()
    
    # Agrupar por produto
    produtos_contagem = {}
    for det in todas_deteccoes:
        produto = det['produto']
        if produto not in produtos_contagem:
            produtos_contagem[produto] = []
        produtos_contagem[produto].append(det['confianca'])
    
    for produto, confidencias in sorted(produtos_contagem.items()):
        qtd = len(confidencias)
        conf_media = sum(confidencias) / qtd
        print(f"  📦 {produto}:")
        print(f"     └─ Quantidade: {qtd}")
        print(f"     └─ Confiança média: {conf_media*100:.1f}%")
    
    print()
    print("🎨 Lista de detecções:")
    for i, det in enumerate(todas_deteccoes, 1):
        print(f"  {i}. {det['produto']} - {det['confianca']*100:.1f}%")
    
    print()
    
    # Criar imagem final com todas as detecções
    img_final = img_original_cv.copy()
    
    # Cores diferentes para cada produto
    cores = [
        (255, 0, 0),    # Azul
        (0, 255, 0),    # Verde
        (0, 0, 255),    # Vermelho
        (255, 255, 0),  # Ciano
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Amarelo
        (128, 0, 128),  # Roxo
        (255, 128, 0),  # Laranja
        (0, 128, 255),  # Azul claro
        (128, 255, 0),  # Verde limão
    ]
    
    for i, det in enumerate(todas_deteccoes):
        x1, y1, x2, y2 = det['bbox']
        cor = cores[i % len(cores)]
        
        # Desenhar retângulo
        cv2.rectangle(img_final, (x1, y1), (x2, y2), cor, 3)
        
        # Preparar texto
        texto = f"{i+1}. {det['produto']} {det['confianca']*100:.0f}%"
        
        # Fundo do texto
        (text_width, text_height), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img_final, (x1, y1 - text_height - 10), (x1 + text_width, y1), cor, -1)
        
        # Texto
        cv2.putText(img_final, texto, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Salvar resultado
    output_path = Path("resultados_deteccao") / "deteccao_iterativa.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img_final)
    
    print(f"💾 Imagem com detecções salva: {output_path}")
    
    print()
    print("=" * 80)
    
    return todas_deteccoes


def main():
    import argparse
    import tkinter as tk
    from tkinter import filedialog
    
    parser = argparse.ArgumentParser(description='Detecção iterativa de múltiplos produtos')
    parser.add_argument('foto', nargs='?', help='Caminho para a foto de teste (opcional)')
    parser.add_argument('--modelo', '-m', help='Caminho para o modelo .pt (opcional)')
    parser.add_argument('--confianca', '-c', type=float, default=0.25, 
                       help='Confiança mínima (0-1). Padrão: 0.25')
    parser.add_argument('--iou', type=float, default=0.45,
                       help='IoU threshold (0-1). Padrão: 0.45')
    parser.add_argument('--max-iteracoes', type=int, default=10,
                       help='Máximo de iterações. Padrão: 10')
    
    args = parser.parse_args()
    
    # Se não passou foto por argumento, abrir dialog
    caminho_foto = args.foto
    
    if caminho_foto is None:
        print("📷 Selecione a foto para análise...")
        root = tk.Tk()
        root.withdraw()
        
        caminho_foto = filedialog.askopenfilename(
            title="Selecionar Foto para Detecção Iterativa",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        root.destroy()
        
        if not caminho_foto:
            print("❌ Nenhuma foto selecionada. Encerrando.")
            return
    
    detectar_iterativo(
        caminho_foto=caminho_foto,
        caminho_modelo=args.modelo,
        max_iteracoes=args.max_iteracoes,
        confianca=args.confianca,
        iou=args.iou
    )


if __name__ == "__main__":
    main()
