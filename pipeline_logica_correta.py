#!/usr/bin/env python3
"""
🎯 PIPELINE LÓGICA CORRETA
========================

FASE 1: YOLO INICIAL (reconhecimento básico)
FASE 2: PREPROCESSAMENTO INTELIGENTE  
FASE 3: YOLO DECISIVO (comparação assertiva)
FASE 4: OCR + LUPA (após decisão do YOLO)
"""

import cv2
import numpy as np
import os
import pytesseract
from datetime import datetime
try:
    from ultralytics import YOLO
    YOLO_DISPONIVEL = True
except ImportError:
    YOLO_DISPONIVEL = False
    print("⚠️ YOLO não disponível")

def ajustar_brilho_automatico(img):
    """Ajusta brilho de acordo com a imagem"""
    # Calcular brilho médio
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brilho_medio = np.mean(gray)
    
    # Ajuste automático
    if brilho_medio < 100:  # Imagem escura
        fator = 1.3
        print(f"    📝 Imagem escura (brilho: {brilho_medio:.1f}) - aumentando brilho {fator}x")
    elif brilho_medio > 180:  # Imagem clara
        fator = 0.8
        print(f"    📝 Imagem clara (brilho: {brilho_medio:.1f}) - diminuindo brilho {fator}x")
    else:
        fator = 1.0
        print(f"    📝 Brilho adequado ({brilho_medio:.1f}) - sem ajuste")
    
    # Aplicar ajuste
    img_ajustada = cv2.convertScaleAbs(img, alpha=fator, beta=0)
    return img_ajustada

def normalizar_pixels(img):
    """Normaliza pixels para escala 0-1"""
    img_normalizada = img.astype(np.float32) / 255.0
    print("    📝 Pixels normalizados (0-1)")
    return img_normalizada

def remover_ruido(img):
    """Remove ruído com filtros"""
    # Gaussian blur para reduzir ruído
    img_blur = cv2.GaussianBlur(img, (3, 3), 0)
    
    # Median filter para artefatos
    img_limpa = cv2.medianBlur(img_blur, 3)
    
    print("    📝 Ruído removido (Gaussian + Median)")
    return img_limpa

def corrigir_perspectiva(img):
    """Endireita imagens inclinadas (básico)"""
    # Detectar bordas para encontrar linhas principais
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Detectar linhas
    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
    
    if lines is not None and len(lines) > 0:
        # Calcular ângulo médio
        angulos = []
        for line in lines[:5]:  # Usar apenas primeiras 5 linhas
            rho, theta = line[0]
            angulo = theta * 180 / np.pi
            if angulo > 90:
                angulo = angulo - 180
            angulos.append(angulo)
        
        angulo_medio = np.mean(angulos)
        
        # Rotacionar se necessário
        if abs(angulo_medio) > 2:  # Apenas se inclinação > 2 graus
            altura, largura = img.shape[:2]
            centro = (largura//2, altura//2)
            matriz_rotacao = cv2.getRotationMatrix2D(centro, angulo_medio, 1.0)
            img_corrigida = cv2.warpAffine(img, matriz_rotacao, (largura, altura))
            print(f"    📝 Perspectiva corrigida ({angulo_medio:.1f}°)")
            return img_corrigida
    
    print("    📝 Perspectiva não necessária")
    return img

def preprocessamento_completo(img_original):
    """Preprocessamento inteligente completo"""
    print("\n🔧 PREPROCESSAMENTO INTELIGENTE:")
    
    # 1. Remoção de fundo
    print("  1️⃣ Removendo fundo...")
    gray = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel, iterations=3)
    
    img_sem_fundo = cv2.bitwise_and(img_original, img_original, mask=mask)
    print("    ✓ Fundo removido")
    
    # 2. Redimensionar para 640x640 (padrão YOLO)
    print("  2️⃣ Redimensionando para 640x640...")
    img_640 = cv2.resize(img_sem_fundo, (640, 640), interpolation=cv2.INTER_AREA)
    print("    ✓ Redimensionado para 640x640")
    
    # 3. Ajustar brilho automaticamente
    print("  3️⃣ Ajustando brilho...")
    img_brilho = ajustar_brilho_automatico(img_640)
    
    # 4. Normalizar pixels
    print("  4️⃣ Normalizando pixels...")
    img_normalizada = normalizar_pixels(img_brilho)
    # Converter de volta para uint8 para próximas operações
    img_normalizada = (img_normalizada * 255).astype(np.uint8)
    
    # 5. Remover ruído
    print("  5️⃣ Removendo ruído...")
    img_limpa = remover_ruido(img_normalizada)
    
    # 6. Corrigir perspectiva
    print("  6️⃣ Corrigindo perspectiva...")
    img_final = corrigir_perspectiva(img_limpa)
    
    print("  ✅ PREPROCESSAMENTO CONCLUÍDO!")
    return img_final

