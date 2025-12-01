import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(os.path.dirname(__file__)))
django.setup()

from verifik.models_anotacao import ImagemUnificada

count = ImagemUnificada.objects.count()
print(f"Total antes: {count}")
ImagemUnificada.objects.all().delete()
print(f"Deletados: {count}")
print(f"Total depois: {ImagemUnificada.objects.count()}")
