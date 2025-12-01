#!/usr/bin/env python3
"""
DIAGNÓSTICO DE DETECÇÃO DE PRODUTOS
Analisa diferentes métodos para contar produtos com precisão
"""

import cv2
import numpy as np
import os
from datetime import datetime

def analisar_imagem_original(img_path):
    """Análise da imagem original"""
    print("=" * 60)
    print("📸 ANÁLISE DA IMAGEM ORIGINAL")
    print("=" * 60)
    
    img = cv2.imread(img_path)
    if img is None:
        print("❌ Erro ao carregar imagem")
        return None
    
    altura, largura = img.shape[:2]
    print(f"📏 Dimensões: {largura}x{altura}")
    print(f"📊 Canais: {img.shape[2] if len(img.shape) == 3 else 1}")
    
    # Análise de cor
    media_cor = np.mean(img, axis=(0, 1))
    print(f"🎨 Cor média (BGR): [{media_cor[0]:.1f}, {media_cor[1]:.1f}, {media_cor[2]:.1f}]")
    
    return img

def metodo_1_contornos_simples(img, pasta_resultado):
    """MÉTODO 1: Contornos simples (método atual)"""
    print("\n🔍 MÉTODO 1: CONTORNOS SIMPLES")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    img_debug = img.copy()
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        if area > 3000:  # Filtro atual
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            if 0.2 < aspect_ratio < 5.0:
                produtos.append({
                    'id': i,
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'bbox': (x, y, w, h)
                })
                
                # Desenhar contorno
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(img_debug, f"{i}: {area:.0f}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    cv2.imwrite(os.path.join(pasta_resultado, "metodo1_contornos_simples.jpg"), img_debug)
    cv2.imwrite(os.path.join(pasta_resultado, "metodo1_threshold.jpg"), thresh)
    
    print(f"   ✓ {len(produtos)} produtos detectados")
    print(f"   📄 Salvo: metodo1_contornos_simples.jpg")
    
    return produtos

def metodo_2_contornos_rigorosos(img, pasta_resultado):
    """MÉTODO 2: Contornos com critérios mais rigorosos"""
    print("\n🔍 MÉTODO 2: CONTORNOS RIGOROSOS")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold mais rigoroso
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 15, 4
    )
    
    # Morfologia para limpar
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    img_debug = img.copy()
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        perimetro = cv2.arcLength(contorno, True)
        
        if area > 15000:  # Área maior para produtos principais
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Critérios mais rigorosos para garrafas/latas
            if 0.3 < aspect_ratio < 2.5 and area > 20000:
                solidez = area / (w * h)  # Quão "sólido" é o contorno
                
                if solidez > 0.3:  # Filtrar formas muito irregulares
                    produtos.append({
                        'id': i,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'solidez': solidez,
                        'perimetro': perimetro,
                        'bbox': (x, y, w, h)
                    })
                    
                    # Desenhar contorno
                    cv2.rectangle(img_debug, (x, y), (x+w, y+h), (255, 0, 0), 3)
                    cv2.putText(img_debug, f"{i}: {area:.0f}", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "metodo2_contornos_rigorosos.jpg"), img_debug)
    cv2.imwrite(os.path.join(pasta_resultado, "metodo2_threshold.jpg"), thresh)
    
    print(f"   ✓ {len(produtos)} produtos detectados")
    print(f"   📄 Salvo: metodo2_contornos_rigorosos.jpg")
    
    return produtos

