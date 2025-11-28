#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

def investigar_estruturas():
    """
    Investiga a estrutura das tabelas nos dois bancos
    """
    print("=== INVESTIGAÇÃO DE ESTRUTURAS ===\n")
    
    # Investigar Django
    print("📊 BANCO DJANGO (db.sqlite3):")
    try:
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela produtos
        cursor.execute("PRAGMA table_info(verifik_produtomae)")
        colunas = cursor.fetchall()
        
        print("Colunas da tabela verifik_produtomae:")
        for coluna in colunas:
            print(f"  - {coluna[1]} ({coluna[2]})")
        
        # Pegar alguns dados de exemplo
        cursor.execute("SELECT * FROM verifik_produtomae LIMIT 3")
        exemplos = cursor.fetchall()
        
        print("\nExemplos de dados:")
        for exemplo in exemplos:
            print(f"  {exemplo}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro no Django: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Investigar Mobile
    print("📱 BANCO MOBILE (mobile_simulator.db):")
    try:
        conn = sqlite3.connect("mobile_simulator.db")
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela produtos
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        
        print("Colunas da tabela produtos:")
        for coluna in colunas:
            print(f"  - {coluna[1]} ({coluna[2]})")
        
        # Pegar alguns dados de exemplo
        cursor.execute("SELECT * FROM produtos LIMIT 3")
        exemplos = cursor.fetchall()
        
        print("\nExemplos de dados:")
        for exemplo in exemplos:
            print(f"  {exemplo}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro no Mobile: {e}")

if __name__ == "__main__":
    investigar_estruturas()