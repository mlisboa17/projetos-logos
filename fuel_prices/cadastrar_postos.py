"""
Script para cadastrar os 11 postos do Grupo Lisboa no banco de dados
"""

import os
import sys
import django

# Adicionar diretório pai ao path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra

# Lista dos 11 postos do Grupo Lisboa
postos_completo = [
    {'codigo': '95406', 'razao': 'AUTO POSTO CASA CAIADA LTDA', 'nome': 'AP CASA CAIADA', 'cnpj': '04284939000186'},
    {'codigo': '107469', 'razao': 'POSTO ENSEADA DO NORTE LTDA', 'nome': 'POSTO ENSEADA DO NOR', 'cnpj': '00338804000103'},
    {'codigo': '11236', 'razao': 'REAL RECIFE LTDA', 'nome': 'POSTO REAL', 'cnpj': '24156978000105'},
    {'codigo': '1153963', 'razao': 'POSTO CIDADE PATRIMONIO LTDA', 'nome': 'POSTO AVENIDA', 'cnpj': '05428059000280'},
    {'codigo': '124282', 'razao': 'R.J. COMBUSTIVEIS E LUBRIFICANTES L', 'nome': 'R J', 'cnpj': '08726064000186'},
    {'codigo': '14219', 'razao': 'AUTO POSTO GLOBO LTDA', 'nome': 'GLOBO105', 'cnpj': '41043647000188'},
    {'codigo': '156075', 'razao': 'DISTRIBUIDORA R S DERIVADO DE PETRO', 'nome': 'POSTO BR SHOPPING', 'cnpj': '07018760000175'},
    {'codigo': '1775869', 'razao': 'POSTO DOZE COMERCIO DE COMBUSTIVEIS', 'nome': 'POSTO DOZE', 'cnpj': '52308604000101'},
    {'codigo': '5039', 'razao': 'RIO DOCE COMERCIO E SERVICOS LTDA', 'nome': 'POSTO VIP', 'cnpj': '03008754000186'},
    {'codigo': '61003', 'razao': 'AUTO POSTO IGARASSU LTDA.', 'nome': 'P IGARASSU', 'cnpj': '04274378000134'},
    {'codigo': '94762', 'razao': 'POSTO CIDADE PATRIMONIO LTDA', 'nome': 'CIDADE PATRIMONIO', 'cnpj': '05428059000107'},
]

def cadastrar_postos():
    """Cadastra todos os postos do Grupo Lisboa"""
    print("=" * 70)
    print("CADASTRO DE POSTOS DO GRUPO LISBOA")
    print("=" * 70)
    
    cadastrados = 0
    atualizados = 0
    
    for posto_info in postos_completo:
        posto, created = PostoVibra.objects.get_or_create(
            cnpj=posto_info['cnpj'],
            defaults={
                'codigo_vibra': posto_info['codigo'],
                'razao_social': posto_info['razao'],
                'nome_fantasia': posto_info['nome'],
            }
        )
        
        if created:
            print(f"[NOVO] {posto_info['nome']} - CNPJ: {posto_info['cnpj']}")
            cadastrados += 1
        else:
            # Atualizar informações se mudaram
            alterou = False
            if posto.codigo_vibra != posto_info['codigo']:
                posto.codigo_vibra = posto_info['codigo']
                alterou = True
            if posto.razao_social != posto_info['razao']:
                posto.razao_social = posto_info['razao']
                alterou = True
            if posto.nome_fantasia != posto_info['nome']:
                posto.nome_fantasia = posto_info['nome']
                alterou = True
            
            if alterou:
                posto.save()
                print(f"[ATUALIZADO] {posto_info['nome']} - CNPJ: {posto_info['cnpj']}")
                atualizados += 1
            else:
                print(f"[JÁ EXISTE] {posto_info['nome']} - CNPJ: {posto_info['cnpj']}")
    
    print("\n" + "=" * 70)
    print(f"RESUMO:")
    print(f"  - Novos cadastrados: {cadastrados}")
    print(f"  - Atualizados: {atualizados}")
    print(f"  - Total no banco: {PostoVibra.objects.count()}")
    print("=" * 70)

if __name__ == '__main__':
    cadastrar_postos()
