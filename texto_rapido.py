import cv2
import os
import numpy as np

def main():
    # Encontra imagem
    pastas = [d for d in os.listdir('.') if d.startswith('processamento_completo_')]
    if not pastas:
        print("Sem pasta de processamento")
        return
    
    pasta = sorted(pastas)[-1]
    img_path = os.path.join(pasta, '01_preprocessamento_final.jpg')
    
    if not os.path.exists(img_path):
        print("Imagem não encontrada")
        return
    
    # Carrega imagem
    img = cv2.imread(img_path)
    print(f"Imagem: {img.shape}")
    
    # Converte para cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Melhora contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Detecta bordas para texto
    edges = cv2.Canny(enhanced, 50, 150)
    
    # Morfologia para conectar letras
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # Encontra contornos
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtra por tamanho
    text_regions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 10 and w < 300 and h < 100:
            area = cv2.contourArea(cnt)
            if area > 200:
                text_regions.append((x, y, w, h, area))
    
    print(f"Regiões de texto encontradas: {len(text_regions)}")
    
    # Desenha regiões
    result = img.copy()
    for i, (x, y, w, h, area) in enumerate(text_regions):
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(result, f"T{i+1}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        print(f"  Região {i+1}: {w}x{h} px, área={area}")
    
    # Salva resultado
    os.makedirs('texto_rapido', exist_ok=True)
    cv2.imwrite('texto_rapido/regioes_texto.jpg', result)
    print("Salvo: texto_rapido/regioes_texto.jpg")

if __name__ == "__main__":
    main()