def comparar_deteccoes_yolo(deteccoes_inicial, deteccoes_preprocessada):
    """Compara detecções para decisão assertiva"""
    print("\n🤔 COMPARAÇÃO YOLO (DECISÃO ASSERTIVA):")
    
    n_inicial = len(deteccoes_inicial)
    n_preprocessada = len(deteccoes_preprocessada)
    
    print(f"  📊 YOLO Inicial: {n_inicial} produtos")
    print(f"  📊 YOLO Preprocessado: {n_preprocessada} produtos")
    
    # LÓGICA DE DECISÃO ASSERTIVA
    if n_preprocessada > n_inicial:
        print("  🎯 DECISÃO: Usar detecções PREPROCESSADAS (mais produtos encontrados)")
        return deteccoes_preprocessada, "PREPROCESSADA"
    elif n_inicial > n_preprocessada:
        print("  🎯 DECISÃO: Usar detecções INICIAIS (preprocessamento removeu produtos válidos)")
        return deteccoes_inicial, "INICIAL"  
    elif n_inicial == n_preprocessada and n_inicial > 0:
        # Comparar confiança média
        conf_inicial = np.mean([d['confianca'] for d in deteccoes_inicial])
        conf_preprocessada = np.mean([d['confianca'] for d in deteccoes_preprocessada])
        
        if conf_preprocessada > conf_inicial:
            print(f"  🎯 DECISÃO: Usar PREPROCESSADAS (confiança maior: {conf_preprocessada:.2f} vs {conf_inicial:.2f})")
            return deteccoes_preprocessada, "PREPROCESSADA"
        else:
            print(f"  🎯 DECISÃO: Usar INICIAIS (confiança maior: {conf_inicial:.2f} vs {conf_preprocessada:.2f})")
            return deteccoes_inicial, "INICIAL"
    else:
        print("  ⚠️ DECISÃO: Nenhuma detecção válida")
        return [], "NENHUMA"

def executar_yolo(img, modelo_yolo, nome_fase):
    """Executa YOLO e retorna detecções"""
    deteccoes = []
    
    if not (YOLO_DISPONIVEL and os.path.exists(modelo_yolo)):
        print(f"    ❌ YOLO não disponível para {nome_fase}")
        return deteccoes
    
    try:
        model = YOLO(modelo_yolo)
        resultados = model(img, verbose=False)
        
        for resultado in resultados:
            boxes = resultado.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confianca = float(box.conf[0])
                    classe_id = int(box.cls[0])
                    
                    nomes_classes = ['LATA_350ML', 'LATA_473ML', 'GARRAFA_LONG_NECK', 'GARRAFA_600ML', 'OUTROS']
                    classe_nome = nomes_classes[classe_id] if classe_id < len(nomes_classes) else f"CLASSE_{classe_id}"
                    
                    if confianca > 0.1:  # Limiar baixo para capturar mais
                        deteccoes.append({
                            'classe': classe_nome,
                            'confianca': confianca,
                            'bbox': (x1, y1, x2, y2),
                            'area': (x2-x1) * (y2-y1)
                        })
        
        print(f"    ✓ {nome_fase}: {len(deteccoes)} produtos detectados")
        return deteccoes
        
    except Exception as e:
        print(f"    ❌ Erro YOLO {nome_fase}: {e}")
        return deteccoes

