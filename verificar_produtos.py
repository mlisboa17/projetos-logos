import sqlite3
import os

# Verificar produtos no banco Django
django_db = "db.sqlite3"
if os.path.exists(django_db):
    print("=== PRODUTOS NO BANCO DJANGO ===")
    conn = sqlite3.connect(django_db)
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%produto%'")
    tabelas = cursor.fetchall()
    print("Tabelas encontradas:", tabelas)
    
    # Tentar diferentes nomes de tabela
    possible_tables = ['verifik_produtomae', 'produtos', 'produto']
    
    for table in possible_tables:
        try:
            cursor.execute(f"SELECT id, descricao_produto FROM {table} LIMIT 5")
            produtos = cursor.fetchall()
            if produtos:
                print(f"\n=== PRODUTOS NA TABELA {table} ===")
                for p in produtos:
                    print(f"{p[0]}: {p[1]}")
                break
        except sqlite3.OperationalError as e:
            print(f"Tabela {table} não encontrada: {e}")
    
    conn.close()
else:
    print("Arquivo db.sqlite3 não encontrado")

# Verificar produtos no simulador mobile
mobile_db = "mobile_simulator.db"
if os.path.exists(mobile_db):
    print("\n=== PRODUTOS NO SIMULADOR MOBILE ===")
    conn = sqlite3.connect(mobile_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, descricao_produto, marca FROM produtos")
    produtos = cursor.fetchall()
    for p in produtos:
        print(f"{p[0]}: {p[1]} - {p[2] or 'Sem marca'}")
    conn.close()
else:
    print("\nArquivo mobile_simulator.db não encontrado")