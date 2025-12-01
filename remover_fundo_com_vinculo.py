#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para remover fundo de TODAS as imagens e VINCULAR ao banco de dados
"""

import os
import sys
import django
from pathlib import Path
from PIL import Image
import numpy as np

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
sys.path.insert(0, str(Path(__file__).parent))
django.setup()

from logos_app.models import ImagemProduto, ProdutoMae, ImagemAnotada

def detectar_cor_fundo(imagem_pil):
    """Detecta a cor de fundo analisando os cantos da imagem"""
    img_array = np.array(imagem_pil)
    
    altura, largura = img_array.shape[:2]
    tamanho_canto = max(int(min(altura, largura) * 0.1), 5)
    
    # Coletar pixels dos 4 cantos
    cantos = []
    cantos.append(img_array[:tamanho_canto, :tamanho_canto])  # Topo-esquerdo
    cantos.append(img_array[:tamanho_canto, -tamanho_canto:])  # Topo-direito
    cantos.append(img_array[-tamanho_canto:, :tamanho_canto])  # Baixo-esquerdo
    cantos.append(img_array[-tamanho_canto:, -tamanho_canto:])  # Baixo-direito
    
    # Concatenar e pegar a cor média
    pixels_cantos = np.vstack(cantos).reshape(-1, img_array.shape[2] if len(img_array.shape) > 2 else 1)
    cor_fundo = np.median(pixels_cantos, axis=0).astype(np.uint8)
    
    return cor_fundo

def remover_fundo_imagem(caminho_imagem):
    """Remove o fundo de uma imagem usando detecção de cantos"""
    try:
        # Abrir imagem
        imagem = Image.open(caminho_imagem).convert('RGB')
        
        # Detectar cor de fundo
        cor_fundo = detectar_cor_fundo(imagem)
        
        # Converter para RGBA
        imagem_rgba = imagem.convert('RGBA')
        dados = np.array(imagem_rgba)
        
        # Criar máscara
        rgb_dados = dados[:, :, :3]
        cor_fundo_rgb = cor_fundo[:3] if len(cor_fundo) >= 3 else cor_fundo
        
        # Tolerância de cor
        tolerancia = 30
        mascara = np.all(np.abs(rgb_dados.astype(int) - cor_fundo_rgb.astype(int)) < tolerancia, axis=2)
        
        # Aplicar transparência
        dados[mascara, 3] = 0
        
        # Converter de volta para PIL
        imagem_final = Image.fromarray(dados, 'RGBA')
        
        return imagem_final
    except Exception as e:
        print(f"    ❌ Erro ao processar {caminho_imagem}: {str(e)}")
        return None

def processar_e_vincular():
    """Processa todas as imagens e vincula ao banco de dados"""
    
    print("\n" + "=" * 80)
    print("✂️  REMOVE FUNDO E VINCULA AO BANCO DE DADOS")
    print("=" * 80 + "\n")
    
    # Criar pasta de saída
    pasta_saida = Path("media/processadas_sem_fundo")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    # Buscar todos os produtos com imagens
    produtos = ProdutoMae.objects.filter(ativo=True).order_by('id')
    
    processadas = 0
    erros = 0
    vinculadas = 0
    
    # Processar cada produto
    for idx, produto in enumerate(produtos, 1):
        # Buscar imagens do produto
        imagens = ImagemProduto.objects.filter(produto_mae=produto)
        
        if not imagens.exists():
            continue
        
        percentual = (idx / produtos.count()) * 100
        print(f"[{idx}/{produtos.count()}] {produto.descricao_produto[:40]:40} - {percentual:.1f}%")
        
        # Processar cada imagem do produto
        for idx_imagem, imagem in enumerate(imagens, 1):
            try:
                # Caminho da imagem original
                caminho_original = imagem.imagem.path
                
                if not os.path.exists(caminho_original):
                    print(f"  ⚠️  Arquivo não encontrado: {caminho_original}")
                    continue
                
                # Remover fundo
                imagem_sem_fundo = remover_fundo_imagem(caminho_original)
                
                if imagem_sem_fundo:
                    # Salvar com novo nome
                    nome_arquivo = f"prod_{produto.id:04d}_{idx_imagem:04d}_sem_fundo.png"
                    caminho_saida = pasta_saida / nome_arquivo
                    
                    imagem_sem_fundo.save(caminho_saida, 'PNG')
                    
                    # Salvar no banco de dados como ImagemAnotada
                    imagem_anotada, created = ImagemAnotada.objects.get_or_create(
                        imagem_original=imagem,
                        defaults={
                            'imagem_anotada': f'processadas_sem_fundo/{nome_arquivo}',
                            'tipo_anotacao': 'fundo_removido',
                            'descricao': f'Fundo removido automaticamente - {os.path.basename(caminho_original)}'
                        }
                    )
                    
                    if created:
                        print(f"  ✂️  {os.path.basename(caminho_original)} → vinculado ao BD")
                        vinculadas += 1
                    else:
                        print(f"  ✂️  {os.path.basename(caminho_original)} (já existia)")
                    
                    processadas += 1
                else:
                    erros += 1
                    
            except Exception as e:
                print(f"  ❌ Erro: {str(e)}")
                erros += 1
    
    # Resumo
    print("\n" + "=" * 80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("=" * 80)
    print(f"✂️  Fundos removidos: {processadas}")
    print(f"🔗 Vinculadas ao BD: {vinculadas}")
    print(f"❌ Erros: {erros}")
    print(f"📁 Salvas em: {pasta_saida}")
    if processadas > 0:
        taxa_sucesso = (processadas / (processadas + erros)) * 100
        print(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
    print("=" * 80 + "\n")
    print("🎉 Concluído!\n")

if __name__ == "__main__":
    processar_e_vincular()
