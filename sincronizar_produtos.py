#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

def sincronizar_produtos():
    """
    Sincroniza produtos do banco Django para o banco do simulador mobile
    """
    # Caminhos dos bancos
    banco_django = "db.sqlite3"
    banco_mobile = "mobile_simulator.db"
    
    print("=== SINCRONIZAÇÃO DE PRODUTOS ===\n")
    
    # Verificar se os bancos existem
    if not os.path.exists(banco_django):
        print(f"❌ Banco Django não encontrado: {banco_django}")
        return False
        
    if not os.path.exists(banco_mobile):
        print(f"❌ Banco mobile não encontrado: {banco_mobile}")
        return False
    
    try:
        # Conectar aos bancos
        conn_django = sqlite3.connect(banco_django)
        conn_mobile = sqlite3.connect(banco_mobile)
        
        cursor_django = conn_django.cursor()
        cursor_mobile = conn_mobile.cursor()
        
        # Buscar produtos do Django (apenas ativos)
        cursor_django.execute("SELECT id, descricao_produto, marca FROM verifik_produtomae WHERE ativo = 1")
        produtos_django = cursor_django.fetchall()
        
        print(f"✅ Encontrados {len(produtos_django)} produtos ativos no banco Django")
        
        # Limpar produtos existentes no mobile
        cursor_mobile.execute("DELETE FROM produtos")
        print("🗑️ Produtos antigos removidos do simulador mobile")
        
        # Inserir produtos do Django no mobile
        produtos_inseridos = 0
        for produto in produtos_django:
            django_id, descricao_produto, marca = produto
            
            # Preparar dados para inserção
            marca_safe = marca if marca else "N/A"
            
            try:
                cursor_mobile.execute("""
                    INSERT INTO produtos (id, descricao_produto, marca, ativo)
                    VALUES (?, ?, ?, ?)
                """, (django_id, descricao_produto, marca_safe, 1))
                
                produtos_inseridos += 1
                print(f"📦 {produtos_inseridos}: {descricao_produto} - {marca_safe}")
                
            except sqlite3.Error as e:
                print(f"❌ Erro ao inserir produto {descricao_produto}: {e}")
        
        # Salvar alterações
        conn_mobile.commit()
        
        # Verificar resultado
        cursor_mobile.execute("SELECT COUNT(*) FROM produtos")
        total_mobile = cursor_mobile.fetchone()[0]
        
        print(f"\n✅ SINCRONIZAÇÃO CONCLUÍDA!")
        print(f"📊 Produtos sincronizados: {produtos_inseridos}")
        print(f"📊 Total no simulador mobile: {total_mobile}")
        
        # Fechar conexões
        conn_django.close()
        conn_mobile.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def verificar_sincronizacao():
    """
    Verifica se a sincronização foi bem sucedida
    """
    print("\n=== VERIFICAÇÃO PÓS-SINCRONIZAÇÃO ===\n")
    
    try:
        # Verificar Django
        conn_django = sqlite3.connect("db.sqlite3")
        cursor_django = conn_django.cursor()
        cursor_django.execute("SELECT COUNT(*) FROM verifik_produtomae")
        total_django = cursor_django.fetchone()[0]
        
        # Verificar Mobile
        conn_mobile = sqlite3.connect("mobile_simulator.db")
        cursor_mobile = conn_mobile.cursor()
        cursor_mobile.execute("SELECT COUNT(*) FROM produtos")
        total_mobile = cursor_mobile.fetchone()[0]
        
        print(f"🏪 Produtos no Django: {total_django}")
        print(f"📱 Produtos no Mobile: {total_mobile}")
        
        if total_django == total_mobile:
            print("✅ Sincronização perfeita!")
        else:
            print("⚠️ Diferença encontrada - verificar logs")
        
        # Mostrar alguns produtos do mobile
        cursor_mobile.execute("SELECT descricao_produto, marca FROM produtos LIMIT 5")
        produtos_sample = cursor_mobile.fetchall()
        
        print("\n📋 Primeiros 5 produtos no simulador mobile:")
        for i, (descricao_produto, marca) in enumerate(produtos_sample, 1):
            print(f"  {i}. {descricao_produto} - {marca}")
        
        conn_django.close()
        conn_mobile.close()
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🔄 Iniciando sincronização de produtos...")
    
    if sincronizar_produtos():
        verificar_sincronizacao()
        print("\n🎉 Processo finalizado com sucesso!")
    else:
        print("\n💥 Falha na sincronização!")