def metodo_3_deteccao_cor(img, pasta_resultado):
    """MÉTODO 3: Detecção baseada em cores (garrafas amarelas/douradas)"""
    print("\n🔍 MÉTODO 3: DETECÇÃO POR COR")
    
    # Converter para HSV para melhor detecção de cor
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Definir faixas para cor dourada/amarela (cerveja)
    # Dourado/Amarelo: Hue ~15-35, Saturation alta, Value alto
    lower_dourado = np.array([10, 50, 50])
    upper_dourado = np.array([35, 255, 255])
    
    mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
    
    # Limpar máscara
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_OPEN, kernel)
    mask_dourado = cv2.morphologyEx(mask_dourado, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos na máscara de cor
    contornos, _ = cv2.findContours(mask_dourado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    produtos = []
    img_debug = img.copy()
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        if area > 10000:  # Área significativa para líquido
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Garrafas tendem a ser mais altas que largas
            if 0.2 < aspect_ratio < 1.5 and h > w:
                produtos.append({
                    'id': i,
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'tipo': 'GARRAFA_COR',
                    'bbox': (x, y, w, h)
                })
                
                cv2.rectangle(img_debug, (x, y), (x+w, y+h), (0, 255, 255), 3)
                cv2.putText(img_debug, f"COR{i}: {area:.0f}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "metodo3_deteccao_cor.jpg"), img_debug)
    cv2.imwrite(os.path.join(pasta_resultado, "metodo3_mask_dourado.jpg"), mask_dourado)
    
    print(f"   ✓ {len(produtos)} produtos por cor detectados")
    print(f"   📄 Salvo: metodo3_deteccao_cor.jpg")
    
    return produtos

def metodo_4_template_matching(img, pasta_resultado):
    """MÉTODO 4: Template matching para formas de garrafas/latas"""
    print("\n🔍 MÉTODO 4: TEMPLATE MATCHING")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Criar templates simples para garrafa e lata
    # Template garrafa (retângulo alto)
    template_garrafa = np.zeros((100, 30), dtype=np.uint8)
    cv2.rectangle(template_garrafa, (5, 10), (25, 90), 255, -1)
    
    # Template lata (retângulo mais largo)
    template_lata = np.zeros((80, 50), dtype=np.uint8)
    cv2.rectangle(template_lata, (5, 10), (45, 70), 255, -1)
    
    # Aplicar template matching
    result_garrafa = cv2.matchTemplate(gray, template_garrafa, cv2.TM_CCOEFF_NORMED)
    result_lata = cv2.matchTemplate(gray, template_lata, cv2.TM_CCOEFF_NORMED)
    
    threshold = 0.3
    locations_garrafa = np.where(result_garrafa >= threshold)
    locations_lata = np.where(result_lata >= threshold)
    
    produtos = []
    img_debug = img.copy()
    
    # Processar detecções de garrafas
    for i, (y, x) in enumerate(zip(*locations_garrafa)):
        w, h = template_garrafa.shape[::-1]
        produtos.append({
            'id': f"G{i}",
            'tipo': 'GARRAFA_TEMPLATE',
            'bbox': (x, y, w, h),
            'confianca': result_garrafa[y, x]
        })
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), (255, 0, 255), 2)
        cv2.putText(img_debug, f"G{i}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    
    # Processar detecções de latas
    for i, (y, x) in enumerate(zip(*locations_lata)):
        w, h = template_lata.shape[::-1]
        produtos.append({
            'id': f"L{i}",
            'tipo': 'LATA_TEMPLATE',
            'bbox': (x, y, w, h),
            'confianca': result_lata[y, x]
        })
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.putText(img_debug, f"L{i}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    cv2.imwrite(os.path.join(pasta_resultado, "metodo4_template_matching.jpg"), img_debug)
    
    print(f"   ✓ {len(produtos)} produtos por template detectados")
    print(f"   📄 Salvo: metodo4_template_matching.jpg")
    
    return produtos

def metodo_5_analise_vertical(img, pasta_resultado):
    """MÉTODO 5: Análise de projeção vertical (conta objetos verticais)"""
    print("\n🔍 MÉTODO 5: ANÁLISE VERTICAL")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar threshold
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Projeção vertical (soma pixels em cada coluna)
    proj_vertical = np.sum(thresh, axis=0)
    
    # Encontrar picos na projeção (indica presença de objetos)
    altura_img = thresh.shape[0]
    threshold_pico = altura_img * 0.1  # 10% da altura da imagem
    
    # Encontrar regiões com atividade significativa
    regioes_ativas = proj_vertical > threshold_pico
    
    # Encontrar grupos contínuos
    grupos = []
    inicio = None
    
    for i, ativo in enumerate(regioes_ativas):
        if ativo and inicio is None:
            inicio = i
        elif not ativo and inicio is not None:
            if i - inicio > 50:  # Largura mínima
                grupos.append((inicio, i))
            inicio = None
    
    # Fechar último grupo se necessário
    if inicio is not None and len(proj_vertical) - inicio > 50:
        grupos.append((inicio, len(proj_vertical)))
    
    produtos = []
    img_debug = img.copy()
    
    for i, (x_inicio, x_fim) in enumerate(grupos):
        largura = x_fim - x_inicio
        # Estimar altura baseada na projeção
        y_inicio = 50
        altura = img.shape[0] - 100
        
        produtos.append({
            'id': f"V{i}",
            'tipo': 'VERTICAL_PROJ',
            'bbox': (x_inicio, y_inicio, largura, altura),
            'largura': largura
        })
        
        cv2.rectangle(img_debug, (x_inicio, y_inicio), (x_fim, y_inicio + altura), (255, 255, 0), 3)
        cv2.putText(img_debug, f"V{i}: {largura}px", (x_inicio, y_inicio-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    # Salvar projeção como gráfico
    img_proj = np.zeros((200, len(proj_vertical), 3), dtype=np.uint8)
    for x, valor in enumerate(proj_vertical):
        altura_barra = int((valor / np.max(proj_vertical)) * 180)
        cv2.line(img_proj, (x, 200), (x, 200 - altura_barra), (0, 255, 0), 1)
    
    cv2.imwrite(os.path.join(pasta_resultado, "metodo5_analise_vertical.jpg"), img_debug)
    cv2.imwrite(os.path.join(pasta_resultado, "metodo5_projecao.jpg"), img_proj)
    cv2.imwrite(os.path.join(pasta_resultado, "metodo5_threshold.jpg"), thresh)
    
    print(f"   ✓ {len(produtos)} produtos por projeção vertical detectados")
    print(f"   📄 Salvo: metodo5_analise_vertical.jpg")
    
    return produtos

def comparar_resultados(resultados_metodos):
    """Compara resultados de todos os métodos"""
    print("\n" + "=" * 60)
    print("📊 COMPARAÇÃO DE RESULTADOS")
    print("=" * 60)
    
    for nome, produtos in resultados_metodos.items():
        print(f"{nome}: {len(produtos)} produtos")
        if produtos:
            areas = [p.get('area', 0) for p in produtos if 'area' in p]
            if areas:
                print(f"   📏 Área média: {np.mean(areas):.0f}")
                print(f"   📐 Área min/max: {min(areas):.0f} / {max(areas):.0f}")
    
    # Encontrar consenso
    contagens = [len(produtos) for produtos in resultados_metodos.values()]
    print(f"\n🎯 CONTAGENS: {contagens}")
    print(f"🎯 CONSENSO: {max(set(contagens), key=contagens.count)} produtos (mais frequente)")
    print(f"🎯 MÉDIA: {np.mean(contagens):.1f} produtos")

def main():
    """Diagnóstico principal"""
    print("=" * 80)
    print("🔬 DIAGNÓSTICO COMPLETO DE DETECÇÃO DE PRODUTOS")
    print("🎯 Objetivo: Encontrar melhor método para detectar EXATAMENTE 4 produtos")
    print("=" * 80)
    
    # Caminho da imagem Corona
    imagem_path = "imagens_teste/corona_produtos.jpeg"
    
    # Criar pasta de diagnóstico
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"diagnostico_deteccao_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta de diagnóstico: {os.path.abspath(pasta_resultado)}")
    
    # Analisar imagem original
    img = analisar_imagem_original(imagem_path)
    if img is None:
        return
    
    # Testar todos os métodos
    resultados_metodos = {}
    
    resultados_metodos["MÉTODO 1 - Contornos Simples"] = metodo_1_contornos_simples(img, pasta_resultado)
    resultados_metodos["MÉTODO 2 - Contornos Rigorosos"] = metodo_2_contornos_rigorosos(img, pasta_resultado)
    resultados_metodos["MÉTODO 3 - Detecção por Cor"] = metodo_3_deteccao_cor(img, pasta_resultado)
    resultados_metodos["MÉTODO 4 - Template Matching"] = metodo_4_template_matching(img, pasta_resultado)
    resultados_metodos["MÉTODO 5 - Análise Vertical"] = metodo_5_analise_vertical(img, pasta_resultado)
    
    # Comparar resultados
    comparar_resultados(resultados_metodos)
    
    # Salvar relatório
    with open(os.path.join(pasta_resultado, "relatorio_diagnostico.txt"), 'w', encoding='utf-8') as f:
        f.write("DIAGNÓSTICO DE DETECÇÃO DE PRODUTOS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Imagem: {imagem_path}\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("OBJETIVO: Detectar exatamente 4 produtos Corona\n\n")
        
        f.write("RESULTADOS POR MÉTODO:\n")
        for nome, produtos in resultados_metodos.items():
            f.write(f"- {nome}: {len(produtos)} produtos\n")
        
        contagens = [len(produtos) for produtos in resultados_metodos.values()]
        f.write(f"\nCONSENSO: {max(set(contagens), key=contagens.count)} produtos (mais frequente)\n")
        f.write(f"MÉDIA: {np.mean(contagens):.1f} produtos\n")
    
    print(f"\n📄 Relatório salvo: relatorio_diagnostico.txt")
    print(f"📁 Todos os arquivos em: {os.path.abspath(pasta_resultado)}")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print("\n" + "=" * 80)
    print("✅ DIAGNÓSTICO COMPLETO FINALIZADO!")
    print("🔍 Analise as imagens geradas para escolher o melhor método")
    print("=" * 80)

if __name__ == "__main__":
    main()