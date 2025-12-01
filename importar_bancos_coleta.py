"""
Importa dados dos bancos SQLite das exportações do sistema de coleta
"""
import os
import sys
import django
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from django.contrib.auth import get_user_model

User = get_user_model()

# Pastas de exportação com bancos SQLite
pastas_exportacao = [
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025",
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025 (2)",
    r"C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\exportacao_28112025 (3)",
]

print("╔════════════════════════════════════════════════════════════╗")
print("║   IMPORTAR DADOS DOS BANCOS DE COLETA                     ║")
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
total_produtos = 0
total_erros = 0

for idx, pasta in enumerate(pastas_exportacao, 1):
    pasta_path = Path(pasta)
    db_path = pasta_path / 'db.sqlite3'
    
    if not db_path.exists():
        print(f"⚠️  Banco não encontrado em: {pasta}")
        continue
    
    print(f"\n📦 IMPORTANDO PASTA {idx}: {pasta_path.name}")
    print("=" * 60)
    
    # Conectar ao banco SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar produtos
    cursor.execute("SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1")
    produtos_db = cursor.fetchall()
    
    print(f"✓ Produtos no banco: {len(produtos_db)}")
    
    # Verificar imagens coletadas
    cursor.execute("SELECT COUNT(*) FROM imagens_coletadas")
    total_imagens = cursor.fetchone()[0]
    
    print(f"✓ Imagens coletadas: {total_imagens}")
    
    if total_imagens == 0:
        print("  ⚠️  Nenhuma imagem encontrada neste banco")
        conn.close()
        continue
    
    # Criar lote
    lote = LoteFotos.objects.create(
        enviado_por=usuario,
        nome=f"Coleta {pasta_path.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        total_imagens=total_imagens
    )
    
    print(f"✓ Lote criado: #{lote.id}\n")
    
    # Buscar imagens com anotações
    cursor.execute("""
        SELECT 
            i.id,
            i.caminho_imagem,
            i.usuario,
            i.observacoes,
            GROUP_CONCAT(a.produto_id) as produtos_ids
        FROM imagens_coletadas i
        LEFT JOIN anotacoes a ON i.id = a.imagem_id
        GROUP BY i.id
    """)
    
    imagens = cursor.fetchall()
    
    for img_id, caminho, usuario_nome, obs, produtos_ids in imagens:
        try:
            arquivo_origem = pasta_path / caminho.replace('\\', '/')
            
            if not arquivo_origem.exists():
                # Tentar caminho relativo
                arquivo_origem = pasta_path / Path(caminho).name
            
            if not arquivo_origem.exists():
                print(f"  ✗ Arquivo não encontrado: {Path(caminho).name}")
                total_erros += 1
                continue
            
            # Determinar produto
            if produtos_ids:
                produto_id_db = int(produtos_ids.split(',')[0])
                
                # Buscar produto no banco de coleta
                cursor.execute("SELECT descricao_produto, marca FROM produtos WHERE id = ?", (produto_id_db,))
                prod_data = cursor.fetchone()
                
                if prod_data:
                    descricao, marca = prod_data
                    
                    # Criar ou buscar produto no Django
                    produto = ProdutoMae.objects.filter(
                        descricao_produto__iexact=descricao
                    ).first()
                    
                    if not produto:
                        produto = ProdutoMae.objects.create(
                            descricao_produto=descricao.upper(),
                            marca=marca or 'A definir',
                            preco=0.00,
                            ativo=True
                        )
                        total_produtos += 1
                        print(f"  ✓ Produto criado: {descricao}")
                else:
                    # Produto padrão
                    produto = ProdutoMae.objects.first()
                    if not produto:
                        produto = ProdutoMae.objects.create(
                            descricao_produto='PRODUTO GENÉRICO',
                            marca='A definir',
                            preco=0.00,
                            ativo=True
                        )
            else:
                # Sem produto definido
                produto = ProdutoMae.objects.first()
                if not produto:
                    produto = ProdutoMae.objects.create(
                        descricao_produto='PRODUTO GENÉRICO',
                        marca='A definir',
                        preco=0.00,
                        ativo=True
                    )
            
            # Copiar imagem
            media_dir = Path('media/produtos/pendentes')
            media_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            novo_nome = f"coleta_{pasta_path.name}_{timestamp}_{img_id}{arquivo_origem.suffix}"
            destino = media_dir / novo_nome
            
            shutil.copy2(arquivo_origem, destino)
            
            # Criar registro
            ImagemProdutoPendente.objects.create(
                lote=lote,
                produto=produto,
                imagem=f"produtos/pendentes/{novo_nome}",
                status='pendente',
                enviado_por=usuario,
                observacoes=obs or ''
            )
            
            total_importadas += 1
            
            if total_importadas % 20 == 0:
                print(f"  ✓ {total_importadas} imagens importadas...")
                
        except Exception as e:
            print(f"  ✗ Erro ao importar imagem {img_id}: {e}")
            total_erros += 1
    
    conn.close()
    print(f"  ✅ Banco importado: {len(imagens)} imagens processadas")

print("\n" + "=" * 60)
print("✅ IMPORTAÇÃO CONCLUÍDA!")
print("=" * 60)
print(f"\n📊 Estatísticas:")
print(f"   Total importadas: {total_importadas}")
print(f"   Produtos criados: {total_produtos}")
print(f"   Erros: {total_erros}")

print("\n💡 Próximos passos:")
print("   1. Acesse: http://127.0.0.1:8000/coleta/lotes/")
print("   2. Revise os lotes importados")
print("   3. Aprove as imagens")
print("   4. Exporte para o dataset de treinamento!")
