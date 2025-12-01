"""
Script para importar corretamente as exportações do sistema de coleta,
associando cada imagem aos produtos ESPECÍFICOS detectados nos bboxes.
"""

import os
import django
import json
import shutil
from datetime import datetime
from pathlib import Path
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from verifik.models import ProdutoMae


def mapear_produtos_sistema_django(produtos_json_path):
    """
    Mapeia produtos do sistema de coleta para produtos Django.
    Retorna dicionário {id_coleta: ProdutoMae}
    """
    with open(produtos_json_path, 'r', encoding='utf-8') as f:
        produtos_coleta = json.load(f)
    
    mapeamento = {}
    produtos_nao_encontrados = []
    produtos_criados = []
    
    for produto in produtos_coleta:
        prod_id = produto['id']
        descricao = produto['descricao_produto'].upper().strip()
        marca = produto.get('marca', '').upper().strip()
        
        # Tentar encontrar produto no Django
        produto_django = ProdutoMae.objects.filter(
            descricao_produto__iexact=descricao
        ).first()
        
        if produto_django:
            mapeamento[prod_id] = produto_django
            print(f"  ✅ ID {prod_id:3d} → Django #{produto_django.id:3d}: {descricao}")
        else:
            # Criar produto no Django
            produto_django = ProdutoMae.objects.create(
                descricao_produto=descricao,
                marca=marca,
                ativo=True,
                preco=0.00
            )
            mapeamento[prod_id] = produto_django
            produtos_criados.append(descricao)
            print(f"  ➕ ID {prod_id:3d} → CRIADO #{produto_django.id:3d}: {descricao}")
    
    return mapeamento, produtos_criados


