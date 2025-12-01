"""
Script para remover fundo das imagens usando rembg
Processa imagens de produtos para treinamento de IA
"""

import os
from pathlib import Path
from PIL import Image
from rembg import remove
from tqdm import tqdm
import shutil

# Configurações
PASTA_ORIGEM = "assets/dataset_augmented"
PASTA_DESTINO = "assets/dataset_sem_fundo"

def remover_fundo_imagem(caminho_entrada, caminho_saida):
    """Remove o fundo de uma imagem e salva"""
    try:
        with open(caminho_entrada, 'rb') as f:
            input_data = f.read()
        
        # Remover fundo
        output_data = remove(input_data)
        
        # Salvar como PNG (para preservar transparência)
        with open(caminho_saida, 'wb') as f:
            f.write(output_data)
        
        return True
    except Exception as e:
        print(f"Erro em {caminho_entrada}: {e}")
        return False

def processar_pasta(pasta_produto):
    """Processa todas as imagens de uma pasta de produto"""
    nome_produto = pasta_produto.name
    pasta_saida = Path(PASTA_DESTINO) / nome_produto
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    # Listar imagens
    extensoes = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    imagens = [f for f in pasta_produto.iterdir() if f.suffix.lower() in extensoes]
    
    if not imagens:
        print(f"  ⚠️ Nenhuma imagem em {nome_produto}")
        return 0, 0
    
    sucesso = 0
    falha = 0
    
    for img in tqdm(imagens, desc=f"  {nome_produto[:30]}", leave=False):
        # Salvar como PNG para manter transparência
        nome_saida = img.stem + "_sem_fundo.png"
        caminho_saida = pasta_saida / nome_saida
        
        if remover_fundo_imagem(str(img), str(caminho_saida)):
            sucesso += 1
        else:
            falha += 1
    
    return sucesso, falha

def main():
    print("=" * 60)
    print("🎨 REMOVEDOR DE FUNDO - rembg")
    print("=" * 60)
    
    pasta_origem = Path(PASTA_ORIGEM)
    
    if not pasta_origem.exists():
        print(f"❌ Pasta não encontrada: {PASTA_ORIGEM}")
        return
    
    # Criar pasta de destino
    Path(PASTA_DESTINO).mkdir(parents=True, exist_ok=True)
    
    # Listar pastas de produtos
    pastas_produtos = [p for p in pasta_origem.iterdir() if p.is_dir()]
    
    print(f"\n📁 Encontradas {len(pastas_produtos)} pastas de produtos")
    print(f"📂 Origem: {PASTA_ORIGEM}")
    print(f"📂 Destino: {PASTA_DESTINO}")
    print()
    
    # Perguntar quais processar
    print("Pastas disponíveis:")
    for i, p in enumerate(pastas_produtos):
        qtd = len([f for f in p.iterdir() if f.is_file()])
        print(f"  {i+1}. {p.name} ({qtd} arquivos)")
    
    print()
    escolha = input("Digite os números das pastas (ex: 1,3,5) ou 'todas': ").strip()
    
    if escolha.lower() == 'todas':
        pastas_selecionadas = pastas_produtos
    else:
        try:
            indices = [int(x.strip()) - 1 for x in escolha.split(',')]
            pastas_selecionadas = [pastas_produtos[i] for i in indices if 0 <= i < len(pastas_produtos)]
        except:
            print("❌ Entrada inválida")
            return
    
    print(f"\n🚀 Processando {len(pastas_selecionadas)} pasta(s)...\n")
    
    total_sucesso = 0
    total_falha = 0
    
    for pasta in pastas_selecionadas:
        print(f"📦 {pasta.name}")
        sucesso, falha = processar_pasta(pasta)
        total_sucesso += sucesso
        total_falha += falha
        print(f"   ✅ {sucesso} | ❌ {falha}")
    
    print()
    print("=" * 60)
    print(f"✅ CONCLUÍDO!")
    print(f"   Sucesso: {total_sucesso} imagens")
    print(f"   Falhas: {total_falha} imagens")
    print(f"   Salvas em: {PASTA_DESTINO}")
    print("=" * 60)

if __name__ == "__main__":
    main()
