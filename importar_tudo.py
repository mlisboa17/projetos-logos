#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

# Importar o módulo
from importar_coletas import buscar_pastas_heineken, processar_pasta

print("=" * 80)
print("🚀 IMPORTAÇÃO AUTOMÁTICA DE TODAS AS PASTAS HEINEKEN")
print("=" * 80)

# Buscar pastas
print("\n🔍 Buscando pastas de Heineken...\n")

pastas = buscar_pastas_heineken()

print(f"✅ Encontradas {len(pastas)} pastas de Heineken:\n")

for i, pasta in enumerate(pastas, 1):
    print(f"  {i}. {pasta.name}")

# Processar cada pasta
print("\n" + "=" * 80)
print("📥 INICIANDO IMPORTAÇÃO")
print("=" * 80)

total_imagens = 0

for i, pasta in enumerate(pastas, 1):
    print(f"\n{i}/{len(pastas)} - Processando: {pasta.name}")
    print("-" * 80)
    
    try:
        resultado = processar_pasta(pasta, modo='completo')
        
        if resultado:
            total_imagens += resultado.get('total', 0)
            print(f"✅ Sucesso! {resultado.get('total', 0)} imagens importadas")
        else:
            print("⚠️  Nenhuma imagem importada desta pasta")
    
    except Exception as e:
        print(f"❌ Erro ao processar: {str(e)[:100]}")

print("\n" + "=" * 80)
print("📊 RESUMO FINAL")
print("=" * 80)
print(f"✅ Total de imagens importadas: {total_imagens}")
print(f"✅ Pastas processadas: {len(pastas)}")

print("\n🎉 Importação concluída!")
print("=" * 80)
