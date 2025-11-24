"""
Verifica produtos com foto que ainda não foram treinados
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("\n" + "="*70)
print("VERIFICAÇÃO DE PRODUTOS VERIFIK")
print("="*70 + "\n")

# Estatísticas
total = ProdutoMae.objects.count()
com_foto = ProdutoMae.objects.filter(imagem_referencia__isnull=False).exclude(imagem_referencia='').count()
treinados = ProdutoMae.objects.filter(imagens_treino__isnull=False).exclude(imagens_treino='').distinct().count()

print(f"📊 ESTATÍSTICAS:")
print(f"   Total de produtos: {total}")
print(f"   Produtos com foto referência: {com_foto}")
print(f"   Produtos com imagens de treino: {treinados}")
print(f"   Produtos SEM foto: {total - com_foto}")

# Produtos com foto mas SEM imagens de treino
nao_treinados = ProdutoMae.objects.filter(
    imagem_referencia__isnull=False
).exclude(imagem_referencia='').filter(
    imagens_treino=''
) | ProdutoMae.objects.filter(
    imagem_referencia__isnull=False
).exclude(imagem_referencia='').filter(
    imagens_treino__isnull=True
)

print(f"\n⚠️  PRODUTOS COM FOTO MAS SEM IMAGENS DE TREINO: {nao_treinados.count()}")
print("="*70)

if nao_treinados.exists():
    print("\nLista de produtos pendentes de treinamento:\n")
    for i, produto in enumerate(nao_treinados, 1):
        print(f"{i:3d}. {produto.descricao_produto}")
        print(f"     Tipo: {produto.tipo}")
        print(f"     Marca: {produto.marca}")
        print(f"     Foto referência: {produto.imagem_referencia}")
        print()
else:
    print("\n✅ Todos os produtos com foto já têm imagens de treino!")

# Produtos prioritários (bebidas alcoólicas populares)
print("\n" + "="*70)
print("🎯 PRODUTOS PRIORITÁRIOS PARA TREINAMENTO")
print("="*70 + "\n")

tipos_prioritarios = ['Cerveja', 'Whisky', 'Vodka', 'Cachaça', 'Vinho', 'Refrigerante']
for tipo in tipos_prioritarios:
    produtos_tipo = ProdutoMae.objects.filter(tipo=tipo).filter(
        imagens_treino=''
    ) | ProdutoMae.objects.filter(tipo=tipo).filter(
        imagens_treino__isnull=True
    )
    if produtos_tipo.exists():
        print(f"\n{tipo}: {produtos_tipo.count()} produto(s) pendente(s)")
        for p in produtos_tipo[:5]:  # Mostrar apenas os 5 primeiros
            status_foto = "✓ COM FOTO" if p.imagem_referencia else "✗ SEM FOTO"
            print(f"  - {p.descricao_produto} ({status_foto})")

print("\n" + "="*70)
