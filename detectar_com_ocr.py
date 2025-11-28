#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detecção híbrida: YOLO + OCR para validação de produtos
"""

import os
import re
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
import cv2
import numpy as np
import pytesseract

# Configurar caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Dicionário de produtos conhecidos e suas variações de texto
PRODUTOS_CONHECIDOS = {
    'HEINEKEN': ['HEINEKEN', 'HEINKEN', 'HENEIKEN'],
    'BUDWEISER': ['BUDWEISER', 'BUD', 'BUDWISER'],
    'AMSTEL': ['AMSTEL', 'AMSTELLL', 'AMSTEL'],
    'STELLA': ['STELLA', 'STELLA ARTOIS', 'ARTOIS'],
    'DEVASSA': ['DEVASSA', 'DEVASA'],
    'PETRA': ['PETRA'],
    'PILSEN': ['PILSEN', 'PILSNER'],
    'PEPSI': ['PEPSI', 'PEPSE'],
    'COCA': ['COCA', 'COCA-COLA', 'COCACOLA'],
}


def ler_texto_bbox(img_cv, bbox):
    """
    Lê texto em uma região da imagem usando OCR com múltiplos processamentos
    Otimizado para fotos escuras
    """
    x1, y1, x2, y2 = map(int, bbox)
    
    # Recortar região
    regiao = img_cv[y1:y2, x1:x2]
    
    # Redimensionar para melhorar OCR (altura mínima 400px)
    altura, largura = regiao.shape[:2]
    if altura < 400:
        escala = 400 / altura
        nova_largura = int(largura * escala)
        regiao = cv2.resize(regiao, (nova_largura, 400), interpolation=cv2.INTER_CUBIC)
    
    # Converter para escala de cinza
    cinza = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
    
    # Tentar múltiplos processamentos
    textos = []
    
    try:
        # Método 1: Aumentar brilho e contraste (fotos escuras)
        alpha = 1.5  # Contraste
        beta = 50    # Brilho
        brilhante = cv2.convertScaleAbs(cinza, alpha=alpha, beta=beta)
        _, thresh1 = cv2.threshold(brilhante, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        texto1 = pytesseract.image_to_string(thresh1, lang='por+eng', config='--psm 3 --oem 3')
        textos.append(texto1)
        
        # Método 2: CLAHE agressivo para equalização
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        equalizado = clahe.apply(cinza)
        _, thresh2 = cv2.threshold(equalizado, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        texto2 = pytesseract.image_to_string(thresh2, lang='por+eng', config='--psm 3 --oem 3')
        textos.append(texto2)
        
        # Método 3: Gamma correction (iluminar sombras)
        gamma = 1.5
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gamma_corrigido = cv2.LUT(cinza, table)
        _, thresh3 = cv2.threshold(gamma_corrigido, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        texto3 = pytesseract.image_to_string(thresh3, lang='por+eng', config='--psm 3 --oem 3')
        textos.append(texto3)
        
        # Método 4: Denoising + threshold adaptativo
        denoised = cv2.fastNlMeansDenoising(cinza, None, 10, 7, 21)
        brilhante_denoised = cv2.convertScaleAbs(denoised, alpha=1.5, beta=50)
        thresh4 = cv2.adaptiveThreshold(brilhante_denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        texto4 = pytesseract.image_to_string(thresh4, lang='por+eng', config='--psm 3 --oem 3')
        textos.append(texto4)
        
        # Método 5: Inversão de cores (caso o texto seja claro no escuro)
        invertido = cv2.bitwise_not(cinza)
        brilhante_inv = cv2.convertScaleAbs(invertido, alpha=1.5, beta=50)
        _, thresh5 = cv2.threshold(brilhante_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        texto5 = pytesseract.image_to_string(thresh5, lang='por+eng', config='--psm 3 --oem 3')
        textos.append(texto5)
        
        # Combinar todos os textos
        texto_completo = ' '.join(textos)
        texto_completo = texto_completo.strip().upper()
        texto_completo = re.sub(r'[^A-Z0-9\s]', '', texto_completo)
        
        return texto_completo
    
    except Exception as e:
        print(f"        ⚠️  Erro no OCR: {e}")
        return ""


def validar_produto_por_texto(produto_detectado, texto_ocr):
    """
    Valida se o produto detectado pelo YOLO bate com o texto do OCR
    Retorna: (produto_corrigido, confianca_ocr, match_encontrado)
    """
    if not texto_ocr or len(texto_ocr) < 3:
        return produto_detectado, 0.0, False
    
    # Extrair nome do produto da classe YOLO
    # Formato: MARCA_TIPO_NOME_VOLUME
    partes = produto_detectado.split('_')
    marca_yolo = partes[0] if len(partes) > 0 else ""
    
    # Procurar por cada produto conhecido no texto OCR
    melhor_match = None
    maior_confianca = 0.0
    
    for produto_key, variacoes in PRODUTOS_CONHECIDOS.items():
        for variacao in variacoes:
            if variacao in texto_ocr:
                # Calcular confiança baseado no tamanho do match
                confianca = len(variacao) / len(texto_ocr)
                
                if confianca > maior_confianca:
                    maior_confianca = confianca
                    melhor_match = produto_key
    
    if melhor_match:
        # Verificar se o match bate com a marca detectada pelo YOLO
        if melhor_match == marca_yolo:
            return produto_detectado, maior_confianca, True  # Confirmado
        else:
            # OCR encontrou produto diferente do YOLO
            return melhor_match, maior_confianca, True  # Corrigido pelo OCR
    
    return produto_detectado, 0.0, False  # Sem match no OCR


def detectar_com_ocr(caminho_foto, caminho_modelo=None, confianca=0.05, iou=0.3, usar_ocr=True):
    """
    Detecta produtos usando YOLO + Grid + validação OCR
    """
    
    print("=" * 80)
    print("🔍 DETECÇÃO HÍBRIDA: YOLO + GRID + OCR")
    print("=" * 80)
    print()
    
    # Verificar foto
    if not os.path.exists(caminho_foto):
        print(f"❌ Erro: Foto não encontrada: {caminho_foto}")
        return
    
    # Carregar imagem
    img_original_cv = cv2.imread(caminho_foto)
    img_original_pil = Image.open(caminho_foto)
    
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
    
    print(f"🤖 Modelo YOLO: {caminho_modelo}")
    model = YOLO(caminho_modelo)
    print(f"✓ Classes disponíveis: {len(model.names)}")
    
    if usar_ocr:
        print("📝 OCR: ATIVADO (validação por texto)")
    else:
        print("📝 OCR: DESATIVADO")
    
    print()
    print(f"🔍 Detectando produtos...")
    print(f"⚙️  Parâmetros: Confiança={confianca*100:.0f}%, IoU={iou*100:.0f}%")
    print("-" * 80)
    print()
    
    # Fazer predição inicial
    try:
        results = model.predict(
            source=caminho_foto,
            conf=confianca,
            iou=iou,
            max_det=100,
            save=False,
            verbose=False
        )
        
        result = results[0]
        boxes = result.boxes
        
        img_altura, img_largura = img_original_cv.shape[:2]
        area_total = img_largura * img_altura
        
        todas_deteccoes = []
        bbox_generica = False
        
        # Verificar se há bbox genérica
        if len(boxes) > 0:
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                bbox_area = (x2 - x1) * (y2 - y1)
                percentual = (bbox_area / area_total) * 100
                
                if percentual > 70:
                    bbox_generica = True
                    print(f"⚠️  BBox genérica detectada ({percentual:.1f}% da imagem)")
                    print(f"🔲 Aplicando detecção por GRID...")
                    print()
                    break
        
        # Se bbox genérica, usar grid
        if bbox_generica or len(boxes) == 0:
            # Criar grid 3x3 com overlap
            grid_deteccoes = []
            
            posicoes_h = [
                ("Esquerda", 0, 0.6),
                ("Esq-Centro", 0.2, 0.8),
                ("Centro", 0.4, 1.0),
                ("Centro-Dir", 0.4, 1.0),
                ("Direita", 0.4, 1.0),
            ]
            
            posicoes_v = [
                ("Superior", 0, 0.5),
                ("Meio", 0.25, 0.75),
                ("Inferior", 0.5, 1.0),
            ]
            
            for nome_v, y_start, y_end in posicoes_v:
                for nome_h, x_start, x_end in posicoes_h:
                    x1_reg = int(img_largura * x_start)
                    x2_reg = int(img_largura * x_end)
                    y1_reg = int(img_altura * y_start)
                    y2_reg = int(img_altura * y_end)
                    
                    regiao = img_original_cv[y1_reg:y2_reg, x1_reg:x2_reg]
                    
                    # Detectar na região
                    results_reg = model.predict(
                        source=regiao,
                        conf=confianca * 0.5,
                        iou=iou * 0.8,
                        max_det=5,
                        save=False,
                        verbose=False
                    )
                    
                    for box in results_reg[0].boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1_local, y1_local, x2_local, y2_local = map(int, xyxy)
                        
                        # Converter para coordenadas globais
                        x1_global = x1_reg + x1_local
                        y1_global = y1_reg + y1_local
                        x2_global = x1_reg + x2_local
                        y2_global = y1_reg + y2_local
                        
                        # Filtrar bboxes muito grandes na região
                        bbox_w = x2_local - x1_local
                        bbox_h = y2_local - y1_local
                        regiao_w = x2_reg - x1_reg
                        regiao_h = y2_reg - y1_reg
                        
                        if bbox_w > regiao_w * 0.9 and bbox_h > regiao_h * 0.9:
                            continue
                        
                        # Filtrar por aspect ratio (produtos são verticais)
                        aspect_ratio = bbox_h / bbox_w if bbox_w > 0 else 0
                        if aspect_ratio < 1.2:  # Produtos devem ser mais altos que largos
                            continue
                        
                        # Filtrar bboxes muito pequenas
                        bbox_area_local = bbox_w * bbox_h
                        regiao_area = regiao_w * regiao_h
                        if bbox_area_local < regiao_area * 0.05:  # Menor que 5% da região
                            continue
                        
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        grid_deteccoes.append({
                            'bbox': (x1_global, y1_global, x2_global, y2_global),
                            'cls_id': cls_id,
                            'conf': conf,
                            'nome_classe': model.names[cls_id],
                            'regiao': f"{nome_v}-{nome_h}"
                        })
            
            print(f"✅ Grid encontrou {len(grid_deteccoes)} detecção(ões)")
            
            # Remover duplicatas
            deteccoes_unicas = []
            for det in grid_deteccoes:
                x1, y1, x2, y2 = det['bbox']
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                
                duplicata = False
                for unica in deteccoes_unicas:
                    ux1, uy1, ux2, uy2 = unica['bbox']
                    ucx = (ux1 + ux2) / 2
                    ucy = (uy1 + uy2) / 2
                    
                    dist = np.sqrt((cx - ucx)**2 + (cy - ucy)**2)
                    diagonal = np.sqrt(img_largura**2 + img_altura**2)
                    
                    if dist < diagonal * 0.15:
                        if det['conf'] > unica['conf']:
                            deteccoes_unicas.remove(unica)
                            break
                        else:
                            duplicata = True
                            break
                
                if not duplicata:
                    deteccoes_unicas.append(det)
            
            print(f"✅ {len(deteccoes_unicas)} produto(s) após remoção de duplicatas")
            print()
            
            # Processar detecções do grid
            for i, det in enumerate(deteccoes_unicas, 1):
                x1, y1, x2, y2 = det['bbox']
                
                print(f"Detecção #{i}:")
                print(f"  🤖 YOLO: {det['nome_classe']} ({det['conf']*100:.1f}%)")
                print(f"  📍 Região: {det['regiao']}")
                print(f"  📏 BBox: ({x1}, {y1}) → ({x2}, {y2})")
                
                # OCR
                if usar_ocr:
                    print(f"  📝 Lendo texto...")
                    texto_ocr = ler_texto_bbox(img_original_cv, (x1, y1, x2, y2))
                    
                    if texto_ocr:
                        print(f"     Texto: '{texto_ocr[:100]}...'")
                        
                        produto_final, conf_ocr, match = validar_produto_por_texto(det['nome_classe'], texto_ocr)
                        
                        if match:
                            if produto_final != det['nome_classe'].split('_')[0]:
                                print(f"  ⚠️  CORREÇÃO OCR: {det['nome_classe']} → {produto_final}")
                                print(f"     Confiança OCR: {conf_ocr*100:.1f}%")
                            else:
                                print(f"  ✅ CONFIRMADO por OCR ({conf_ocr*100:.1f}%)")
                        else:
                            print(f"  ⚠️  OCR não confirmou")
                            produto_final = det['nome_classe']
                    else:
                        print(f"     Nenhum texto legível")
                        produto_final = det['nome_classe']
                else:
                    produto_final = det['nome_classe']
                
                todas_deteccoes.append({
                    'produto_yolo': det['nome_classe'],
                    'produto_final': produto_final if usar_ocr else det['nome_classe'],
                    'confianca_yolo': det['conf'],
                    'bbox': (x1, y1, x2, y2),
                    'cls_id': det['cls_id'],
                    'texto_ocr': texto_ocr if usar_ocr else "",
                    'validado_ocr': match if usar_ocr else False
                })
                
                print()
        
        else:
            # Processar detecções normais
            print(f"✅ YOLO detectou {len(boxes)} objeto(s)")
            print()
            
            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                nome_classe = model.names[cls_id]
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                
                print(f"Detecção #{i+1}:")
                print(f"  🤖 YOLO: {nome_classe} ({conf*100:.1f}%)")
                print(f"  📏 BBox: ({x1}, {y1}) → ({x2}, {y2})")
                
                if usar_ocr:
                    print(f"  📝 Lendo texto...")
                    texto_ocr = ler_texto_bbox(img_original_cv, (x1, y1, x2, y2))
                    
                    if texto_ocr:
                        print(f"     Texto: '{texto_ocr[:100]}...'")
                        produto_final, conf_ocr, match = validar_produto_por_texto(nome_classe, texto_ocr)
                        
                        if match:
                            if produto_final != nome_classe.split('_')[0]:
                                print(f"  ⚠️  CORREÇÃO OCR: {nome_classe} → {produto_final}")
                            else:
                                print(f"  ✅ CONFIRMADO por OCR ({conf_ocr*100:.1f}%)")
                        else:
                            print(f"  ⚠️  OCR não confirmou")
                            produto_final = nome_classe
                    else:
                        print(f"     Nenhum texto legível")
                        produto_final = nome_classe
                else:
                    produto_final = nome_classe
                
                todas_deteccoes.append({
                    'produto_yolo': nome_classe,
                    'produto_final': produto_final if usar_ocr else nome_classe,
                    'confianca_yolo': conf,
                    'bbox': (x1, y1, x2, y2),
                    'cls_id': cls_id,
                    'texto_ocr': texto_ocr if usar_ocr else "",
                    'validado_ocr': match if usar_ocr else False
                })
                
                print()
        
        if len(todas_deteccoes) == 0:
            print("⚠️  Nenhuma detecção válida")
            return
        
        # Resumo
        print("=" * 80)
        print("📊 RESUMO FINAL:")
        print("=" * 80)
        print()
        print(f"✅ {len(todas_deteccoes)} produto(s) detectado(s)")
        print()
        
        for i, det in enumerate(todas_deteccoes, 1):
            status = "✅ Validado" if det['validado_ocr'] else "🤖 YOLO"
            print(f"  {i}. {det['produto_final']} - {status} ({det['confianca_yolo']*100:.1f}%)")
        
        # Criar imagem
        print()
        print("🎨 Gerando imagem com detecções...")
        
        img_final = img_original_cv.copy()
        
        cores = [
            (255, 0, 0),    # Azul
            (0, 255, 0),    # Verde
            (0, 0, 255),    # Vermelho
            (255, 255, 0),  # Ciano
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Amarelo
        ]
        
        for i, det in enumerate(todas_deteccoes):
            x1, y1, x2, y2 = det['bbox']
            cor = cores[i % len(cores)]
            
            cv2.rectangle(img_final, (x1, y1), (x2, y2), cor, 3)
            
            status_icon = "✓" if det['validado_ocr'] else ""
            texto = f"{i+1}. {det['produto_final']} {status_icon} {det['confianca_yolo']*100:.0f}%"
            
            (text_width, text_height), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img_final, (x1, y1 - text_height - 10), (x1 + text_width, y1), cor, -1)
            cv2.putText(img_final, texto, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        output_path = Path("resultados_deteccao") / "deteccao_yolo_ocr.jpg"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), img_final)
        
        print(f"💾 Imagem salva: {output_path}")
        print()
        print("=" * 80)
        
        return todas_deteccoes
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    import argparse
    import tkinter as tk
    from tkinter import filedialog
    
    parser = argparse.ArgumentParser(description='Detecção híbrida YOLO + OCR')
    parser.add_argument('foto', nargs='?', help='Caminho para a foto (opcional)')
    parser.add_argument('--modelo', '-m', help='Caminho para o modelo .pt (opcional)')
    parser.add_argument('--confianca', '-c', type=float, default=0.05,
                       help='Confiança mínima (0-1). Padrão: 0.05')
    parser.add_argument('--iou', type=float, default=0.3,
                       help='IoU threshold (0-1). Padrão: 0.3')
    parser.add_argument('--sem-ocr', action='store_true',
                       help='Desativar validação por OCR')
    
    args = parser.parse_args()
    
    # Se não passou foto, abrir dialog
    caminho_foto = args.foto
    
    if caminho_foto is None:
        print("📷 Selecione a foto...")
        root = tk.Tk()
        root.withdraw()
        
        caminho_foto = filedialog.askopenfilename(
            title="Selecionar Foto",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        root.destroy()
        
        if not caminho_foto:
            print("❌ Nenhuma foto selecionada.")
            return
    
    detectar_com_ocr(
        caminho_foto=caminho_foto,
        caminho_modelo=args.modelo,
        confianca=args.confianca,
        iou=args.iou,
        usar_ocr=not args.sem_ocr
    )


if __name__ == "__main__":
    main()
