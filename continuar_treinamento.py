"""
Script para continuar treinamento do checkpoint anterior
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from pathlib import Path

print("=" * 70)
print("🔍 VERIFICANDO ÚLTIMO TREINAMENTO")
print("=" * 70)

# Procurar checkpoints
checkpoints = [
    Path('fuel_prices/runs/detect/heineken_330ml/weights/last.pt'),
    Path('verifik/runs/treino_verifik/weights/last.pt'),
    Path('verifik/runs/treino_incremental/weights/last.pt'),
]

checkpoint_path = None
for path in checkpoints:
    if path.exists():
        checkpoint_path = path
        print(f"\n✅ Checkpoint encontrado: {path}")
        
        # Verificar tamanho do arquivo
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"   Tamanho: {size_mb:.2f} MB")
        
        # Tentar carregar informações do modelo
        try:
            from ultralytics import YOLO
            model = YOLO(str(path))
            print(f"   Modelo carregado com sucesso!")
            
            # Verificar quantas épocas já foram treinadas
            if hasattr(model.model, 'epoch'):
                print(f"   Épocas já treinadas: {model.model.epoch}")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao carregar: {e}")
        
        break

if not checkpoint_path:
    print("\n❌ Nenhum checkpoint encontrado!")
    print("\nProcurados:")
    for path in checkpoints:
        print(f"   - {path}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🚀 CONTINUANDO TREINAMENTO")
print("=" * 70)

# Iniciar treinamento via comando Django
print("\nExecutando: python manage.py treinar_incremental --only-new")
print("\nPressione Ctrl+C para cancelar ou Enter para continuar...")
input()

os.system('python manage.py treinar_incremental --only-new --epochs 50')
