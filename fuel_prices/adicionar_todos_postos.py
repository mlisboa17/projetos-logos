"""
Script para adicionar todos os 11 postos do Grupo Lisboa no banco de dados
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra


def adicionar_todos_postos():
    """Adiciona todos os 11 postos do Grupo Lisboa"""
    
    postos = [
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
    
    print("🏪 Adicionando postos no banco de dados...\n")
    
    adicionados = 0
    atualizados = 0
    
    for posto in postos:
        posto_obj, created = PostoVibra.objects.update_or_create(
            cnpj=posto['cnpj'],
            defaults={
                'codigo_vibra': posto['codigo'],
                'razao_social': posto['razao'],
                'nome_fantasia': posto['nome'],
                'ativo': True,
            }
        )
        
        if created:
            print(f"✅ Adicionado: {posto['nome']} (CNPJ: {posto['cnpj']})")
            adicionados += 1
        else:
            print(f"🔄 Atualizado: {posto['nome']} (CNPJ: {posto['cnpj']})")
            atualizados += 1
    
    print(f"\n✅ Concluído!")
    print(f"   Novos postos: {adicionados}")
    print(f"   Atualizados: {atualizados}")
    print(f"   Total: {adicionados + atualizados}")


if __name__ == '__main__':
    adicionar_todos_postos()
