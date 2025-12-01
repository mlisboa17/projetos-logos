"""
Django Management Command - Resumo do Banco de Dados
Mostra estatísticas de ImagemUnificada
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from verifik.models_anotacao import ImagemUnificada
from verifik.models import ProdutoMae


class Command(BaseCommand):
    help = 'Mostra resumo estatístico de ImagemUnificada'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('RESUMO - IMAGEMUNIFICADA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Total geral
        total = ImagemUnificada.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 TOTAL DE IMAGENS: {total}'))

        # Por tipo
        tipos = ImagemUnificada.objects.values('tipo_imagem').annotate(
            count=Count('id')
        ).order_by('tipo_imagem')

        self.stdout.write(f'\n📁 DISTRIBUIÇÃO POR TIPO:')
        for t in tipos:
            tipo = t['tipo_imagem']
            count = t['count']
            percent = (count / total * 100) if total > 0 else 0
            self.stdout.write(f'   {tipo:20} {count:6} ({percent:5.1f}%)')

        # Augmentacoes por tipo
        augmentacoes = ImagemUnificada.objects.filter(
            tipo_imagem='augmentada'
        ).values('tipo_augmentacao').annotate(
            count=Count('id')
        ).order_by('-count')

        if augmentacoes:
            self.stdout.write(f'\n🎨 AUGMENTACOES POR TIPO:')
            for a in augmentacoes:
                tipo = a['tipo_augmentacao']
                count = a['count']
                self.stdout.write(f'   {tipo:20} {count:6}')

        # Produtos com mais imagens
        self.stdout.write(f'\n🏆 TOP 10 PRODUTOS (por quantidade de imagens):')
        top_produtos = []
        for produto in ProdutoMae.objects.all():
            count = ImagemUnificada.objects.filter(produto=produto).count()
            if count > 0:
                top_produtos.append((produto.descricao_produto[:40], count))

        top_produtos.sort(key=lambda x: x[1], reverse=True)
        for i, (desc, count) in enumerate(top_produtos[:10], 1):
            self.stdout.write(f'   {i:2}. {desc:40} {count:6}')

        # Status de treino
        self.stdout.write(f'\n🔬 STATUS DE TREINO:')
        treinadas = ImagemUnificada.objects.filter(num_treinos__gt=0).count()
        nao_treinadas = total - treinadas
        if total > 0:
            self.stdout.write(self.style.SUCCESS(f'   Já treinadas: {treinadas} ({treinadas/total*100:.1f}%)'))
            self.stdout.write(f'   Não treinadas: {nao_treinadas} ({nao_treinadas/total*100:.1f}%)')
        else:
            self.stdout.write(f'   Já treinadas: 0')
            self.stdout.write(f'   Não treinadas: 0')

        # Ativas vs inativas
        self.stdout.write(f'\n✅ STATUS DE ATIVACAO:')
        ativas = ImagemUnificada.objects.filter(ativa=True).count()
        inativas = total - ativas
        if total > 0:
            self.stdout.write(self.style.SUCCESS(f'   Ativas: {ativas} ({ativas/total*100:.1f}%)'))
            self.stdout.write(f'   Inativas: {inativas} ({inativas/total*100:.1f}%)')
        else:
            self.stdout.write(f'   Ativas: 0')
            self.stdout.write(f'   Inativas: 0')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))
