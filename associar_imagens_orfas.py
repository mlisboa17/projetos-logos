"""
Script para associar imagens órfãs aos produtos no banco de dados
"""
import os
import django
from pathlib import Path
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from django.core.files import File

def normalizar_nome(nome):
    """Remove caracteres especiais e normaliza nome para comparação"""
    nome = nome.lower()
    nome = re.sub(r'[_\-\s]+', '', nome)
    nome = re.sub(r'\d+ml', '', nome)
    nome = re.sub(r'\d+g', '', nome)
    nome = re.sub(r'latao|lata|longneck|garrafa', '', nome)
    return nome

def encontrar_produto_por_nome_arquivo(nome_arquivo):
    """Tenta encontrar o produto baseado no nome do arquivo"""
    nome_base = Path(nome_arquivo).stem
    nome_normalizado = normalizar_nome(nome_base)
    
    # Tentar por nome exato da pasta
    pasta_pai = Path(nome_arquivo).parent.name
    if pasta_pai and pasta_pai != 'produtos':
        # Mapeamento manual de pastas problemáticas
        mapeamento_manual = {
            'heineiken350ml_lata': 54,  # CERVEJA HEINEKEN LATA 350ML
        }
        
        pasta_lower = pasta_pai.lower()
        if pasta_lower in mapeamento_manual:
            try:
                return ProdutoMae.objects.get(id=mapeamento_manual[pasta_lower])
            except ProdutoMae.DoesNotExist:
                pass
        
        # Buscar por descrição ou marca similar
        produtos = ProdutoMae.objects.filter(ativo=True)
        for produto in produtos:
            desc = normalizar_nome(produto.descricao_produto or '')
            marca = normalizar_nome(produto.marca or '')
            pasta_norm = normalizar_nome(pasta_pai)
            
            if pasta_norm in desc or pasta_norm in marca or desc in pasta_norm or marca in pasta_norm:
                return produto
    
    return None

def associar_imagens_orfas():
    print("=" * 80)
    print("ASSOCIAÇÃO DE IMAGENS ÓRFÃS AOS PRODUTOS")
    print("=" * 80)
    
    # Buscar todas as imagens registradas no banco
    caminhos_banco = set()
    for img in ImagemProduto.objects.all():
        if img.imagem:
            caminho_normalizado = Path(img.imagem.name).as_posix()
            caminhos_banco.add(caminho_normalizado)
    
    # Buscar arquivos físicos
    media_path = Path('media/produtos')
    if not media_path.exists():
        print("❌ Diretório media/produtos/ não encontrado")
        return
    
    img_files = (list(media_path.rglob('*.jpg')) + 
                 list(media_path.rglob('*.jpeg')) + 
                 list(media_path.rglob('*.png')))
    
    # Identificar órfãs
    orfas = []
    for img_file in img_files:
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
            f'media/{caminho_sem_media}' not in caminhos_banco):
            orfas.append(img_file)
    
    print(f"\n📊 Encontradas {len(orfas)} imagens órfãs")
    
    if not orfas:
        print("✅ Não há imagens órfãs para associar!")
        return
    
    # Agrupar por pasta
    por_pasta = {}
    for orfa in orfas:
        pasta = orfa.parent.name
        if pasta not in por_pasta:
            por_pasta[pasta] = []
        por_pasta[pasta].append(orfa)
    
    print(f"\n📂 Distribuição por pasta:")
    for pasta, imgs in sorted(por_pasta.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {pasta:<40} {len(imgs):3d} imagens")
    
    # Processar associações
    print("\n" + "=" * 80)
    print("PROCESSANDO ASSOCIAÇÕES")
    print("=" * 80)
    
    associadas = 0
    nao_associadas = 0
    erros = 0
    
    for pasta, imgs in por_pasta.items():
        print(f"\n📁 Processando pasta: {pasta}")
        
        # Tentar encontrar produto
        produto = encontrar_produto_por_nome_arquivo(str(imgs[0]))
        
        if not produto:
            print(f"   ⚠️  Produto não encontrado para pasta '{pasta}'")
            nao_associadas += len(imgs)
            
            # Listar produtos similares
            pasta_norm = normalizar_nome(pasta)
            produtos_similares = []
            for p in ProdutoMae.objects.filter(ativo=True):
                desc = normalizar_nome(p.descricao_produto or '')
                marca = normalizar_nome(p.marca or '')
                if pasta_norm[:5] in desc or pasta_norm[:5] in marca:
                    produtos_similares.append(p)
            
            if produtos_similares:
                print(f"   💡 Produtos similares encontrados:")
                for i, p in enumerate(produtos_similares[:3], 1):
                    print(f"      {i}. {p.descricao_produto} - {p.marca}")
            continue
        
        print(f"   ✅ Produto encontrado: {produto.descricao_produto} - {produto.marca}")
        print(f"   📸 Associando {len(imgs)} imagens...")
        
        # Associar imagens
        for img_file in imgs:
            try:
                # Calcular caminho relativo ao media/
                caminho_relativo = img_file.relative_to(Path('media'))
                
                # Verificar se já existe
                if ImagemProduto.objects.filter(produto=produto, imagem=str(caminho_relativo)).exists():
                    print(f"      ⚠️  Já existe: {img_file.name}")
                    continue
                
                # Criar registro
                ordem = ImagemProduto.objects.filter(produto=produto).count() + 1
                ImagemProduto.objects.create(
                    produto=produto,
                    imagem=str(caminho_relativo),
                    descricao=f"Importada automaticamente de {pasta}",
                    ordem=ordem,
                    ativa=True
                )
                associadas += 1
                print(f"      ✅ {img_file.name}")
                
            except Exception as e:
                print(f"      ❌ Erro ao associar {img_file.name}: {e}")
                erros += 1
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA ASSOCIAÇÃO")
    print("=" * 80)
    print(f"  ✅ Imagens associadas: {associadas}")
    print(f"  ⚠️  Imagens não associadas: {nao_associadas}")
    print(f"  ❌ Erros: {erros}")
    print(f"  📦 Total processado: {len(orfas)}")
    
    if associadas > 0:
        print(f"\n🎉 {associadas} imagens foram associadas com sucesso!")
        print("   Execute 'python verificar_imagens_treino.py' para ver as estatísticas atualizadas")

if __name__ == '__main__':
    associar_imagens_orfas()
