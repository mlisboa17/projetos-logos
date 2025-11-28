"""
Script para adicionar funcionalidade de sincronização automática ao sistema v2
"""

# Ler arquivo original (v1)
with open('sistema_coleta_standalone.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# Adicionar imports
codigo = codigo.replace(
    'import sqlite3',
    'import sqlite3\nimport requests\nimport tempfile'
)

# Adicionar constante do Google Drive logo após os imports
adicionar_depois = 'from pathlib import Path'
link_constant = '''

# ============================================================================
# LINK DO GOOGLE DRIVE PARA SINCRONIZAÇÃO DE PRODUTOS
# ============================================================================
LINK_GOOGLE_DRIVE_BANCO = "https://drive.google.com/uc?export=download&id=1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V"
'''
codigo = codigo.replace(adicionar_depois, adicionar_depois + link_constant)

# Adicionar métodos de sincronização na classe
metodos_sync = '''
    def baixar_produtos_google_drive(self):
        """Baixa produtos do Google Drive"""
        try:
            response = requests.get(LINK_GOOGLE_DRIVE_BANCO, timeout=30, allow_redirects=True)
            
            if response.status_code != 200:
                return None
            
            if not response.content.startswith(b'SQLite format 3'):
                return None
            
            # Salvar temporariamente
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"Erro ao baixar produtos: {e}")
            return None
    
    def sincronizar_produtos(self):
        """Sincroniza produtos do banco central"""
        try:
            # Baixar banco
            temp_db = self.baixar_produtos_google_drive()
            
            if not temp_db:
                # Se falhar, continua com produtos locais
                return False
            
            # Importar produtos
            conn_central = sqlite3.connect(temp_db)
            cursor_central = conn_central.cursor()
            
            cursor_central.execute("""
                SELECT id, descricao_produto, marca, tipo 
                FROM verifik_produtomae 
                WHERE ativo = 1
                ORDER BY descricao_produto
            """)
            produtos_centrais = cursor_central.fetchall()
            conn_central.close()
            
            # Limpar arquivo temporário
            import os
            os.unlink(temp_db)
            
            if not produtos_centrais:
                return False
            
            # Atualizar banco local
            conn_local = sqlite3.connect(self.db_path)
            cursor_local = conn_local.cursor()
            
            # Limpar produtos antigos
            cursor_local.execute('DELETE FROM produtos')
            
            # Inserir produtos novos
            for produto in produtos_centrais:
                cursor_local.execute("""
                    INSERT INTO produtos (id, descricao_produto, marca, ativo)
                    VALUES (?, ?, ?, 1)
                """, (produto[0], produto[1], produto[2]))
            
            conn_local.commit()
            conn_local.close()
            
            return True
            
        except Exception as e:
            print(f"Erro na sincronização: {e}")
            return False
'''

# Inserir métodos após init_database
codigo = codigo.replace(
    '        conn.commit()\n        conn.close()\n\n    def criar_interface(self):',
    '        conn.commit()\n        conn.close()\n' + metodos_sync + '\n    def criar_interface(self):'
)

# Modificar o __init__ para chamar sincronização
codigo = codigo.replace(
    '        # Carregar produtos\n        self.carregar_produtos()',
    '''        # Sincronizar produtos do Google Drive
        print("Sincronizando produtos...")
        if self.sincronizar_produtos():
            print("✅ Produtos sincronizados com sucesso!")
        else:
            print("⚠️ Usando produtos locais")
        
        # Carregar produtos
        self.carregar_produtos()'''
)

# Adicionar botão de atualizar produtos no painel de produtos
codigo_botao_sync = '''
        # Botão para sincronizar produtos
        tk.Button(
            frame,
            text="🔄 Atualizar Produtos",
            command=self.atualizar_produtos_manual,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=5)
'''

codigo = codigo.replace(
    '''        tk.Button(
            frame,
            text="➕ Adicionar Novo Produto",''',
    codigo_botao_sync + '''        
        tk.Button(
            frame,
            text="➕ Adicionar Novo Produto",'''
)

# Adicionar método para atualizar produtos manualmente
codigo = codigo.replace(
    '    def adicionar_produto(self):',
    '''    def atualizar_produtos_manual(self):
        """Atualiza produtos manualmente via botão"""
        resposta = messagebox.askyesno(
            "Atualizar Produtos",
            "Deseja baixar a lista atualizada de produtos do servidor central?"
        )
        
        if not resposta:
            return
        
        # Janela de progresso
        progress = tk.Toplevel(self.root)
        progress.title("Atualizando...")
        progress.geometry("300x100")
        progress.configure(bg='white')
        progress.transient(self.root)
        progress.grab_set()
        
        tk.Label(
            progress,
            text="🔄 Baixando produtos...",
            font=('Segoe UI', 12),
            bg='white'
        ).pack(pady=30)
        
        progress.update()
        
        if self.sincronizar_produtos():
            progress.destroy()
            self.carregar_produtos()
            messagebox.showinfo("Sucesso", "✅ Produtos atualizados com sucesso!")
        else:
            progress.destroy()
            messagebox.showerror("Erro", "❌ Não foi possível atualizar os produtos.\\nVerifique sua conexão com a internet.")
    
    def adicionar_produto(self):'''
)

# Salvar arquivo modificado
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Arquivo sistema_coleta_standalone_v2.py atualizado com sucesso!")
print("\nModificações aplicadas:")
print("- ✅ Imports adicionados (requests, tempfile)")
print("- ✅ Link do Google Drive configurado")
print("- ✅ Método baixar_produtos_google_drive() adicionado")
print("- ✅ Método sincronizar_produtos() adicionado")
print("- ✅ Sincronização automática no início")
print("- ✅ Botão 'Atualizar Produtos' adicionado")
print("- ✅ Método atualizar_produtos_manual() adicionado")
