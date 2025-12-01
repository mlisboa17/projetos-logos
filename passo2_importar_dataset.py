"""
Passo 2: Importar anotadas para dataset de treino
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.db.models import Count

print("=" * 60)
print("PASSO 2: IMPORTAR ANOTADAS PARA DATASET DE TREINO")
print("=" * 60)
print()

# Buscar imagens anotadas concluídas
imagens_concluidas = ImagemAnotada.objects.filter(status='concluida')
print(f"Imagens com status 'concluida': {imagens_concluidas.count()}")
print()

total_importadas = 0

for img_anotada in imagens_concluidas:
    anotacoes = img_anotada.anotacoes.all()
    
    for anotacao in anotacoes:
        produto = anotacao.produto
        
        # Verificar se já existe essa imagem para esse produto
        ja_existe = ImagemProduto.objects.filter(
            produto=produto,
            imagem=img_anotada.imagem
        ).exists()
        
        if not ja_existe:
            # Criar entrada no ImagemProduto
            ImagemProduto.objects.create(
                produto=produto,
                imagem=img_anotada.imagem,
                descricao='Importado de anotacao',
                ativa=True
            )
            total_importadas += 1
            print(f"  + {produto.descricao_produto}")

print()
print(f"Total importadas para dataset: {total_importadas}")
print()
print("=" * 60)
print("RESUMO ATUALIZADO")
print("=" * 60)

produtos = ImagemProduto.objects.values(
    'produto_id', 
    'produto__descricao_produto'
).annotate(
    total=Count('id')
).order_by('-total')

for p in produtos[:15]:
    prod_id = p['produto_id']
    nome = p['produto__descricao_produto']
    total = p['total']
    print(f"  ID {prod_id}: {nome} = {total} imgs")

print()
print(f"Total geral: {ImagemProduto.objects.count()} imagens")
print("=" * 60)
