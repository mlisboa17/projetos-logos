#!/usr/bin/env python
import os
import django
import shutil
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae

print("=" * 80)
print("🔄 RECONSTRUÇÃO DE DATASET DE TREINAMENTO")
print("=" * 80)

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / 'dataset'
DATASET_CLEAN_DIR = BASE_DIR / 'dataset_clean'

# ============================================================================
# 1. BACKUP DO DATASET ANTIGO
# ============================================================================
print("\n1️⃣  FAZENDO BACKUP DO DATASET ANTIGO")
print("-" * 80)

if DATASET_DIR.exists():
    backup_dir = BASE_DIR / 'dataset_backup_compromised'
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    shutil.move(str(DATASET_DIR), str(backup_dir))
    print(f"✅ Dataset antigo movido para: {backup_dir}")
else:
    print("✅ Nenhum dataset anterior encontrado")

# ============================================================================
# 2. CRIAR ESTRUTURA NOVA
# ============================================================================
print("\n2️⃣  CRIANDO ESTRUTURA NOVA DO DATASET")
print("-" * 80)

# Criar diretórios
TRAIN_DIR = DATASET_DIR / 'images' / 'train'
VAL_DIR = DATASET_DIR / 'images' / 'val'
LABELS_TRAIN_DIR = DATASET_DIR / 'labels' / 'train'
LABELS_VAL_DIR = DATASET_DIR / 'labels' / 'val'

for dir_path in [TRAIN_DIR, VAL_DIR, LABELS_TRAIN_DIR, LABELS_VAL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

print(f"✅ Diretórios criados:")
print(f"   • {TRAIN_DIR}")
print(f"   • {VAL_DIR}")
print(f"   • {LABELS_TRAIN_DIR}")
print(f"   • {LABELS_VAL_DIR}")

# ============================================================================
# 3. COPIAR APENAS IMAGENS VÁLIDAS
# ============================================================================
print("\n3️⃣  COPIANDO IMAGENS VÁLIDAS PARA DATASET LIMPO")
print("-" * 80)

from PIL import Image

imagens_copiadas = 0
imagens_rejeitadas = 0
produtos_com_imagens = {}

todas_imagens = ImagemProduto.objects.all().order_by('produto_id', 'id')

for idx, img in enumerate(todas_imagens):
    try:
        if not img.imagem:
            continue
        
        arquivo_path = img.imagem.path
        
        # Verificar se existe e é válida
        if not os.path.exists(arquivo_path):
            imagens_rejeitadas += 1
            continue
        
        # Validar imagem
        try:
            image = Image.open(arquivo_path)
            image.verify()
        except:
            imagens_rejeitadas += 1
            continue
        
        # Obter extensão
        ext = Path(arquivo_path).suffix.lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
            ext = '.jpg'
        
        # Nome único: produto_id_imagem_id
        novo_nome = f"{img.produto_id}_{img.id}{ext}"
        
        # Dividir: 80% treino, 20% validação
        if idx % 5 == 0:  # 20% validação
            dest_path = VAL_DIR / novo_nome
        else:  # 80% treino
            dest_path = TRAIN_DIR / novo_nome
        
        # Copiar imagem
        shutil.copy2(arquivo_path, str(dest_path))
        imagens_copiadas += 1
        
        # Rastrear produtos
        if img.produto_id not in produtos_com_imagens:
            produtos_com_imagens[img.produto_id] = {
                'nome': img.produto.descricao_produto,
                'count': 0
            }
        produtos_com_imagens[img.produto_id]['count'] += 1
        
        if imagens_copiadas % 50 == 0:
            print(f"  ✅ {imagens_copiadas} imagens copiadas...")
    
    except Exception as e:
        imagens_rejeitadas += 1
        print(f"  ⚠️  Erro ao processar ID {img.id}: {str(e)[:40]}")

print(f"\n✅ Total de imagens copiadas: {imagens_copiadas}")
print(f"❌ Imagens rejeitadas: {imagens_rejeitadas}")

# ============================================================================
# 4. GERAR ARQUIVO YAML PARA YOLO
# ============================================================================
print("\n4️⃣  GERANDO ARQUIVO YAML PARA YOLO")
print("-" * 80)

# Mapear IDs de produtos para índices de classe
produtos_ordenados = sorted(
    ProdutoMae.objects.filter(id__in=produtos_com_imagens.keys()),
    key=lambda x: x.id
)

class_map = {}
classes_yaml = []

for idx, produto in enumerate(produtos_ordenados):
    class_map[produto.id] = idx
    classes_yaml.append(produto.descricao_produto)

# Criar data.yaml
yaml_content = f"""path: {DATASET_DIR}
train: images/train
val: images/val

nc: {len(classes_yaml)}
names: {classes_yaml}
"""

yaml_path = DATASET_DIR / 'data.yaml'
with open(yaml_path, 'w', encoding='utf-8') as f:
    f.write(yaml_content)

print(f"✅ Arquivo data.yaml criado: {yaml_path}")
print(f"   • Classes: {len(classes_yaml)}")
print(f"   • Primeiras 5: {classes_yaml[:5]}")

# ============================================================================
# 5. CRIAR ARQUIVO DE MAPEAMENTO
# ============================================================================
print("\n5️⃣  CRIANDO ARQUIVO DE MAPEAMENTO DE CLASSES")
print("-" * 80)

import json

mapping = {
    'class_to_id': {name: idx for idx, name in enumerate(classes_yaml)},
    'id_to_class': {str(idx): name for idx, name in enumerate(classes_yaml)},
    'produto_mapping': {
        str(produto.id): {
            'nome': produto.descricao_produto,
            'class_idx': class_map[produto.id],
            'total_imagens': produtos_com_imagens[produto.id]['count']
        }
        for produto in produtos_ordenados
    }
}

mapping_path = DATASET_DIR / 'class_mapping.json'
with open(mapping_path, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"✅ Arquivo de mapeamento criado: {mapping_path}")

# ============================================================================
# 6. ESTATÍSTICAS FINAIS
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 ESTATÍSTICAS DO NOVO DATASET")
print("=" * 80)

train_count = len(list(TRAIN_DIR.glob('*')))
val_count = len(list(VAL_DIR.glob('*')))

print(f"\n📦 Composição do Dataset:")
print(f"   • Imagens de treino: {train_count}")
print(f"   • Imagens de validação: {val_count}")
print(f"   • Total: {train_count + val_count}")
print(f"   • Proporção: {train_count/(train_count+val_count)*100:.1f}% treino / {val_count/(train_count+val_count)*100:.1f}% validação")

print(f"\n🏷️  Classes (Produtos):")
print(f"   • Total de produtos: {len(produtos_ordenados)}")
print(f"   • Top 5 com mais imagens:")

produtos_ordenados_count = sorted(
    produtos_com_imagens.items(),
    key=lambda x: x[1]['count'],
    reverse=True
)

for i, (prod_id, info) in enumerate(produtos_ordenados_count[:5], 1):
    print(f"     {i}. {info['nome']}: {info['count']} imagens")

print(f"\n✨ Dataset limpo pronto para treinamento!")
print(f"   Caminho: {DATASET_DIR}")

print("\n" + "=" * 80)
print("🚀 PRÓXIMAS ETAPAS:")
print("=" * 80)
print("""
1. Executar novo treinamento YOLO:
   python train_yolo.py --dataset dataset/data.yaml --epochs 50 --imgsz 416

2. Validar resultados:
   python validate_model.py

3. Usar modelo treinado para fazer detecções:
   python detect_products.py --model runs/detect/train/weights/best.pt
""")

print("=" * 80)
