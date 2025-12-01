"""
Script para verificar imagens de treino disponíveis e ainda não treinadas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from django.db.models import Count
from pathlib import Path

def verificar_imagens():
    print("=" * 80)
    print("VERIFICAÇÃO DE IMAGENS PARA TREINAMENTO")
    print("=" * 80)
    
    # Total de imagens
    total_imagens = ImagemProduto.objects.count()
    print(f"\n📊 Total de imagens no banco: {total_imagens}")
    
    # Imagens por produto
    print("\n📦 Imagens por produto (Top 20):")
    print("-" * 80)
    stats = ImagemProduto.objects.values('produto__descricao_produto', 'produto__marca').annotate(
        total=Count('id')
    ).order_by('-total')[:20]
    
    for i, s in enumerate(stats, 1):
        produto_nome = s['produto__descricao_produto'] or 'Sem descrição'
        marca = s['produto__marca'] or 'Sem marca'
        print(f"  {i:2d}. {produto_nome:40s} - {marca:20s} - {s['total']:3d} imagens")
    
    # Verificar produtos sem imagens
    print("\n❌ Produtos sem imagens:")
    print("-" * 80)
    produtos_sem_img = ProdutoMae.objects.annotate(
        num_imgs=Count('imagens_treino')
    ).filter(num_imgs=0)
    
    if produtos_sem_img.exists():
        for p in produtos_sem_img[:10]:
            print(f"  - {p.descricao_produto} - {p.marca or 'Sem marca'}")
        if produtos_sem_img.count() > 10:
            print(f"  ... e mais {produtos_sem_img.count() - 10} produtos")
    else:
        print("  ✅ Todos os produtos têm pelo menos uma imagem")
    
    # Verificar arquivos de imagem
    print("\n📁 Verificando arquivos físicos:")
    print("-" * 80)
    
    media_root = Path('media')
    if media_root.exists():
        imagens_fisicas = list(media_root.rglob('*.jpg')) + list(media_root.rglob('*.jpeg')) + list(media_root.rglob('*.png'))
        print(f"  Total de arquivos de imagem em media/: {len(imagens_fisicas)}")
        
        # Verificar diretórios específicos de treino
        diretorios_treino = [
            'media/imagens_treino',
            'media/produtos_treino',
            'verifik/dataset_treino',
            'dataset_corrigido',
        ]
        
        for dir_path in diretorios_treino:
            path = Path(dir_path)
            if path.exists():
                imgs = list(path.rglob('*.jpg')) + list(path.rglob('*.jpeg')) + list(path.rglob('*.png'))
                print(f"  {dir_path}: {len(imgs)} imagens")
    
    # Verificar configurações de paths
    print("\n⚙️ Configurações de Paths:")
    print("-" * 80)
    
    paths_configs = {
        'treinar_modelo_yolo.py': [
            ('Dataset dir', 'dataset_dir'),
            ('Checkpoint', 'checkpoint_path'),
            ('Final model', 'final_model_path'),
        ],
        'treinar_simples.py': [
            ('Dataset path', 'dataset_path'),
            ('Images path', 'images_path'),
            ('Labels path', 'labels_path'),
        ],
    }
    
    for arquivo, configs in paths_configs.items():
        file_path = Path(arquivo)
        if file_path.exists():
            print(f"\n  📄 {arquivo}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for descricao, var_name in configs:
                    # Buscar definição da variável
                    import re
                    pattern = rf'{var_name}\s*=\s*(.+)'
                    match = re.search(pattern, content)
                    if match:
                        valor = match.group(1).strip()
                        # Limpar aspas e comentários
                        valor = valor.split('#')[0].strip()
                        if len(valor) > 100:
                            valor = valor[:100] + '...'
                        print(f"    {descricao:20s}: {valor}")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)

if __name__ == '__main__':
    verificar_imagens()
