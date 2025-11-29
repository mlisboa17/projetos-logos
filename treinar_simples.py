"""
Continuar treinamento sem data augmentation (versão simplificada)
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from ultralytics import YOLO
import yaml
from datetime import datetime

print("=" * 70)
print("🚀 CONTINUANDO TREINAMENTO - MODO SIMPLIFICADO")
print("=" * 70)

# Importar models
try:
    from verifik.models import ProdutoMae, ImagemProduto
except:
    print("⚠️ Usando treinar_modelo_yolo.py existente...")
    os.system('python treinar_modelo_yolo.py')
    sys.exit(0)

# Buscar checkpoint
checkpoint_paths = [
    Path('fuel_prices/runs/detect/heineken_330ml/weights/last.pt'),
    Path('verifik/runs/treino_verifik/weights/last.pt'),
    Path('verifik/runs/treino_incremental/weights/last.pt'),
]

checkpoint_path = None
for path in checkpoint_paths:
    if path.exists():
        checkpoint_path = path
        break

if checkpoint_path:
    print(f"\n✅ Checkpoint encontrado: {checkpoint_path}")
    print("   CONTINUANDO treinamento do último estado...")
    model = YOLO(str(checkpoint_path))
else:
    print("\n⚠️ Nenhum checkpoint encontrado, iniciando do zero...")
    model = YOLO('yolov8n.pt')

# Buscar imagens não treinadas
print("\n📊 Buscando imagens não treinadas...")
produtos_com_imagens = {}
total_imagens = 0

for produto in ProdutoMae.objects.all():
    try:
        imagens = list(produto.imagens_treino.filter(treinada=False))
        if imagens:
            produtos_com_imagens[produto] = imagens
            total_imagens += len(imagens)
            print(f"  ✓ {produto.marca} {produto.descricao_produto}: {len(imagens)} imagens")
    except:
        imagens = list(produto.imagens_treino.all())
        if imagens:
            produtos_com_imagens[produto] = imagens
            total_imagens += len(imagens)
            print(f"  ✓ {produto.marca} {produto.descricao_produto}: {len(imagens)} imagens")

if not produtos_com_imagens:
    print("\n❌ Nenhuma imagem para treinar!")
    sys.exit(1)

print(f"\n✓ Total: {len(produtos_com_imagens)} produtos, {total_imagens} imagens")

# Criar dataset YOLO
print("\n📁 Preparando dataset YOLO...")
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
dataset_path = Path('verifik/dataset_treino') / timestamp
images_path = dataset_path / 'images' / 'train'
labels_path = dataset_path / 'labels' / 'train'

images_path.mkdir(parents=True, exist_ok=True)
labels_path.mkdir(parents=True, exist_ok=True)

# Mapear classes
class_mapping = {}
for idx, produto in enumerate(sorted(produtos_com_imagens.keys(), key=lambda p: f"{p.marca}_{p.descricao_produto}")):
    class_name = f"{produto.marca}_{produto.descricao_produto}".replace(' ', '_')
    class_mapping[produto.id] = {'index': idx, 'name': class_name}

# Copiar imagens e criar labels
print("\n🔄 Copiando imagens...")
total_copied = 0

for produto, imagens in produtos_com_imagens.items():
    class_idx = class_mapping[produto.id]['index']
    class_name = class_mapping[produto.id]['name']
    
    for img_idx, imagem_obj in enumerate(imagens):
        img_path = Path(imagem_obj.imagem.path)
        if not img_path.exists():
            continue
        
        # Copiar imagem
        dest_name = f"{class_name}_{img_idx}.jpg"
        dest_img = images_path / dest_name
        dest_label = labels_path / f"{class_name}_{img_idx}.txt"
        
        import shutil
        shutil.copy(str(img_path), str(dest_img))
        
        # Criar label YOLO (produto centralizado ocupando 90% da imagem)
        with open(dest_label, 'w') as f:
            f.write(f"{class_idx} 0.5 0.5 0.9 0.9\n")
        
        total_copied += 1

print(f"  ✓ {total_copied} imagens copiadas")

# Criar data.yaml
data_yaml = {
    'path': str(dataset_path.absolute()),
    'train': 'images/train',
    'val': 'images/train',
    'nc': len(class_mapping),
    'names': [class_mapping[pid]['name'] for pid in sorted(class_mapping.keys(), key=lambda k: class_mapping[k]['index'])]
}

yaml_path = dataset_path / 'data.yaml'
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)

print(f"\n✓ Dataset configurado: {yaml_path}")
print(f"✓ Classes: {data_yaml['names']}")

# Treinar
print("\n" + "=" * 70)
print("🎯 INICIANDO TREINAMENTO")
print("=" * 70)

try:
    results = model.train(
        data=str(yaml_path),
        epochs=50,
        batch=8,
        imgsz=640,
        patience=15,
        save=True,
        project='verifik/runs',
        name='treino_continuado',
        exist_ok=True,
        verbose=True,
    )
    
    print("\n" + "=" * 70)
    print("✅ TREINAMENTO CONCLUÍDO!")
    print("=" * 70)
    print(f"\n📊 Imagens treinadas: {total_copied}")
    print(f"📦 Classes: {len(class_mapping)}")
    print(f"💾 Modelo salvo em: verifik/runs/treino_continuado/")
    
    # Marcar imagens como treinadas
    try:
        from django.utils import timezone
        ImagemProduto.objects.filter(treinada=False).update(
            treinada=True,
            data_treinamento=timezone.now()
        )
        print("\n✓ Imagens marcadas como treinadas")
    except:
        pass
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
