"""
Cria arquivos de anotação YOLO simples para imagens sem anotação
Assume que o produto ocupa toda a imagem (bbox full)
"""
from pathlib import Path

dataset_dir = Path('assets/dataset/train')

# Mapear categorias para IDs de classe
categorias = sorted([d for d in dataset_dir.iterdir() if d.is_dir()])
categoria_to_class = {cat.name: idx for idx, cat in enumerate(categorias)}

print("="*60)
print("📝 CRIANDO ANOTAÇÕES YOLO SIMPLES")
print("="*60)
print(f"\n📦 {len(categorias)} categorias encontradas:\n")

for class_id, (nome, idx) in enumerate(categoria_to_class.items()):
    print(f"   Classe {idx}: {nome}")

print("\n" + "="*60)

total_criadas = 0

for categoria_dir in categorias:
    class_id = categoria_to_class[categoria_dir.name]
    
    # Buscar imagens sem anotação
    imagens = list(categoria_dir.glob("*.jpg")) + list(categoria_dir.glob("*.jpeg")) + list(categoria_dir.glob("*.png"))
    
    criadas_categoria = 0
    
    for img_path in imagens:
        txt_path = img_path.with_suffix('.txt')
        
        # Se já existe anotação, pular
        if txt_path.exists():
            continue
        
        # Criar anotação simples (produto centralizado, ocupa 90% da imagem)
        with open(txt_path, 'w') as f:
            f.write(f"{class_id} 0.5 0.5 0.9 0.9\n")
        
        criadas_categoria += 1
        total_criadas += 1
    
    if criadas_categoria > 0:
        print(f"✅ {categoria_dir.name}: {criadas_categoria} anotações criadas")

print("\n" + "="*60)
print(f"✅ Total: {total_criadas} anotações criadas")
print("="*60)
print("\n💡 Agora execute: python aumentar_dataset.py")
print()
