#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

def verificar_carregamento_mobile():
    """
    Verifica se o simulador mobile está carregando todos os produtos
    """
    print("=== VERIFICAÇÃO DO CARREGAMENTO NO MOBILE ===\n")
    
    db_path = "mobile_simulator.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database mobile não encontrado: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Executar a mesma query do simulador
        cursor.execute('SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1')
        produtos = cursor.fetchall()
        
        print(f"✅ Produtos ativos encontrados: {len(produtos)}")
        
        # Mostrar primeiros 10 produtos
        print("\n📋 Primeiros 10 produtos que o simulador carregará:")
        for i, produto in enumerate(produtos[:10], 1):
            id_produto, desc, marca = produto
            desc_completa = f"{desc} - {marca}" if marca else desc
            print(f"  {i:2d}. {desc_completa}")
        
        # Verificar se há produtos duplicados
        cursor.execute('SELECT COUNT(*), COUNT(DISTINCT id) FROM produtos WHERE ativo = 1')
        total, unicos = cursor.fetchone()
        
        if total == unicos:
            print(f"\n✅ Sem duplicatas - {total} produtos únicos")
        else:
            print(f"\n⚠️ Possíveis duplicatas - {total} total, {unicos} únicos")
        
        # Verificar produtos por marca (top 5)
        cursor.execute('''
            SELECT marca, COUNT(*) as qtd 
            FROM produtos 
            WHERE ativo = 1 
            GROUP BY marca 
            ORDER BY qtd DESC 
            LIMIT 5
        ''')
        marcas = cursor.fetchall()
        
        print("\n🏷️ Top 5 marcas por quantidade:")
        for marca, qtd in marcas:
            print(f"  {marca}: {qtd} produtos")
        
        conn.close()
        
        print(f"\n🎯 RESUMO:")
        print(f"   - Total de produtos ativos: {len(produtos)}")
        print(f"   - Base de dados: {db_path}")
        print(f"   - Status: Pronto para uso no simulador mobile")
        
    except sqlite3.Error as e:
        print(f"❌ Erro de banco: {e}")
    except Exception as e:
        print(f"❌ Erro geral: {e}")

def comparar_com_django():
    """
    Compara contagem de produtos entre Django e Mobile
    """
    print("\n" + "="*60)
    print("=== COMPARAÇÃO DJANGO vs MOBILE ===\n")
    
    try:
        # Django
        conn_django = sqlite3.connect("db.sqlite3")
        cursor_django = conn_django.cursor()
        cursor_django.execute("SELECT COUNT(*) FROM verifik_produtomae WHERE ativo = 1")
        django_count = cursor_django.fetchone()[0]
        
        # Mobile
        conn_mobile = sqlite3.connect("mobile_simulator.db")
        cursor_mobile = conn_mobile.cursor()
        cursor_mobile.execute("SELECT COUNT(*) FROM produtos WHERE ativo = 1")
        mobile_count = cursor_mobile.fetchone()[0]
        
        print(f"🏪 Produtos no Django: {django_count}")
        print(f"📱 Produtos no Mobile: {mobile_count}")
        
        if django_count == mobile_count:
            print("✅ Sincronização perfeita!")
        else:
            diff = abs(django_count - mobile_count)
            print(f"⚠️ Diferença de {diff} produtos")
        
        conn_django.close()
        conn_mobile.close()
        
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")

if __name__ == "__main__":
    verificar_carregamento_mobile()
    comparar_com_django()
    print("\n🔄 Para re-sincronizar: python sincronizar_produtos.py")
    print("📱 Para abrir simulador: python mobile_simulator.py")