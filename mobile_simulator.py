"""
VerifiK Mobile Simulator - Versão Desktop para Teste
Simula a interface mobile usando tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageDraw
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
import shutil


class MobileSimulator:
    """Simulador da interface mobile para desktop"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("📱 VerifiK Mobile - Simulador Desktop")
        
        # Configurar janela como mobile (9:16 ratio)
        width, height = 400, 700
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(False, True)
        self.root.configure(bg='#f8f9fa')
        
        # Variáveis
        self.produtos = []
        self.produto_selecionado = None
        self.imagem_atual = None
        self.annotations = []
        self.current_annotation = None
        
        # Inicializar database
        self.init_database()
        
        # Criar interface
        self.create_interface()
        
        # Carregar produtos
        self.load_produtos()
    
    def create_interface(self):
        """Cria interface mobile-like"""
        # Container principal com scroll
        canvas = tk.Canvas(self.root, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        self.create_header()
        
        # Seções
        self.create_produto_section()
        self.create_image_section()
        self.create_annotation_section()
        self.create_actions_section()
        
        # Empacotar
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Bind scroll do mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def create_header(self):
        """Cria cabeçalho mobile"""
        header = tk.Frame(self.scrollable_frame, bg='#667eea', height=80)
        header.pack(fill='x', pady=15)
        
        tk.Label(
            header,
            text="📱 VerifiK Mobile",
            font=('Segoe UI', 16, 'bold'),
            bg='#667eea',
            fg='white',
            pady=15
        ).pack()
        
        tk.Label(
            header,
            text="Sistema de Coleta de Imagens",
            font=('Segoe UI', 10),
            bg='#667eea',
            fg='white'
        ).pack()
    
    def create_produto_section(self):
        """Seção de seleção de produto"""
        section = tk.LabelFrame(
            self.scrollable_frame, 
            text="🎯 1. Selecione o Produto",
            font=('Segoe UI', 12, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        section.pack(fill='x', pady=5)
        
        # Combobox produtos
        tk.Label(section, text="Produto:", bg='#f8f9fa').pack(anchor='w')
        self.produto_combo = ttk.Combobox(section, state="readonly", width=40)
        self.produto_combo.pack(fill='x', pady=5)
        self.produto_combo.bind('<<ComboboxSelected>>', self.on_produto_selected)
        
        # Botão refresh
        ttk.Button(
            section, 
            text="🔄 Atualizar Lista",
            command=self.load_produtos
        ).pack(fill='x', pady=5)
    
    def create_image_section(self):
        """Seção de captura de imagem"""
        section = tk.LabelFrame(
            self.scrollable_frame,
            text="📷 2. Capture ou Carregue Imagem", 
            font=('Segoe UI', 12, 'bold'),
            bg='#f8f9fa',
            fg='#8e44ad',
            padx=10,
            pady=10
        )
        section.pack(fill='x', pady=5)
        
        # Botões de ação
        btn_frame = tk.Frame(section, bg='#f8f9fa')
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(
            btn_frame,
            text="📷 Simular Câmera",
            command=self.simulate_camera
        ).pack(side='left', padx=2, expand=True, fill='x')
        
        ttk.Button(
            btn_frame,
            text="🖼️ Galeria",
            command=self.open_gallery
        ).pack(side='right', padx=2, expand=True, fill='x')
        
        # Preview da imagem
        self.image_label = tk.Label(
            section,
            text="📷 Nenhuma imagem carregada",
            bg='#ecf0f1',
            fg='#7f8c8d',
            width=45,
            height=8,
            relief='solid',
            borderwidth=1
        )
        self.image_label.pack(pady=10)
    
    def create_annotation_section(self):
        """Seção de anotações"""
        section = tk.LabelFrame(
            self.scrollable_frame,
            text="✏️ 3. Marque o Produto",
            font=('Segoe UI', 12, 'bold'),
            bg='#f8f9fa',
            fg='#e67e22',
            padx=10,
            pady=10
        )
        section.pack(fill='x', pady=5)
        
        # Instruções
        tk.Label(
            section,
            text="Clique na imagem para marcar onde está o produto",
            font=('Segoe UI', 9),
            bg='#f8f9fa',
            fg='#7f8c8d'
        ).pack(pady=5)
        
        # Canvas para anotações (simulado)
        self.annotation_canvas = tk.Canvas(
            section,
            width=350,
            height=200,
            bg='#ecf0f1',
            relief='solid',
            borderwidth=1
        )
        self.annotation_canvas.pack(pady=5)
        
        # Texto informativo
        self.annotation_canvas.create_text(
            175, 100,
            text="📍 Área de anotação\nClique para marcar produto",
            font=('Segoe UI', 10),
            fill='#7f8c8d',
            justify='center'
        )
        
        # Bind cliques
        self.annotation_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Lista de anotações
        tk.Label(section, text="Marcações:", bg='#f8f9fa').pack(anchor='w', pady=(10, 0))
        self.annotations_listbox = tk.Listbox(section, height=3)
        self.annotations_listbox.pack(fill='x', pady=5)
        
        # Botão limpar
        ttk.Button(
            section,
            text="🧽 Limpar Marcações",
            command=self.clear_annotations
        ).pack(fill='x', pady=5)
    
    def create_actions_section(self):
        """Seção de ações"""
        section = tk.LabelFrame(
            self.scrollable_frame,
            text="💾 4. Salvar e Exportar",
            font=('Segoe UI', 12, 'bold'),
            bg='#f8f9fa',
            fg='#2980b9',
            padx=10,
            pady=10
        )
        section.pack(fill='x', pady=5)
        
        # Campo observações
        tk.Label(section, text="Observações:", bg='#f8f9fa').pack(anchor='w')
        self.obs_text = scrolledtext.ScrolledText(section, height=3, width=40)
        self.obs_text.pack(fill='x', pady=5)
        
        # Botões de ação
        btn_frame = tk.Frame(section, bg='#f8f9fa')
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            btn_frame,
            text="💾 Salvar",
            command=self.save_annotation
        ).pack(side='left', padx=2, expand=True, fill='x')
        
        ttk.Button(
            btn_frame,
            text="📤 Exportar",
            command=self.export_data
        ).pack(side='right', padx=2, expand=True, fill='x')
        
        # Status
        self.status_label = tk.Label(
            section,
            text="✅ Pronto para coletar imagens",
            bg='#f8f9fa',
            fg='#27ae60',
            font=('Segoe UI', 9)
        )
        self.status_label.pack(pady=5)
    
    def init_database(self):
        """Inicializa banco de dados"""
        self.db_path = "mobile_simulator.db"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabelas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                descricao_produto TEXT NOT NULL,
                marca TEXT,
                ativo INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagens_coletadas (
                id INTEGER PRIMARY KEY,
                produto_id INTEGER,
                caminho_imagem TEXT,
                anotacoes TEXT,
                observacoes TEXT,
                data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
                sincronizado INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Produtos padrão
        self.add_default_produtos()
    
    def add_default_produtos(self):
        """Adiciona produtos padrão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM produtos')
        if cursor.fetchone()[0] == 0:
            produtos = [
                ('Coca-Cola 350ml', 'Coca-Cola'),
                ('Guaraná Antarctica 350ml', 'Antarctica'),
                ('Água Crystal 500ml', 'Crystal'),
                ('Biscoito Passatempo', 'Nestlé'),
                ('Chocolate Bis', 'Lacta')
            ]
            
            cursor.executemany(
                'INSERT INTO produtos (descricao_produto, marca) VALUES (?, ?)',
                produtos
            )
            conn.commit()
        
        conn.close()
    
    def load_produtos(self):
        """Carrega produtos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1')
        self.produtos = cursor.fetchall()
        conn.close()
        
        # Atualizar combobox
        values = []
        for p in self.produtos:
            desc = p[1]
            if p[2]:
                desc += f' - {p[2]}'
            values.append(desc)
        
        self.produto_combo['values'] = values
        self.status_label.config(text=f"✅ {len(values)} produtos carregados")
    
    def on_produto_selected(self, event):
        """Produto selecionado"""
        selection = self.produto_combo.current()
        if selection >= 0:
            self.produto_selecionado = self.produtos[selection]
            self.status_label.config(
                text=f"🎯 Produto selecionado: {self.produto_selecionado[1]}"
            )
    
    def simulate_camera(self):
        """Simula captura de câmera"""
        messagebox.showinfo(
            "📷 Simulador de Câmera",
            "Em um dispositivo real, isso abriria a câmera.\n\n" +
            "Para testar, use 'Galeria' para selecionar uma imagem."
        )
    
    def open_gallery(self):
        """Abre galeria (file chooser)"""
        filepath = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if filepath:
            self.load_image(filepath)
    
    def load_image(self, filepath):
        """Carrega imagem"""
        try:
            self.imagem_atual = filepath
            
            # Carregar e redimensionar para preview
            img = Image.open(filepath)
            img.thumbnail((340, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Manter referência
            
            # Limpar anotações
            self.clear_annotations()
            
            self.status_label.config(text="📷 Imagem carregada! Faça as marcações.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar imagem:\n{e}")
    
    def on_canvas_click(self, event):
        """Clique no canvas"""
        if not self.produto_selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto primeiro!")
            return
        
        if not self.imagem_atual:
            messagebox.showwarning("Atenção", "Carregue uma imagem primeiro!")
            return
        
        # Simular anotação
        x, y = event.x, event.y
        annotation = {
            'produto': self.produto_selecionado[1],
            'x': x,
            'y': y,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        self.annotations.append(annotation)
        
        # Desenhar ponto no canvas
        self.annotation_canvas.create_oval(
            x-5, y-5, x+5, y+5,
            fill='red',
            outline='darkred',
            width=2
        )
        
        # Adicionar à lista
        self.annotations_listbox.insert(
            'end', 
            f"{annotation['produto']} ({x},{y}) - {annotation['timestamp']}"
        )
        
        self.status_label.config(text=f"✅ {len(self.annotations)} marcações feitas")
    
    def clear_annotations(self):
        """Limpa anotações"""
        self.annotations = []
        self.annotations_listbox.delete(0, 'end')
        self.annotation_canvas.delete("all")
        
        # Recriar texto informativo
        self.annotation_canvas.create_text(
            175, 100,
            text="📍 Área de anotação\nClique para marcar produto",
            font=('Segoe UI', 10),
            fill='#7f8c8d',
            justify='center'
        )
        
        self.status_label.config(text="🧽 Marcações limpas")
    
    def save_annotation(self):
        """Salva anotação"""
        if not self.produto_selecionado:
            messagebox.showerror("Erro", "Selecione um produto!")
            return
        
        if not self.imagem_atual:
            messagebox.showerror("Erro", "Carregue uma imagem!")
            return
        
        if not self.annotations:
            messagebox.showerror("Erro", "Faça pelo menos uma marcação!")
            return
        
        # Salvar no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO imagens_coletadas 
            (produto_id, caminho_imagem, anotacoes, observacoes)
            VALUES (?, ?, ?, ?)
        ''', (
            self.produto_selecionado[0],
            self.imagem_atual,
            json.dumps(self.annotations),
            self.obs_text.get('1.0', 'end-1c')
        ))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Sucesso", "Anotação salva com sucesso!")
        
        # Limpar para próxima
        self.clear_annotations()
        self.obs_text.delete('1.0', 'end')
        self.status_label.config(text="💾 Dados salvos! Pronto para próxima imagem.")
    
    def export_data(self):
        """Exporta dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ic.*, p.descricao_produto, p.marca
            FROM imagens_coletadas ic
            JOIN produtos p ON ic.produto_id = p.id
            WHERE ic.sincronizado = 0
        ''')
        
        dados = cursor.fetchall()
        
        if not dados:
            messagebox.showinfo("Info", "Nenhum dado novo para exportar")
            conn.close()
            return
        
        # Preparar exportação
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'simulator': True,
            'total_imagens': len(dados),
            'imagens': []
        }
        
        for row in dados:
            export_data['imagens'].append({
                'id': row[0],
                'produto_id': row[1],
                'produto_nome': row[6],
                'produto_marca': row[7] or '',
                'caminho_imagem': row[2],
                'anotacoes': json.loads(row[3]),
                'observacoes': row[4],
                'data_coleta': row[5]
            })
        
        # Salvar arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'verifik_mobile_export_{timestamp}.json'
        
        filepath = filedialog.asksaveasfilename(
            title="Salvar Exportação",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialname=filename
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Marcar como sincronizado
            cursor.execute('UPDATE imagens_coletadas SET sincronizado = 1 WHERE sincronizado = 0')
            conn.commit()
            
            messagebox.showinfo(
                "Sucesso", 
                f"Dados exportados para:\n{filepath}\n\n{len(dados)} imagens processadas"
            )
        
        conn.close()


def main():
    """Função principal"""
    root = tk.Tk()
    app = MobileSimulator(root)
    root.mainloop()


if __name__ == '__main__':
    main()