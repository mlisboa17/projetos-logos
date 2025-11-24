"""
Comando Django para executar scraping da Vibra Energia
Uso: python manage.py scrape_vibra
"""
from django.core.management.base import BaseCommand
from fuel_prices.scrapers.vibra_scraper import VibraScraper


class Command(BaseCommand):
    help = 'Executa scraping de preços da Vibra Energia e salva no banco'

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Executar navegador em modo headless (sem interface gráfica)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Processar todos os 11 postos (padrão: apenas 3 de teste)',
        )

    def handle(self, *args, **options):
        headless = options['headless']
        process_all = options['all']
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Iniciando scraping da Vibra Energia...\n'))
        
        # Credenciais do Grupo Lisboa
        scraper = VibraScraper(
            username='95406',
            password='Apcc2350',
            headless=headless
        )
        
        # Lista dos 11 postos do Grupo Lisboa
        postos_completo = [
            {'codigo': '95406', 'razao': 'AUTO POSTO CASA CAIADA LTDA', 'nome': 'AP CASA CAIADA', 'cnpj': '04284939000186'},  # SEMPRE PRIMEIRO
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
        
        # Escolher postos
        if process_all:
            postos = postos_completo
            self.stdout.write(f'📊 Processando TODOS os {len(postos)} postos\n')
        else:
            postos = [
                postos_completo[0],  # Casa Caiada - Posto mestre
                postos_completo[2],  # Posto Real
                postos_completo[3],  # Posto Avenida
            ]
            self.stdout.write(f'📊 Processando {len(postos)} postos de teste\n')
        
        try:
            todos_dados = scraper.run_scraping_multiplos_postos(postos)
            
            # Resumo
            total_produtos = sum(len(d.get('produtos', [])) for d in todos_dados)
            self.stdout.write(self.style.SUCCESS(f'\n✅ Scraping concluído!'))
            self.stdout.write(f'   Postos processados: {len(todos_dados)}/{len(postos)}')
            self.stdout.write(f'   Total de produtos coletados: {total_produtos}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {e}'))
            raise
