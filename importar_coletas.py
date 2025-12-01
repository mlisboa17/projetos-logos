"""
Script completo para importar pastas de coleta para o VerifiK
Com opções flexíveis de importação
"""
import django
import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


def encontrar_pastas_exportacao(pasta_base):
    """
    Encontra todas as pastas de exportação recursivamente
    Procura por pastas que contenham 'dados_exportacao.json'
    """
    pasta_base = Path(pasta_base)
    pastas_encontradas = []
    
    for item in pasta_base.rglob('dados_exportacao.json'):
        pastas_encontradas.append(item.parent)
    
    return pastas_encontradas


def passo1_importar_pasta(pasta_exportacao):
    """
    Passo 1: Importa uma pasta de exportação para ImagemAnotada
    """
    pasta = Path(pasta_exportacao)
    
    if not pasta.exists():
        print(f"  ❌ Pasta não encontrada: {pasta}")
        return 0, 0
        
    arquivo_json = pasta / 'dados_exportacao.json'
    
    if not arquivo_json.exists():
        print(f"  ⚠️ dados_exportacao.json não encontrado")
        return 0, 0
    
    # Ler dados
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        
    usuario_nome = dados.get('usuario', 'Funcionario')
    if not usuario_nome:
        usuario_nome = 'Funcionario'
    imagens = dados.get('imagens', [])
    
    if not imagens:
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
            print(f"  ⚠️ Erro: {e}")
            
    return importadas, anotacoes_total


def passo2_importar_dataset():
    """
    Passo 2: Importa imagens anotadas para o dataset de treino (ImagemProduto)
    """
    # Buscar imagens anotadas concluídas
    imagens_concluidas = ImagemAnotada.objects.filter(status='concluida')
    
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
    
    return total_importadas, 0


def mostrar_resumo():
    """Mostra resumo do banco de dados"""
    print()
    print("=" * 60)
    print("RESUMO DO BANCO DE DADOS")
    print("=" * 60)
    
    produtos = ImagemProduto.objects.values(
        'produto_id', 
        'produto__descricao_produto'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    for p in produtos[:20]:
        prod_id = p['produto_id']
        nome = p['produto__descricao_produto']
        total = p['total']
        print(f"  ID {prod_id}: {nome} = {total} imgs")
    
    if produtos.count() > 20:
        print(f"  ... e mais {produtos.count() - 20} produtos")
    
    print()
    print(f"Total geral: {ImagemProduto.objects.count()} imagens no dataset")
    print(f"Total anotadas: {ImagemAnotada.objects.count()} imagens anotadas")
    print("=" * 60)


def importar_completo(pasta_base):
    """
    Executa os dois passos: importar pasta + importar dataset
    """
    print()
    print("=" * 60)
    print("IMPORTAÇÃO COMPLETA (PASSO 1 + PASSO 2)")
    print("=" * 60)
    print()
    
    pasta_base = Path(pasta_base)
    
    if not pasta_base.exists():
        print(f"❌ Pasta não encontrada: {pasta_base}")
        return
    
    # Encontrar todas as pastas de exportação
    print(f"🔍 Buscando pastas de exportação em: {pasta_base}")
    pastas = encontrar_pastas_exportacao(pasta_base)
    
    if not pastas:
        print("❌ Nenhuma pasta de exportação encontrada!")
        print("   (Procurando por 'dados_exportacao.json')")
        return
    
    print(f"📁 Encontradas {len(pastas)} pastas de exportação")
    print()
    
    # PASSO 1: Importar todas as pastas
    print("━" * 60)
    print("PASSO 1: IMPORTANDO PASTAS...")
    print("━" * 60)
    
    total_imagens = 0
    total_anotacoes = 0
    
    for pasta in sorted(pastas):
        nome_pasta = pasta.name
        print(f"📂 {nome_pasta}...")
        imgs, anots = passo1_importar_pasta(pasta)
        total_imagens += imgs
        total_anotacoes += anots
        if imgs > 0:
            print(f"   ✅ {imgs} imagens, {anots} anotações")
        else:
            print(f"   ⏭️ Já importada ou vazia")
    
    print()
    print(f"📊 Passo 1 concluído: {total_imagens} imagens, {total_anotacoes} anotações")
    
    # PASSO 2: Importar para dataset
    print()
    print("━" * 60)
    print("PASSO 2: IMPORTANDO PARA DATASET DE TREINO...")
    print("━" * 60)
    
    importadas_dataset = passo2_importar_dataset()
    print(f"✅ {importadas_dataset} imagens adicionadas ao dataset")
    
    # Mostrar resumo
    mostrar_resumo()
    
    print()
    print("🎉 IMPORTAÇÃO COMPLETA FINALIZADA!")


def menu_interativo():
    """Menu interativo para escolher opções"""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       IMPORTADOR DE COLETAS - VerifiK                     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("Opções:")
    print("  1. Importar COMPLETO (Passo 1 + Passo 2) - Uma pasta com subpastas")
    print("  2. Apenas Passo 1 - Importar pastas para ImagemAnotada")
    print("  3. Apenas Passo 2 - Importar anotadas para Dataset de Treino")
    print("  4. Ver resumo do banco de dados")
    print("  5. Sair")
    print()
    
    opcao = input("Escolha uma opção (1-5): ").strip()
    
    if opcao == '1':
        print()
        print("Digite o caminho da pasta raiz (que contém as subpastas de exportação):")
        print("Exemplo: C:\\Users\\gabri\\Downloads\\OneDrive_2025-11-30\\BRUNO SENA CASA CAIADA\\Produtos_MarcaHeineken")
        print()
        pasta = input("Caminho: ").strip().strip('"')
        if pasta:
            importar_completo(pasta)
        
    elif opcao == '2':
        print()
        print("Digite o caminho da pasta raiz:")
        pasta = input("Caminho: ").strip().strip('"')
        if pasta:
            pasta_base = Path(pasta)
            pastas = encontrar_pastas_exportacao(pasta_base)
            print(f"\n📁 Encontradas {len(pastas)} pastas")
            total_imgs = 0
            total_anots = 0
            for p in sorted(pastas):
                print(f"📂 {p.name}...")
                imgs, anots = passo1_importar_pasta(p)
                total_imgs += imgs
                total_anots += anots
                if imgs > 0:
                    print(f"   ✅ {imgs} imagens, {anots} anotações")
            print(f"\n✅ Total: {total_imgs} imagens, {total_anots} anotações")
        
    elif opcao == '3':
        print()
        print("Executando Passo 2...")
        importadas = passo2_importar_dataset()
        print(f"✅ {importadas} imagens adicionadas ao dataset de treino")
        mostrar_resumo()
        
    elif opcao == '4':
        mostrar_resumo()
        
    elif opcao == '5':
        print("Até logo!")
        return False
    
    else:
        print("Opção inválida!")
    
    return True


def main():
    # Se passou argumentos, usar modo direto
    if len(sys.argv) > 1:
        pasta = sys.argv[1]
        importar_completo(pasta)
    else:
        # Modo interativo
        while menu_interativo():
            print()
            input("Pressione ENTER para continuar...")
            print("\n" * 2)


if __name__ == '__main__':
    main()
