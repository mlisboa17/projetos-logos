import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Configurações
IMAGEM_ORIGINAL = "imagens_teste/corona_produtos.jpeg"
FATOR_LUMINOSIDADE = 0.8

print("=" * 60)
print("🚀 PROCESSAMENTO CONSERVADOR + OCR")
print("=" * 60)

# Criar pasta de resultados
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = Path(f'resultado_completo_{timestamp}')
output_dir.mkdir(exist_ok=True)

print(f"📁 Pasta: {output_dir.absolute()}")

# ETAPA 1: Carregar imagem
print(f"\n📥 ETAPA 1: CARREGAMENTO")
img_original = cv2.imread(IMAGEM_ORIGINAL)
altura, largura = img_original.shape[:2]
print(f"✓ Imagem: {largura}x{altura}")

# Salvar original
cv2.imwrite(str(output_dir / '01_original.jpg'), img_original)

# ETAPA 2: Remoção de fundo conservadora
print(f"\n🎭 ETAPA 2: REMOÇÃO DE FUNDO CONSERVADORA")

# Detectar bordas
gray = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 30, 100)

# Dilatar bordas
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
edges_dilated = cv2.dilate(edges, kernel, iterations=2)

# Encontrar contornos
contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Criar máscara
mask_contours = np.zeros(gray.shape, dtype=np.uint8)
area_minima = (altura * largura) * 0.001
contornos_validos = [c for c in contours if cv2.contourArea(c) > area_minima]

print(f"✓ {len(contornos_validos)} contornos de produtos encontrados")

# Preencher contornos
cv2.fillPoly(mask_contours, contornos_validos, 255)

# Expandir máscara (MUITO conservador)
kernel_expand = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
mask_expanded = cv2.dilate(mask_contours, kernel_expand, iterations=3)

# Suavizar bordas
mask_smooth = cv2.GaussianBlur(mask_expanded, (21, 21), 0)
mask_norm = mask_smooth.astype(np.float32) / 255.0

# Aplicar máscara com fundo cinza claro
fundo = np.full_like(img_original, (240, 240, 240), dtype=np.uint8)
img_result = img_original.astype(np.float32)
fundo_float = fundo.astype(np.float32)

for c in range(3):
    img_result[:, :, c] = (img_result[:, :, c] * mask_norm + 
                         fundo_float[:, :, c] * (1 - mask_norm))

img_sem_fundo = img_result.astype(np.uint8)

# Salvar
cv2.imwrite(str(output_dir / '02_fundo_removido.jpg'), img_sem_fundo)
print(f"✓ Fundo removido preservando produtos")

# ETAPA 3: Melhoria de qualidade
print(f"\n✨ ETAPA 3: MELHORIA DE QUALIDADE")

# Ajustar luminosidade e contraste
lab = cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2LAB)
l_channel, a_channel, b_channel = cv2.split(lab)

# Reduzir luminosidade
l_channel_reduced = cv2.multiply(l_channel, FATOR_LUMINOSIDADE)

# CLAHE
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
l_channel_clahe = clahe.apply(l_channel_reduced.astype(np.uint8))

img_clahe = cv2.merge([l_channel_clahe, a_channel, b_channel])
img_clahe = cv2.cvtColor(img_clahe, cv2.COLOR_LAB2BGR)

# Redução de ruído suave
img_denoised = cv2.GaussianBlur(img_clahe, (3, 3), 0)

# Sharpening controlado
kernel_sharp = np.array([[-0.5, -0.5, -0.5],
                        [-0.5,  5.0, -0.5],
                        [-0.5, -0.5, -0.5]], dtype=np.float32)
img_sharp = cv2.filter2D(img_denoised, -1, kernel_sharp)

# Misturar com original (70% processada + 30% original)
img_final = cv2.addWeighted(img_sharp, 0.7, img_denoised, 0.3, 0)

# Salvar resultado do processamento
cv2.imwrite(str(output_dir / '03_processada_final.jpg'), img_final)
print(f"✓ Qualidade melhorada (luminosidade: {FATOR_LUMINOSIDADE*100:.0f}%)")

