"""
Verifica os dados no banco de dados do sistema de coleta
"""
import sqlite3
from pathlib import Path

db_path = Path('dados_coleta/coleta.db')

if not db_path.exists():
    print("❌ Banco de dados não encontrado!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("╔════════════════════════════════════════════════════════════╗")
print("║     DADOS DO SISTEMA DE COLETA - VerifiK                  ║")
print("╚════════════════════════════════════════════════════════════╝")
print()

# Verificar produtos
cursor.execute("SELECT COUNT(*) FROM produtos")
total_produtos = cursor.fetchone()[0]
print(f"📦 Produtos cadastrados: {total_produtos}")

if total_produtos > 0:
    cursor.execute("SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1")
    produtos = cursor.fetchall()
    print("\nProdutos:")
    for produto_id, descricao, marca in produtos:
        print(f"   {produto_id}. {descricao} - {marca}")

print()

# Verificar imagens coletadas
cursor.execute("SELECT COUNT(*) FROM imagens_coletadas")
total_imagens = cursor.fetchone()[0]
print(f"📸 Imagens coletadas: {total_imagens}")

if total_imagens > 0:
    cursor.execute("""
        SELECT 
            id, 
            caminho_imagem, 
            usuario, 
            data_envio, 
            total_anotacoes,
            sincronizado
        FROM imagens_coletadas 
        ORDER BY data_envio DESC
        LIMIT 10
    """)
    imagens = cursor.fetchall()
    
    print("\nÚltimas 10 imagens:")
    for img_id, caminho, usuario, data, anotacoes, sync in imagens:
        sync_status = "✓" if sync else "✗"
        print(f"   {sync_status} [{img_id}] {Path(caminho).name}")
        print(f"      Usuário: {usuario}")
        print(f"      Data: {data}")
        print(f"      Anotações: {anotacoes}")
        print()

print()

# Verificar anotações
cursor.execute("SELECT COUNT(*) FROM anotacoes")
total_anotacoes = cursor.fetchone()[0]
print(f"🏷️  Anotações (bboxes): {total_anotacoes}")

# Estatísticas por produto
if total_anotacoes > 0:
    cursor.execute("""
        SELECT 
            p.descricao_produto,
            COUNT(*) as total
        FROM anotacoes a
        JOIN produtos p ON a.produto_id = p.id
        GROUP BY p.descricao_produto
        ORDER BY total DESC
    """)
    stats = cursor.fetchall()
    
    print("\nAnotações por produto:")
    for produto, total in stats:
        print(f"   {produto}: {total} anotações")

print()

# Verificar imagens não sincronizadas
cursor.execute("SELECT COUNT(*) FROM imagens_coletadas WHERE sincronizado = 0")
nao_sincronizadas = cursor.fetchone()[0]

print(f"⚠️  Imagens NÃO sincronizadas: {nao_sincronizadas}")

print()
print("=" * 64)

if nao_sincronizadas > 0:
    print("💡 Próximos passos:")
    print("   1. Exportar dados do sistema standalone (botão 'Exportar Dados')")
    print("   2. Usar: python importar_dados_coletados.py <pasta_exportacao>")
    print()
    print("   OU")
    print()
    print("   Importar diretamente do banco de dados SQLite")
else:
    print("✅ Todas as imagens já foram sincronizadas!")

conn.close()
