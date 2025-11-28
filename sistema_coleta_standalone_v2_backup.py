"""
Sistema de Coleta de Imagens para Funcionários - Standalone
Aplicação offline para coletar fotos de produtos com anotações
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3


class SistemaColetaImagens:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Coleta de Imagens - VerifiK")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f5f6fa')
        
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
        
        # Diretórios
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = self.base_dir / "dados_coleta"
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "coleta.db"
        
        # Inicializar banco de dados
        self.init_database()
        
        # Criar interface
        self.criar_interface()
        
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
        
    def criar_interface(self):
        """Cria a interface gráfica"""
        
        # Frame superior - Informações do usuário
        frame_topo = tk.Frame(self.root, bg='#667eea', height=80)
        frame_topo.pack(fill='x', padx=0, pady=0)
        
        tk.Label(
            frame_topo,
            text="📸 Sistema de Coleta de Imagens - VerifiK",
            font=('Segoe UI', 20, 'bold'),
            bg='#667eea',
            fg='white'
        ).pack(pady=15)
        
        # Frame principal - 3 colunas
        frame_principal = tk.Frame(self.root, bg='#f5f6fa')
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Coluna 1 - Lista de produtos
        self.criar_painel_produtos(frame_principal)
        
        # Coluna 2 - Canvas de imagem
        self.criar_painel_imagem(frame_principal)
        
        # Coluna 3 - Controles e anotações
        self.criar_painel_controles(frame_principal)
        
    def criar_painel_produtos(self, parent):
        """Painel lateral com lista de produtos"""
        frame = tk.Frame(parent, bg='white', relief='ridge', borderwidth=2)
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        tk.Label(
            frame,
            text="🎯 Selecione o Produto",
            font=('Segoe UI', 14, 'bold'),
            bg='white'
        ).pack(pady=10)
        
        # Campo de busca
        tk.Label(frame, text="Buscar:", bg='white', font=('Segoe UI', 10)).pack(pady=(5, 0))
        self.busca_var = tk.StringVar()
        self.busca_var.trace('w', self.filtrar_produtos)
        
        busca_entry = tk.Entry(frame, textvariable=self.busca_var, font=('Segoe UI', 10))
        busca_entry.pack(fill='x', padx=10, pady=5)
        
        # Lista de produtos
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
        
        # Botão para adicionar produto
        tk.Button(
            frame,
            text="➕ Adicionar Novo Produto",
            command=self.adicionar_produto,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=10)
        
    def criar_painel_imagem(self, parent):
        """Painel central com canvas para desenhar bounding boxes"""
        frame = tk.Frame(parent, bg='white', relief='ridge', borderwidth=2)
        frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Botões superiores
        frame_botoes = tk.Frame(frame, bg='white')
        frame_botoes.pack(fill='x', pady=10)
        
        tk.Button(
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
        ).pack(side='left', padx=10)
        
        # Canvas para desenhar
        frame_canvas = tk.Frame(frame, bg='#e0e0e0', relief='sunken', borderwidth=2)
        frame_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            frame_canvas,
            bg='#f0f0f0',
            cursor='crosshair'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Instruções
        self.label_instrucoes = tk.Label(
            frame,
            text="📖 Selecione um produto e clique + arraste na imagem para desenhar o box",
            font=('Segoe UI', 10, 'italic'),
            bg='white',
            fg='#7f8c8d'
        )
        self.label_instrucoes.pack(pady=5)
        
        # Eventos do canvas
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
    def criar_painel_controles(self, parent):
        """Painel direito com controles e lista de anotações"""
        frame = tk.Frame(parent, bg='white', relief='ridge', borderwidth=2)
        frame.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        
        # Produto selecionado
        tk.Label(
            frame,
            text="📦 Produto Atual",
            font=('Segoe UI', 12, 'bold'),
            bg='white'
        ).pack(pady=10)
        
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
        
        # Contador
        tk.Label(
            frame,
            text="📊 Estatísticas",
            font=('Segoe UI', 12, 'bold'),
            bg='white'
        ).pack(pady=(20, 5))
        
        self.label_contador = tk.Label(
            frame,
            text="0 produtos anotados",
            font=('Segoe UI', 16, 'bold'),
            bg='#667eea',
            fg='white',
            pady=15
        )
        self.label_contador.pack(fill='x', padx=10)
        
        # Lista de anotações
        tk.Label(
            frame,
            text="📋 Anotações Criadas",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        ).pack(pady=(20, 5))
        
        frame_lista_anotacoes = tk.Frame(frame, bg='white')
        frame_lista_anotacoes.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(frame_lista_anotacoes)
        scrollbar.pack(side='right', fill='y')
        
        self.lista_anotacoes = tk.Listbox(
            frame_lista_anotacoes,
            yscrollcommand=scrollbar.set,
            font=('Segoe UI', 9),
            selectmode='single',
            activestyle='none',
            selectbackground='#e74c3c',
            selectforeground='white'
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
        
        # Observações
        tk.Label(
            frame,
            text="📝 Observações",
            font=('Segoe UI', 10, 'bold'),
            bg='white'
        ).pack(pady=(10, 5))
        
        self.text_observacoes = tk.Text(frame, height=3, font=('Segoe UI', 9))
        self.text_observacoes.pack(fill='x', padx=10)
        
        # Botões de ação
        frame_acoes = tk.Frame(frame, bg='white')
        frame_acoes.pack(fill='x', pady=20, padx=10)
        
        tk.Button(
            frame_acoes,
            text="🗑️ Limpar Tudo",
            command=self.limpar_tudo,
            bg='#95a5a6',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', pady=2)
        
        tk.Button(
            frame_acoes,
            text="💾 Salvar Anotações",
            command=self.salvar_anotacoes,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            cursor='hand2',
            pady=10
        ).pack(fill='x', pady=2)
        
        tk.Button(
            frame_acoes,
            text="📤 Exportar para Sincronização",
            command=self.exportar_dados,
            bg='#f39c12',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(fill='x', pady=2)
        
        # Configurar grid
        parent.columnconfigure(0, weight=1, minsize=300)
        parent.columnconfigure(1, weight=3, minsize=600)
        parent.columnconfigure(2, weight=1, minsize=300)
        parent.rowconfigure(0, weight=1)
        
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
                        text=f"✓ {descricao}",
                        bg='#d4edda',
                        fg='#155724'
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
        """Exibe a imagem no canvas"""
        self.foto_pil = Image.open(filepath)
        self.imagem_original = self.foto_pil.copy()
        
        # Redimensionar para caber no canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.foto_pil.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
            
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
            messagebox.showwarning("Aviso", "Selecione um produto primeiro!")
            return
            
        if not self.imagem_path:
            messagebox.showwarning("Aviso", "Carregue uma imagem primeiro!")
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
            
            # Redesenhar com cor permanente
            if self.bbox_temp:
                self.canvas.delete(self.bbox_temp)
                
            bbox_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='#667eea',
                width=2
            )
            
            # Adicionar label
            label_id = self.canvas.create_text(
                x1, y1 - 5,
                text=self.produto_selecionado[1][:30],
                anchor='sw',
                fill='#667eea',
                font=('Segoe UI', 9, 'bold')
            )
            
            bbox_info['canvas_ids'] = (bbox_id, label_id)
            
            self.bbox_temp = None
            self.inicio_bbox = None
            
            self.atualizar_lista_anotacoes()
            
    def atualizar_lista_anotacoes(self):
        """Atualiza a lista de anotações e contador"""
        self.lista_anotacoes.delete(0, tk.END)
        for i, bbox in enumerate(self.bboxes):
            self.lista_anotacoes.insert(tk.END, f"{i+1}. {bbox['produto_nome']}")
            
        total = len(self.bboxes)
        self.label_contador.config(text=f"{total} produto{'s' if total != 1 else ''} anotado{'s' if total != 1 else ''}")
        
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
        """Exporta dados para sincronização com o servidor"""
        pasta_exportacao = filedialog.askdirectory(title="Selecione a pasta para exportar")
        
        if not pasta_exportacao:
            return
            
        export_dir = Path(pasta_exportacao) / f"exportacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_dir.mkdir(exist_ok=True)
        
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
            
        conn.close()
        
        messagebox.showinfo(
            "Exportação Concluída",
            f"✓ {len(imagens)} imagens exportadas!\n\n"
            f"Pasta: {export_dir}\n\n"
            f"Copie esta pasta para sincronizar com o servidor."
        )


def main():
    root = tk.Tk()
    app = SistemaColetaImagens(root)
    root.mainloop()


if __name__ == '__main__':
    main()
