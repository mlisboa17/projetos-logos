"""
Script para listar imagens não treinadas e sua localização
"""
import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae

def localizar_imagens():
    print("=" * 80)
    print("LOCALIZAÇÃO DAS IMAGENS NÃO TREINADAS")
    print("=" * 80)
    
    # Total de imagens
    total_imgs = ImagemProduto.objects.count()
    print(f"\n📊 Total de imagens no banco de dados: {total_imgs}")
    
    # Imagens físicas
    media_path = Path('media/produtos')
    if media_path.exists():
        img_files = list(media_path.rglob('*.jpg')) + list(media_path.rglob('*.jpeg')) + list(media_path.rglob('*.png'))
        print(f"📁 Total de arquivos físicos em media/produtos/: {len(img_files)}")
    else:
        print("❌ Diretório media/produtos/ não encontrado")
        img_files = []
    
    # Listar primeiras 20 imagens do banco
    print("\n📦 Primeiras 20 imagens cadastradas no banco:")
    print("-" * 80)
    imgs = ImagemProduto.objects.select_related('produto').all()[:20]
    
    for i, img in enumerate(imgs, 1):
        produto_nome = img.produto.descricao_produto if img.produto else 'Sem produto'
        marca = img.produto.marca if img.produto else 'Sem marca'
        caminho = img.imagem.name if img.imagem else 'Sem caminho'
        existe = Path(img.imagem.path).exists() if img.imagem else False
        status = "✅" if existe else "❌"
        
        print(f"  {i:2d}. {status} {produto_nome[:30]:30s} - {marca[:15]:15s}")
        print(f"      Caminho: {caminho}")
    
    # Verificar imagens órfãs (no disco mas não no banco)
    print("\n🔍 Verificando imagens no disco que NÃO estão no banco:")
    print("-" * 80)
    
    # Pegar todos os caminhos do banco
    caminhos_banco = set()
    for img in ImagemProduto.objects.all():
        if img.imagem:
            # Normalizar caminho
            caminho_normalizado = Path(img.imagem.name).as_posix()
            caminhos_banco.add(caminho_normalizado)
    
    print(f"Total de caminhos únicos no banco: {len(caminhos_banco)}")
    
    # Verificar arquivos físicos
    orfas = []
    for img_file in img_files:
        # Tentar diferentes formatos de caminho
        try:
            caminho_relativo = img_file.relative_to(Path.cwd()).as_posix()
        except ValueError:
            caminho_relativo = str(img_file).replace('\\', '/')
        
        try:
            caminho_sem_media = str(img_file.relative_to(Path('media'))).replace('\\', '/')
        except ValueError:
            caminho_sem_media = str(img_file).replace('\\', '/')
        
        if (caminho_relativo not in caminhos_banco and 
            caminho_sem_media not in caminhos_banco and
            f"media/{caminho_sem_media}" not in caminhos_banco and
            f"produtos/{caminho_sem_media.split('produtos/')[-1]}" not in caminhos_banco):
            orfas.append(img_file)
    
    if orfas:
        print(f"\n❌ Encontradas {len(orfas)} imagens ÓRFÃS (no disco mas não no banco):")
        for img in orfas[:10]:
            try:
                caminho_exibir = img.relative_to(Path.cwd())
            except ValueError:
                caminho_exibir = img
            print(f"  - {caminho_exibir}")
        if len(orfas) > 10:
            print(f"  ... e mais {len(orfas) - 10} arquivos")
    else:
        print("✅ Todas as imagens físicas estão registradas no banco")
    
    # Verificar imagens quebradas (no banco mas não no disco)
    print("\n🔍 Verificando imagens cadastradas mas AUSENTES no disco:")
    print("-" * 80)
    
    quebradas = []
    for img in ImagemProduto.objects.all():
        if img.imagem:
            try:
                if not Path(img.imagem.path).exists():
                    quebradas.append(img)
            except:
                quebradas.append(img)
    
    if quebradas:
        print(f"\n❌ Encontradas {len(quebradas)} imagens QUEBRADAS (cadastradas mas arquivo não existe):")
        for img in quebradas[:10]:
            produto = img.produto.descricao_produto if img.produto else 'Sem produto'
            print(f"  - {produto[:40]:40s} | {img.imagem.name if img.imagem else 'N/A'}")
        if len(quebradas) > 10:
            print(f"  ... e mais {len(quebradas) - 10} registros")
    else:
        print("✅ Todas as imagens cadastradas existem no disco")
    
    # Resumo por diretório
    print("\n📂 Distribuição de imagens por diretório:")
    print("-" * 80)
    
    dirs_count = {}
    for img_file in img_files:
        parent_dir = img_file.parent.name
        dirs_count[parent_dir] = dirs_count.get(parent_dir, 0) + 1
    
    for dir_name, count in sorted(dirs_count.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {dir_name:30s}: {count:3d} imagens")
    
    print("\n" + "=" * 80)
    print("📍 LOCALIZAÇÃO RESUMIDA:")
    print("=" * 80)
    print(f"  Banco de dados: {total_imgs} registros")
    print(f"  Disco (media/produtos/): {len(img_files)} arquivos")
    print(f"  Órfãs (disco sem banco): {len(orfas)} arquivos")
    print(f"  Quebradas (banco sem disco): {len(quebradas)} registros")
    print("=" * 80)

if __name__ == '__main__':
    localizar_imagens()
