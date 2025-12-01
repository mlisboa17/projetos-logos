"""
Importa múltiplas pastas de exportação do sistema de coleta
"""
import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from django.contrib.auth import get_user_model
from datetime import datetime
import shutil
import json

User = get_user_model()

# Pastas de exportação
pastas_exportacao = [
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025",
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025 (2)",
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025 (3)",
]

print("╔════════════════════════════════════════════════════════════╗")
print("║   IMPORTAR EXPORTAÇÕES DO SISTEMA DE COLETA               ║")
print("╚════════════════════════════════════════════════════════════╝")
print()

# Buscar ou criar usuário
usuario, created = User.objects.get_or_create(
    username='coletor',
    defaults={
        'first_name': 'Sistema de Coleta',
        'is_active': True
    }
)

total_importadas = 0
total_erros = 0
produtos_criados = []

for idx, pasta in enumerate(pastas_exportacao, 1):
    pasta_path = Path(pasta)
    
    if not pasta_path.exists():
        print(f"⚠️  Pasta {idx} não encontrada: {pasta}")
        continue
    
    print(f"\n📦 IMPORTANDO PASTA {idx}: {pasta_path.name}")
    print("=" * 60)
    
    # Verificar se tem arquivo dados_exportacao.json
    arquivo_json = pasta_path / 'dados_exportacao.json'
    pasta_imagens = pasta_path / 'imagens'
    
    if arquivo_json.exists():
        # Formato com JSON (exportação oficial)
        print("✓ Formato: Exportação oficial (com JSON)")
        
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        usuario_nome = dados.get('usuario', 'Funcionário')
        imagens_data = dados.get('imagens', [])
        
        print(f"  Usuário: {usuario_nome}")
        print(f"  Imagens: {len(imagens_data)}")
        
        # Criar lote
        lote = LoteFotos.objects.create(
            enviado_por=usuario,
            nome=f"Exportação {pasta_path.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            total_imagens=len(imagens_data)
        )
        
        print(f"  Lote criado: #{lote.id}\n")
        
        # Importar imagens
        for img_data in imagens_data:
            try:
                arquivo_origem = pasta_imagens / img_data['arquivo']
                
                if not arquivo_origem.exists():
                    print(f"  ✗ Arquivo não encontrado: {img_data['arquivo']}")
                    total_erros += 1
                    continue
                
                # Buscar ou criar produto
                produto_id = img_data.get('produto_id')
                produto_nome = img_data.get('produto_nome', 'Produto Desconhecido')
                
                if produto_id:
                    try:
                        produto = ProdutoMae.objects.get(id=produto_id)
                    except ProdutoMae.DoesNotExist:
                        produto = ProdutoMae.objects.create(
                            descricao_produto=produto_nome.upper(),
                            marca='A definir',
                            preco=0.00,
                            ativo=True
                        )
                        produtos_criados.append(produto_nome)
                else:
                    # Criar produto baseado no nome
                    produto = ProdutoMae.objects.create(
                        descricao_produto=produto_nome.upper(),
                        marca='A definir',
                        preco=0.00,
                        ativo=True
                    )
                    produtos_criados.append(produto_nome)
                
                # Copiar imagem para media/produtos/pendentes
                media_dir = Path('media/produtos/pendentes')
                media_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                novo_nome = f"{produto.descricao_produto.replace(' ', '_')}_{timestamp}_{total_importadas}{arquivo_origem.suffix}"
                destino = media_dir / novo_nome
                
                shutil.copy2(arquivo_origem, destino)
                
                # Criar registro
                ImagemProdutoPendente.objects.create(
                    lote=lote,
                    produto=produto,
                    imagem=f"produtos/pendentes/{novo_nome}",
                    status='pendente',
                    enviado_por=usuario,
                    observacoes=img_data.get('observacoes', '')
                )
                
                total_importadas += 1
                
                if total_importadas % 50 == 0:
                    print(f"  ✓ {total_importadas} imagens importadas...")
                    
            except Exception as e:
                print(f"  ✗ Erro: {e}")
                total_erros += 1
    
    else:
        # Formato sem JSON (apenas imagens em pastas)
        print("✓ Formato: Pastas de produtos (sem JSON)")
        
        # Buscar subpastas (cada subpasta = um produto)
        imagens_encontradas = 0
        
        for subpasta in pasta_path.iterdir():
            if not subpasta.is_dir():
                continue
            
            nome_produto = subpasta.name
            
            # Buscar imagens nesta subpasta
            imagens = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                imagens.extend(list(subpasta.glob(ext)))
            
            if not imagens:
                continue
            
            print(f"  📦 {nome_produto}: {len(imagens)} imagens")
            imagens_encontradas += len(imagens)
            
            # Criar ou buscar produto
            produto = ProdutoMae.objects.filter(
                descricao_produto__icontains=nome_produto
            ).first()
            
            if not produto:
                produto = ProdutoMae.objects.create(
                    descricao_produto=nome_produto.upper().replace('_', ' '),
                    marca='A definir',
                    preco=0.00,
                    ativo=True
                )
                produtos_criados.append(nome_produto)
            
            # Importar imagens
            for img_path in imagens:
                try:
                    media_dir = Path('media/produtos/pendentes')
                    media_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    novo_nome = f"{produto.descricao_produto.replace(' ', '_')}_{timestamp}_{total_importadas}{img_path.suffix}"
                    destino = media_dir / novo_nome
                    
                    shutil.copy2(img_path, destino)
                    
                    # Criar lote se não existir
                    if imagens_encontradas > 0 and total_importadas == 0:
                        lote = LoteFotos.objects.create(
                            enviado_por=usuario,
                            nome=f"Importação {pasta_path.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                            total_imagens=imagens_encontradas
                        )
                        print(f"  Lote criado: #{lote.id}\n")
                    
                    ImagemProdutoPendente.objects.create(
                        lote=lote,
                        produto=produto,
                        imagem=f"produtos/pendentes/{novo_nome}",
                        status='pendente',
                        enviado_por=usuario
                    )
                    
                    total_importadas += 1
                    
                except Exception as e:
                    print(f"  ✗ Erro: {e}")
                    total_erros += 1

print("\n" + "=" * 60)
print("✅ IMPORTAÇÃO CONCLUÍDA!")
print("=" * 60)
print(f"\n📊 Estatísticas:")
print(f"   Total importadas: {total_importadas}")
print(f"   Erros: {total_erros}")
print(f"   Produtos novos criados: {len(set(produtos_criados))}")

if produtos_criados:
    print("\n📦 Produtos criados:")
    for prod in set(produtos_criados)[:10]:
        print(f"   - {prod}")
    if len(set(produtos_criados)) > 10:
        print(f"   ... e mais {len(set(produtos_criados)) - 10}")

print("\n💡 Próximos passos:")
print("   1. Acesse: http://127.0.0.1:8000/coleta/lotes/")
print("   2. Revise os lotes importados")
print("   3. Aprove as imagens")
print("   4. Exporte para o dataset de treinamento!")
