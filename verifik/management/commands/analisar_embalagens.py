"""
Django Command - Analisa tipos de embalagens
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from verifik.models_anotacao import ImagemUnificada
from verifik.models import ProdutoMae
import re


class Command(BaseCommand):
    help = 'Analisa tipos de embalagens na base de dados'

    def handle(self, *args, **options):
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('ANALISE DE EMBALAGENS NA BASE DE DADOS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Padrões para detectar tipo de embalagem (ordem importa!)
        padroes = {
            'LATAS': [
                r'\bLATA\b', r'473\s*ML', r'269\s*ML', r'350\s*ML', r'ENERGETICO', r'ALUMINIO'
            ],
            'GARRAFA LONG NECK': [
                r'LONG NECK', r'LONGNECK', r'330\s*ML(?!.*600)', r'LN\s*330'
            ],
            'GARRAFA 600ML': [
                r'600\s*ML', r'GF\s*600', r'GARRAFA\s*600'
            ],
            'GARRAFAS': [
                r'GARRAFA', r'VIDRO'
            ],
            'PET 2LITROS': [
                r'\bPET\b', r'2\s*L', r'2LITRO', r'\b2L\b'
            ]
        }
        
        # Processar em ordem: LATAS > LONG NECK > 600ML > GARRAFAS > PET
        ordem_processamento = ['LATAS', 'GARRAFA LONG NECK', 'GARRAFA 600ML', 'GARRAFAS', 'PET 2LITROS']
        
        # Buscar todos os produtos únicos
        produtos = ProdutoMae.objects.all().order_by('descricao_produto')
        
        total_prods = produtos.count()
        total_imgs = ImagemUnificada.objects.count()
        
        self.stdout.write(f'\n📊 Totais:')
        self.stdout.write(f'   Produtos: {total_prods}')
        self.stdout.write(f'   Imagens: {total_imgs}')
        
        # Classificar por embalagem
        classificacao = {
            'LATAS': [],
            'GARRAFA LONG NECK': [],
            'GARRAFA 600ML': [],
            'GARRAFAS': [],
            'PET 2LITROS': [],
            'OUTROS': []
        }
        
        for prod in produtos:
            desc_upper = prod.descricao_produto.upper()
            encontrado = False
            
            # Processar em ordem LATAS -> GARRAFAS -> PET
            for tipo in ordem_processamento:
                patterns = padroes[tipo]
                for pattern in patterns:
                    if re.search(pattern, desc_upper):
                        count = ImagemUnificada.objects.filter(produto=prod).count()
                        classificacao[tipo].append({
                            'nome': prod.descricao_produto,
                            'id': prod.id,
                            'imagens': count
                        })
                        encontrado = True
                        break
                if encontrado:
                    break
            
            if not encontrado:
                count = ImagemUnificada.objects.filter(produto=prod).count()
                classificacao['OUTROS'].append({
                    'nome': prod.descricao_produto,
                    'id': prod.id,
                    'imagens': count
                })
        
        # Exibir resultados
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('DISTRIBUIÇÃO POR TIPO DE EMBALAGEM'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        total_geral = 0
        
        for tipo in ['LATAS', 'GARRAFA LONG NECK', 'GARRAFA 600ML', 'GARRAFAS', 'PET 2LITROS', 'OUTROS']:
            prods = classificacao[tipo]
            total_imgs_tipo = sum(p['imagens'] for p in prods)
            total_geral += total_imgs_tipo
            
            self.stdout.write(self.style.SUCCESS(f'\n🏷️  {tipo}: {len(prods)} produtos, {total_imgs_tipo} imagens'))
            self.stdout.write('-' * 80)
            
            # Ordenar por quantidade de imagens
            prods.sort(key=lambda x: x['imagens'], reverse=True)
            
            for i, prod in enumerate(prods[:15], 1):  # Top 15
                self.stdout.write(f"   {i:2}. {prod['nome'][:55]:55} {prod['imagens']:6} imgs")
            
            if len(prods) > 15:
                remaining = sum(p['imagens'] for p in prods[15:])
                self.stdout.write(f"   ... +{len(prods)-15} produtos com {remaining} imagens")
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS(f'TOTAL GERAL: {total_geral} imagens'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))
