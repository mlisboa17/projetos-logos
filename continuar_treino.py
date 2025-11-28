"""
Continuar treinamento incremental de onde parou
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.verifik.management.commands.treinar_incremental import Command

print("=" * 70)
print("🚀 CONTINUANDO TREINAMENTO INCREMENTAL")
print("=" * 70)
print("\nCarregando do checkpoint anterior...")
print("Treinando apenas imagens não treinadas (treinada=False)")
print("Aplicando data augmentation (7x por imagem)")
print("\n" + "=" * 70 + "\n")

# Criar instância do comando e executar
command = Command()
options = {
    'only_new': True,
    'epochs': 50,
    'batch_size': 8,
    'augmentations': 7,
    'produto_id': None
}

try:
    command.handle(**options)
except Exception as e:
    print(f"\n❌ Erro durante treinamento: {e}")
    import traceback
    traceback.print_exc()

