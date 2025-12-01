import sqlite3
import os

db_path = 'dados_coleta/coleta.db'

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = cursor.fetchall()
print(f"📊 Tabelas encontradas: {[t[0] for t in tabelas]}\n")

# Ver estrutura de cada tabela
for tabela in tabelas:
    nome_tabela = tabela[0]
    print(f"\n=== Tabela: {nome_tabela} ===")
    
    # Ver colunas
    cursor.execute(f"PRAGMA table_info({nome_tabela})")
    colunas = cursor.fetchall()
    print(f"Colunas: {[col[1] for col in colunas]}")
    
    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
    total = cursor.fetchone()[0]
    print(f"Total de registros: {total}")
    
    # Ver primeiros 3 registros
    if total > 0:
        cursor.execute(f"SELECT * FROM {nome_tabela} LIMIT 3")
        registros = cursor.fetchall()
        print(f"\nPrimeiros registros:")
        for i, reg in enumerate(registros, 1):
            print(f"  {i}. {reg[:5] if len(reg) > 5 else reg}")  # Mostra primeiros 5 campos

conn.close()
print("\n✅ Análise concluída")
