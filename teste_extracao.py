import os
import cv2

def main():
    print("=== TESTE DE LEITURA DE RÓTULO ===")
    
    # Caminho da foto
    caminho_foto = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    # 1. Verificar arquivo
    if os.path.exists(caminho_foto):
        size = os.path.getsize(caminho_foto)
        print(f"✅ Arquivo encontrado: {size} bytes")
    else:
        print("❌ Arquivo não encontrado")
        return
    
    # 2. Carregar imagem
    img = cv2.imread(caminho_foto)
    if img is not None:
        h, w = img.shape[:2] 
        print(f"✅ Imagem carregada: {w}x{h}")
    else:
        print("❌ Erro ao carregar imagem")
        return
    
    # 3. Extrair região do produto (baseado na detecção anterior)
    x1, y1, x2, y2 = 217, 55, 696, 1029
    produto = img[y1:y2, x1:x2]
    
    if produto.size > 0:
        print(f"✅ Produto extraído: {produto.shape}")
        cv2.imwrite("produto_completo.jpg", produto)
        print("💾 Salvo: produto_completo.jpg")
    else:
        print("❌ Erro ao extrair produto")
        return
    
    # 4. Focar no rótulo (parte superior central)
    altura_prod = y2 - y1
    largura_prod = x2 - x1
    
    # Região do rótulo (onde geralmente fica a marca)
    x1_rot = int(largura_prod * 0.15)  # 15% da esquerda
    y1_rot = int(altura_prod * 0.15)   # 15% do topo
    x2_rot = int(largura_prod * 0.85)  # 85% da direita
    y2_rot = int(altura_prod * 0.6)    # 60% da altura (metade superior)
    
    rotulo = produto[y1_rot:y2_rot, x1_rot:x2_rot]
    
    if rotulo.size > 0:
        print(f"✅ Rótulo extraído: {rotulo.shape}")
        cv2.imwrite("rotulo_marca.jpg", rotulo)
        print("💾 Salvo: rotulo_marca.jpg")
    else:
        print("❌ Erro ao extrair rótulo")
        return
    
    print("\n🎯 ARQUIVOS GERADOS:")
    print("  - produto_completo.jpg (produto inteiro)")
    print("  - rotulo_marca.jpg (região da marca)")
    print("\n👁️  EXAMINE os arquivos para ver se a região está correta!")

if __name__ == "__main__":
    main()