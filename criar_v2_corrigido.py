"""
Script corrigido para adicionar sincronização ao sistema v2
"""

# Ler arquivo original
with open('sistema_coleta_standalone.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# 1. Adicionar imports
if 'import requests' not in codigo:
    codigo = codigo.replace(
        'import sqlite3',
        'import sqlite3\nimport requests\nimport tempfile'
    )

# 2. Adicionar constante do Google Drive
if 'LINK_GOOGLE_DRIVE_BANCO' not in codigo:
    codigo = codigo.replace(
        'from pathlib import Path',
        'from pathlib import Path\n\n# Link do Google Drive para sincronização\nLINK_GOOGLE_DRIVE_BANCO = "https://drive.google.com/uc?export=download&id=1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V"'
    )

# 3. Adicionar métodos de sincronização ANTES de criar_interface
metodos_sincronizacao = '''
    def baixar_produtos_google_drive(self):
        """Baixa produtos do Google Drive"""
        try:
            response = requests.get(LINK_GOOGLE_DRIVE_BANCO, timeout=30, allow_redirects=True)
            if response.status_code != 200 or not response.content.startswith(b'SQLite format 3'):
                return None
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_file.write(response.content)
            temp_file.close()
            return temp_file.name
        except:
            return None
    
    def sincronizar_produtos(self):
        """Sincroniza produtos do banco central"""
        try:
            temp_db = self.baixar_produtos_google_drive()
            if not temp_db:
                return False
            
            conn_central = sqlite3.connect(temp_db)
            cursor_central = conn_central.cursor()
            cursor_central.execute("SELECT id, descricao_produto, marca, tipo FROM verifik_produtomae WHERE ativo = 1 ORDER BY descricao_produto")
            produtos_centrais = cursor_central.fetchall()
            conn_central.close()
            
            import os
            os.unlink(temp_db)
            
            if not produtos_centrais:
                return False
            
            conn_local = sqlite3.connect(self.db_path)
            cursor_local = conn_local.cursor()
            cursor_local.execute('DELETE FROM produtos')
            
            for produto in produtos_centrais:
                cursor_local.execute("INSERT INTO produtos (id, descricao_produto, marca, ativo) VALUES (?, ?, ?, 1)", (produto[0], produto[1], produto[2]))
            
            conn_local.commit()
            conn_local.close()
            return True
        except:
            return False
    
    def atualizar_produtos_manual(self):
        """Atualiza produtos manualmente via botão"""
        resposta = messagebox.askyesno("Atualizar Produtos", "Deseja baixar a lista atualizada de produtos?")
        if not resposta:
            return
        
        progress = tk.Toplevel(self.root)
        progress.title("Atualizando...")
        progress.geometry("300x100")
        progress.configure(bg='white')
        progress.transient(self.root)
        progress.grab_set()
        tk.Label(progress, text="🔄 Baixando produtos...", font=('Segoe UI', 12), bg='white').pack(pady=30)
        progress.update()
        
        if self.sincronizar_produtos():
            progress.destroy()
            self.carregar_produtos()
            messagebox.showinfo("Sucesso", "✅ Produtos atualizados!")
        else:
            progress.destroy()
            messagebox.showerror("Erro", "❌ Não foi possível atualizar.\\nVerifique sua internet.")
'''

if 'def baixar_produtos_google_drive' not in codigo:
    codigo = codigo.replace(
        '    def criar_interface(self):',
        metodos_sincronizacao + '\n    def criar_interface(self):'
    )

# 4. Modificar __init__ para chamar sincronização
if 'self.sincronizar_produtos()' not in codigo:
    codigo = codigo.replace(
        '        # Carregar produtos\n        self.carregar_produtos()',
        '        # Sincronizar produtos\n        print("Sincronizando produtos...")\n        if self.sincronizar_produtos():\n            print("✅ Produtos sincronizados!")\n        else:\n            print("⚠️ Usando produtos locais")\n        \n        # Carregar produtos\n        self.carregar_produtos()'
    )

# 5. Adicionar botão de atualizar
if '🔄 Atualizar Produtos' not in codigo:
    codigo = codigo.replace(
        "        tk.Button(\n            frame,\n            text=\"➕ Adicionar Novo Produto\",",
        "        tk.Button(\n            frame,\n            text=\"🔄 Atualizar Produtos\",\n            command=self.atualizar_produtos_manual,\n            bg='#3498db',\n            fg='white',\n            font=('Segoe UI', 10, 'bold'),\n            cursor='hand2'\n        ).pack(fill='x', padx=10, pady=5)\n        \n        tk.Button(\n            frame,\n            text=\"➕ Adicionar Novo Produto\","
    )

# Salvar
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Arquivo atualizado com sucesso!")

# Verificar
with open('sistema_coleta_standalone_v2.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()
    print(f"\n✓ baixar_produtos_google_drive: {'def baixar_produtos_google_drive' in conteudo}")
    print(f"✓ sincronizar_produtos: {'def sincronizar_produtos' in conteudo}")
    print(f"✓ atualizar_produtos_manual: {'def atualizar_produtos_manual' in conteudo}")
    print(f"✓ LINK_GOOGLE_DRIVE_BANCO: {'LINK_GOOGLE_DRIVE_BANCO' in conteudo}")
    print(f"✓ Botão Atualizar: {'🔄 Atualizar Produtos' in conteudo}")
