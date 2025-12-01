#!/usr/bin/env python
"""
Script para importar TODAS as pastas de Heineken automaticamente
"""
import django
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from importar_coletas import encontrar_pastas_exportacao, passo1_importar_pasta, passo2_importar_dataset

print("=" * 80)
print("🚀 IMPORTAÇÃO AUTOMÁTICA - TODAS AS PASTAS")
print("=" * 80)

# Buscar pastas
print("\n🔍 Buscando pastas com dados_exportacao.json...\n")

base_path = Path(r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\Produtos_MarcaHeineken")
pastas = encontrar_pastas_exportacao(base_path)

print(f"✅ Encontradas {len(pastas)} pastas:\n")

for i, pasta in enumerate(pastas, 1):
    nome_relativo = pasta.relative_to(base_path)
    print(f"  {i}. {nome_relativo}")

if len(pastas) == 0:
    print("❌ Nenhuma pasta encontrada!")
    sys.exit(1)

# Processar
print("\n" + "=" * 80)
print("📥 INICIANDO IMPORTAÇÃO")
print("=" * 80)

total_imagens = 0
total_anotacoes = 0

for i, pasta in enumerate(pastas, 1):
    nome_relativo = pasta.relative_to(base_path)
    print(f"\n{i}/{len(pastas)} - {nome_relativo}")
    print("-" * 80)
    
    try:
        # Passo 1: Importar para ImagemAnotada
        print("  Executando Passo 1 (ImagemAnotada)...")
        img_p1, anot_p1 = passo1_importar_pasta(pasta)
        print(f"    ✅ {img_p1} imagens, {anot_p1} anotações")
        
        total_imagens += img_p1
        total_anotacoes += anot_p1
        
    except Exception as e:
        print(f"  ❌ Erro: {str(e)[:80]}")

# Executar Passo 2 uma única vez no final
print("\n" + "=" * 80)
print("📥 EXECUTANDO PASSO 2 (Dataset de Treino)")
print("=" * 80)

try:
    print("  Processando todas as imagens anotadas...")
    img_p2, anot_p2 = passo2_importar_dataset()
    print(f"    ✅ {img_p2} imagens adicionadas ao dataset")
    
    total_imagens += img_p2
    total_anotacoes += anot_p2
except Exception as e:
    print(f"  ❌ Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
print("📊 RESUMO FINAL")
print("=" * 80)
print(f"✅ Pastas processadas: {len(pastas)}")
print(f"✅ Total de imagens importadas: {total_imagens}")
print(f"✅ Total de anotações: {total_anotacoes}")

print("\n🎉 Importação concluída!")
print("=" * 80)
