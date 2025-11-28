#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VerifiK Mobile Simulator - Versão Otimizada
Interface mobile otimizada para melhor visualização
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

class MobileSimulatorOtimizado:
    """Simulador mobile otimizado"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("📱 VerifiK Mobile - Otimizado")
        
        # Configurar janela mobile otimizada
        width, height = 420, 750
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.configure(bg='#2c3e50')
        
        # Variáveis
        self.produtos = []
        self.produto_selecionado = None
        self.imagem_atual = None
        self.annotations = []
        
        # Inicializar database
        self.init_database()
        
        # Criar interface
        self.create_interface()
        
        # Carregar produtos
        self.load_produtos()
    
    def create_interface(self):
        """Interface mobile otimizada"""
        # Header fixo
        header = tk.Frame(self.root, bg='#34495e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📱 VerifiK Mobile",
            font=('Segoe UI', 14, 'bold'),
            bg='#34495e',
            fg='white'
        ).pack(expand=True)
        
        # Container principal com scroll
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas com scroll
        canvas = tk.Canvas(main_frame, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Seções compactas
        self.create_produto_section_compact()
        self.create_image_section_compact()
        self.create_annotation_section_compact()
        self.create_actions_section_compact()
        
        # Footer fixo com status
        footer = tk.Frame(self.root, bg='#34495e', height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        self.status_label = tk.Label(
            footer,
            text="✅ Sistema pronto",
            font=('Segoe UI', 9),
            bg='#34495e',
            fg='#2ecc71'
        )
        self.status_label.pack(expand=True)
        
        # Layout final
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Scroll com mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Bind global para scroll
        self.root.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_produto_section_compact(self):
        """Seção produtos compacta"""
        section = tk.Frame(self.content_frame, bg='white', relief='raised', bd=1)
        section.pack(fill='x', pady=2, padx=5)
        
        # Título
        title = tk.Frame(section, bg='#3498db')
        title.pack(fill='x')
        tk.Label(
            title,
            text="🎯 Produto",
            font=('Segoe UI', 10, 'bold'),
            bg='#3498db',
            fg='white',
            pady=5
        ).pack()
        
        # Conteúdo
        content = tk.Frame(section, bg='white')
        content.pack(fill='x', padx=10, pady=10)
        
        self.produto_combo = ttk.Combobox(content, state="readonly", font=('Segoe UI', 9))
        self.produto_combo.pack(fill='x', pady=2)
        self.produto_combo.bind('<<ComboboxSelected>>', self.on_produto_selected)
        
        ttk.Button(
            content,
            text="🔄 Atualizar",
            command=self.load_produtos
        ).pack(fill='x', pady=2)
    
    def create_image_section_compact(self):
        """Seção imagem compacta"""
        section = tk.Frame(self.content_frame, bg='white', relief='raised', bd=1)
        section.pack(fill='x', pady=2, padx=5)
        
        # Título
        title = tk.Frame(section, bg='#9b59b6')
        title.pack(fill='x')
        tk.Label(
            title,
            text="📷 Imagem",
            font=('Segoe UI', 10, 'bold'),
            bg='#9b59b6',
            fg='white',
            pady=5
        ).pack()
        
        # Conteúdo
        content = tk.Frame(section, bg='white')
        content.pack(fill='x', padx=10, pady=10)
        
        # Botões
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill='x', pady=2)
        
        ttk.Button(
            btn_frame,
            text="📷 Câmera",
            command=self.simulate_camera
        ).pack(side='left', padx=(0,2), expand=True, fill='x')
        
        ttk.Button(
            btn_frame,
            text="🖼️ Galeria",
            command=self.open_gallery
        ).pack(side='right', padx=(2,0), expand=True, fill='x')
        
        # Preview
        self.image_label = tk.Label(
            content,
            text="📷 Nenhuma imagem",
            bg='#f8f9fa',
            fg='#7f8c8d',
            height=6,
            relief='solid',
            borderwidth=1
        )
        self.image_label.pack(fill='x', pady=5)
    
    def create_annotation_section_compact(self):
        """Seção anotação compacta"""
        section = tk.Frame(self.content_frame, bg='white', relief='raised', bd=1)
        section.pack(fill='x', pady=2, padx=5)
        
        # Título
        title = tk.Frame(section, bg='#e67e22')
        title.pack(fill='x')
        tk.Label(
            title,
            text="✏️ Marcações",
            font=('Segoe UI', 10, 'bold'),
            bg='#e67e22',
            fg='white',
            pady=5
        ).pack()
        
        # Conteúdo
        content = tk.Frame(section, bg='white')
        content.pack(fill='x', padx=10, pady=10)
        
        # Canvas pequeno
        self.annotation_canvas = tk.Canvas(
            content,
            width=350,
            height=120,
            bg='#f8f9fa',
            relief='solid',
            borderwidth=1
        )
        self.annotation_canvas.pack(pady=2)
        
        self.annotation_canvas.create_text(
            175, 60,
            text="📍 Clique para marcar",
            font=('Segoe UI', 9),
            fill='#7f8c8d'
        )
        
        self.annotation_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Lista pequena
        self.annotations_listbox = tk.Listbox(content, height=2, font=('Segoe UI', 8))
        self.annotations_listbox.pack(fill='x', pady=2)
        
        ttk.Button(
            content,
            text="🧽 Limpar",
            command=self.clear_annotations
        ).pack(fill='x', pady=2)
    
    def create_actions_section_compact(self):
        """Seção ações - SEMPRE VISÍVEL"""
        section = tk.Frame(self.content_frame, bg='white', relief='raised', bd=2)
        section.pack(fill='x', pady=5, padx=5)
        
        # Título destacado
        title = tk.Frame(section, bg='#2ecc71')
        title.pack(fill='x')
        tk.Label(
            title,
            text="💾 AÇÕES - SALVAR",
            font=('Segoe UI', 11, 'bold'),
            bg='#2ecc71',
            fg='white',
            pady=8
        ).pack()
        
        # Conteúdo
        content = tk.Frame(section, bg='white')
        content.pack(fill='x', padx=15, pady=15)
        
        # Observações compactas
        tk.Label(content, text="Observações:", bg='white', font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        self.obs_text = scrolledtext.ScrolledText(content, height=2, font=('Segoe UI', 8))
        self.obs_text.pack(fill='x', pady=5)
        
        # Botões DESTACADOS
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill='x', pady=10)
        
        # Botão Salvar - GRANDE e VERDE
        self.btn_salvar = tk.Button(
            btn_frame,
            text="💾 SALVAR",
            command=self.save_annotation,
            font=('Segoe UI', 12, 'bold'),
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            activeforeground='white',
            relief='raised',
            bd=3,
            pady=10
        )
        self.btn_salvar.pack(side='left', padx=(0,5), expand=True, fill='x')
        
        # Botão Exportar - GRANDE e AZUL
        self.btn_exportar = tk.Button(
            btn_frame,
            text="📤 EXPORTAR",
            command=self.export_data,
            font=('Segoe UI', 12, 'bold'),
            bg='#2980b9',
            fg='white',
            activebackground='#21618c',
            activeforeground='white',
            relief='raised',
            bd=3,
            pady=10
        )
        self.btn_exportar.pack(side='right', padx=(5,0), expand=True, fill='x')
        
        # Espaço extra para garantir visibilidade
        tk.Frame(content, bg='white', height=20).pack()
    
    def init_database(self):
        """Inicializa banco"""
        self.db_path = "mobile_simulator.db"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
            desc = p[1][:50] + "..." if len(p[1]) > 50 else p[1]  # Truncar para interface
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
            nome = self.produto_selecionado[1][:30] + "..." if len(self.produto_selecionado[1]) > 30 else self.produto_selecionado[1]
            self.status_label.config(text=f"🎯 {nome}")
    
    def simulate_camera(self):
        """Simula câmera"""
        result = messagebox.askyesno(
            "Câmera",
            "Simular captura de câmera?\n\n(Isso abriria a câmera real no celular)"
        )
        if result:
            self.imagem_atual = "camera_capture_simulated.jpg"
            self.image_label.config(text="📷 Imagem capturada\n(Simulação)")
            self.status_label.config(text="📷 Imagem da câmera carregada")
    
    def open_gallery(self):
        """Abre galeria"""
        filepath = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Todos", "*.*")
            ]
        )
        
        if filepath:
            self.imagem_atual = filepath
            
            try:
                # Carregar preview
                img = Image.open(filepath)
                img.thumbnail((300, 150))
                photo = ImageTk.PhotoImage(img)
                
                self.image_label.config(image=photo, text="")
                self.image_label.image = photo  # Manter referência
                
                nome_arquivo = os.path.basename(filepath)
                self.status_label.config(text=f"🖼️ {nome_arquivo}")
                
            except Exception as e:
                self.image_label.config(text="❌ Erro ao carregar imagem")
                self.status_label.config(text=f"❌ Erro: {str(e)}")
    
    def on_canvas_click(self, event):
        """Clique no canvas"""
        x, y = event.x, event.y
        
        # Adicionar marcação
        self.annotations.append((x, y))
        
        # Desenhar ponto
        self.annotation_canvas.create_oval(
            x-5, y-5, x+5, y+5,
            fill='red',
            outline='darkred',
            width=2
        )
        
        # Atualizar lista
        self.annotations_listbox.insert(tk.END, f"📍 Ponto {len(self.annotations)}: ({x}, {y})")
        
        self.status_label.config(text=f"📍 {len(self.annotations)} marcação(ões)")
    
    def clear_annotations(self):
        """Limpa marcações"""
        self.annotations = []
        self.annotation_canvas.delete("all")
        self.annotation_canvas.create_text(
            175, 60,
            text="📍 Clique para marcar",
            font=('Segoe UI', 9),
            fill='#7f8c8d'
        )
        
        self.annotations_listbox.delete(0, tk.END)
        self.status_label.config(text="🧽 Marcações limpas")
    
    def save_annotation(self):
        """SALVAR - Função principal"""
        print("🔥 BOTÃO SALVAR PRESSIONADO!")  # Debug
        
        if not self.produto_selecionado:
            messagebox.showerror("Erro", "❌ Selecione um produto primeiro!")
            return
        
        if not self.imagem_atual:
            messagebox.showerror("Erro", "❌ Carregue uma imagem primeiro!")
            return
        
        if not self.annotations:
            messagebox.showerror("Erro", "❌ Faça pelo menos uma marcação!")
            return
        
        try:
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
            
            messagebox.showinfo("✅ Sucesso!", f"Dados salvos com sucesso!\n\nProduto: {self.produto_selecionado[1][:30]}...\nMarcações: {len(self.annotations)}")
            
            # Limpar para próxima
            self.clear_annotations()
            self.obs_text.delete('1.0', 'end')
            self.status_label.config(text="💾 Salvo! Pronto para próxima imagem")
            
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao salvar:\n{str(e)}")
            self.status_label.config(text=f"❌ Erro ao salvar")
    
    def export_data(self):
        """EXPORTAR dados"""
        print("🔥 BOTÃO EXPORTAR PRESSIONADO!")  # Debug
        
        try:
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
                messagebox.showinfo("ℹ️ Info", "Nenhum dado novo para exportar")
                conn.close()
                return
            
            # Exportar para JSON
            export_data = []
            for row in dados:
                export_data.append({
                    'id': row[0],
                    'produto_id': row[1],
                    'produto_nome': row[6],
                    'marca': row[7],
                    'caminho_imagem': row[2],
                    'anotacoes': json.loads(row[3]) if row[3] else [],
                    'observacoes': row[4],
                    'data_coleta': row[5]
                })
            
            # Salvar arquivo
            filename = f"export_verifik_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Marcar como sincronizado
            cursor.execute('UPDATE imagens_coletadas SET sincronizado = 1 WHERE sincronizado = 0')
            conn.commit()
            conn.close()
            
            messagebox.showinfo(
                "✅ Exportado!", 
                f"Dados exportados com sucesso!\n\nArquivo: {filename}\nRegistros: {len(dados)}"
            )
            
            self.status_label.config(text=f"📤 {len(dados)} registros exportados")
            
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao exportar:\n{str(e)}")
            self.status_label.config(text=f"❌ Erro ao exportar")

def main():
    """Função principal"""
    root = tk.Tk()
    app = MobileSimulatorOtimizado(root)
    
    print("🚀 MOBILE SIMULATOR OTIMIZADO INICIADO")
    print("📱 Interface mobile com botões GRANDES e VISÍVEIS")
    print("💾 Botão SALVAR: Verde, grande, sempre visível")
    print("📤 Botão EXPORTAR: Azul, grande, sempre visível")
    print("="*50)
    
    root.mainloop()

if __name__ == "__main__":
    main()