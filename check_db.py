#!/usr/bin/env python3

import sqlite3
import os

print("🔍 Verificando estruturas dos bancos de dados...")

# Verificar mobile_simulator.db
if os.path.exists('mobile_simulator.db'):
    print("\n📊 mobile_simulator.db encontrado!")
    try:
        conn = sqlite3.connect('mobile_simulator.db')
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tabelas: {[t[0] for t in tables]}")
        
        # Verificar estrutura da tabela produtos se existir
        if any('produtos' in str(t) for t in tables):
            cursor.execute("PRAGMA table_info(produtos)")
            columns = cursor.fetchall()
            print(f"Colunas da tabela produtos: {[(c[1], c[2]) for c in columns]}")
            
            # Testar query
            cursor.execute("SELECT * FROM produtos LIMIT 3")
            samples = cursor.fetchall()
            print(f"Exemplo de dados: {samples}")
        
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")
else:
    print("❌ mobile_simulator.db não encontrado")

# Verificar db.sqlite3
if os.path.exists('db.sqlite3'):
    print("\n📊 db.sqlite3 encontrado!")
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tabelas: {[t[0] for t in tables]}")
        
        # Procurar por tabelas relacionadas a produtos
        for table in tables:
            table_name = table[0]
            if 'produto' in table_name.lower():
                print(f"\n🎯 Tabela relacionada a produtos: {table_name}")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"Colunas: {[(c[1], c[2]) for c in columns]}")
                
                # Testar query
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                print(f"Exemplo de dados: {samples}")
        
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")
else:
    print("❌ db.sqlite3 não encontrado")

print("\n✅ Verificação concluída!")