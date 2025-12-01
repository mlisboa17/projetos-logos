from django.core.management.base import BaseCommand
from verifik.models_anotacao import ImagemUnificada


class Command(BaseCommand):
    help = 'Limpa todos os registros de ImagemUnificada'

    def handle(self, *args, **options):
        count = ImagemUnificada.objects.count()
        self.stdout.write(f'Total antes: {count}')
        ImagemUnificada.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deletados: {count}'))
        self.stdout.write(self.style.SUCCESS(f'Total depois: {ImagemUnificada.objects.count()}'))
