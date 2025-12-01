import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from django.db.models import Count

print("=" * 80)
print("IMAGENS ADICIONADAS - ImagemProduto")
print("=" * 80)
print()

# Produtos que tiveram imagens adicionadas
produtos_novos = [1, 49, 50, 52, 53, 54]

for prod_id in produtos_novos:
    imagens = ImagemProduto.objects.filter(produto_id=prod_id)
    nome_produto = imagens.first().produto.descricao_produto if imagens.exists() else f"ID {prod_id}"
    
    print(f"\n🆔 ID {prod_id}: {nome_produto} ({imagens.count()} imagens)")
    print("-" * 80)
    
    for img in imagens.order_by('-id'):
        caminho_completo = f"media/{img.imagem}"
        print(f"  ID {img.id}: {img.imagem.name}")
        print(f"     Status: {img.ativa}")
        print(f"     Descrição: {img.descricao}")
        print(f"     Arquivo: {caminho_completo}")
        print()

print()
print("=" * 80)
print("PARA VISUALIZAR AS IMAGENS:")
print("=" * 80)
print()
print("Abra no navegador:")
print("  http://127.0.0.1:8000/media/produtos/anotacoes/2025/11/30/")
print()
print("Ou acesse o Django Admin:")
print("  http://127.0.0.1:8000/admin/verifik/imagemproduto/")
print()