# ETAPA 4: OCR
print(f"\n📖 ETAPA 4: OCR PARA RECONHECIMENTO")

try:
    import pytesseract
    print(f"✓ Tesseract disponível")
    
    # Preparar para OCR
    gray_ocr = cv2.cvtColor(img_final, cv2.COLOR_BGR2GRAY)
    clahe_ocr = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_ocr = clahe_ocr.apply(gray_ocr)
    
    # Sharpening para texto
    kernel_text = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
    sharpened_ocr = cv2.filter2D(enhanced_ocr, -1, kernel_text)
    
    # Salvar imagem para OCR
    cv2.imwrite(str(output_dir / '04_preparada_ocr.jpg'), sharpened_ocr)
    
    # Configuração Tesseract
    config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%°.'
    
    # Executar OCR
    texto_completo = pytesseract.image_to_string(sharpened_ocr, config=config, lang='por+eng')
    linhas = [linha.strip() for linha in texto_completo.split('\n') if linha.strip() and len(linha.strip()) > 2]
    
    print(f"\n📝 TEXTOS ENCONTRADOS ({len(linhas)} linhas):")
    
    # Marcas conhecidas
    marcas = {
        'CORONA': ['corona', 'coronita'],
        'HEINEKEN': ['heineken'],
        'SKOL': ['skol'],
        'BRAHMA': ['brahma'], 
        'ANTARCTICA': ['antarctica'],
        'STELLA': ['stella', 'artois'],
        'BUDWEISER': ['budweiser', 'bud'],
        'DEVASSA': ['devassa'],
        'ORIGINAL': ['original']
    }
    
    textos_encontrados = []
    produtos_identificados = []
    
    for i, linha in enumerate(linhas, 1):
        textos_encontrados.append(linha)
        print(f"[{i:2d}] \"{linha}\"")
        
        # Verificar produtos
        linha_lower = linha.lower()
        for marca, variantes in marcas.items():
            for variante in variantes:
                if variante in linha_lower:
                    produtos_identificados.append({
                        'marca': marca,
                        'texto_original': linha,
                        'variante_encontrada': variante
                    })
                    print(f"     🎯 {marca} DETECTADO!")
                    break
    
    # Contagem de produtos
    print(f"\n📊 RESUMO:")
    print(f"   Total de textos: {len(textos_encontrados)}")
    print(f"   Produtos identificados: {len(produtos_identificados)}")
    
    if produtos_identificados:
        print(f"\n🏷️  PRODUTOS ENCONTRADOS:")
        produtos_contagem = {}
        for produto in produtos_identificados:
            marca = produto['marca']
            produtos_contagem[marca] = produtos_contagem.get(marca, 0) + 1
        
        for marca, count in produtos_contagem.items():
            print(f"   - {marca}: {count}x")
    else:
        print(f"   - Nenhum produto conhecido identificado")
    
    # Salvar resultados JSON
    resultado = {
        'textos_encontrados': textos_encontrados,
        'produtos_identificados': produtos_identificados,
        'total_textos': len(textos_encontrados),
        'total_produtos': len(produtos_identificados),
        'contagem_produtos': produtos_contagem if produtos_identificados else {},
        'configuracao': {
            'luminosidade': FATOR_LUMINOSIDADE,
            'imagem_original': IMAGEM_ORIGINAL
        }
    }
    
    with open(output_dir / '04_resultado_ocr.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultado salvo: 04_resultado_ocr.json")
    
except ImportError:
    print(f"✗ Tesseract não disponível")
    print(f"  Execute: pip install pytesseract")
    print(f"  Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
except Exception as e:
    print(f"✗ Erro no OCR: {str(e)}")

# Salvar resultado final
cv2.imwrite(str(output_dir / '99_resultado_final.jpg'), img_final)

print(f"\n🎯 PROCESSAMENTO CONCLUÍDO!")
print(f"📁 Todos os arquivos em: {output_dir.absolute()}")

# Abrir resultado final
try:
    import os
    os.startfile(str(output_dir / '99_resultado_final.jpg'))
    print(f"👁️  Resultado aberto!")
except:
    print(f"📁 Abra manualmente: 99_resultado_final.jpg")

print("=" * 60)