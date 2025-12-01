#!/usr/bin/env python
"""Debug script para verificar import"""
import django
import os
from pathlib import Path
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from importar_coletas import passo1_importar_pasta

pasta = Path(r'C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\Produtos_MarcaHeineken\exportacao_20251129_091414')
print(f'Pasta existe: {pasta.exists()}')

arquivo_json = pasta / 'dados_exportacao.json'
print(f'JSON existe: {arquivo_json.exists()}')

with open(arquivo_json) as f:
    dados = json.load(f)
    print(f'Imagens no JSON: {len(dados["imagens"])}')
    
    for img in dados['imagens']:
        arquivo = pasta / 'imagens' / img['arquivo']
        print(f'  {img["arquivo"]}: {arquivo.exists()}')

# Testar a função
print("\nTestando passo1_importar_pasta:")
try:
    result = passo1_importar_pasta(pasta)
    print(f'Resultado: {result}')
except Exception as e:
    print(f'Erro: {e}')
    import traceback
    traceback.print_exc()
