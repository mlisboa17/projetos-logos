"""
Treina modelo YOLO apenas com produtos que têm novas imagens
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count

# Produtos que foram treinados no último treino
PRODUTOS_ULTIMO_TREINO = {
    'AMSTEL CERVEJA AMSTEL 473ML': 34,
    'BUDWEISER CERVEJA BUDWEISER LN 330ML': 27,
    'DEVASSA CERVEJA DEVASSA LAGER 350 ML': 50,
    'DEVASSA CERVEJA DEVASSA LAGER 473ML': 106,
    'HEINEKEN CERVEJA HEINEKEN 330ML': 27,
    'HEINEKEN CERVEJA HEINEKEN LATA 350ML': 20,
    'PETRA CERVEJA PETRA 473ML': 5,
    'PILSEN CERVEJA PILSEN LOKAL LATA 473ML': 24,
    'STELLA CERVEJA STELLA PURE GOLD S GLUTEN LONG 330ML': 40,
    'REFRIGERANTE REFRIGERANTE BLACK PEPSI 350ML': 54,
}

print("\n" + "="*80)
print("🎯 TREINAMENTO SELETIVO")
print("="*80)

# Produtos específicos para treinar
PRODUTOS_SELECIONADOS = [
    {'marca': 'HEINEKEN', 'busca': 'CERVEJA HEINEKEN 330ML', 'nome_friendly': 'Heineken 330ml Longneck'},
    {'marca': 'AMSTEL', 'busca': '473ML', 'nome_friendly': 'Amstel 473ml Latão'},
    {'marca': 'BUDWEISER', 'busca': 'LN 330ML', 'nome_friendly': 'Budweiser 330ml Longneck'},
]

produtos_para_treinar = []

print("\n🔍 Buscando produtos selecionados...")

for config in PRODUTOS_SELECIONADOS:
    marca = config['marca']
    busca = config['busca']
    nome = config['nome_friendly']
    
    try:
        produto = ProdutoMae.objects.get(
            marca=marca,
            descricao_produto__icontains=busca
        )
        
        num_imagens = produto.imagens_treino.count()
        
        if num_imagens > 0:
            produtos_para_treinar.append({
                'produto': produto,
                'atual': num_imagens,
                'nome': nome
            })
            print(f"  ✅ {nome:35} ({num_imagens} imagens)")
        else:
            print(f"  ⚠️  {nome:35} (sem imagens de treino)")
            
    except ProdutoMae.DoesNotExist:
        print(f"  ❌ {nome:35} (não encontrado no banco)")
    except ProdutoMae.MultipleObjectsReturned:
        print(f"  ⚠️  {nome:35} (múltiplos produtos encontrados)")
        # Pegar o primeiro
        produto = ProdutoMae.objects.filter(
            marca=marca,
            descricao_produto__icontains=busca
        ).first()
        
        if produto:
            num_imagens = produto.imagens_treino.count()
            if num_imagens > 0:
                produtos_para_treinar.append({
                    'produto': produto,
                    'atual': num_imagens,
                    'nome': nome
                })
                print(f"     ↳ Usando: {produto.descricao_produto} ({num_imagens} imagens)")

if not produtos_para_treinar:
    print("\n⚠️  Nenhum produto com novas imagens!")
    sys.exit(0)

print("\n" + "="*80)
print(f"📊 RESUMO:")
print(f"   Produtos para treinar: {len(produtos_para_treinar)}")
print(f"   Total de imagens: {sum(p['atual'] for p in produtos_para_treinar)}")
print("="*80)

# Confirmar
confirmar = input("\n▶️  Iniciar treinamento? (s/n): ").strip().lower()

if confirmar != 's':
    print("❌ Cancelado")
    sys.exit(0)

# Importar o que precisamos
import cv2
from PIL import Image
import shutil
from pathlib import Path

print("\n" + "="*80)
print("📦 PREPARANDO DATASET")
print("="*80)

# Criar diretório do dataset
dataset_dir = Path('verifik/dataset_yolo')
if dataset_dir.exists():
    print("🗑️  Removendo dataset anterior...")
    shutil.rmtree(dataset_dir)

dataset_dir.mkdir(parents=True)
(dataset_dir / 'train' / 'images').mkdir(parents=True)
(dataset_dir / 'train' / 'labels').mkdir(parents=True)

# Preparar dataset apenas com os produtos selecionados
produtos_obj = [p['produto'] for p in produtos_para_treinar]

# Verificar ultralytics
from treinar_modelo_yolo import verificar_ultralytics

verificar_ultralytics()

from ultralytics import YOLO

print(f"\n📸 Preparando imagens de {len(produtos_obj)} produtos...")

# Criar mapeamento de classes
class_mapping = {}
class_names = []

for i, p in enumerate(produtos_obj):
    classe_nome = f"{p.marca} {p.descricao_produto}"
    class_mapping[p.id] = i
    class_names.append(classe_nome)
    print(f"  Classe {i}: {classe_nome}")

# Copiar e criar labels
images_dir = dataset_dir / 'train' / 'images'
labels_dir = dataset_dir / 'train' / 'labels'

total_images = 0
corrupt_images = 0

for produto in produtos_obj:
    classe_id = class_mapping[produto.id]
    imagens = produto.imagens_treino.all()
    
    print(f"\n📦 {produto.marca} - {produto.descricao_produto}")
    print(f"   Processando {imagens.count()} imagens...")
    
    for img_obj in imagens:
        try:
            # Caminho da imagem
            img_path = Path('media') / img_obj.imagem.name
            
            if not img_path.exists():
                print(f"  ⚠️  Arquivo não encontrado: {img_path}")
                continue
            
            # Verificar se é imagem válida
            try:
                test_img = Image.open(img_path)
                test_img.verify()
            except Exception as e:
                print(f"  ⚠️  Imagem corrompida: {img_path.name}")
                corrupt_images += 1
                continue
            
            # Copiar imagem
            dest_img = images_dir / f"{produto.id}_{img_path.name}"
            shutil.copy2(img_path, dest_img)
            
            # Criar label (imagem completa = objeto único)
            label_file = labels_dir / f"{produto.id}_{img_path.stem}.txt"
            
            # Obter dimensões da imagem
            img = cv2.imread(str(img_path))
            if img is None:
                continue
                
            altura, largura = img.shape[:2]
            
            # YOLO format: class_id x_center y_center width height (normalized)
            # Para imagem completa: centro (0.5, 0.5), tamanho (1.0, 1.0)
            with open(label_file, 'w') as f:
                f.write(f"{classe_id} 0.5 0.5 1.0 1.0\n")
            
            total_images += 1
            
        except Exception as e:
            print(f"  ❌ Erro processando {img_path.name}: {e}")
            continue

print(f"\n✅ Dataset preparado:")
print(f"   Total de imagens: {total_images}")
print(f"   Imagens corrompidas ignoradas: {corrupt_images}")
print(f"   Classes: {len(class_names)}")

# Criar data.yaml
data_yaml_path = dataset_dir / 'data.yaml'
with open(data_yaml_path, 'w', encoding='utf-8') as f:
    f.write(f"path: {dataset_dir.absolute()}\n")
    f.write("train: train/images\n")
    f.write("val: train/images\n")
    f.write(f"nc: {len(class_names)}\n")
    f.write(f"names: {class_names}\n")

print(f"📝 Arquivo data.yaml criado")

# Treinar
from treinar_modelo_yolo import treinar_modelo

print("\n" + "="*80)
print("🚀 INICIANDO TREINAMENTO")
print("="*80)

model, results = treinar_modelo(data_yaml_path, class_names)

print("\n" + "="*80)
print("✅ TREINAMENTO CONCLUÍDO!")
print("="*80)
print(f"\n📁 Modelo salvo em: verifik/runs/treino_verifik/weights/best.pt")
print(f"📊 Total de classes: {len(class_names)}")
print(f"🎯 Produtos treinados:")

for info in produtos_para_treinar:
    p = info['produto']
    print(f"   - {p.marca} {p.descricao_produto} ({info['atual']} imagens)")
