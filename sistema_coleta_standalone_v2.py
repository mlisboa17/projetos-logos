"""
Sistema de Coleta de Imagens para Funcionários - Standalone
Aplicação offline para coletar fotos de produtos com anotações
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Link do Google Drive para sincronização de produtos (download)
LINK_GOOGLE_DRIVE_BANCO = "https://drive.google.com/uc?export=download&id=1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V"

# Pasta Google Drive para exportação de imagens coletadas
# INSTRUÇÕES PARA CONFIGURAR:
# 
# OPÇÃO 1 - Google Drive para Desktop (RECOMENDADO):
#   1. Instale: https://www.google.com/drive/download/
#   2. Faça login com sua conta Google
#   3. A pasta ficará em: C:\Users\SEU_USUARIO\Google Drive\
#   4. Cole o caminho abaixo, exemplo:
#      PASTA_EXPORTACAO_DRIVE = r"C:\Users\mlisb\Google Drive\VerifiK - Coletas"
#
# OPÇÃO 2 - OneDrive (se já usa):
#   1. Crie pasta em: C:\Users\SEU_USUARIO\OneDrive\VerifiK
#   2. Cole o caminho abaixo
#
# Deixe vazio ("") para escolher pasta manualmente toda vez
PASTA_EXPORTACAO_DRIVE = r""  # Cole o caminho completo aqui

import sqlite3
import requests
import tempfile


class SistemaColetaImagens:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Coleta de Imagens - VerifiK")
        
        # Detectar tamanho da tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Usar 95% da tela disponível
        window_width = int(screen_width * 0.95)
        window_height = int(screen_height * 0.95)
        
        # Centralizar janela
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.state('zoomed')  # Maximizar janela
        self.root.configure(bg='#f5f6fa')
        
        # Configurar evento de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        
        # Variáveis
        self.imagem_atual = None
        self.imagem_original = None
        self.imagem_path = None
        self.foto_pil = None
        self.canvas_image = None
        self.bboxes = []  # Lista de bounding boxes
        self.inicio_bbox = None
        self.bbox_temp = None
        self.produto_selecionado = None
        self.usuario_nome = ""
        self.dados_nao_salvos = False  # Flag para rastrear dados não salvos
        
        # Diretórios
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = self.base_dir / "dados_coleta"
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "coleta.db"
        
        # Inicializar banco de dados
        self.init_database()
        
        # Sincronizar produtos do Google Drive ANTES de criar interface
        self.sincronizar_produtos()
        
        # Criar interface
        self.criar_interface()
        
        # Mostrar ajuda inicial
        self.mostrar_ajuda_inicial()
        
        # Carregar produtos
        self.carregar_produtos()
        
    def init_database(self):
        """Inicializa o banco de dados SQLite local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de produtos (será preenchida manualmente ou importada)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao_produto TEXT NOT NULL,
                marca TEXT,
                ativo INTEGER DEFAULT 1
            )
        ''')
        
        # Tabela de imagens coletadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagens_coletadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caminho_imagem TEXT NOT NULL,
                tipo TEXT NOT NULL,
                usuario TEXT,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_anotacoes INTEGER DEFAULT 0,
                observacoes TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de anotações (bounding boxes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anotacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imagem_id INTEGER,
                produto_id INTEGER,
                bbox_x REAL,
                bbox_y REAL,
                bbox_width REAL,
                bbox_height REAL,
                FOREIGN KEY (imagem_id) REFERENCES imagens_coletadas(id),
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        

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
            messagebox.showerror("Erro", "❌ Não foi possível atualizar.\nVerifique sua internet.")

    def mostrar_ajuda_inicial(self):
        """Mostra instruções na primeira execução"""
        ajuda = messagebox.askyesno(
            "📖 Bem-vindo ao Sistema de Coleta!",
            "COMO USAR (4 passos simples):\n\n" +
            "1️⃣ Escolha o PRODUTO na lista à esquerda\n" +
            "2️⃣ Carregue uma FOTO ou tire com a câmera\n" +
            "3️⃣ DESENHE retângulos: clique e arraste onde está o produto\n" +
            "4️⃣ Clique em SALVAR quando terminar\n\n" +
            "💡 DICAS IMPORTANTES:\n" +
            "   • Você pode marcar VÁRIOS produtos na mesma foto!\n" +
            "   • Selecione produto diferente e marque novamente\n" +
            "   • Duplo clique na lista para remover marcação\n" +
            "   • Cada produto será salvo separadamente\n\n" +
            "Deseja ver um tutorial em vídeo?"
        )
        
        if ajuda:
            messagebox.showinfo(
                "📺 Tutorial",
                "Tutorial em vídeo disponível em:\n\n" +
                "https://drive.google.com/tutorial\n\n" +
                "(Cole este link no navegador)"
            )
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        
        # Aplicar tema moderno (claro e profissional)
        # Para tema escuro, use: theme='darkly' ou 'cyborg' ou 'superhero'
        # Para tema colorido, use: theme='minty' ou 'pulse'
        # Para tema clean, use: theme='flatly' ou 'litera' ou 'cosmo'
        # Para tema contraste, use: theme='vapor'
        # Para tema papel, use: theme='journal' ou 'sandstone'
        # Mais temas: 'lumen', 'united', 'yeti'
        # Temas escuros: 'darkly', 'cyborg', 'superhero', 'solar'
        
        
        # Frame superior - Informações do usuário
        frame_topo = tk.Frame(self.root, bg='#667eea', height=80)
        frame_topo.pack(fill='x', padx=0, pady=0)
        
        tk.Label(
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
        ).pack(pady=10)
        
        # Frame principal - 3 colunas
        frame_principal = tk.Frame(self.root, bg='#f5f6fa')
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configurar pesos das colunas para responsividade
        frame_principal.grid_rowconfigure(0, weight=1)
        frame_principal.grid_columnconfigure(0, weight=1, minsize=280)  # Produtos
        frame_principal.grid_columnconfigure(1, weight=5, minsize=700)  # Imagem (MAIOR)
        frame_principal.grid_columnconfigure(2, weight=1, minsize=300)  # Controles
        
        # Coluna 1 - Lista de produtos
        self.criar_painel_produtos(frame_principal)
        
        # Coluna 2 - Canvas de imagem
        self.criar_painel_imagem(frame_principal)
        
        # Coluna 3 - Controles e anotações
        self.criar_painel_controles(frame_principal)
        
    def criar_painel_produtos(self, parent):
        """Painel lateral com lista de produtos"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # Cabeçalho Passo 1
        header_frame = tk.Frame(frame, bg='#3498db', relief='raised', bd=2)
        header_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="📦 PASSO 1: Selecione o Produto",
            font=('Segoe UI', 13, 'bold'),
            bg='#3498db',
            fg='white',
            pady=8
        ).pack()
        
        tk.Label(
            frame,
            text="👆 Clique no produto que está na foto",
            font=('Segoe UI', 9),
            bg='white',
            fg='#34495e'
        ).pack(pady=2)
        
        # Campo de busca com ícone
        search_container = tk.Frame(frame, bg='white')
        search_container.pack(fill='x', padx=10, pady=(5, 0))
        
        tk.Label(
            search_container, 
            text="🔍", 
            bg='white', 
            font=('Segoe UI', 12)
        ).pack(side='left', padx=(0, 5))
        
        self.busca_var = tk.StringVar()
        self.busca_var.trace('w', self.filtrar_produtos)
        
        busca_entry = ttk.Entry(
            search_container, 
            textvariable=self.busca_var, 
            font=('Segoe UI', 10))
        busca_entry.pack(fill='x', padx=10, pady=5)
        
        # Lista de produtos com altura limitada
        frame_lista = tk.Frame(frame, bg='white')
        frame_lista.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(frame_lista)
        scrollbar.pack(side='right', fill='y')
        
        self.lista_produtos = tk.Listbox(
            frame_lista,
            yscrollcommand=scrollbar.set,
            font=('Segoe UI', 10),
            selectmode='single',
            activestyle='none',
            selectbackground='#667eea',
            selectforeground='white'
        )
        self.lista_produtos.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.lista_produtos.yview)
        
        self.lista_produtos.bind('<<ListboxSelect>>', self.on_produto_selecionado)
        
        # Botão de atualizar com estilo
        btn_atualizar = tk.Button(
            frame,
            text="🔄 Atualizar Lista de Produtos",
            command=self.atualizar_produtos_manual,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='raised',
            bd=2,
            cursor='hand2'
        )
        btn_atualizar.pack(fill='x', padx=10, pady=5)
        
        # Separador visual
        ttk.Separator(frame).pack(fill='x', padx=10, pady=10)
        
        # Botão desabilitado - produtos vêm do servidor
        btn_adicionar = tk.Button(
            frame,
            text="➕ Adicionar Produto (Desabilitado)",
            state='disabled',
            bg='#95a5a6',
            fg='white',
            font=('Segoe UI', 10, 'bold')
        )
        btn_adicionar.pack(fill='x', padx=10, pady=10)
        
        # Dica sobre atualização com fundo colorido
        dica_frame = tk.Frame(frame, bg='#d5f4e6', relief='solid', bd=1)
        dica_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            dica_frame,
            text="✅ Produtos sincronizados automaticamente na nuvem",
            font=('Segoe UI', 8, 'bold'),
            bg='#d5f4e6',
            fg='#27ae60',
            pady=5
        ).pack()
        
    def criar_painel_imagem(self, parent):
        """Painel central com canvas para desenhar bounding boxes"""
        frame = tk.Frame(parent, bg='white', relief='ridge', borderwidth=2)
        frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Cabeçalho Passo 2
        header_passo2 = tk.Frame(frame, bg='#9b59b6', relief='raised', bd=2)
        header_passo2.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header_passo2,
            text="📸 PASSO 2: Carregar ou Tirar Foto",
            font=('Segoe UI', 13, 'bold'),
            bg='#9b59b6',
            fg='white',
            pady=8
        ).pack()
        
        # Botões superiores
        frame_botoes = tk.Frame(frame, bg='white')
        frame_botoes.pack(fill='x', pady=10)
        
        # Dica importante
        dica_varios = tk.Frame(frame, bg='#fff3cd', relief='solid', bd=1)
        dica_varios.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(
            dica_varios,
            text="⭐ DICA: Você pode marcar VÁRIOS produtos na mesma foto!",
            font=('Segoe UI', 9, 'bold'),
            bg='#fff3cd',
            fg='#856404',
            pady=5
        ).pack()
        
        # Botão Carregar Imagem
        btn_carregar = tk.Button(
            frame_botoes,
            text="📂 Carregar do Computador",
            command=self.carregar_imagem,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief='raised',
            bd=3,
            cursor='hand2',
            padx=20,
            pady=10
        )
        btn_carregar.pack(side='left', padx=5)
        
        tk.Label(
            frame_botoes,
            text="OU",
            font=('Segoe UI', 12, 'bold'),
            bg='white',
            fg='#95a5a6'
        ).pack(side='left', padx=15)
        
        # Botão Câmera
        btn_camera = tk.Button(
            frame_botoes,
            text="📷 Tirar Foto Agora",
            command=self.tirar_foto_webcam,
            bg='#e74c3c',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief='raised',
            bd=3,
            cursor='hand2',
            padx=20,
            pady=10
        )
        btn_camera.pack(side='left', padx=5)
        
        # Canvas para desenhar
        frame_canvas = tk.Frame(frame, bg='#e0e0e0', relief='sunken', borderwidth=2)
        frame_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            frame_canvas,
            bg='#f0f0f0',
            cursor='crosshair'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Instruções detalhadas
        instrucoes_frame = tk.Frame(frame, bg='#e8f5e9', relief='ridge', bd=2)
        instrucoes_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            instrucoes_frame,
            text="👉 COMO USAR:",
            font=('Segoe UI', 11, 'bold'),
            bg='#e8f5e9',
            fg='#1b5e20'
        ).pack(anchor='w', padx=10, pady=(5, 0))
        
        instrucoes_texto = [
            "1️⃣ Clique em um produto da lista à esquerda",
            "2️⃣ Carregue uma foto ou tire com a câmera",
            "3️⃣ Clique e ARRASTE na foto para marcar o produto",
            "4️⃣ Repita o passo 1 e 3 para marcar outros produtos na MESMA foto",
            "5️⃣ Quando terminar TODOS os produtos da foto, clique em SALVAR ANOTAÇÕES",
            "6️⃣ Ao final do dia, clique em EXPORTAR DADOS para enviar ao servidor"
        ]
        
        for inst in instrucoes_texto:
            tk.Label(
                instrucoes_frame,
                text=inst,
                font=('Segoe UI', 9),
                bg='#e8f5e9',
                fg='#2e7d32'
            ).pack(anchor='w', padx=20, pady=2)
        
        tk.Label(
            instrucoes_frame,
            text="",
            bg='#e8f5e9'
        ).pack(pady=2)
        
        self.label_instrucoes = tk.Label(
            frame,
            text="📍 DICA: Clique e ARRASTE na imagem onde está o produto",
            font=('Segoe UI', 10, 'bold'),
            bg='#fff3cd',
            fg='#856404',
            wraplength=600,
            padx=10,
            pady=10
        )
        self.label_instrucoes.pack(pady=5, fill='x', padx=10)
        
        # Eventos do canvas
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
    def criar_painel_controles(self, parent):
        """Painel direito com controles e lista de anotações"""
        # Frame com scrollbar para telas pequenas
        container = tk.Frame(parent, bg='white')
        container.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        
        # Canvas com scrollbar
        canvas_scroll = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar_vertical = tk.Scrollbar(container, orient='vertical', command=canvas_scroll.yview)
        
        frame = tk.Frame(canvas_scroll, bg='white', relief='ridge', borderwidth=2)
        
        # Configurar scrollbar
        frame.bind('<Configure>', lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox('all')))
        canvas_scroll.create_window((0, 0), window=frame, anchor='nw')
        canvas_scroll.configure(yscrollcommand=scrollbar_vertical.set)
        
        # Empacotar canvas e scrollbar
        canvas_scroll.pack(side='left', fill='both', expand=True)
        scrollbar_vertical.pack(side='right', fill='y')
        
        # Cabeçalho Produto Selecionado
        header_produto = tk.Frame(frame, bg='#e67e22', relief='raised', bd=2)
        header_produto.pack(fill='x')
        
        tk.Label(
            header_produto,
            text="📦 Produto Selecionado",
            font=('Segoe UI', 12, 'bold'),
            bg='#e67e22',
            fg='white',
            pady=8
        ).pack()
        
        tk.Label(
            frame,
            text="Produto marcado atualmente",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#7f8c8d'
        ).pack(pady=2)
        
        self.label_produto_atual = tk.Label(
            frame,
            text="Nenhum produto selecionado",
            font=('Segoe UI', 10),
            bg='#fff3cd',
            fg='#856404',
            wraplength=250,
            padx=10,
            pady=5
        )
        self.label_produto_atual.pack(fill='x', padx=10)
        
        # Contador com mais detalhes
        stats_frame = tk.Frame(frame, bg='#e3f2fd', relief='ridge', bd=2)
        stats_frame.pack(fill='x', padx=10, pady=(20, 10))
        
        tk.Label(
            stats_frame,
            text="📊 Estatísticas",
            font=('Segoe UI', 12, 'bold'),
            bg='#e3f2fd',
            fg='#1565c0'
        ).pack(pady=5)
        
        self.label_contador = tk.Label(
            stats_frame,
            text="0 produtos marcados",
            font=('Segoe UI', 16, 'bold'),
            bg='#1976d2',
            fg='white',
            pady=15
        )
        self.label_contador.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            stats_frame,
            text="👆 Total de retângulos desenhados nesta foto",
            font=('Segoe UI', 8),
            bg='#e3f2fd',
            fg='#424242'
        ).pack(pady=(0, 5))
        
        # Lista de anotações com altura limitada
        tk.Label(
            frame,
            text="📋 Anotações Criadas",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        ).pack(pady=(20, 5))
        
        frame_lista_anotacoes = tk.Frame(frame, bg='white')
        frame_lista_anotacoes.pack(fill='x', padx=10, pady=5)  # fill='x' ao invés de expand=True
        
        scrollbar = tk.Scrollbar(frame_lista_anotacoes)
        scrollbar.pack(side='right', fill='y')
        
        self.lista_anotacoes = tk.Listbox(
            frame_lista_anotacoes,
            yscrollcommand=scrollbar.set,
            font=('Segoe UI', 10),
            selectmode='single',
            activestyle='none',
            selectbackground='#e74c3c',
            selectforeground='white',
            height=10,
            width=35
        )
        self.lista_anotacoes.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.lista_anotacoes.yview)
        
        self.lista_anotacoes.bind('<Double-Button-1>', self.remover_anotacao_selecionada)
        
        tk.Label(
            frame,
            text="💡 Dica: Dê duplo clique para remover",
            font=('Segoe UI', 8, 'italic'),
            bg='white',
            fg='#95a5a6'
        ).pack()
        
        # Observações (campo maior para ver melhor)
        tk.Label(
            frame,
            text="📝 Observações",
            font=('Segoe UI', 9, 'bold'),
            bg='white'
        ).pack(pady=(5, 2))
        
        self.text_observacoes = tk.Text(
            frame, 
            height=3,
            font=('Segoe UI', 10),
            relief='solid',
            borderwidth=1,
            bg='#f8f9fa',
            wrap='word'
        )
        self.text_observacoes.pack(fill='x', padx=10, pady=2)
        
        # Botões de ação (compactos)
        frame_acoes = tk.Frame(frame, bg='white')
        frame_acoes.pack(fill='x', pady=5, padx=10)
        
        # Botão Limpar (compacto)
        tk.Button(
            frame_acoes,
            text="🧽 Limpar",
            command=self.limpar_tudo,
            bg='#95a5a6',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='raised',
            bd=2,
            cursor='hand2',
            pady=5
        ).pack(fill='x', pady=2)
        
        # Botão Salvar (compacto)
        tk.Button(
            frame_acoes,
            text="✅ SALVAR ANOTAÇÕES",
            command=self.salvar_anotacoes,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='raised',
            bd=3,
            cursor='hand2',
            pady=8
        ).pack(fill='x', pady=2)
        
        # Botão Exportar (compacto)
        tk.Button(
            frame_acoes,
            text="📤 EXPORTAR DADOS",
            command=self.exportar_dados,
            bg='#f39c12',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='raised',
            bd=2,
            cursor='hand2',
            pady=6
        ).pack(fill='x', pady=2)
        
        # Dica sobre exportar (compacta)
        tk.Label(
            frame,
            text="💡 Use EXPORTAR no fim do dia",
            font=('Segoe UI', 7),
            bg='#fff3cd',
            fg='#856404',
            pady=3
        ).pack(fill='x', padx=10, pady=2)
        
    def carregar_produtos(self):
        """Carrega produtos do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1 ORDER BY descricao_produto')
        self.produtos = cursor.fetchall()
        conn.close()
        
        self.produtos_dict = {p[0]: f"{p[1]}" + (f" - {p[2]}" if p[2] else "") for p in self.produtos}
        self.atualizar_lista_produtos()
        
    def atualizar_lista_produtos(self, filtro=""):
        """Atualiza a lista de produtos com filtro"""
        self.lista_produtos.delete(0, tk.END)
        for produto_id, descricao in self.produtos_dict.items():
            if filtro.lower() in descricao.lower():
                self.lista_produtos.insert(tk.END, descricao)
                
    def filtrar_produtos(self, *args):
        """Filtra produtos baseado no texto de busca"""
        filtro = self.busca_var.get()
        self.atualizar_lista_produtos(filtro)
        
    def on_produto_selecionado(self, event):
        """Callback quando um produto é selecionado"""
        selection = self.lista_produtos.curselection()
        if selection:
            descricao = self.lista_produtos.get(selection[0])
            # Encontrar o ID do produto
            for produto_id, desc in self.produtos_dict.items():
                if desc == descricao:
                    self.produto_selecionado = (produto_id, descricao)
                    self.label_produto_atual.config(
                        text=f"✓ SELECIONADO: {descricao}",
                        bg='#d4edda',
                        fg='#155724',
                        font=('Segoe UI', 11, 'bold')
                    )
                    break
                    
    def adicionar_produto(self):
        """Adiciona um novo produto ao banco de dados"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Novo Produto")
        dialog.geometry("400x250")
        dialog.configure(bg='white')
        
        tk.Label(
            dialog,
            text="Descrição Completa do Produto:",
            bg='white',
            font=('Segoe UI', 10, 'bold')
        ).pack(pady=(20, 5), padx=20)
        
        entry_descricao = tk.Entry(dialog, font=('Segoe UI', 10), width=40)
        entry_descricao.pack(pady=5, padx=20)
        entry_descricao.focus()
        
        tk.Label(
            dialog,
            text="Marca (opcional):",
            bg='white',
            font=('Segoe UI', 10, 'bold')
        ).pack(pady=(10, 5), padx=20)
        
        entry_marca = tk.Entry(dialog, font=('Segoe UI', 10), width=40)
        entry_marca.pack(pady=5, padx=20)
        
        def salvar():
            descricao = entry_descricao.get().strip()
            marca = entry_marca.get().strip()
            
            if not descricao:
                messagebox.showwarning("Aviso", "Digite a descrição do produto!")
                return
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO produtos (descricao_produto, marca) VALUES (?, ?)',
                (descricao, marca if marca else None)
            )
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", f"Produto '{descricao}' adicionado!")
            dialog.destroy()
            self.carregar_produtos()
            
        tk.Button(
            dialog,
            text="💾 Salvar Produto",
            command=salvar,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            pady=10
        ).pack(pady=20)
        
    def carregar_imagem(self):
        """Carrega uma imagem do disco"""
        filepath = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if filepath:
            self.imagem_path = filepath
            self.exibir_imagem(filepath)
            
    def tirar_foto_webcam(self):
        """Captura foto da webcam"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                messagebox.showerror("Erro", "Não foi possível acessar a webcam!")
                return
                
            messagebox.showinfo("Webcam", "Pressione ESPAÇO para capturar ou ESC para cancelar")
            
            while True:
                ret, frame = cap.read()
                if ret:
                    cv2.imshow('Webcam - Pressione ESPAÇO para capturar', frame)
                    
                key = cv2.waitKey(1)
                if key == 32:  # ESPAÇO
                    # Salvar imagem temporária
                    temp_dir = self.data_dir / "temp"
                    temp_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_path = temp_dir / f"webcam_{timestamp}.jpg"
                    cv2.imwrite(str(temp_path), frame)
                    self.imagem_path = str(temp_path)
                    break
                elif key == 27:  # ESC
                    break
                    
            cap.release()
            cv2.destroyAllWindows()
            
            if self.imagem_path and os.path.exists(self.imagem_path):
                self.exibir_imagem(self.imagem_path)
                
        except ImportError:
            messagebox.showerror("Erro", "OpenCV não instalado!\nInstale com: pip install opencv-python")
            
    def exibir_imagem(self, filepath):
        """Exibe a imagem no canvas usando TODO o espaço disponível"""
        self.foto_pil = Image.open(filepath)
        self.imagem_original = self.foto_pil.copy()
        
        # Aguardar atualização do canvas
        self.canvas.update_idletasks()
        
        # Pegar dimensões do canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Usar dimensões maiores se o canvas ainda não foi renderizado
        if canvas_width <= 1:
            canvas_width = 1000  # Ainda maior
        if canvas_height <= 1:
            canvas_height = 750
            
        # Redimensionar usando QUASE TODO o espaço (margem mínima)
        margem = 10  # Margem MÍNIMA
        max_width = canvas_width - margem
        max_height = canvas_height - margem
        
        # Calcular proporção
        img_ratio = self.foto_pil.width / self.foto_pil.height
        canvas_ratio = max_width / max_height
        
        if img_ratio > canvas_ratio:
            # Imagem mais larga - ajustar pela largura
            new_width = max_width
            new_height = int(max_width / img_ratio)
        else:
            # Imagem mais alta - ajustar pela altura
            new_height = max_height
            new_width = int(max_height * img_ratio)
        
        # Redimensionar para o tamanho MÁXIMO
        self.foto_pil = self.foto_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        self.imagem_atual = ImageTk.PhotoImage(self.foto_pil)
        
        self.canvas.delete('all')
        self.canvas_image = self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.imagem_atual,
            anchor='center'
        )
        
        self.bboxes = []
        self.atualizar_lista_anotacoes()
        
    def on_canvas_click(self, event):
        """Início do desenho do bounding box"""
        if not self.produto_selecionado:
            messagebox.showwarning(
                "⚠️ Falta Selecionar Produto", 
                "PASSO 1: Clique em um produto da lista à esquerda primeiro!\n\nDepois volte aqui para desenhar."
            )
            return
            
        if not self.imagem_path:
            messagebox.showwarning(
                "⚠️ Falta Carregar Foto", 
                "PASSO 2: Clique em 'Carregar Imagem' ou 'Tirar Foto' primeiro!\n\nDepois volte aqui para desenhar."
            )
            return
            
        self.inicio_bbox = (event.x, event.y)
        
    def on_canvas_drag(self, event):
        """Desenho em tempo real do bounding box"""
        if self.inicio_bbox:
            if self.bbox_temp:
                self.canvas.delete(self.bbox_temp)
                
            self.bbox_temp = self.canvas.create_rectangle(
                self.inicio_bbox[0],
                self.inicio_bbox[1],
                event.x,
                event.y,
                outline='#f39c12',
                width=3
            )
            
    def on_canvas_release(self, event):
        """Finaliza o desenho do bounding box"""
        if self.inicio_bbox:
            x1, y1 = self.inicio_bbox
            x2, y2 = event.x, event.y
            
            # Validar tamanho mínimo
            if abs(x2 - x1) < 20 or abs(y2 - y1) < 20:
                if self.bbox_temp:
                    self.canvas.delete(self.bbox_temp)
                self.bbox_temp = None
                self.inicio_bbox = None
                return
                
            # Normalizar coordenadas (0-1)
            img_width = self.foto_pil.width
            img_height = self.foto_pil.height
            
            # Calcular offset da imagem no canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            offset_x = (canvas_width - img_width) // 2
            offset_y = (canvas_height - img_height) // 2
            
            # Ajustar coordenadas
            x1_adj = max(0, min(x1 - offset_x, img_width))
            y1_adj = max(0, min(y1 - offset_y, img_height))
            x2_adj = max(0, min(x2 - offset_x, img_width))
            y2_adj = max(0, min(y2 - offset_y, img_height))
            
            # Converter para formato YOLO (centro, width, height)
            center_x = (x1_adj + x2_adj) / 2 / img_width
            center_y = (y1_adj + y2_adj) / 2 / img_height
            width = abs(x2_adj - x1_adj) / img_width
            height = abs(y2_adj - y1_adj) / img_height
            
            # Adicionar anotação
            bbox_info = {
                'produto_id': self.produto_selecionado[0],
                'produto_nome': self.produto_selecionado[1],
                'x': center_x,
                'y': center_y,
                'width': width,
                'height': height,
                'canvas_coords': (x1, y1, x2, y2)
            }
            
            self.bboxes.append(bbox_info)
            
            # Marcar como não salvo
            self.dados_nao_salvos = True
            
            # Redesenhar com cor permanente
            if self.bbox_temp:
                self.canvas.delete(self.bbox_temp)
                
            # Cores vibrantes e distintas para cada produto (melhor visibilidade)
            cores = [
                '#FF1744',  # Vermelho vibrante
                '#00E676',  # Verde neon
                '#2979FF',  # Azul elétrico
                '#FFEA00',  # Amarelo brilhante
                '#D500F9',  # Roxo magenta
                '#00E5FF',  # Ciano
                '#FF6D00',  # Laranja intenso
                '#76FF03',  # Verde limão
                '#FF4081',  # Rosa pink
                '#00BFA5',  # Teal
                '#FFD600',  # Ouro
                '#F50057',  # Rosa profundo
                '#651FFF',  # Índigo
                '#00C853',  # Verde escuro
                '#FF3D00',  # Vermelho-laranja
            ]
            
            # Usar hash do ID do produto para cor consistente
            produto_index = hash(str(self.produto_selecionado[0])) % len(cores)
            cor = cores[produto_index]
            
            bbox_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=cor,
                width=4  # Linha mais grossa para melhor visibilidade
            )
            
            # Adicionar label com fundo colorido
            produto_nome_curto = self.produto_selecionado[1][:25]  # Limitar caracteres
            label_x = min(x1, x2)
            label_y = min(y1, y2) - 5
            
            # Fundo do label
            label_bg = self.canvas.create_rectangle(
                label_x, label_y - 20, 
                label_x + len(produto_nome_curto) * 7 + 10, label_y,
                fill=cor,
                outline='',
                tags='label'
            )
            
            # Texto do label
            label_text = self.canvas.create_text(
                label_x + 5, label_y - 10,
                text=produto_nome_curto,
                anchor='w',
                fill='white',
                font=('Segoe UI', 9, 'bold'),
                tags='label'
            )
            
            bbox_info['canvas_ids'] = (bbox_id, label_bg, label_text)
            
            self.bbox_temp = None
            self.inicio_bbox = None
            
            self.atualizar_lista_anotacoes()
            
    def atualizar_lista_anotacoes(self):
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
            self.lista_anotacoes.insert(tk.END, f"{i+1}. {nome_display}")
            
        total = len(self.bboxes)
        # Contar produtos únicos
        produtos_unicos = set(bbox['produto_id'] for bbox in self.bboxes)
        total_produtos = len(produtos_unicos)
        self.label_contador.config(
            text=f"{total} bbox{'es' if total != 1 else ''} | {total_produtos} produto{'s' if total_produtos != 1 else ''}"
        )
        
    def remover_anotacao_selecionada(self, event):
        """Remove uma anotação da lista"""
        selection = self.lista_anotacoes.curselection()
        if selection:
            index = selection[0]
            bbox = self.bboxes[index]
            
            # Remover do canvas
            if 'canvas_ids' in bbox:
                for canvas_id in bbox['canvas_ids']:
                    self.canvas.delete(canvas_id)
                    
            # Remover da lista
            del self.bboxes[index]
            self.atualizar_lista_anotacoes()
            
    def limpar_tudo(self):
        """Limpa todas as anotações"""
        if self.bboxes and messagebox.askyesno("Confirmar", "Deseja limpar todas as anotações?"):
            for bbox in self.bboxes:
                if 'canvas_ids' in bbox:
                    for canvas_id in bbox['canvas_ids']:
                        self.canvas.delete(canvas_id)
                        
            self.bboxes = []
            self.atualizar_lista_anotacoes()
            
    def salvar_anotacoes(self):
        """Salva as anotações no banco de dados local"""
        if not self.imagem_path:
            messagebox.showwarning("Aviso", "Carregue uma imagem primeiro!")
            return
            
        if not self.bboxes:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma anotação!")
            return
            
        # Copiar imagem para diretório de dados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_dir = self.data_dir / "imagens"
        img_dir.mkdir(exist_ok=True)
        
        ext = os.path.splitext(self.imagem_path)[1]
        novo_nome = f"anotada_{timestamp}{ext}"
        novo_caminho = img_dir / novo_nome
        shutil.copy2(self.imagem_path, novo_caminho)
        
        # Salvar no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        observacoes = self.text_observacoes.get('1.0', tk.END).strip()
        
        cursor.execute('''
            INSERT INTO imagens_coletadas 
            (caminho_imagem, tipo, total_anotacoes, observacoes, usuario)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(novo_caminho), 'anotada', len(self.bboxes), observacoes, self.usuario_nome))
        
        imagem_id = cursor.lastrowid
        
        # Salvar anotações
        for bbox in self.bboxes:
            cursor.execute('''
                INSERT INTO anotacoes
                (imagem_id, produto_id, bbox_x, bbox_y, bbox_width, bbox_height)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (imagem_id, bbox['produto_id'], bbox['x'], bbox['y'], bbox['width'], bbox['height']))
            
        conn.commit()
        conn.close()
        
        messagebox.showinfo(
            "Sucesso",
            f"✓ Imagem salva com {len(self.bboxes)} anotações!\n\n"
            f"Arquivo: {novo_nome}"
        )
        
        # Limpar para próxima
        self.limpar_tudo()
        self.canvas.delete('all')
        self.imagem_path = None
        self.text_observacoes.delete('1.0', tk.END)
        
    def exportar_dados(self):
        """Exporta dados para pasta compartilhada (Google Drive/OneDrive)"""
        
        # Verificar se há pasta configurada
        if PASTA_EXPORTACAO_DRIVE and os.path.exists(PASTA_EXPORTACAO_DRIVE):
            # Usar pasta pré-configurada
            resposta = messagebox.askyesno(
                "📁 Pasta Configurada",
                f"Exportar para a pasta sincronizada?\n\n"
                f"📂 {PASTA_EXPORTACAO_DRIVE}\n\n"
                f"✅ SIM = Exportar e sincronizar automaticamente\n"
                f"❌ NÃO = Escolher outra pasta"
            )
            
            if resposta:
                pasta_base = PASTA_EXPORTACAO_DRIVE
            else:
                pasta_base = filedialog.askdirectory(
                    title="📁 Escolha a pasta (Google Drive ou OneDrive)",
                    initialdir=os.path.expanduser("~")
                )
        else:
            # Pedir para escolher pasta
            messagebox.showinfo(
                "💡 Dica",
                "Escolha uma pasta do Google Drive ou OneDrive\n"
                "para sincronização automática!\n\n"
                "Exemplos:\n"
                "• C:\\Users\\SEU_NOME\\Google Drive\\VerifiK\n"
                "• C:\\Users\\SEU_NOME\\OneDrive\\VerifiK"
            )
            
            pasta_base = filedialog.askdirectory(
                title="📁 Escolha a pasta para exportar",
                initialdir=os.path.expanduser("~")
            )
        
        if not pasta_base:
            return
        
        # Criar subpasta com timestamp
        export_dir = Path(pasta_base) / f"exportacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_dir.mkdir(exist_ok=True, parents=True)
        
        # Copiar imagens
        img_export = export_dir / "imagens"
        img_export.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Exportar imagens não sincronizadas
        cursor.execute('SELECT * FROM imagens_coletadas WHERE sincronizado = 0')
        imagens = cursor.fetchall()
        
        dados_exportacao = {
            'data_exportacao': datetime.now().isoformat(),
            'usuario': self.usuario_nome,
            'imagens': []
        }
        
        for img in imagens:
            img_id, caminho, tipo, usuario, data, total, obs, sync = img
            
            # Copiar arquivo
            if os.path.exists(caminho):
                nome_arquivo = os.path.basename(caminho)
                shutil.copy2(caminho, img_export / nome_arquivo)
                
                # Buscar anotações
                cursor.execute('SELECT produto_id, bbox_x, bbox_y, bbox_width, bbox_height FROM anotacoes WHERE imagem_id = ?', (img_id,))
                anotacoes = cursor.fetchall()
                
                img_data = {
                    'id': img_id,
                    'arquivo': nome_arquivo,
                    'tipo': tipo,
                    'data': data,
                    'observacoes': obs,
                    'anotacoes': [
                        {
                            'produto_id': a[0],
                            'x': a[1],
                            'y': a[2],
                            'width': a[3],
                            'height': a[4]
                        }
                        for a in anotacoes
                    ]
                }
                
                dados_exportacao['imagens'].append(img_data)
                
        # Salvar JSON
        with open(export_dir / 'dados_exportacao.json', 'w', encoding='utf-8') as f:
            json.dump(dados_exportacao, f, indent=2, ensure_ascii=False)
            
        # Exportar produtos
        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()
        
        produtos_data = [
            {'id': p[0], 'descricao_produto': p[1], 'marca': p[2]}
            for p in produtos
        ]
        
        with open(export_dir / 'produtos.json', 'w', encoding='utf-8') as f:
            json.dump(produtos_data, f, indent=2, ensure_ascii=False)
            
        # Marcar como sincronizado
        cursor.execute('UPDATE imagens_coletadas SET sincronizado = 1 WHERE sincronizado = 0')
        conn.commit()
        conn.close()
        
        # Marcar como salvo
        self.dados_nao_salvos = False
        
        # Detectar se é pasta sincronizada
        eh_drive = 'Google Drive' in str(export_dir) or 'GoogleDrive' in str(export_dir)
        eh_onedrive = 'OneDrive' in str(export_dir)
        
        if eh_drive or eh_onedrive:
            servico = "Google Drive" if eh_drive else "OneDrive"
            messagebox.showinfo(
                "✅ Exportação Concluída",
                f"📤 {len(imagens)} imagens exportadas!\n\n"
                f"📂 Pasta: {export_dir.name}\n\n"
                f"☁️ Sincronizando com {servico}...\n"
                f"Aguarde alguns instantes para o upload concluir.\n\n"
                f"💡 Você pode acompanhar o progresso no ícone\n"
                f"do {servico} na barra de tarefas."
            )
        else:
            messagebox.showinfo(
                "✅ Exportação Concluída",
                f"📤 {len(imagens)} imagens exportadas!\n\n"
                f"📂 Pasta: {export_dir}\n\n"
                f"💡 DICA: Para sincronização automática,\n"
                f"exporte para uma pasta do Google Drive ou OneDrive."
            )
    
    
    def ao_fechar_janela(self):
        """Confirmação ao fechar o sistema"""
        # Verificar se há anotações na imagem atual não salvas
        if len(self.bboxes) > 0:
            resposta = messagebox.askyesnocancel(
                "⚠️ Anotações Não Salvas",
                "Você tem anotações não salvas nesta foto!\n\n"
                "Deseja salvar antes de sair?",
                icon='warning'
            )
            
            if resposta is None:  # Cancelou
                return
            elif resposta:  # Sim, salvar
                self.salvar_anotacoes()
        
        # Verificar se há dados não exportados
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM imagens_coletadas WHERE sincronizado = 0')
        nao_exportados = cursor.fetchone()[0]
        conn.close()
        
        if nao_exportados > 0:
            resposta = messagebox.askyesnocancel(
                "📤 Dados Não Exportados",
                f"Você tem {nao_exportados} imagem(ns) não exportada(s)!\n\n"
                "Deseja exportar agora antes de sair?\n\n"
                "💡 Você precisará exportar para enviar ao servidor.",
                icon='warning'
            )
            
            if resposta is None:  # Cancelou
                return
            elif resposta:  # Sim, exportar
                self.exportar_dados()
        
        # Confirmação final
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair do sistema?"):
            self.root.destroy()


def main():
    root = tk.Tk()
    root.title("VerifiK - Sistema de Coleta de Imagens")
    app = SistemaColetaImagens(root)
    root.mainloop()


if __name__ == '__main__':
    main()

