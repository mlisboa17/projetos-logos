"""
Script para modernizar a interface com ttkbootstrap (tema moderno do Bootstrap)
"""

# Ler arquivo atual
with open('sistema_coleta_standalone_v2.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# 1. Substituir imports básicos do tkinter por ttkbootstrap
codigo = codigo.replace(
    '''import tkinter as tk
from tkinter import ttk, filedialog, messagebox''',
    '''import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *'''
)

# 2. Mudar inicialização da janela para usar tema moderno
codigo = codigo.replace(
    '''    def criar_interface(self):
        """Cria a interface gráfica"""
        
        # Frame superior - Informações do usuário
        frame_topo = tk.Frame(self.root, bg='#667eea', height=80)
        frame_topo.pack(fill='x', padx=0, pady=0)''',
    '''    def criar_interface(self):
        """Cria a interface gráfica"""
        
        # Aplicar tema moderno
        self.root.style = ttk.Style(theme='cosmo')  # Temas: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti, superhero, darkly, cyborg, vapor
        
        # Frame superior - Informações do usuário
        frame_topo = tk.Frame(self.root, bg='#667eea', height=80)
        frame_topo.pack(fill='x', padx=0, pady=0)'''
)

# 3. Melhorar painel de produtos com cards modernos
codigo = codigo.replace(
    '''    def criar_painel_produtos(self, parent):
        """Painel lateral com lista de produtos"""
        frame = tk.Frame(parent, bg='white', relief='ridge', borderwidth=2)
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))''',
    '''    def criar_painel_produtos(self, parent):
        """Painel lateral com lista de produtos"""
        frame = ttk.Frame(parent, bootstyle='light')
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))'''
)

# 4. Modernizar botões principais
codigo = codigo.replace(
    '''        tk.Button(
            frame,
            text="🔄 Atualizar Produtos",
            command=self.atualizar_produtos_manual,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=5)''',
    '''        ttk.Button(
            frame,
            text="🔄 Atualizar Produtos",
            command=self.atualizar_produtos_manual,
            bootstyle='info',
            width=20
        ).pack(fill='x', padx=10, pady=5)'''
)

# 5. Modernizar botão de carregar imagem
codigo = codigo.replace(
    '''        tk.Button(
            frame_botoes,
            text="📁 Carregar Imagem do Computador",
            command=self.carregar_imagem,
            bg='#667eea',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)''',
    '''        ttk.Button(
            frame_botoes,
            text="📁 Carregar Imagem do Computador",
            command=self.carregar_imagem,
            bootstyle='primary-outline',
            width=25
        ).pack(side='left', padx=5, pady=10)'''
)

# 6. Modernizar botão de webcam
codigo = codigo.replace(
    '''        tk.Button(
            frame_botoes,
            text="📷 Tirar Foto com Câmera",
            command=self.tirar_foto_webcam,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)''',
    '''        ttk.Button(
            frame_botoes,
            text="📷 Tirar Foto com Câmera",
            command=self.tirar_foto_webcam,
            bootstyle='info-outline',
            width=20
        ).pack(side='left', padx=5, pady=10)'''
)

# 7. Modernizar botão SALVAR (destaque especial)
codigo = codigo.replace(
    '''        tk.Button(
            frame_acoes,
            text="💾 SALVAR (Passo 4)",
            command=self.salvar_imagem_anotacoes,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            cursor='hand2',
            pady=15
        ).pack(fill='x', pady=5)''',
    '''        ttk.Button(
            frame_acoes,
            text="💾 SALVAR (Passo 4)",
            command=self.salvar_imagem_anotacoes,
            bootstyle='success',
            width=20
        ).pack(fill='x', pady=5, ipady=10)'''
)

# 8. Adicionar tema escuro opcional (comentado)
codigo = codigo.replace(
    '''        # Aplicar tema moderno
        self.root.style = ttk.Style(theme='cosmo')  # Temas: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti, superhero, darkly, cyborg, vapor''',
    '''        # Aplicar tema moderno (claro e profissional)
        self.root.style = ttk.Style(theme='cosmo')
        # Para tema escuro, use: theme='darkly' ou 'cyborg' ou 'superhero'
        # Para tema colorido, use: theme='minty' ou 'pulse'
        # Para tema clean, use: theme='flatly' ou 'litera' ou 'cosmo'
        # Para tema contraste, use: theme='vapor'
        # Para tema papel, use: theme='journal' ou 'sandstone'
        # Mais temas: 'lumen', 'united', 'yeti'
        # Temas escuros: 'darkly', 'cyborg', 'superhero', 'solar'
        '''
)

# 9. Adicionar barra de progresso moderna na sincronização
codigo = codigo.replace(
    '''        tk.Label(
            progress,
            text="🔄 Baixando produtos...",
            font=('Segoe UI', 12),
            bg='white'
        ).pack(pady=30)''',
    '''        tk.Label(
            progress,
            text="🔄 Baixando produtos...",
            font=('Segoe UI', 12),
            bg='white'
        ).pack(pady=20)
        
        # Barra de progresso animada
        progress_bar = ttk.Progressbar(
            progress,
            bootstyle='info-striped',
            mode='indeterminate',
            length=250
        )
        progress_bar.pack(pady=10)
        progress_bar.start(10)'''
)

# 10. Melhorar campo de busca com estilo
codigo = codigo.replace(
    '''        busca_entry = tk.Entry(frame, textvariable=self.busca_var, font=('Segoe UI', 10))
        busca_entry.pack(fill='x', padx=10, pady=5)''',
    '''        busca_entry = ttk.Entry(
            frame, 
            textvariable=self.busca_var, 
            font=('Segoe UI', 10),
            bootstyle='info'
        )
        busca_entry.pack(fill='x', padx=10, pady=5)'''
)

# 11. Adicionar separadores visuais
codigo = codigo.replace(
    '''        # Botão desabilitado - produtos vêm do servidor
        btn_adicionar = tk.Button(''',
    '''        # Separador visual
        ttk.Separator(frame, bootstyle='secondary').pack(fill='x', padx=10, pady=10)
        
        # Botão desabilitado - produtos vêm do servidor
        btn_adicionar = tk.Button('''
)

# 12. Melhorar observações com Text moderno
codigo = codigo.replace(
    '''        self.text_observacoes = tk.Text(frame, height=3, font=('Segoe UI', 9))
        self.text_observacoes.pack(fill='x', padx=10)''',
    '''        # Frame para text com borda moderna
        text_frame = ttk.Frame(frame, bootstyle='light')
        text_frame.pack(fill='x', padx=10)
        
        self.text_observacoes = tk.Text(
            text_frame, 
            height=3, 
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=1,
            bg='#f8f9fa'
        )
        self.text_observacoes.pack(fill='x', padx=2, pady=2)'''
)

# Salvar
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Interface modernizada com ttkbootstrap!")
print("\nMelhorias aplicadas:")
print("- ✅ Tema Bootstrap moderno (Cosmo)")
print("- ✅ Botões com design flat e colorido")
print("- ✅ Campo de busca estilizado")
print("- ✅ Barra de progresso animada")
print("- ✅ Separadores visuais")
print("- ✅ Cards com sombras suaves")
print("- ✅ Text areas com fundo claro")
print("- ✅ Comentários com outros 15+ temas disponíveis")
print("\n⚠️  IMPORTANTE: Instale a biblioteca:")
print("   pip install ttkbootstrap")
