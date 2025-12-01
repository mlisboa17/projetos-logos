import os
import django
import json
import shutil
from datetime import datetime
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from verifik.models import ProdutoMae

def importar_exportacoes_json(pasta_base):
    """Importa pastas de exportação com formato JSON"""
    pastas_exportacao = [d for d in Path(pasta_base).iterdir() if d.is_dir() and d.name.startswith('exportacao_')]
    
    if not pastas_exportacao:
        print(f"❌ Nenhuma pasta de exportação encontrada em {pasta_base}")
        return 0, set()
    
    print(f"\n📦 Encontradas {len(pastas_exportacao)} pastas de exportação")
    
    total_imagens = 0
    produtos_importados = set()
    
    for pasta_exp in pastas_exportacao:
        print(f"\n🔍 Processando: {pasta_exp.name}")
        
        # Arquivos esperados
        dados_json = pasta_exp / "dados_exportacao.json"
        produtos_json = pasta_exp / "produtos.json"
        pasta_imagens = pasta_exp / "imagens"
        
        if not dados_json.exists() or not produtos_json.exists():
            print(f"  ⚠️ Arquivos JSON não encontrados, pulando...")
            continue
        
        # Carregar produtos
        with open(produtos_json, 'r', encoding='utf-8') as f:
            produtos = json.load(f)
        
        # Carregar dados de exportação
        with open(dados_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Obter informações do produto
        produto_info = dados.get('produto', {})
        produto_nome = produto_info.get('nome', 'DESCONHECIDO')
        
        # Buscar ou criar produto
        produto_mae, created = ProdutoMae.objects.get_or_create(
            descricao_produto=produto_nome.upper(),
            defaults={
                'ativo': True,
                'preco': 0.00,
                'marca': produto_info.get('marca', ''),
                'tipo': produto_info.get('tipo', '')
            }
        )
        
        if created:
            print(f"  ✅ Produto criado: {produto_mae.descricao_produto}")
            produtos_importados.add(produto_mae.descricao_produto)
        else:
            print(f"  ℹ️ Produto existente: {produto_mae.descricao_produto}")
        
        # Processar imagens
        if pasta_imagens.exists():
            imagens = list(pasta_imagens.glob("*.jpg")) + list(pasta_imagens.glob("*.jpeg")) + list(pasta_imagens.glob("*.png"))
            
            for img_path in imagens:
                # Criar diretório de destino
                destino_dir = Path('media/produtos/pendentes') / produto_mae.descricao_produto
                destino_dir.mkdir(parents=True, exist_ok=True)
                
                # Nome único para evitar conflitos
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                novo_nome = f"{produto_mae.descricao_produto}_{timestamp}{img_path.suffix}"
                destino = destino_dir / novo_nome
                
                # Copiar imagem
                shutil.copy2(img_path, destino)
                
                # Caminho relativo para o Django
                caminho_relativo = f"produtos/pendentes/{produto_mae.descricao_produto}/{novo_nome}"
                
                # Criar registro no banco
                ImagemProdutoPendente.objects.create(
                    produto=produto_mae,
                    imagem=caminho_relativo,
                    observacoes=f"Importado de {pasta_exp.name}"
                )
                
                total_imagens += 1
                print(f"  ✅ Imagem importada: {img_path.name}")
        else:
            print(f"  ⚠️ Pasta de imagens não encontrada")
    
    return total_imagens, produtos_importados


def importar_imagens_whatsapp(pasta_imagens, produto_nome="FAMILIA_HEINEKEN"):
    """Importa imagens diretas (ex: do WhatsApp)"""
    pasta = Path(pasta_imagens)
    
    if not pasta.exists():
        print(f"❌ Pasta não encontrada: {pasta_imagens}")
        return 0
    
    # Buscar todas as imagens
    imagens = list(pasta.glob("*.jpg")) + list(pasta.glob("*.jpeg")) + list(pasta.glob("*.png"))
    
    if not imagens:
        print(f"❌ Nenhuma imagem encontrada em {pasta_imagens}")
        return 0
    
    print(f"\n📷 Encontradas {len(imagens)} imagens do WhatsApp")
    
    # Buscar ou criar produto
    produto_mae, created = ProdutoMae.objects.get_or_create(
        descricao_produto=produto_nome.upper(),
        defaults={
            'ativo': True,
            'preco': 0.00,
            'marca': 'HEINEKEN',
            'tipo': 'CERVEJA'
        }
    )
    
    if created:
        print(f"✅ Produto criado: {produto_mae.descricao_produto}")
    
    total = 0
    for img_path in imagens:
        # Criar diretório de destino
        destino_dir = Path('media/produtos/pendentes') / produto_mae.descricao_produto
        destino_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        novo_nome = f"{produto_mae.descricao_produto}_{timestamp}{img_path.suffix}"
        destino = destino_dir / novo_nome
        
        # Copiar imagem
        shutil.copy2(img_path, destino)
        
        # Caminho relativo
        caminho_relativo = f"produtos/pendentes/{produto_mae.descricao_produto}/{novo_nome}"
        
        # Criar registro
        ImagemProdutoPendente.objects.create(
            produto=produto_mae,
            imagem=caminho_relativo,
            observacoes="Importado do WhatsApp"
        )
        
        total += 1
    
    print(f"✅ {total} imagens importadas para {produto_mae.descricao_produto}")
    return total


def main():
    print("="*70)
    print("🚀 IMPORTAÇÃO DE DADOS DO ONEDRIVE")
    print("="*70)
    
    # Caminhos das pastas
    pasta_exportacoes = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\FAMILIA HEINEKEN"
    pasta_whatsapp = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\IMAGENS ( AMSTEL, HEINEKEN, CORONA, SPATEN )"
    
    total_geral = 0
    
    # 1. Importar exportações JSON
    print("\n" + "="*70)
    print("📦 PARTE 1: IMPORTANDO EXPORTAÇÕES DO SISTEMA DE COLETA")
    print("="*70)
    total_exp, produtos = importar_exportacoes_json(pasta_exportacoes)
    total_geral += total_exp
    
    # 2. Importar imagens do WhatsApp
    print("\n" + "="*70)
    print("📷 PARTE 2: IMPORTANDO IMAGENS DO WHATSAPP")
    print("="*70)
    total_wpp = importar_imagens_whatsapp(pasta_whatsapp, "FAMILIA_HEINEKEN_MANUAL")
    total_geral += total_wpp
    
    # 3. Criar lote com todas as imagens importadas
    print("\n" + "="*70)
    print("📋 CRIANDO LOTE COM IMAGENS IMPORTADAS")
    print("="*70)
    
    # Buscar imagens sem lote
    imagens_sem_lote = ImagemProdutoPendente.objects.filter(lote__isnull=True)
    
    if imagens_sem_lote.exists():
        # Criar novo lote
        nome_lote = f"Importação OneDrive - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        lote = LoteFotos.objects.create(
            nome=nome_lote,
            total_imagens=imagens_sem_lote.count()
        )
        
        # Associar imagens ao lote
        imagens_sem_lote.update(lote=lote)
        
        print(f"✅ Lote criado: {lote.nome}")
        print(f"📝 Total de imagens: {lote.total_imagens}")
    else:
        print("ℹ️ Nenhuma imagem sem lote encontrada")
    
    # 4. Resumo final
    print("\n" + "="*70)
    print("📊 RESUMO DA IMPORTAÇÃO")
    print("="*70)
    print(f"📦 Exportações do sistema: {total_exp} imagens")
    print(f"📷 Imagens do WhatsApp: {total_wpp} imagens")
    print(f"✅ TOTAL IMPORTADO: {total_geral} imagens")
    
    if produtos:
        print(f"\n🏷️ Produtos importados das exportações:")
        for prod in sorted(produtos):
            print(f"  • {prod}")
    
    print("\n" + "="*70)
    print("🎉 IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print("\n📌 Próximos passos:")
    print("  1. Acesse: http://127.0.0.1:8000/coleta/lotes/")
    print("  2. Revise as imagens no novo lote")
    print("  3. Aprove as imagens válidas")
    print("  4. Execute aumentação e retreinamento do modelo")


if __name__ == '__main__':
    main()
