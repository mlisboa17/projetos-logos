#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae

print("=" * 80)
print("⚖️  REDISTRIBUINDO IMAGENS DEVASSA PARA EQUILIBRIO")
print("=" * 80)

# Pegar produtos
devassa_35 = ProdutoMae.objects.get(id=35)  # 473ML - 159 imagens
devassa_34 = ProdutoMae.objects.get(id=34)  # 350ML - 100 imagens
devassa_36 = ProdutoMae.objects.get(id=36)  # 269ML - 0 imagens

print(f"\nEstado ANTES:")
print(f"  ID 34 (350ML): {devassa_34.imagens_treino.count()} imagens")
print(f"  ID 35 (473ML): {devassa_35.imagens_treino.count()} imagens")
print(f"  ID 36 (269ML): {devassa_36.imagens_treino.count()} imagens")

# Pegar todas as 159 imagens de ID 35
imagens_35 = list(devassa_35.imagens_treino.all().order_by('id'))

print(f"\n⚖️  REDISTRIBUIÇÃO:")
print("-" * 80)

# Dividir em 3 grupos
grupo_1 = imagens_35[0:50]      # IDs 0-49 → permanecem em 35
grupo_2 = imagens_35[50:100]    # IDs 50-99 → vai para 34
grupo_3 = imagens_35[100:159]   # IDs 100-158 → vai para 36

print(f"\n1️⃣  Mantendo em ID 35 (473ML): {len(grupo_1)} imagens")
for img in grupo_1[:3]:
    print(f"   • {img.id}: {img.imagem.name}")
print(f"   ... e mais {len(grupo_1)-3}")

print(f"\n2️⃣  Movendo para ID 34 (350ML): {len(grupo_2)} imagens")
for img in grupo_2:
    img.produto = devassa_34
    img.save()
print(f"   ✅ {len(grupo_2)} imagens movidas para ID 34")

print(f"\n3️⃣  Movendo para ID 36 (269ML): {len(grupo_3)} imagens")
for img in grupo_3:
    img.produto = devassa_36
    img.save()
print(f"   ✅ {len(grupo_3)} imagens movidas para ID 36")

# Recarregar e exibir novo estado
devassa_34.refresh_from_db()
devassa_35.refresh_from_db()
devassa_36.refresh_from_db()

print(f"\n\nEstado DEPOIS:")
print("-" * 80)
print(f"  ID 34 (350ML): {devassa_34.imagens_treino.count()} imagens ← +{len(grupo_2)}")
print(f"  ID 35 (473ML): {devassa_35.imagens_treino.count()} imagens ← {len(grupo_1)}")
print(f"  ID 36 (269ML): {devassa_36.imagens_treino.count()} imagens ← +{len(grupo_3)}")

novo_total = (
    devassa_34.imagens_treino.count() + 
    devassa_35.imagens_treino.count() + 
    devassa_36.imagens_treino.count()
)

print(f"\n✅ Total de imagens Devassa: {novo_total}")
print(f"✅ Distribuição equilibrada alcançada!")

print("\n" + "=" * 80)