def importar_exportacao_com_produtos_corretos(pasta_base):
    """
    Importa exportações associando cada imagem aos produtos detectados nos bboxes
    """
    pastas_exportacao = sorted([
        d for d in Path(pasta_base).iterdir() 
        if d.is_dir() and d.name.startswith('exportacao_')
    ])
    
    if not pastas_exportacao:
        print(f"❌ Nenhuma pasta de exportação encontrada em {pasta_base}")
        return 0
    
    print(f"\n📦 Encontradas {len(pastas_exportacao)} pastas de exportação\n")
    
    # Carregar produtos uma vez (todas as pastas têm os mesmos produtos)
    produtos_json = pastas_exportacao[0] / "produtos.json"
    print("🔗 MAPEANDO PRODUTOS DO SISTEMA DE COLETA PARA DJANGO")
    print("-" * 70)
    mapeamento_produtos, novos = mapear_produtos_sistema_django(produtos_json)
    print("-" * 70)
    print(f"✅ {len(mapeamento_produtos)} produtos mapeados")
    if novos:
        print(f"➕ {len(novos)} produtos criados no Django")
    print()
    
    total_imagens = 0
    estatisticas_produtos = defaultdict(int)
    
    for pasta_exp in pastas_exportacao:
        print(f"\n📁 Processando: {pasta_exp.name}")
        print("-" * 70)
        
        dados_json = pasta_exp / "dados_exportacao.json"
        pasta_imagens = pasta_exp / "imagens"
        
        if not dados_json.exists():
            print("  ⚠️ Arquivo dados_exportacao.json não encontrado")
            continue
        
        # Carregar dados
        with open(dados_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Processar cada imagem
        for imagem_info in dados.get('imagens', []):
            arquivo = imagem_info.get('arquivo')
            tipo = imagem_info.get('tipo')
            anotacoes = imagem_info.get('anotacoes', [])
            
            img_path = pasta_imagens / arquivo
            
            if not img_path.exists():
                print(f"  ⚠️ Imagem não encontrada: {arquivo}")
                continue
            
            # Para imagens ANOTADAS, criar uma entrada para cada produto detectado
            if tipo == 'anotada' and anotacoes:
                # Agrupar anotações por produto
                produtos_detectados = defaultdict(list)
                for anotacao in anotacoes:
                    prod_id = anotacao['produto_id']
                    produtos_detectados[prod_id].append(anotacao)
                
                # Criar uma imagem para cada produto detectado
                for prod_id, bboxes in produtos_detectados.items():
                    produto_django = mapeamento_produtos.get(prod_id)
                    
                    if not produto_django:
                        print(f"  ❌ Produto ID {prod_id} não encontrado no mapeamento")
                        continue
                    
                    # Criar diretório de destino
                    destino_dir = Path('media/produtos/pendentes') / produto_django.descricao_produto
                    destino_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Nome único
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    novo_nome = f"{produto_django.descricao_produto}_{timestamp}{img_path.suffix}"
                    destino = destino_dir / novo_nome
                    
                    # Copiar imagem
                    shutil.copy2(img_path, destino)
                    
                    # Caminho relativo
                    caminho_relativo = f"produtos/pendentes/{produto_django.descricao_produto}/{novo_nome}"
                    
                    # Criar registro com informações sobre os bboxes
                    observacoes = f"Exportação: {pasta_exp.name}\n"
                    observacoes += f"Imagem original: {arquivo}\n"
                    observacoes += f"Produto detectado: {produto_django.descricao_produto}\n"
                    observacoes += f"Bounding boxes: {len(bboxes)}\n"
                    for idx, bbox in enumerate(bboxes, 1):
                        observacoes += f"  BBox {idx}: x={bbox['x']:.3f}, y={bbox['y']:.3f}, w={bbox['width']:.3f}, h={bbox['height']:.3f}\n"
                    
                    # Salvar dados do bbox em formato JSON para uso posterior
                    bbox_data = json.dumps(bboxes)
                    
                    ImagemProdutoPendente.objects.create(
                        produto=produto_django,
                        imagem=caminho_relativo,
                        observacoes=observacoes.strip(),
                        bbox_data=bbox_data  # Salvar coordenadas do bbox
                    )
                    
                    total_imagens += 1
                    estatisticas_produtos[produto_django.descricao_produto] += 1
                    print(f"  ✅ {arquivo} → {produto_django.descricao_produto} ({len(bboxes)} bbox)")
            
            # Para imagens SEM anotação, criar com produto DESCONHECIDO
            elif tipo == 'sem_anotacao':
                produto_desconhecido, _ = ProdutoMae.objects.get_or_create(
                    descricao_produto='SEM_PRODUTO_DETECTADO',
                    defaults={'ativo': True, 'preco': 0.00}
                )
                
                destino_dir = Path('media/produtos/pendentes') / produto_desconhecido.descricao_produto
                destino_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                novo_nome = f"{produto_desconhecido.descricao_produto}_{timestamp}{img_path.suffix}"
                destino = destino_dir / novo_nome
                
                shutil.copy2(img_path, destino)
                caminho_relativo = f"produtos/pendentes/{produto_desconhecido.descricao_produto}/{novo_nome}"
                
                ImagemProdutoPendente.objects.create(
                    produto=produto_desconhecido,
                    imagem=caminho_relativo,
                    observacoes=f"Exportação: {pasta_exp.name}\nSem produtos detectados"
                )
                
                total_imagens += 1
                estatisticas_produtos[produto_desconhecido.descricao_produto] += 1
                print(f"  ⚠️ {arquivo} → SEM PRODUTOS DETECTADOS")
    
    return total_imagens, estatisticas_produtos


def main():
    print("=" * 70)
    print("🚀 IMPORTAÇÃO INTELIGENTE - SISTEMA DE COLETA COM BBOXES")
    print("=" * 70)
    print("\nEste script:")
    print("  ✅ Lê as anotações JSON de cada exportação")
    print("  ✅ Identifica qual produto foi detectado em cada bbox")
    print("  ✅ Cria entradas separadas para cada produto na mesma imagem")
    print("  ✅ Mapeia produtos do sistema de coleta para Django")
    print("=" * 70)
    
    pasta_exportacoes = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\FAMILIA HEINEKEN"
    
    # Limpar importações anteriores (opcional)
    print("\n⚠️ LIMPEZA DE IMPORTAÇÕES ANTIGAS")
    produtos_genericos = ['DESCONHECIDO', 'FAMILIA_HEINEKEN_MANUAL', 'FAMILIA_HEINEKEN']
    total_removido = 0
    
    for nome in produtos_genericos:
        try:
            produto = ProdutoMae.objects.get(descricao_produto=nome)
            imagens = ImagemProdutoPendente.objects.filter(produto=produto, lote__isnull=True)
            count = imagens.count()
            if count > 0:
                print(f"  🗑️ Removendo {count} imagens de '{nome}'")
                imagens.delete()
                total_removido += count
        except ProdutoMae.DoesNotExist:
            pass
    
    if total_removido > 0:
        print(f"✅ {total_removido} imagens antigas removidas\n")
    else:
        print("✅ Nenhuma imagem antiga para remover\n")
    
    # Importar com produtos corretos
    print("\n" + "=" * 70)
    print("📦 IMPORTANDO EXPORTAÇÕES")
    print("=" * 70)
    
    total_imagens, stats = importar_exportacao_com_produtos_corretos(pasta_exportacoes)
    
    # Criar lote
    print("\n" + "=" * 70)
    print("📋 CRIANDO LOTE")
    print("=" * 70)
    
    imagens_sem_lote = ImagemProdutoPendente.objects.filter(lote__isnull=True)
    
    if imagens_sem_lote.exists():
        nome_lote = f"Importação Inteligente OneDrive - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        lote = LoteFotos.objects.create(
            nome=nome_lote,
            total_imagens=imagens_sem_lote.count()
        )
        
        imagens_sem_lote.update(lote=lote)
        print(f"✅ Lote criado: {lote.nome}")
        print(f"📝 ID do Lote: {lote.id}")
        print(f"📊 Total de imagens: {lote.total_imagens}")
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 ESTATÍSTICAS DA IMPORTAÇÃO")
    print("=" * 70)
    print(f"✅ Total de imagens importadas: {total_imagens}\n")
    
    print("📦 Distribuição por produto:")
    print("-" * 70)
    for produto, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count:3d} imagens → {produto}")
    
    print("\n" + "=" * 70)
    print("🎉 IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print("\n📌 Próximos passos:")
    print(f"  1. Acesse: http://127.0.0.1:8000/verifik/coleta/lotes/")
    print(f"  2. Abra o lote criado")
    print(f"  3. Veja imagens AGRUPADAS por produto")
    print(f"  4. Aprove cada produto individualmente")
    print(f"  5. As imagens irão para o dataset de treinamento organizadas")


if __name__ == '__main__':
    main()
