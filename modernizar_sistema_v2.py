"""
Script para modernizar interface e permitir múltiplos produtos por foto
"""

with open('sistema_coleta_standalone_v2.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# 1. Adicionar import do ttkbootstrap
codigo = codigo.replace(
    'import tkinter as tk\nfrom tkinter import ttk, filedialog, messagebox',
    'import tkinter as tk\nfrom tkinter import filedialog, messagebox\nimport ttkbootstrap as ttk\nfrom ttkbootstrap.constants import *'
)

# 2. Mudar root para usar ttkbootstrap
codigo = codigo.replace(
    'def main():\n    root = tk.Tk()',
    'def main():\n    root = ttk.Window(themename="superhero")  # Tema moderno e escuro'
)

# 3. Atualizar label de contador para mostrar total de produtos marcados
codigo = codigo.replace(
    '        self.label_contador.config(text=f"{total} produto{\'s\' if total != 1 else \'\'} anotado{\'s\' if total != 1 else \'\'}")',
    '''        # Contar produtos únicos
        produtos_unicos = set(bbox['produto_id'] for bbox in self.bboxes)
        total_produtos = len(produtos_unicos)
        self.label_contador.config(
            text=f"{total} bbox{'es' if total != 1 else ''} | {total_produtos} produto{'s' if total_produtos != 1 else ''}"
        )'''
)

# 4. Melhorar mensagem de salvamento para mostrar produtos distintos
codigo = codigo.replace(
    '''            messagebox.showinfo(
                "✅ Sucesso!", 
                f"Imagem salva com {len(self.bboxes)} produto(s) marcado(s)!\\n\\n" +
                f"Arquivo: {os.path.basename(filepath)}\\n\\n" +
                "Você pode carregar outra foto agora."
            )''',
    '''            # Contar produtos distintos
            produtos_distintos = {}
            for bbox in self.bboxes:
                produto_nome = bbox['produto_nome']
                produtos_distintos[produto_nome] = produtos_distintos.get(produto_nome, 0) + 1
            
            detalhes = "\\n".join([f"  • {nome}: {qtd} marca(ções)" for nome, qtd in produtos_distintos.items()])
            
            messagebox.showinfo(
                "✅ Imagem Salva com Sucesso!", 
                f"Total: {len(self.bboxes)} marcação(ões)\\n\\n" +
                f"Produtos marcados:\\n{detalhes}\\n\\n" +
                f"Arquivo: {os.path.basename(filepath)}\\n\\n" +
                "✅ Você pode marcar VÁRIOS produtos na mesma foto!\\n" +
                "Carregue outra foto ou continue marcando."
            )'''
)

# 5. Adicionar instrução sobre múltiplos produtos
codigo = codigo.replace(
    '''        tk.Label(
            frame_instrucao_foto,
            text="Passo 2:",
            font=('Segoe UI', 9, 'bold'),
            bg='white',
            fg='#667eea'
        ).pack()''',
    '''        tk.Label(
            frame_instrucao_foto,
            text="Passo 2: (pode marcar VÁRIOS produtos!)",
            font=('Segoe UI', 9, 'bold'),
            bg='white',
            fg='#667eea'
        ).pack()'''
)

# 6. Atualizar botão limpar para ser mais claro
codigo = codigo.replace(
    '''        tk.Button(
            frame_acoes,
            text="🗑️ Limpar Tudo",
            command=self.limpar_tudo,
            bg='#e74c3c',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            pady=10
        ).pack(fill='x', pady=5)''',
    '''        tk.Button(
            frame_acoes,
            text="🗑️ Limpar Tudo e Recomeçar",
            command=self.limpar_tudo,
            bg='#e74c3c',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            pady=10
        ).pack(fill='x', pady=5)
        
        tk.Label(
            frame_acoes,
            text="Remove todos os produtos marcados",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#e74c3c'
        ).pack()'''
)

# 7. Melhorar lista de anotações para mostrar produtos agrupados
codigo = codigo.replace(
    '''    def atualizar_lista_anotacoes(self):
        """Atualiza a lista de anotações e contador"""
        self.lista_anotacoes.delete(0, tk.END)
        for i, bbox in enumerate(self.bboxes):
            self.lista_anotacoes.insert(tk.END, f"{i+1}. {bbox['produto_nome']}")''',
    '''    def atualizar_lista_anotacoes(self):
        """Atualiza a lista de anotações e contador"""
        self.lista_anotacoes.delete(0, tk.END)
        
        # Agrupar por produto
        produtos_count = {}
        for bbox in self.bboxes:
            nome = bbox['produto_nome']
            produtos_count[nome] = produtos_count.get(nome, 0) + 1
        
        # Mostrar cada anotação com número
        for i, bbox in enumerate(self.bboxes):
            nome = bbox['produto_nome']
            # Mostrar nome curto se muito longo
            nome_display = nome[:35] + '...' if len(nome) > 35 else nome
            self.lista_anotacoes.insert(tk.END, f"{i+1}. {nome_display}")'''
)

# 8. Adicionar dica sobre múltiplos produtos na ajuda inicial
codigo = codigo.replace(
    '''            "COMO USAR (4 passos simples):\\n\\n" +
            "1️⃣ Escolha o PRODUTO na lista à esquerda\\n" +
            "2️⃣ Carregue uma FOTO ou tire com a câmera\\n" +
            "3️⃣ DESENHE retângulos: clique e arraste onde está cada produto\\n" +
            "4️⃣ Clique em SALVAR quando terminar\\n\\n" +
            "💡 DICA: Você pode marcar VÁRIOS produtos na mesma foto!\\n\\n" +
            "Deseja ver um tutorial em vídeo?"''',
    '''            "COMO USAR (4 passos simples):\\n\\n" +
            "1️⃣ Escolha o PRODUTO na lista à esquerda\\n" +
            "2️⃣ Carregue uma FOTO ou tire com a câmera\\n" +
            "3️⃣ DESENHE retângulos: clique e arraste onde está o produto\\n" +
            "4️⃣ Clique em SALVAR quando terminar\\n\\n" +
            "💡 DICAS IMPORTANTES:\\n" +
            "   • Você pode marcar VÁRIOS produtos na mesma foto!\\n" +
            "   • Selecione produto diferente e marque novamente\\n" +
            "   • Duplo clique na lista para remover marcação\\n" +
            "   • Cada produto será salvo separadamente\\n\\n" +
            "Deseja ver um tutorial em vídeo?"'''
)

# 9. Adicionar cores diferentes para cada produto no canvas
codigo = codigo.replace(
    '''            bbox_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='#667eea',
                width=2
            )''',
    '''            # Cores diferentes para produtos diferentes
            cores = ['#667eea', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
            produto_index = self.produto_selecionado[0] % len(cores)
            cor = cores[produto_index]
            
            bbox_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=cor,
                width=3
            )''')

codigo = codigo.replace(
    '''            label_id = self.canvas.create_text(
                x1, y1 - 5,
                text=self.produto_selecionado[1][:30],
                anchor='sw',
                fill='#667eea',
                font=('Segoe UI', 9, 'bold')
            )''',
    '''            label_id = self.canvas.create_text(
                x1, y1 - 5,
                text=self.produto_selecionado[1][:30],
                anchor='sw',
                fill=cor,
                font=('Segoe UI', 10, 'bold'),
                tags='label'
            )
            
            # Adicionar fundo branco para melhor legibilidade
            bbox_text = self.canvas.bbox(label_id)
            if bbox_text:
                self.canvas.create_rectangle(
                    bbox_text[0]-2, bbox_text[1]-2,
                    bbox_text[2]+2, bbox_text[3]+2,
                    fill='white',
                    outline=cor,
                    tags='label_bg'
                )
                self.canvas.tag_lower('label_bg')
                self.canvas.tag_raise(label_id)'''
)

# 10. Melhorar feedback visual ao selecionar produto
codigo = codigo.replace(
    '''                    self.label_produto_atual.config(
                        text=f"✓ {descricao}",
                        bg='#d4edda',
                        fg='#155724'
                    )''',
    '''                    self.label_produto_atual.config(
                        text=f"✓ SELECIONADO: {descricao}",
                        bg='#d4edda',
                        fg='#155724',
                        font=('Segoe UI', 11, 'bold')
                    )'''
)

# Salvar
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Sistema modernizado com sucesso!")
print("\n🎨 Melhorias aplicadas:")
print("- ✅ Tema moderno 'superhero' (ttkbootstrap)")
print("- ✅ Múltiplos produtos na mesma foto")
print("- ✅ Cores diferentes para cada produto")
print("- ✅ Contador mostra produtos únicos")
print("- ✅ Mensagem de salvamento com detalhes")
print("- ✅ Instruções sobre marcar vários produtos")
print("- ✅ Labels com fundo branco para legibilidade")
print("- ✅ Feedback visual melhorado")
print("- ✅ Cada bbox salvo separadamente por produto")
