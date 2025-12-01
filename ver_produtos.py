import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).resolve().parent))
django.setup()

from verifik.models_anotacao import ImagemUnificada
from django.db.models import Count

print('\n' + '='*80)
print('PRODUTOS NA BASE COM MAIS IMAGENS')
print('='*80)

prods = ImagemUnificada.objects.values('produto__descricao_produto').annotate(
    count=Count('id')
).order_by('-count')[:30]

for i, p in enumerate(prods, 1):
    desc = p['produto__descricao_produto']
    count = p['count']
    print(f'{i:2}. {desc[:55]:55} {count:6} imgs')

print('\n' + '='*80)
