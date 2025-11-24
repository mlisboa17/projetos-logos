"""
Script para verificar dados cadastrados no banco
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra, PrecoVibra

print("\n" + "="*60)
print("VERIFICAÇÃO DE DADOS NO BANCO")
print("="*60)

# Postos cadastrados
postos = PostoVibra.objects.all()
print(f"\n📍 POSTOS CADASTRADOS: {postos.count()}")
for posto in postos:
    print(f"   {posto.codigo_vibra} - {posto.razao_social}")

# Preços cadastrados
precos = PrecoVibra.objects.all()
print(f"\n💰 PREÇOS CADASTRADOS: {precos.count()}")

# Preços por posto
print("\n📊 PREÇOS POR POSTO:")
for posto in postos:
    count = PrecoVibra.objects.filter(posto=posto).count()
    print(f"   {posto.codigo_vibra} - {posto.razao_social}: {count} preços")

print("\n" + "="*60)
