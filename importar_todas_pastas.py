"""
Script para importar TODAS as pastas de exportação automaticamente
E depois executar a importação para o dataset de treino
"""
import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime
import shutil

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.contrib.auth import get_user_model

User = get_user_model()


def importar_pasta_exportacao(pasta_exportacao):
    """Importa uma única pasta de exportação"""
    
    pasta = Path(pasta_exportacao)
    
    if not pasta.exists():
        print(f"❌ Pasta não encontrada: {pasta}")
        return 0, 0
        
    arquivo_json = pasta / 'dados_exportacao.json'
    
    if not arquivo_json.exists():
        print(f"⚠️ dados_exportacao.json não encontrado em: {pasta.name}")
        return 0, 0
    
    # Ler dados
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        
    usuario_nome = dados.get('usuario', 'Funcionário')
    imagens = dados.get('imagens', [])
    
    if not imagens:
        print(f"⚠️ Nenhuma imagem em: {pasta.name}")
        return 0, 0
    
    # Buscar ou criar usuário
    usuario, _ = User.objects.get_or_create(
        username=usuario_nome.lower().replace(' ', '_'),
        defaults={'first_name': usuario_nome, 'is_active': True}
    )
    
    # Diretório de destino
    media_dir = Path('media/produtos/anotacoes')
    media_dir.mkdir(parents=True, exist_ok=True)
    
    importadas = 0
    anotacoes_total = 0
    
    for img_data in imagens:
        try:
            arquivo_origem = pasta / 'imagens' / img_data['arquivo']
            
            if not arquivo_origem.exists():
                continue
                
            # Criar subpasta por data
            data_pasta = datetime.now().strftime('%Y/%m/%d')
            destino_dir = media_dir / data_pasta
            destino_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar imagem
            arquivo_destino = destino_dir / img_data['arquivo']
            if not arquivo_destino.exists():
                shutil.copy2(arquivo_origem, arquivo_destino)
            
            # Caminho relativo para o Django
            caminho_relativo = f"produtos/anotacoes/{data_pasta}/{img_data['arquivo']}"
            
            # Verificar se já existe
            if ImagemAnotada.objects.filter(imagem=caminho_relativo).exists():
                continue
            
            # Criar registro de imagem
            imagem_anotada = ImagemAnotada.objects.create(
                imagem=caminho_relativo,
                enviado_por=usuario,
                observacoes=img_data.get('observacoes', ''),
                status='concluida',
                total_anotacoes=len(img_data.get('anotacoes', []))
            )
            
            # Criar anotações
            for anotacao_data in img_data.get('anotacoes', []):
                produto_id = anotacao_data['produto_id']
                
                try:
                    produto = ProdutoMae.objects.get(id=produto_id)
                    
                    AnotacaoProduto.objects.create(
                        imagem_anotada=imagem_anotada,
                        produto=produto,
                        bbox_x=anotacao_data['x'],
                        bbox_y=anotacao_data['y'],
                        bbox_width=anotacao_data['width'],
                        bbox_height=anotacao_data['height']
                    )
                    anotacoes_total += 1
                    
                except ProdutoMae.DoesNotExist:
                    pass
                    
            importadas += 1
            
        except Exception as e:
            pass
            
    return importadas, anotacoes_total


def importar_anotadas_para_dataset():
    """
    Importa imagens anotadas para o dataset de treino (ImagemProduto)
    Equivalente ao botão "Importar Anotadas" do sistema web
    """
    print("\n" + "=" * 60)
    print("📥 IMPORTANDO ANOTADAS PARA DATASET DE TREINO")
    print("=" * 60)
    
    # Buscar imagens anotadas concluídas
    imagens_concluidas = ImagemAnotada.objects.filter(status='concluida')
    
    print(f"Encontradas {imagens_concluidas.count()} imagens concluídas")
    
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
                    descricao=f"Importado de anotação - {img_anotada.enviado_por}",
                    ativa=True
                )
                total_importadas += 1
    
    print(f"✅ {total_importadas} imagens adicionadas ao dataset de treino")
    return total_importadas


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   IMPORTAÇÃO AUTOMÁTICA DE TODAS AS PASTAS - VerifiK      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Pasta base com todas as exportações
    pasta_base = Path(r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\Produtos_MarcaHeineken")
    
    if not pasta_base.exists():
        print(f"❌ Pasta não encontrada: {pasta_base}")
        return
    
    # Listar todas as pastas de exportação
    pastas_exportacao = [p for p in pasta_base.iterdir() if p.is_dir() and p.name.startswith('exportacao_')]
    
    print(f"📁 Encontradas {len(pastas_exportacao)} pastas de exportação")
    print()
    
    total_imagens = 0
    total_anotacoes = 0
    
    for pasta in sorted(pastas_exportacao):
        print(f"📂 Processando: {pasta.name}...")
        imgs, anots = importar_pasta_exportacao(pasta)
        total_imagens += imgs
        total_anotacoes += anots
        if imgs > 0:
            print(f"   ✅ {imgs} imagens, {anots} anotações")
    
    print()
    print("=" * 60)
    print(f"📊 RESUMO DA IMPORTAÇÃO:")
    print(f"   Pastas processadas: {len(pastas_exportacao)}")
    print(f"   Total de imagens: {total_imagens}")
    print(f"   Total de anotações: {total_anotacoes}")
    print("=" * 60)
    
    # Agora importar para o dataset de treino
    if total_imagens > 0:
        importar_anotadas_para_dataset()
    
    # Mostrar resumo final
    print()
    print("=" * 60)
    print("📊 RESUMO FINAL DO BANCO:")
    print("=" * 60)
    
    from django.db.models import Count
    produtos = ImagemProduto.objects.values(
        'produto_id', 
        'produto__descricao_produto'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    for p in produtos:
        print(f"  ID {p['produto_id']}: {p['produto__descricao_produto']} = {p['total']} imgs")
    
    print()
    print(f"Total geral: {ImagemProduto.objects.count()} imagens")
    print("=" * 60)
    
    print("\n🎉 Importação completa!")


if __name__ == '__main__':
    main()
