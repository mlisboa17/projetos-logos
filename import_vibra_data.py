"""
Script para importar dados do scraping Vibra para o banco Django
Lê os arquivos JSON gerados pelo scraper e salva no banco
"""
import os
import django
import json
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra, PrecoVibra
from django.utils import timezone
from decimal import Decimal


def importar_consolidado_para_banco(arquivo='vibra_precos_CONSOLIDADO.json'):
    """Importa dados do arquivo consolidado para o banco"""
    print(f"\n📂 Lendo {arquivo}...")
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    total_produtos = 0
    
    for produto in dados.get('produtos', []):
        nome_produto = produto['nome']
        codigo_produto = produto.get('codigo', '')
        
        for posto_data in produto.get('postos', []):
            cnpj = posto_data['cnpj']
            codigo_vibra = posto_data['codigo_vibra']
            razao = posto_data['razao_social']
            nome = posto_data.get('nome_posto', 'Posto')
            
            # Criar ou atualizar posto
            posto, created = PostoVibra.objects.get_or_create(
                cnpj=cnpj,
                defaults={
                    'codigo_vibra': codigo_vibra,
                    'razao_social': razao,
                    'nome_fantasia': nome,
                }
            )
            
            if created:
                print(f"  ✓ Posto criado: {posto.nome_fantasia} (CNPJ: {cnpj})")
            
            # Converter preço
            preco_str = posto_data['preco'].replace('Preço:', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                preco_decimal = Decimal(preco_str)
            except:
                continue
            
            # Salvar preço
            PrecoVibra.objects.create(
                posto=posto,
                produto_nome=nome_produto,
                produto_codigo=codigo_produto,
                preco=preco_decimal,
                prazo_pagamento=posto_data.get('prazo', ''),
                base_distribuicao=posto_data.get('base', ''),
                modalidade='',
                data_coleta=timezone.now(),
                disponivel=True
            )
            total_produtos += 1
    
    print(f"  💾 Salvos {total_produtos} produtos no total")
    return total_produtos


def main():
    """Importar dados consolidados"""
    print("\n🚀 Importando dados do scraping Vibra...\n")
    
    arquivo_consolidado = Path('vibra_precos_CONSOLIDADO.json')
    
    if not arquivo_consolidado.exists():
        print("❌ Arquivo vibra_precos_CONSOLIDADO.json não encontrado")
        print("   Execute o scraper primeiro: python fuel_prices\\scrapers\\vibra_scraper.py")
        return
    
    try:
        total = importar_consolidado_para_banco(arquivo_consolidado)
        print(f"\n✅ Importação concluída!")
        print(f"   Total de produtos importados: {total}")
        print(f"\n📊 Acesse o dashboard em: http://127.0.0.1:8000/fuel/")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
