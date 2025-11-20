from django.core.management.base import BaseCommand
from verifik.services.analisador import processar_todas_deteccoes


class Command(BaseCommand):
    help = 'Analisa detecções pendentes e cria incidentes automaticamente'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Iniciando análise de detecções...'))
        
        incidentes = processar_todas_deteccoes()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Análise concluída: {len(incidentes)} incidentes criados')
        )
