"""
Script para importar dados do JSON para o banco de dados
"""
import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra, PrecoVibra
from django.utils import timezone as django_tz

print("\n" + "="*60)
print("IMPORTANDO DADOS DO JSON PARA O BANCO")
print("="*60)

# Ler arquivo JSON
json_file = 'vibra_precos_TESTE.json'
print(f"\n📂 Lendo {json_file}...")

with open(json_file, 'r', encoding='utf-8') as f:
    dados_postos = json.load(f)

print(f"  ✓ {len(dados_postos)} postos encontrados no arquivo")

# Importar cada posto
total_precos = 0
for dados in dados_postos:
    codigo_vibra = dados.get('codigo_vibra')
    razao_social = dados.get('razao_social')
    cnpj = dados.get('cnpj')
    
    if not all([codigo_vibra, razao_social, cnpj]):
        print(f"  ⚠️  Posto sem dados completos, pulando...")
        continue
    
    print(f"\n📍 Processando posto {codigo_vibra} - {razao_social[:30]}...")
    
    # Buscar posto no banco
    try:
        posto = PostoVibra.objects.get(codigo_vibra=codigo_vibra)
        print(f"  ✓ Posto encontrado no banco")
    except PostoVibra.DoesNotExist:
        print(f"  ❌ Posto {codigo_vibra} NÃO encontrado no banco!")
        continue
    
    # Limpar preços antigos deste posto
    deletados = PrecoVibra.objects.filter(posto=posto).delete()
    print(f"  🗑️  Removidos {deletados[0]} preços antigos")
    
    # Salvar novos preços
    precos_salvos = 0
    for produto in dados.get('produtos', []):
        # Converter preço
        preco_str = produto.get('preco', '')
        preco_str = preco_str.replace('Preço:', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
        
        try:
            preco_decimal = float(preco_str)
        except:
            print(f"  ⚠️  Erro ao converter preço: {produto.get('preco', '')} - Pulando...")
            continue
        
        # Criar preço
        PrecoVibra.objects.create(
            posto=posto,
            produto_nome=produto.get('nome', ''),
            produto_codigo=produto.get('codigo', ''),
            preco=preco_decimal,
            prazo_pagamento=produto.get('prazo', ''),
            base_distribuicao=produto.get('base', ''),
            modalidade=dados.get('modalidade') or 'NÃO COLETADO',  # Default se null
            data_coleta=django_tz.now(),
            disponivel=True
        )
        precos_salvos += 1
    
    print(f"  ✅ Salvos {precos_salvos} preços")
    total_precos += precos_salvos

print("\n" + "="*60)
print(f"✅ IMPORTAÇÃO CONCLUÍDA!")
print(f"   Total de preços importados: {total_precos}")
print("="*60)
print(f"\n📊 Acesse o dashboard em: http://127.0.0.1:8000/fuel/\n")
