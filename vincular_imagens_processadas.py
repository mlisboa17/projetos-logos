#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para vincular as imagens já processadas ao banco de dados
"""

import os
import sys
import django
from pathlib import Path
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
sys.path.insert(0, str(Path(__file__).parent))
django.setup()

from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemProcessada

def vincular_imagens_processadas():
    """Vincula as imagens já processadas ao banco de dados"""
    
    print("\n" + "=" * 80)
    print("🔗 VINCULANDO IMAGENS JÁ PROCESSADAS AO BANCO DE DADOS")
    print("=" * 80 + "\n")
    
    pasta_processadas = Path("media/processadas_sem_fundo")
    
    # Listar todas as imagens processadas
    imagens_processadas = list(pasta_processadas.glob("*.png"))
    
    if not imagens_processadas:
        print("❌ Nenhuma imagem processada encontrada!")
        return
    
    print(f"📊 Encontradas {len(imagens_processadas)} imagens processadas\n")
    
    vinculadas = 0
    erros = 0
    ja_existentes = 0
    
    # Mapear imagens originais por produto
    for arquivo_processado in sorted(imagens_processadas):
        try:
            # Extrair ID do produto do nome do arquivo
            # Formato: prod_XXXX_YYYY_sem_fundo.png
            match = re.match(r'prod_(\d+)_(\d+)_sem_fundo\.png', arquivo_processado.name)
            
            if not match:
                print(f"⚠️  Formato inválido: {arquivo_processado.name}")
                continue
            
            prod_id = int(match.group(1))
            idx_imagem = int(match.group(2))
            
            # Buscar todas as imagens do produto
            imagens_produto = ImagemProduto.objects.filter(produto_id=prod_id).order_by('id')
            
            if idx_imagem > imagens_produto.count():
                print(f"⚠️  Índice {idx_imagem} fora do intervalo para produto {prod_id}")
                continue
            
            # Pegar a imagem na posição correta
            imagem_original = imagens_produto[idx_imagem - 1]
            
            # Caminho relativo
            caminho_relativo = f'processadas_sem_fundo/{arquivo_processado.name}'
            
            # Verificar se já existe
            anotada_existente = ImagemProcessada.objects.filter(
                imagem_original=imagem_original,
                tipo_processamento='fundo_removido'
            ).first()
            
            if anotada_existente:
                print(f"✅ prod_{prod_id:04d}_{idx_imagem:04d} (já vinculado)")
                ja_existentes += 1
                continue
            
            # Criar vínculo no banco de dados
            ImagemProcessada.objects.create(
                imagem_original=imagem_original,
                imagem_processada=caminho_relativo,
                tipo_processamento='fundo_removido',
                descricao=f'Fundo removido automaticamente de {imagem_original.imagem.name}'
            )
            
            print(f"🔗 prod_{prod_id:04d}_{idx_imagem:04d} → Vinculado!")
            vinculadas += 1
            
        except Exception as e:
            print(f"❌ Erro ao vincular {arquivo_processado.name}: {str(e)}")
            erros += 1
    
    # Resumo
    print("\n" + "=" * 80)
    print("✅ VINCULAÇÃO CONCLUÍDA")
    print("=" * 80)
    print(f"🔗 Vinculadas: {vinculadas}")
    print(f"⏭️  Já existentes: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total: {vinculadas + ja_existentes}/{len(imagens_processadas)}")
    print("=" * 80 + "\n")
    print("🎉 Concluído!\n")

if __name__ == "__main__":
    vincular_imagens_processadas()
