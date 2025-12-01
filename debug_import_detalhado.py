#!/usr/bin/env python
"""Debug avançado para verificar por que não importa"""
import django
import os
from pathlib import Path
import json
import shutil
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.contrib.auth import get_user_model

User = get_user_model()

pasta = Path(r'C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\Produtos_MarcaHeineken\exportacao_20251129_091414')

arquivo_json = pasta / 'dados_exportacao.json'
with open(arquivo_json) as f:
    dados = json.load(f)

usuario_nome = dados.get('usuario', 'Funcionario') or 'Funcionario'
imagens = dados.get('imagens', [])

print(f"Usuario: {usuario_nome}")
print(f"Total imagens no JSON: {len(imagens)}")

if not imagens:
    print("Nenhuma imagem no JSON!")
else:
    usuario, created = User.objects.get_or_create(
        username=usuario_nome.lower().replace(' ', '_'),
        defaults={'first_name': usuario_nome, 'is_active': True}
    )
    print(f"Usuario criado: {created}, ID: {usuario.id}")
    
    media_dir = Path('media/produtos/anotacoes')
    media_dir.mkdir(parents=True, exist_ok=True)
    
    importadas = 0
    anotacoes_total = 0
    
    for i, img_data in enumerate(imagens):
        print(f"\n--- Imagem {i+1} ---")
        print(f"Arquivo: {img_data['arquivo']}")
        
        arquivo_origem = pasta / 'imagens' / img_data['arquivo']
        print(f"Origem existe: {arquivo_origem.exists()}")
        
        if not arquivo_origem.exists():
            print("PULANDO: arquivo não existe")
            continue
        
        data_pasta = datetime.now().strftime('%Y/%m/%d')
        destino_dir = media_dir / data_pasta
        destino_dir.mkdir(parents=True, exist_ok=True)
        
        arquivo_destino = destino_dir / img_data['arquivo']
        print(f"Destino: {arquivo_destino}")
        print(f"Destino existe: {arquivo_destino.exists()}")
        
        if not arquivo_destino.exists():
            print("Copiando...")
            shutil.copy2(arquivo_origem, arquivo_destino)
        
        caminho_relativo = f"produtos/anotacoes/{data_pasta}/{img_data['arquivo']}"
        print(f"Caminho relativo: {caminho_relativo}")
        
        ja_existe = ImagemAnotada.objects.filter(imagem=caminho_relativo).exists()
        print(f"Já existe no DB: {ja_existe}")
        
        if ja_existe:
            print("PULANDO: já importada")
            continue
        
        print("Criando registro...")
        imagem_anotada = ImagemAnotada.objects.create(
            imagem=caminho_relativo,
            enviado_por=usuario,
            observacoes=img_data.get('observacoes', ''),
            status='concluida',
            total_anotacoes=len(img_data.get('anotacoes', []))
        )
        print(f"ImagemAnotada criada: ID {imagem_anotada.id}")
        
        anotacoes = img_data.get('anotacoes', [])
        print(f"Anotações: {len(anotacoes)}")
        
        for j, anotacao_data in enumerate(anotacoes):
            produto_id = anotacao_data['produto_id']
            print(f"  Anotação {j+1}: produto_id={produto_id}")
            
            try:
                produto = ProdutoMae.objects.get(id=produto_id)
                print(f"    Produto encontrado: {produto.descricao_produto}")
                
                AnotacaoProduto.objects.create(
                    imagem_anotada=imagem_anotada,
                    produto=produto,
                    bbox_x=anotacao_data['x'],
                    bbox_y=anotacao_data['y'],
                    bbox_width=anotacao_data['width'],
                    bbox_height=anotacao_data['height']
                )
                anotacoes_total += 1
                print(f"    ✅ Anotação criada")
                
            except ProdutoMae.DoesNotExist:
                print(f"    ❌ Produto não encontrado!")
        
        importadas += 1

print(f"\n\nRESULTADO FINAL: {importadas} imagens, {anotacoes_total} anotações")
