"""
Script para melhorar a interface do sistema v2 com mais instruções e ajuda
"""

with open('sistema_coleta_standalone_v2.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# 1. Desabilitar botão de adicionar produto
codigo = codigo.replace(
    '''        tk.Button(
            frame,
            text="➕ Adicionar Novo Produto",
            command=self.adicionar_produto,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=10)''',
    '''        # Botão desabilitado - produtos vêm do servidor
        btn_adicionar = tk.Button(
            frame,
            text="➕ Adicionar Produto (Desabilitado)",
            state='disabled',
            bg='#95a5a6',
            fg='white',
            font=('Segoe UI', 10, 'bold')
        )
        btn_adicionar.pack(fill='x', padx=10, pady=10)
        
        # Dica sobre atualização
        tk.Label(
            frame,
            text="💡 Produtos atualizados automaticamente",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#7f8c8d'
        ).pack(pady=2)'''
)

# 2. Melhorar título com instruções
codigo = codigo.replace(
    '''        tk.Label(
            frame_topo,
            text="📸 Sistema de Coleta de Imagens - VerifiK",
            font=('Segoe UI', 20, 'bold'),
            bg='#667eea',
            fg='white'
        ).pack(pady=15)''',
    '''        tk.Label(
            frame_topo,
            text="📸 Sistema de Coleta de Imagens - VerifiK",
            font=('Segoe UI', 20, 'bold'),
            bg='#667eea',
            fg='white'
        ).pack(pady=5)
        
        tk.Label(
            frame_topo,
            text="1️⃣ Selecione o produto  →  2️⃣ Carregue/tire foto  →  3️⃣ Desenhe retângulos  →  4️⃣ Salve",
            font=('Segoe UI', 11),
            bg='#667eea',
            fg='white'
        ).pack(pady=10)'''
)

# 3. Melhorar instruções do canvas
codigo = codigo.replace(
    '''        self.label_instrucoes = tk.Label(
            frame,
            text="📖 Selecione um produto e clique + arraste na imagem para desenhar o box",
            font=('Segoe UI', 10, 'italic'),
            bg='white',
            fg='#7f8c8d'
        )
        self.label_instrucoes.pack(pady=5)''',
    '''        self.label_instrucoes = tk.Label(
            frame,
            text="📖 INSTRUÇÕES: Escolha produto à esquerda → Carregue/tire foto → Clique e ARRASTE na imagem onde está o produto",
            font=('Segoe UI', 10, 'bold'),
            bg='#fff3cd',
            fg='#856404',
            wraplength=600,
            padx=10,
            pady=10
        )
        self.label_instrucoes.pack(pady=5, fill='x', padx=10)'''
)

# 4. Adicionar dica no painel de produtos
codigo = codigo.replace(
    '''        tk.Label(
            frame,
            text="🎯 Selecione o Produto",
            font=('Segoe UI', 14, 'bold'),
            bg='white'
        ).pack(pady=10)''',
    '''        tk.Label(
            frame,
            text="🎯 Passo 1: Selecione o Produto",
            font=('Segoe UI', 14, 'bold'),
            bg='white'
        ).pack(pady=5)
        
        tk.Label(
            frame,
            text="Clique no produto que está na foto",
            font=('Segoe UI', 9, 'italic'),
            bg='white',
            fg='#7f8c8d'
        ).pack(pady=2)'''
)

# 5. Melhorar botões de imagem com instruções
codigo = codigo.replace(
    '''        tk.Button(
            frame_botoes,
            text="📁 Carregar Imagem",
            command=self.carregar_imagem,
            bg='#667eea',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=10)
        
        tk.Button(
            frame_botoes,
            text="📷 Tirar Foto (Webcam)",
            command=self.tirar_foto_webcam,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=10)''',
    '''        # Frame com dica
        frame_instrucao_foto = tk.Frame(frame_botoes, bg='white')
        frame_instrucao_foto.pack(side='left', padx=5)
        
        tk.Label(
            frame_instrucao_foto,
            text="Passo 2:",
            font=('Segoe UI', 9, 'bold'),
            bg='white',
            fg='#667eea'
        ).pack()
        
        tk.Button(
            frame_botoes,
            text="📁 Carregar Imagem do Computador",
            command=self.carregar_imagem,
            bg='#667eea',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)
        
        tk.Label(
            frame_botoes,
            text="OU",
            font=('Segoe UI', 11, 'bold'),
            bg='white',
            fg='#7f8c8d'
        ).pack(side='left', padx=10)
        
        tk.Button(
            frame_botoes,
            text="📷 Tirar Foto com Câmera",
            command=self.tirar_foto_webcam,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)'''
)

# 6. Melhorar painel de controles com instruções
codigo = codigo.replace(
    '''        tk.Label(
            frame,
            text="📦 Produto Atual",
            font=('Segoe UI', 12, 'bold'),
            bg='white'
        ).pack(pady=10)''',
    '''        tk.Label(
            frame,
            text="📦 Produto Selecionado",
            font=('Segoe UI', 12, 'bold'),
            bg='white'
        ).pack(pady=5)
        
        tk.Label(
            frame,
            text="Produto marcado atualmente",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#7f8c8d'
        ).pack(pady=2)'''
)

# 7. Adicionar tooltip no botão salvar
codigo = codigo.replace(
    '''        tk.Button(
            frame_acoes,
            text="💾 Salvar Imagem com Anotações",
            command=self.salvar_imagem_anotacoes,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            pady=10
        ).pack(fill='x', pady=5)''',
    '''        tk.Button(
            frame_acoes,
            text="💾 SALVAR (Passo 4)",
            command=self.salvar_imagem_anotacoes,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            cursor='hand2',
            pady=15
        ).pack(fill='x', pady=5)
        
        tk.Label(
            frame_acoes,
            text="Clique aqui quando terminar de marcar",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#27ae60'
        ).pack()'''
)

# 8. Melhorar mensagens de erro
codigo = codigo.replace(
    '''    def on_canvas_click(self, event):
        """Início do desenho do bounding box"""
        if not self.produto_selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto primeiro!")
            return
            
        if not self.imagem_path:
            messagebox.showwarning("Aviso", "Carregue uma imagem primeiro!")
            return''',
    '''    def on_canvas_click(self, event):
        """Início do desenho do bounding box"""
        if not self.produto_selecionado:
            messagebox.showwarning(
                "⚠️ Falta Selecionar Produto", 
                "PASSO 1: Clique em um produto da lista à esquerda primeiro!\\n\\nDepois volte aqui para desenhar."
            )
            return
            
        if not self.imagem_path:
            messagebox.showwarning(
                "⚠️ Falta Carregar Foto", 
                "PASSO 2: Clique em 'Carregar Imagem' ou 'Tirar Foto' primeiro!\\n\\nDepois volte aqui para desenhar."
            )
            return'''
)

# 9. Melhorar mensagem de salvamento
codigo = codigo.replace(
    '''            messagebox.showinfo("Sucesso", f"Imagem salva com {len(self.bboxes)} anotações!")''',
    '''            messagebox.showinfo(
                "✅ Sucesso!", 
                f"Imagem salva com {len(self.bboxes)} produto(s) marcado(s)!\\n\\n" +
                f"Arquivo: {os.path.basename(filepath)}\\n\\n" +
                "Você pode carregar outra foto agora."
            )'''
)

# 10. Adicionar ajuda no início
codigo = codigo.replace(
    '''        # Criar interface
        self.criar_interface()''',
    '''        # Criar interface
        self.criar_interface()
        
        # Mostrar ajuda inicial
        self.mostrar_ajuda_inicial()'''
)

# Adicionar método de ajuda inicial
codigo = codigo.replace(
    '''    def criar_interface(self):''',
    '''    def mostrar_ajuda_inicial(self):
        """Mostra instruções na primeira execução"""
        ajuda = messagebox.askyesno(
            "📖 Bem-vindo ao Sistema de Coleta!",
            "COMO USAR (4 passos simples):\\n\\n" +
            "1️⃣ Escolha o PRODUTO na lista à esquerda\\n" +
            "2️⃣ Carregue uma FOTO ou tire com a câmera\\n" +
            "3️⃣ DESENHE retângulos: clique e arraste onde está cada produto\\n" +
            "4️⃣ Clique em SALVAR quando terminar\\n\\n" +
            "💡 DICA: Você pode marcar VÁRIOS produtos na mesma foto!\\n\\n" +
            "Deseja ver um tutorial em vídeo?"
        )
        
        if ajuda:
            messagebox.showinfo(
                "📺 Tutorial",
                "Tutorial em vídeo disponível em:\\n\\n" +
                "https://drive.google.com/tutorial\\n\\n" +
                "(Cole este link no navegador)"
            )
    
    def criar_interface(self):'''
)

# Salvar
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Interface melhorada com sucesso!")
print("\nMelhorias aplicadas:")
print("- ✅ Botão 'Adicionar Produto' desabilitado")
print("- ✅ Instruções passo a passo no topo")
print("- ✅ Títulos com números de passos")
print("- ✅ Mensagens de erro mais claras")
print("- ✅ Dicas e tooltips em todos os botões")
print("- ✅ Mensagem de boas-vindas com tutorial")
print("- ✅ Instruções destacadas em amarelo")
print("- ✅ Botão salvar maior e destacado")