def main():
    print("=" * 80)
    print("🎯 PIPELINE LÓGICA CORRETA")
    print("🚀 YOLO Inicial → Preprocessamento → YOLO Decisivo → OCR + Lupa")
    print("=" * 80)
    
    # Caminhos
    imagem_original = "imagens_teste/corona_produtos.jpeg"
    modelo_yolo = r"C:\dataset_yolo_verifik\yolo_embalagens_best.pt"
    
    # Criar pasta de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"pipeline_logica_correta_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    # Carregar imagem
    if not os.path.exists(imagem_original):
        print(f"❌ Imagem não encontrada: {imagem_original}")
        return
    
    img = cv2.imread(imagem_original)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
        
    altura, largura = img.shape[:2]
    print(f"\n📥 Imagem: {largura}x{altura}")
    
    # =====================================
    # FASE 1: YOLO INICIAL (Reconhecimento básico)
    # =====================================
    print("\n🎯 FASE 1: YOLO INICIAL (Reconhecimento básico)")
    deteccoes_inicial = executar_yolo(img.copy(), modelo_yolo, "INICIAL")
    
    # Salvar visualização
    img_yolo_inicial = img.copy()
    for det in deteccoes_inicial:
        x1, y1, x2, y2 = det['bbox']
        cv2.rectangle(img_yolo_inicial, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_yolo_inicial, f"{det['classe']} {det['confianca']:.2f}", 
                  (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "1_yolo_inicial.jpg"), img_yolo_inicial)
    
    # =====================================
    # FASE 2: PREPROCESSAMENTO INTELIGENTE
    # =====================================
    print("\n🔧 FASE 2: PREPROCESSAMENTO INTELIGENTE")
    img_preprocessada = preprocessamento_completo(img.copy())
    cv2.imwrite(os.path.join(pasta_resultado, "2_preprocessada_640x640.jpg"), img_preprocessada)
    
    # =====================================
    # FASE 3: YOLO DECISIVO (Comparação assertiva)
    # =====================================
    print("\n🎯 FASE 3: YOLO DECISIVO (Comparação assertiva)")
    deteccoes_preprocessada = executar_yolo(img_preprocessada.copy(), modelo_yolo, "PREPROCESSADA")
    
    # Salvar visualização
    img_yolo_preprocessada = img_preprocessada.copy()
    for det in deteccoes_preprocessada:
        x1, y1, x2, y2 = det['bbox']
        cv2.rectangle(img_yolo_preprocessada, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(img_yolo_preprocessada, f"{det['classe']} {det['confianca']:.2f}", 
                  (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "3_yolo_preprocessada.jpg"), img_yolo_preprocessada)
    
    # DECISÃO ASSERTIVA
    deteccoes_finais, origem_decisao = comparar_deteccoes_yolo(deteccoes_inicial, deteccoes_preprocessada)
    
    # =====================================
    # FASE 4: OCR + LUPA (Após decisão)
    # =====================================
    print(f"\n🔍 FASE 4: OCR + LUPA (Usando detecções {origem_decisao})")
    
    if origem_decisao == "PREPROCESSADA":
        img_para_ocr = img_preprocessada.copy()
    else:
        img_para_ocr = img.copy()
    
    resultados_ocr = []
    
    # OCR DE EMERGÊNCIA - quando YOLO não detecta nada
    if len(deteccoes_finais) == 0:
        print("\n  🚨 OCR DE EMERGÊNCIA - YOLO não detectou produtos")
        print("  🔍 Tentando OCR na imagem inteira...")
        
        # OCR na imagem original
        try:
            gray_completa = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            texto_original = pytesseract.image_to_string(gray_completa, config="--psm 6").strip()
            if texto_original:
                print(f"    📝 Texto na imagem ORIGINAL: {texto_original}")
                resultados_ocr.append({
                    'produto': 'ORIGINAL',
                    'classe': 'IMAGEM_COMPLETA',
                    'confianca': 1.0,
                    'texto': texto_original
                })
        except Exception as e:
            print(f"    ❌ Erro OCR original: {e}")
        
        # OCR na imagem preprocessada
        try:
            gray_preprocessada = cv2.cvtColor(img_preprocessada, cv2.COLOR_BGR2GRAY)
            texto_preprocessada = pytesseract.image_to_string(gray_preprocessada, config="--psm 6").strip()
            if texto_preprocessada:
                print(f"    📝 Texto na imagem PREPROCESSADA: {texto_preprocessada}")
                resultados_ocr.append({
                    'produto': 'PREPROCESSADA',
                    'classe': 'IMAGEM_640x640',
                    'confianca': 1.0,
                    'texto': texto_preprocessada
                })
        except Exception as e:
            print(f"    ❌ Erro OCR preprocessada: {e}")
        
        # OCR com zoom 2x na imagem original
        try:
            img_zoom = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            gray_zoom = cv2.cvtColor(img_zoom, cv2.COLOR_BGR2GRAY)
            texto_zoom = pytesseract.image_to_string(gray_zoom, config="--psm 6").strip()
            if texto_zoom:
                print(f"    📝 Texto com ZOOM 2x: {texto_zoom}")
                resultados_ocr.append({
                    'produto': 'ZOOM_2x',
                    'classe': 'IMAGEM_AMPLIADA',
                    'confianca': 1.0,
                    'texto': texto_zoom
                })
            cv2.imwrite(os.path.join(pasta_resultado, "4_ocr_emergencia_zoom_2x.jpg"), img_zoom)
        except Exception as e:
            print(f"    ❌ Erro OCR zoom: {e}")
        
        if len(resultados_ocr) == 0:
            print("    ❌ OCR DE EMERGÊNCIA não encontrou texto")
        else:
            print(f"    ✅ OCR DE EMERGÊNCIA encontrou {len(resultados_ocr)} textos!")
    
    for i, det in enumerate(deteccoes_finais):
        x1, y1, x2, y2 = det['bbox']
        classe = det['classe']
        confianca = det['confianca']
        
        print(f"\n  📦 Produto {i+1}: {classe} (conf: {confianca:.2f})")
        
        # Extrair região do produto
        produto_regiao = img_para_ocr[y1:y2, x1:x2].copy()
        
        if produto_regiao.size > 0:
            # LUPA - Zoom 3x
            produto_zoom = cv2.resize(produto_regiao, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(os.path.join(pasta_resultado, f"4_produto_{i+1}_zoom_3x.jpg"), produto_zoom)
            
            # OCR
            try:
                gray_produto = cv2.cvtColor(produto_zoom, cv2.COLOR_BGR2GRAY)
                texto = pytesseract.image_to_string(gray_produto, config="--psm 6").strip()
                
                if texto:
                    print(f"    📝 Texto: {texto}")
                    resultados_ocr.append({
                        'produto': i+1,
                        'classe': classe,
                        'confianca': confianca,
                        'texto': texto
                    })
                else:
                    print(f"    ❌ Nenhum texto detectado")
                    
            except Exception as e:
                print(f"    ❌ Erro OCR: {e}")
    
    # RESULTADOS FINAIS
    print(f"\n🎉 RESULTADOS FINAIS:")
    print(f"  🎯 Decisão YOLO: {origem_decisao}")
    print(f"  📦 Produtos detectados: {len(deteccoes_finais)}")
    print(f"  📝 Textos extraídos: {len(resultados_ocr)}")
    
    for resultado in resultados_ocr:
        print(f"  • {resultado['classe']} - {resultado['texto']}")
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_final.txt"), 'w', encoding='utf-8') as f:
        f.write("=== PIPELINE LÓGICA CORRETA ===\n\n")
        f.write(f"Imagem: {imagem_original}\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write(f"FASE 1 - YOLO INICIAL: {len(deteccoes_inicial)} produtos\n")
        f.write(f"FASE 3 - YOLO PREPROCESSADA: {len(deteccoes_preprocessada)} produtos\n")
        f.write(f"DECISÃO ASSERTIVA: {origem_decisao}\n\n")
        
        f.write("RESULTADOS FINAIS:\n")
        for resultado in resultados_ocr:
            f.write(f"- {resultado['classe']}: {resultado['texto']}\n")
    
    print(f"\n📁 Resultados salvos em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass

if __name__ == "__main__":
    main()