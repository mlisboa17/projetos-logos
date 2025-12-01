#!/usr/bin/env python3
"""
TESTE COM IMAGEM HEINEKEN
Usando detector genérico para produtos próximos
Cuidado com zoom - produtos muito próximos podem confundir
"""

import cv2
import numpy as np
import os
from datetime import datetime

def salvar_imagem_anexada():
    """Salva a imagem Heineken anexada pelo usuário"""
    # A imagem anexada deve ser salva manualmente ou via interface
    # Por enquanto, vamos usar uma imagem de teste se disponível
    
    possible_paths = [
        "imagens_teste/heineken_produtos.jpg",
        "imagens_teste/heineken.jpg", 
        "heineken_produtos.jpg",
        "produtos_heineken.jpg"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Encontrada imagem Heineken: {path}")
            return path
    
    print("⚠️ Imagem Heineken anexada deve ser salva manualmente em imagens_teste/")
    return None

def detectar_produtos_heineken_genericos(img):
    """
    Detecção genérica otimizada para produtos próximos
    Especial atenção para produtos Heineken que podem estar muito juntos
    """
    print("🍺 DETECÇÃO PRODUTOS PRÓXIMOS (Heineken)")
    print("⚠️ Cuidado especial: produtos muito próximos")
    
    # Converter para escala de cinza
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Aplicar blur mais suave para não perder separação entre produtos
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)  # Blur menor
    
    # Múltiplas técnicas com parâmetros ajustados para produtos próximos
    
    # 1. Threshold adaptativo (mais sensível)
    thresh1 = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 9, 3  # Janela menor, C maior
    )
    
    # 2. Otsu
    _, thresh2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 3. Canny (mais sensível para detectar bordas entre produtos próximos)
    edges = cv2.Canny(blurred, 30, 100)  # Thresholds menores
    
    # Combinar com pesos diferentes (priorizar Canny para separação)
    mask_produtos = cv2.bitwise_or(thresh1, thresh2)
    mask_produtos = cv2.bitwise_or(mask_produtos, edges)
    
    # Limpeza morfológica SUAVE (não perder separação)
    kernel_pequeno = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_OPEN, kernel_pequeno)
    
    # Salvar máscara para debug
    cv2.imwrite("debug_mask_heineken.jpg", mask_produtos)
    
    # Encontrar contornos
    contornos, _ = cv2.findContours(mask_produtos, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"   🔍 {len(contornos)} contornos encontrados")
    
    produtos_candidatos = []
    
    for i, contorno in enumerate(contornos):
        area = cv2.contourArea(contorno)
        
        # Área mínima menor para capturar produtos médios
        if area > 5000:  # Reduzido para produtos próximos
            x, y, w, h = cv2.boundingRect(contorno)
            aspect_ratio = w / float(h)
            
            # Filtros de tamanho (produtos Heineken são razoavelmente grandes)
            if w > 50 and h > 80:  # Largura e altura mínimas
                
                # Classificação por forma (mais flexível)
                if 0.25 < aspect_ratio < 0.75:  # Garrafas (mais altas)
                    tipo = "GARRAFA"
                elif 0.75 <= aspect_ratio <= 1.8:  # Latas (mais quadradas)
                    tipo = "LATA" 
                else:
                    tipo = "PRODUTO"
                
                # Confiança baseada em área e proporção
                conf_area = min(area / 30000, 1.0)
                conf_forma = 1.0 if 0.25 < aspect_ratio < 1.8 else 0.5
                confianca = (conf_area + conf_forma) / 2
                
                produtos_candidatos.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'tipo': tipo,
                    'confianca': confianca,
                    'centro': (x + w//2, y + h//2)
                })
                
                print(f"      ✅ Produto {len(produtos_candidatos)}: {tipo}, área {area:.0f}, ratio {aspect_ratio:.2f}")
    
    print(f"   📊 {len(produtos_candidatos)} produtos candidatos")
    
    # Remover sobreposições com cuidado especial para produtos próximos
    produtos_candidatos.sort(key=lambda x: x['area'], reverse=True)
    produtos_filtrados = []
    
    for produto in produtos_candidatos:
        x1, y1, w1, h1 = produto['bbox']
        centro1 = produto['centro']
        
        muito_proximo = False
        
        for aceito in produtos_filtrados:
            x2, y2, w2, h2 = aceito['bbox']
            centro2 = aceito['centro']
            
            # Distância entre centros
            distancia = np.sqrt((centro1[0] - centro2[0])**2 + (centro1[1] - centro2[1])**2)
            
            # Sobreposição
            overlap_x = max(0, min(x1+w1, x2+w2) - max(x1, x2))
            overlap_y = max(0, min(y1+h1, y2+h2) - max(y1, y2))
            overlap_area = overlap_x * overlap_y
            
            # Critério mais restritivo para produtos próximos
            if (overlap_area > 0.4 * min(produto['area'], aceito['area']) or 
                distancia < 80):  # Distância menor para produtos próximos
                muito_proximo = True
                break
        
        if not muito_proximo:
            produtos_filtrados.append(produto)
    
    # Estatísticas
    garrafas = [p for p in produtos_filtrados if p['tipo'] == 'GARRAFA']
    latas = [p for p in produtos_filtrados if p['tipo'] == 'LATA']
    outros = [p for p in produtos_filtrados if p['tipo'] == 'PRODUTO']
    
    print(f"   ✅ RESULTADO FINAL: {len(produtos_filtrados)} produtos")
    print(f"      🍺 Garrafas: {len(garrafas)}")
    print(f"      🥤 Latas: {len(latas)}")
    if outros:
        print(f"      📦 Outros: {len(outros)}")
    
    return produtos_filtrados

