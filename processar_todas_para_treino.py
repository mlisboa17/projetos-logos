#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para remover fundo de TODAS as imagens e vincular ao banco de dados
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

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import ImagemProcessada

def detectar_cor_fundo(imagem_pil):
    """Detecta a cor de fundo analisando os cantos da imagem"""
    img_array = np.array(imagem_pil)
    
    altura, largura = img_array.shape[:2]
    tamanho_canto = max(int(min(altura, largura) * 0.1), 5)
    
    # Coletar pixels dos 4 cantos
    cantos = []
    cantos.append(img_array[:tamanho_canto, :tamanho_canto])
    cantos.append(img_array[:tamanho_canto, -tamanho_canto:])
    cantos.append(img_array[-tamanho_canto:, :tamanho_canto])
    cantos.append(img_array[-tamanho_canto:, -tamanho_canto:])
    
    pixels_cantos = np.vstack(cantos).reshape(-1, img_array.shape[2] if len(img_array.shape) > 2 else 1)
    cor_fundo = np.median(pixels_cantos, axis=0).astype(np.uint8)
    
    return cor_fundo

def remover_fundo_imagem(caminho_imagem):
    """Remove o fundo de uma imagem"""
    try:
        imagem = Image.open(caminho_imagem).convert('RGB')
        cor_fundo = detectar_cor_fundo(imagem)
        imagem_rgba = imagem.convert('RGBA')
        dados = np.array(imagem_rgba)
        rgb_dados = dados[:, :, :3]
        cor_fundo_rgb = cor_fundo[:3] if len(cor_fundo) >= 3 else cor_fundo
        tolerancia = 30
        mascara = np.all(np.abs(rgb_dados.astype(int) - cor_fundo_rgb.astype(int)) < tolerancia, axis=2)
        dados[mascara, 3] = 0
        imagem_final = Image.fromarray(dados, 'RGBA')
        return imagem_final
    except Exception as e:
        print(f"    ❌ Erro: {str(e)}")
        return None

def processar_todas_imagens():
    """Processa TODAS as imagens e vincula ao banco de dados"""
    
    print("\n" + "=" * 80)
    print("✂️  PROCESSANDO TODAS AS IMAGENS PARA TREINO")
    print("=" * 80 + "\n")
    
    pasta_saida = Path("media/processadas_sem_fundo")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    produtos = ProdutoMae.objects.filter(ativo=True).order_by('id')
    total_produtos = produtos.count()
    
    processadas = 0
    vinculadas = 0
    erros = 0
    
    for idx, produto in enumerate(produtos, 1):
        imagens = ImagemProduto.objects.filter(produto=produto).order_by('id')
        
        if not imagens.exists():
            continue
        
        percentual = (idx / total_produtos) * 100
        print(f"[{idx}/{total_produtos}] {produto.descricao_produto[:40]:40} ({imagens.count()} imgs) - {percentual:.1f}%")
        
        for idx_imagem, imagem in enumerate(imagens, 1):
            try:
                caminho_original = imagem.imagem.path
                
                if not os.path.exists(caminho_original):
                    continue
                
                # Verificar se já foi processada
                ja_processada = ImagemProcessada.objects.filter(
                    imagem_original=imagem,
                    tipo_processamento='fundo_removido'
                ).exists()
                
                if ja_processada:
                    print(f"  ✓ {os.path.basename(caminho_original)} (já processada)")
                    continue
                
                # Remover fundo
                imagem_sem_fundo = remover_fundo_imagem(caminho_original)
                
                if imagem_sem_fundo:
                    nome_arquivo = f"prod_{produto.id:04d}_{idx_imagem:04d}_sem_fundo.png"
                    caminho_saida = pasta_saida / nome_arquivo
                    imagem_sem_fundo.save(caminho_saida, 'PNG')
                    
                    # Vincular ao banco
                    ImagemProcessada.objects.create(
                        imagem_original=imagem,
                        imagem_processada=f'processadas_sem_fundo/{nome_arquivo}',
                        tipo_processamento='fundo_removido',
                        descricao=f'Removido automaticamente - {os.path.basename(caminho_original)}'
                    )
                    
                    print(f"  ✂️  {os.path.basename(caminho_original)}")
                    processadas += 1
                    vinculadas += 1
                else:
                    erros += 1
                    
            except Exception as e:
                print(f"  ❌ Erro: {str(e)}")
                erros += 1
    
    print("\n" + "=" * 80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("=" * 80)
    print(f"✂️  Processadas: {processadas}")
    print(f"🔗 Vinculadas: {vinculadas}")
    print(f"❌ Erros: {erros}")
    if processadas > 0:
        taxa = (processadas / (processadas + erros)) * 100 if (processadas + erros) > 0 else 0
        print(f"📊 Taxa: {taxa:.1f}%")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    processar_todas_imagens()
