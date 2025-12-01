#!/usr/bin/env python
"""
Script simples de teste - processa 10 imagens
"""
import django
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from acessorios.processador import ProcessadorImagensGenerico
from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemAnotada

print("Buscando imagens não anotadas...")

anotadas = set()
for img_anotada in ImagemAnotada.objects.all():
    anotadas.add(img_anotada.imagem)

queryset = ImagemProduto.objects.filter(ativa=True).exclude(imagem__in=anotadas)[:10]

caminhos = []
for img in queryset:
    try:
        caminho = Path(f'media/{img.imagem}')
        if caminho.exists():
            caminhos.append(str(caminho))
            print(f"  ✓ {caminho.name}")
    except:
        pass

print(f"\nTotal encontradas: {len(caminhos)}")

if caminhos:
    print("\nIniciando processamento de fundo...")
    processador = ProcessadorImagensGenerico()
    
    for i, caminho in enumerate(caminhos, 1):
        try:
            nome_saida = f"teste_{i}.png"
            print(f"{i}. Processando {Path(caminho).name}...", end=" ")
            resultado = processador.remover_fundo(caminho, nome_saida)
            print(f"✓ {nome_saida}")
        except Exception as e:
            print(f"✗ Erro: {str(e)[:50]}")

print("\nDone!")
