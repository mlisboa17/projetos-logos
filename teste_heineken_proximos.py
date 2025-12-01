#!/usr/bin/env python3
"""
TESTE HEINEKEN - PRODUTOS PRÓXIMOS
Adaptação do detector híbrido para produtos Heineken
CUIDADO: Produtos muito próximos podem confundir no zoom
"""

import cv2
import numpy as np
import os
from datetime import datetime

def detectar_produtos_heineken(img, pasta_resultado):
    """
    Detecta produtos Heineken especificamente
    1 garrafa verde + 3 latas (verde/azul)
    DESAFIO: Produtos muito próximos
    """
    print("🍺 DETECTANDO PRODUTOS HEINEKEN")
    print("   ⚠️ Cuidado: produtos muito próximos")
    
    altura, largura = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # CORES HEINEKEN ESPECÍFICAS
    print("   🎨 Detectando cores Heineken...")
    
    # VERDE HEINEKEN (garrafa + latas verdes)
    lower_verde = np.array([35, 40, 40])    # Verde mais amplo
    upper_verde = np.array([85, 255, 255])
    mask_verde = cv2.inRange(hsv, lower_verde, upper_verde)
    
    # AZUL HEINEKEN (lata azul)
    lower_azul = np.array([100, 50, 50])    # Azul
    upper_azul = np.array([130, 255, 255])
    mask_azul = cv2.inRange(hsv, lower_azul, upper_azul)
    
    # Combinar máscaras
    mask_heineken = cv2.bitwise_or(mask_verde, mask_azul)
    
    # Limpeza morfológica mais suave (produtos próximos)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # Menor para não juntar produtos
    mask_heineken = cv2.morphologyEx(mask_heineken, cv2.MORPH_OPEN, kernel)
    mask_heineken = cv2.morphologyEx(mask_heineken, cv2.MORPH_CLOSE, kernel)
    
    # Salvar máscaras
    cv2.imwrite(os.path.join(pasta_resultado, "mask_verde.jpg"), mask_verde)
    cv2.imwrite(os.path.join(pasta_resultado, "mask_azul.jpg"), mask_azul)
    cv2.imwrite(os.path.join(pasta_resultado, "mask_heineken.jpg"), mask_heineken)
    
    # Encontrar contornos
    contornos, _ = cv2.findContours(mask_heineken, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"   🔍 {len(contornos)} contornos encontrados")
    
    produtos_candidatos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        # Área mínima menor (produtos podem ser menores na foto)
        if area > 3000:  # Reduzido para capturar produtos menores
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Analisar cor dominante
            roi_verde = mask_verde[y:y+h, x:x+w]
            roi_azul = mask_azul[y:y+h, x:x+w]
            
            pixels_verde = np.sum(roi_verde > 0)
            pixels_azul = np.sum(roi_azul > 0)
            
            # Classificar por cor e forma
            if pixels_azul > pixels_verde:
                # Mais azul = lata azul
                tipo = "LATA_AZUL_HEINEKEN"
                cor_debug = (255, 0, 0)  # Azul
                confianca = pixels_azul / (pixels_verde + pixels_azul + 1)
            else:
                # Mais verde = garrafa ou lata verde
                if aspect_ratio < 0.6:  # Mais alto = garrafa
                    tipo = "GARRAFA_VERDE_HEINEKEN"
                    cor_debug = (0, 255, 0)  # Verde
                else:  # Mais largo = lata
                    tipo = "LATA_VERDE_HEINEKEN"
                    cor_debug = (0, 200, 0)  # Verde escuro
                confianca = pixels_verde / (pixels_verde + pixels_azul + 1)
            
            produtos_candidatos.append({
                'tipo': tipo,
                'bbox': (x, y, w, h),
                'area': area,
                'aspect_ratio': aspect_ratio,
                'confianca': confianca,
                'centro': (x + w//2, y + h//2),
                'cor_debug': cor_debug
            })
            
            print(f"      ✅ {tipo}: {area:.0f}px, ratio {aspect_ratio:.2f}")
    
    # REMOÇÃO DE SOBREPOSIÇÕES (CRÍTICO para produtos próximos)
    print("   🔧 Removendo sobreposições (produtos próximos)...")
    
    # Ordenar por área (maiores primeiro)
    produtos_candidatos.sort(key=lambda x: x['area'], reverse=True)
    
    produtos_finais = []
    DISTANCIA_MINIMA = 50  # Reduzido para produtos próximos
    
    for candidato in produtos_candidatos:
        muito_proximo = False
        centro1 = candidato['centro']
        
        for aceito in produtos_finais:
            centro2 = aceito['centro']
            distancia = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            # Se muito próximo, verificar se é realmente o mesmo produto
            if distancia < DISTANCIA_MINIMA:
                # Verificar sobreposição de bounding boxes
                x1, y1, w1, h1 = candidato['bbox']
                x2, y2, w2, h2 = aceito['bbox']
                
                overlap_x = max(0, min(x1+w1, x2+w2) - max(x1, x2))
                overlap_y = max(0, min(y1+h1, y2+h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                # Se sobreposição > 40%, é o mesmo produto
                if overlap_area > 0.4 * min(candidato['area'], aceito['area']):
                    muito_proximo = True
                    break
        
        if not muito_proximo:
            produtos_finais.append(candidato)
    
    # Estatísticas
    garrafas = [p for p in produtos_finais if 'GARRAFA' in p['tipo']]
    latas_verdes = [p for p in produtos_finais if 'LATA_VERDE' in p['tipo']]
    latas_azuis = [p for p in produtos_finais if 'LATA_AZUL' in p['tipo']]
    
    print(f"   ✅ RESULTADO HEINEKEN: {len(produtos_finais)} produtos")
    print(f"      🍺 Garrafas verdes: {len(garrafas)}")
    print(f"      🥤 Latas verdes: {len(latas_verdes)}")
    print(f"      🔵 Latas azuis: {len(latas_azuis)}")
    
    # Desenhar detecções
    img_debug = img.copy()
    for i, produto in enumerate(produtos_finais):
        x, y, w, h = produto['bbox']
        cor = produto['cor_debug']
        
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor, 3)
        cv2.putText(img_debug, f"{produto['tipo'][:8]} {i+1}", (x, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    
    cv2.imwrite(os.path.join(pasta_resultado, "deteccao_heineken.jpg"), img_debug)
    
    return produtos_finais

def testar_zoom_cuidadoso_heineken(img_produto, pasta_resultado, produto_id):
    """
    Teste de zoom cuidadoso para produtos Heineken próximos
    Menos agressivo para não perder detalhes
    """
    print(f"    🔍 Zoom cuidadoso para produto Heineken {produto_id}...")
    
    if img_produto is None or img_produto.size == 0:
        return []
    
    altura_original, largura_original = img_produto.shape[:2]
    
    # ZOOMS MAIS CONSERVADORES (produtos próximos)
    zooms_heineken = [
        {'nome': 'CONSERVADOR', 'fator': 1.3, 'desc': 'zoom mínimo'},
        {'nome': 'MODERADO', 'fator': 1.8, 'desc': 'zoom médio'},
        {'nome': 'MAXIMO', 'fator': 2.5, 'desc': 'zoom máximo seguro'}
    ]
    
    resultados_zoom = []
    
    for config in zooms_heineken:
        fator = config['fator']
        nome = config['nome']
        
        print(f"       📏 {nome}: {fator}x ({config['desc']})")
        
        # Aplicar zoom
        nova_largura = int(largura_original * fator)
        nova_altura = int(altura_original * fator)
        
        # Limite de segurança
        if nova_largura > 1500 or nova_altura > 1500:
            fator_ajustado = min(1500 / largura_original, 1500 / altura_original)
            nova_largura = int(largura_original * fator_ajustado)
            nova_altura = int(altura_original * fator_ajustado)
            print(f"          ⚠️ Limitado a {fator_ajustado:.1f}x")
        
        img_zoom = cv2.resize(img_produto, (nova_largura, nova_altura), interpolation=cv2.INTER_CUBIC)
        
        # Salvar para análise
        nome_arquivo = f"produto_{produto_id}_zoom_{nome.lower()}.jpg"
        cv2.imwrite(os.path.join(pasta_resultado, nome_arquivo), img_zoom)
        
        resultados_zoom.append({
            'nome': nome,
            'fator': fator,
            'imagem': img_zoom,
            'dimensoes': f"{nova_largura}x{nova_altura}"
        })
    
    return resultados_zoom

def main():
    """Teste com imagem Heineken - produtos próximos"""
    print("=" * 70)
    print("🍺 TESTE HEINEKEN - PRODUTOS PRÓXIMOS")
    print("⚠️ DESAFIO: 4 produtos muito próximos")
    print("🎯 META: 1 garrafa + 3 latas Heineken")
    print("=" * 70)
    
    # Criar pasta de teste
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultado = f"teste_heineken_proximos_{timestamp}"
    os.makedirs(pasta_resultado, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_resultado)}")
    
    # Simular carregamento da imagem anexada
    # (Em ambiente real, a imagem seria salva automaticamente)
    possible_paths = [
        "heineken_produtos.jpg",
        "imagens_teste/heineken.jpeg",
        "imagens_teste/corona_produtos.jpeg"  # Fallback para teste
    ]
    
    imagem_path = None
    for path in possible_paths:
        if os.path.exists(path):
            imagem_path = path
            break
    
    if imagem_path is None:
        print("❌ Imagem Heineken não encontrada")
        print("ℹ️ Salve a imagem anexada como 'heineken_produtos.jpg'")
        return
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Salvar original
    cv2.imwrite(os.path.join(pasta_resultado, "00_original_heineken.jpg"), img)
    
    # ETAPA 1: DETECÇÃO HEINEKEN
    produtos = detectar_produtos_heineken(img, pasta_resultado)
    
    if not produtos:
        print("❌ Nenhum produto Heineken detectado")
        return
    
    # ETAPA 2: TESTE DE ZOOM CUIDADOSO
    print(f"\n🔧 TESTE DE ZOOM CUIDADOSO - {len(produtos)} PRODUTOS")
    
    for i, produto in enumerate(produtos):
        print(f"\n  📦 Produto {i+1}: {produto['tipo']}")
        
        # Extrair produto com margem pequena (produtos próximos)
        x, y, w, h = produto['bbox']
        margem = 10  # Margem menor para não pegar produtos vizinhos
        
        x1 = max(0, x - margem)
        y1 = max(0, y - margem)
        x2 = min(img.shape[1], x + w + margem)
        y2 = min(img.shape[0], y + h + margem)
        
        produto_recortado = img[y1:y2, x1:x2]
        
        # Testar zooms conservadores
        zooms_testados = testar_zoom_cuidadoso_heineken(produto_recortado, pasta_resultado, i+1)
        
        print(f"    ✅ {len(zooms_testados)} níveis de zoom testados")
    
    # ANÁLISE FINAL
    print(f"\n🎉 ANÁLISE FINAL HEINEKEN")
    print(f"📊 Produtos detectados: {len(produtos)}")
    
    # Contar por tipo
    garrafas = len([p for p in produtos if 'GARRAFA' in p['tipo']])
    latas_verdes = len([p for p in produtos if 'LATA_VERDE' in p['tipo']])
    latas_azuis = len([p for p in produtos if 'LATA_AZUL' in p['tipo']])
    
    print(f"   🍺 Garrafas: {garrafas}")
    print(f"   🟢 Latas verdes: {latas_verdes}")
    print(f"   🔵 Latas azuis: {latas_azuis}")
    
    # Avaliar resultado
    total_esperado = 4  # 1 garrafa + 3 latas
    if len(produtos) == total_esperado:
        print(f"🏆 EXCELENTE! Detectou exatamente {total_esperado} produtos Heineken")
        if garrafas == 1:
            print(f"   ✅ 1 garrafa detectada corretamente")
        if (latas_verdes + latas_azuis) == 3:
            print(f"   ✅ 3 latas detectadas corretamente")
    elif len(produtos) > total_esperado:
        print(f"⚠️ Detectou {len(produtos)} produtos (esperado: {total_esperado})")
        print(f"   Possível causa: produtos próximos foram separados incorretamente")
    else:
        print(f"⚠️ Detectou apenas {len(produtos)} produtos (esperado: {total_esperado})")
        print(f"   Possível causa: produtos próximos foram agrupados incorretamente")
    
    # Relatório
    with open(os.path.join(pasta_resultado, "relatorio_heineken.txt"), 'w', encoding='utf-8') as f:
        f.write("TESTE HEINEKEN - PRODUTOS PRÓXIMOS\n")
        f.write("=" * 35 + "\n\n")
        f.write("DESAFIO: Produtos muito próximos na imagem\n")
        f.write("OBJETIVO: Detectar 1 garrafa + 3 latas Heineken\n\n")
        
        f.write(f"RESULTADO:\n")
        f.write(f"- Total detectado: {len(produtos)} produtos\n")
        f.write(f"- Garrafas: {garrafas}\n")
        f.write(f"- Latas verdes: {latas_verdes}\n")
        f.write(f"- Latas azuis: {latas_azuis}\n\n")
        
        f.write("ESTRATÉGIAS APLICADAS:\n")
        f.write("- Área mínima reduzida (3000px)\n")
        f.write("- Distância mínima reduzida (50px)\n")
        f.write("- Zoom conservador (máx 2.5x)\n")
        f.write("- Margem pequena (10px)\n")
        f.write("- Limpeza morfológica suave\n\n")
        
        f.write("PRODUTOS DETECTADOS:\n")
        for i, produto in enumerate(produtos, 1):
            f.write(f"{i}. {produto['tipo']}\n")
            f.write(f"   Área: {produto['area']:.0f}px\n")
            f.write(f"   Proporção: {produto['aspect_ratio']:.2f}\n")
            f.write(f"   Confiança: {produto['confianca']:.2f}\n")
            f.write(f"   Centro: {produto['centro']}\n\n")
        
        if len(produtos) == 4 and garrafas == 1 and (latas_verdes + latas_azuis) == 3:
            f.write("✅ SUCESSO: Detectou corretamente todos os produtos Heineken\n")
        else:
            f.write("⚠️ AJUSTE NECESSÁRIO: Detecção não ideal para produtos próximos\n")
    
    try:
        os.startfile(os.path.abspath(pasta_resultado))
        print("📂 Pasta de resultados aberta!")
    except:
        pass

if __name__ == "__main__":
    main()