def desenhar_deteccoes_heineken(img, produtos):
    """Desenha as detecções na imagem Heineken"""
    img_debug = img.copy()
    
    cores_tipo = {
        'GARRAFA': (0, 255, 0),    # Verde
        'LATA': (255, 0, 0),       # Azul  
        'PRODUTO': (0, 165, 255)   # Laranja
    }
    
    for i, produto in enumerate(produtos):
        x, y, w, h = produto['bbox']
        tipo = produto['tipo']
        cor = cores_tipo.get(tipo, (128, 128, 128))
        
        # Desenhar retângulo
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), cor, 3)
        
        # Texto com informações
        texto = f"{tipo} {i+1}"
        cv2.putText(img_debug, texto, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
        
        # Informações adicionais
        info = f"A:{produto['area']:.0f}"
        cv2.putText(img_debug, info, (x, y+h+20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)
    
    return img_debug

def main():
    """Teste específico para imagem Heineken"""
    print("=" * 70)
    print("🍺 TESTE HEINEKEN: PRODUTOS PRÓXIMOS")
    print("⚠️ Desafio: produtos muito próximos podem confundir zoom")
    print("🎯 Esperado: 4 produtos Heineken (1 garrafa + 3 latas)")
    print("=" * 70)
    
    # Procurar imagem Heineken
    imagem_path = salvar_imagem_anexada()
    
    if imagem_path is None:
        print("❌ Imagem Heineken não encontrada")
        print("📝 Salve a imagem anexada como 'imagens_teste/heineken_produtos.jpg'")
        return
    
    # Criar pasta de teste
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_teste = f"teste_heineken_{timestamp}"
    os.makedirs(pasta_teste, exist_ok=True)
    
    print(f"📁 Pasta: {os.path.abspath(pasta_teste)}")
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar: {imagem_path}")
        return
    
    altura, largura = img.shape[:2]
    print(f"📏 Imagem: {largura}x{altura}")
    
    # Salvar original
    cv2.imwrite(os.path.join(pasta_teste, "00_original.jpg"), img)
    
    # Detecção específica para produtos próximos
    produtos = detectar_produtos_heineken_genericos(img)
    
    # Desenhar detecções
    img_resultado = desenhar_deteccoes_heineken(img, produtos)
    cv2.imwrite(os.path.join(pasta_teste, "01_deteccoes.jpg"), img_resultado)
    
    # Análise de resultado
    print(f"\n🎉 ANÁLISE HEINEKEN:")
    print(f"   🎯 Esperado: ~4 produtos Heineken")
    print(f"   ✅ Detectado: {len(produtos)} produtos")
    
    garrafas = [p for p in produtos if p['tipo'] == 'GARRAFA']
    latas = [p for p in produtos if p['tipo'] == 'LATA']
    
    if len(produtos) == 4:
        print(f"   🏆 EXCELENTE! Detectou exatamente 4 produtos")
        if len(garrafas) == 1 and len(latas) == 3:
            print(f"   🎯 PERFEITO! 1 garrafa + 3 latas = configuração Heineken ideal")
    elif 3 <= len(produtos) <= 5:
        print(f"   👍 BOM RESULTADO! Próximo do ideal")
    else:
        print(f"   🔧 PRECISA AJUSTE: muito diferente do esperado")
    
    # Relatório
    with open(os.path.join(pasta_teste, "relatorio_heineken.txt"), 'w', encoding='utf-8') as f:
        f.write("TESTE HEINEKEN: PRODUTOS PRÓXIMOS\n")
        f.write("=" * 35 + "\n\n")
        
        f.write("DESAFIO:\n")
        f.write("- Produtos Heineken muito próximos uns dos outros\n")
        f.write("- Zoom pode se perder entre objetos próximos\n")
        f.write("- Necessário detecção precisa de separação\n\n")
        
        f.write(f"RESULTADO:\n")
        f.write(f"- Total detectado: {len(produtos)} produtos\n")
        f.write(f"- Garrafas: {len(garrafas)}\n")
        f.write(f"- Latas: {len(latas)}\n\n")
        
        f.write("PRODUTOS DETECTADOS:\n")
        for i, produto in enumerate(produtos, 1):
            f.write(f"{i}. {produto['tipo']}\n")
            f.write(f"   Área: {produto['area']:.0f} pixels\n")
            f.write(f"   Proporção: {produto['aspect_ratio']:.2f}\n")
            f.write(f"   Confiança: {produto['confianca']:.2f}\n")
            f.write(f"   Posição: {produto['bbox']}\n\n")
        
        f.write("OBSERVAÇÕES:\n")
        f.write("- Produtos próximos requerem parâmetros de detecção ajustados\n")
        f.write("- Blur menor para preservar separação\n")
        f.write("- Canny mais sensível para detectar bordas\n")
        f.write("- Critério de sobreposição mais restritivo\n")
    
    print(f"\n📄 Relatório: relatorio_heineken.txt")
    
    try:
        os.startfile(os.path.abspath(pasta_teste))
        print("📂 Pasta aberta!")
    except:
        pass
    
    print(f"\n💡 DICA DE ZOOM:")
    print(f"   ⚠️ Com produtos tão próximos, zoom muito alto pode cortar")
    print(f"   ✅ Recomenda-se zoom moderado (1.5x) para manter contexto")
    print(f"   🔍 Zoom individual só após separação bem-sucedida")

if __name__ == "__main__":
    main()