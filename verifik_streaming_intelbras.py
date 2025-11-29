#!/usr/bin/env python3
"""
VerifiK - Streaming Contínuo Intelbras com Captura sob Demanda
Sistema que mantém streaming ao vivo e captura apenas quando solicitado
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPBasicAuth
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os
import io
import threading
import time

class StreamingIntelbras:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Streaming Contínuo Intelbras")
        self.root.geometry("1200x800")
        
        # Configuração da câmera
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.base_url = f"http://{self.camera_ip}"
        
        # Session para manter conexão
        self.session = requests.Session()
        self.auth = HTTPBasicAuth(self.camera_user, self.camera_pass)
        
        # Variáveis de controle
        self.streaming_active = False
        self.current_frame = None
        self.captured_images = []
        self.produtos = []
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # URLs de captura prioritárias
        self.snapshot_urls = [
            "/cgi-bin/snapshot.cgi?channel=1&subtype=0",
            "/cgi-bin/magicBox.cgi?action=getSnapshot&channel=1&subtype=0",
            f"/cgi-bin/snapshot.cgi?chn=1&u={self.camera_user}&p={self.camera_pass}",
            "/Streaming/Channels/101/picture",
            "/cgi-bin/configManager.cgi?action=attachFileProc&name=Snap&channel=1&subtype=0"
        ]
        
        # Carregar produtos
        self.load_products()
        
        # Interface
        self.setup_interface()
        
        # Auto-iniciar streaming
        self.root.after(1000, self.start_streaming)
    
    def load_products(self):
        """Carrega produtos da base de dados"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT descricao_produto FROM produtos WHERE ativo = 1 ORDER BY descricao_produto")
            self.produtos = [row[0] for row in cursor.fetchall()]
            conn.close()
            print(f"✅ {len(self.produtos)} produtos carregados")
        except Exception as e:
            print(f"❌ Erro ao carregar produtos: {e}")
            self.produtos = ["PRODUTO TESTE 1", "PRODUTO TESTE 2"]
    
    def setup_interface(self):
        """Interface otimizada para streaming"""
        
        # Header - Informações da câmera
        header_frame = ttk.LabelFrame(self.root, text="📹 Câmera Intelbras - Streaming Ao Vivo", padding="10")
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # Info em grid
        info_grid = ttk.Frame(header_frame)
        info_grid.pack(fill='x')
        
        ttk.Label(info_grid, text=f"📷 IP: {self.camera_ip}", font=('Arial', 10)).grid(row=0, column=0, sticky='w', padx=(0, 20))
        ttk.Label(info_grid, text=f"👤 User: {self.camera_user}", font=('Arial', 10)).grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        self.status_label = ttk.Label(info_grid, text="🔴 Iniciando...", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=0, column=2, sticky='w', padx=(0, 20))
        
        self.fps_label = ttk.Label(info_grid, text="FPS: 0", font=('Arial', 10))
        self.fps_label.grid(row=0, column=3, sticky='w')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Lado esquerdo - Streaming
        left_frame = ttk.LabelFrame(main_frame, text="🎥 Visualização ao Vivo", padding="10")
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Container do streaming com proporção fixa
        self.streaming_container = ttk.Frame(left_frame)
        self.streaming_container.pack(expand=True, fill='both')
        
        # Label para o streaming (tamanho grande)
        self.stream_label = ttk.Label(
            self.streaming_container, 
            text="📹\nIniciando Streaming...\nAguarde conexão com a câmera",
            justify=tk.CENTER,
            font=('Arial', 14),
            background='black',
            foreground='white'
        )
        self.stream_label.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Controles de streaming
        stream_controls = ttk.Frame(left_frame)
        stream_controls.pack(fill='x', pady=(10, 0))
        
        # Botões principais
        self.capture_btn = ttk.Button(
            stream_controls, 
            text="📸 CAPTURAR AGORA", 
            command=self.capture_current_frame,
            style='Accent.TButton'
        )
        self.capture_btn.pack(side='left', padx=(0, 10))
        
        self.stream_btn = ttk.Button(
            stream_controls,
            text="⏸️ Pausar Stream",
            command=self.toggle_streaming
        )
        self.stream_btn.pack(side='left', padx=(0, 10))
        
        ttk.Button(
            stream_controls,
            text="🔄 Reconectar",
            command=self.restart_streaming
        ).pack(side='left', padx=(0, 10))
        
        # Indicador de qualidade
        quality_frame = ttk.Frame(stream_controls)
        quality_frame.pack(side='right')
        
        ttk.Label(quality_frame, text="Qualidade:", font=('Arial', 9)).pack(side='left')
        self.quality_indicator = ttk.Label(quality_frame, text="●", font=('Arial', 16), foreground='red')
        self.quality_indicator.pack(side='left', padx=(5, 0))
        
        # Lado direito - Produtos e Controles
        right_frame = ttk.LabelFrame(main_frame, text="📦 Produtos", padding="10")
        right_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # Busca de produtos
        ttk.Label(right_frame, text="🔍 Buscar produto:", font=('Arial', 10)).pack(anchor='w')
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_products)
        search_entry = ttk.Entry(right_frame, textvariable=self.search_var, width=35, font=('Arial', 10))
        search_entry.pack(fill='x', pady=(5, 10))
        
        # Lista de produtos
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill='both', expand=True)
        
        self.product_listbox = tk.Listbox(
            list_frame, 
            width=35, 
            height=20,
            font=('Arial', 9),
            selectmode=tk.SINGLE
        )
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_listbox.yview)
        
        self.product_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.product_listbox.config(yscrollcommand=scrollbar.set)
        
        # Preencher lista
        self.update_product_list(self.produtos)
        
        # Produto selecionado
        selected_frame = ttk.LabelFrame(right_frame, text="Produto Selecionado", padding="10")
        selected_frame.pack(fill='x', pady=(10, 0))
        
        self.selected_product_var = tk.StringVar(value="Selecione um produto...")
        self.selected_label = ttk.Label(
            selected_frame, 
            textvariable=self.selected_product_var,
            wraplength=300,
            font=('Arial', 9, 'bold')
        )
        self.selected_label.pack()
        
        # Atualizar seleção
        self.product_listbox.bind('<<ListboxSelect>>', self.on_product_select)
        
        # Agora que tudo está criado, fazer seleção inicial
        if self.produtos:
            self.product_listbox.selection_set(0)
            self.on_product_select(None)
        
        # Footer - Status e Capturas
        footer_frame = ttk.LabelFrame(self.root, text="📊 Status e Capturas", padding="10")
        footer_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        # Status em grid
        status_grid = ttk.Frame(footer_frame)
        status_grid.pack(fill='x')
        
        # Contadores
        self.capture_count_var = tk.StringVar(value="Capturas: 0")
        self.stream_status_var = tk.StringVar(value="Aguardando...")
        
        ttk.Label(status_grid, textvariable=self.stream_status_var, font=('Arial', 10)).pack(side='left')
        ttk.Label(status_grid, textvariable=self.capture_count_var, font=('Arial', 10, 'bold')).pack(side='right')
        
        # Botões de ação
        action_buttons = ttk.Frame(footer_frame)
        action_buttons.pack(fill='x', pady=(10, 0))
        
        ttk.Button(action_buttons, text="📋 Ver Capturas", command=self.show_captures).pack(side='left', padx=(0, 10))
        ttk.Button(action_buttons, text="📤 Exportar", command=self.export_captures).pack(side='left', padx=(0, 10))
        ttk.Button(action_buttons, text="🗑️ Limpar", command=self.clear_captures).pack(side='left', padx=(0, 10))
        ttk.Button(action_buttons, text="📁 Abrir Pasta", command=self.open_captures_folder).pack(side='left')
    
    def filter_products(self, *args):
        """Filtra produtos baseado na busca"""
        query = self.search_var.get().lower()
        if query:
            filtered = [p for p in self.produtos if query in p.lower()]
        else:
            filtered = self.produtos
        
        self.update_product_list(filtered)
    
    def update_product_list(self, products):
        """Atualiza lista de produtos"""
        self.product_listbox.delete(0, tk.END)
        for product in products:
            self.product_listbox.insert(tk.END, product)
        
        # Auto-selecionar primeiro se existir (apenas se a variável já existir)
        if products and hasattr(self, 'selected_product_var'):
            self.product_listbox.selection_set(0)
            self.on_product_select(None)
    
    def on_product_select(self, event):
        """Atualiza produto selecionado"""
        selection = self.product_listbox.curselection()
        if selection:
            product = self.product_listbox.get(selection[0])
            # Truncar nome longo
            display_name = product[:50] + "..." if len(product) > 50 else product
            self.selected_product_var.set(display_name)
        else:
            self.selected_product_var.set("Nenhum produto selecionado")
    
    def get_snapshot(self):
        """Obtém uma única captura da câmera"""
        for url_path in self.snapshot_urls:
            try:
                url = f"{self.base_url}{url_path}"
                
                response = self.session.get(
                    url,
                    auth=self.auth,
                    timeout=10,
                    stream=True
                )
                
                content_type = response.headers.get('content-type', '').lower()
                
                if (response.status_code == 200 and 
                    ('image' in content_type or 'jpeg' in content_type) and
                    len(response.content) > 5000):
                    
                    return {
                        'success': True,
                        'data': response.content,
                        'url': url_path,
                        'size': len(response.content)
                    }
                    
            except Exception as e:
                continue
        
        return {'success': False, 'error': 'Todos os endpoints falharam'}
    
    def start_streaming(self):
        """Inicia o streaming contínuo"""
        if self.streaming_active:
            return
            
        self.streaming_active = True
        self.status_label.config(text="🟢 Streaming Ativo")
        self.stream_btn.config(text="⏸️ Pausar Stream")
        self.stream_status_var.set("🎥 Streaming ao vivo - Clique 'CAPTURAR' para fotografar")
        
        # Thread de streaming
        def streaming_thread():
            while self.streaming_active:
                try:
                    result = self.get_snapshot()
                    
                    if result['success']:
                        # Processar imagem
                        image = Image.open(io.BytesIO(result['data']))
                        
                        # Redimensionar mantendo proporção para caber na tela
                        display_image = image.copy()
                        display_image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                        
                        # Converter para PhotoImage
                        photo = ImageTk.PhotoImage(display_image)
                        
                        # Atualizar na thread principal
                        self.root.after(0, self.update_stream_display, photo, result)
                        
                        # Armazenar frame atual
                        self.current_frame = result['data']
                        
                        # Controle de FPS
                        self.fps_counter += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            fps = self.fps_counter / (current_time - self.last_fps_time)
                            self.root.after(0, lambda: self.fps_label.config(text=f"FPS: {fps:.1f}"))
                            self.fps_counter = 0
                            self.last_fps_time = current_time
                        
                        # Qualidade da conexão
                        self.root.after(0, lambda: self.quality_indicator.config(foreground='green'))
                        
                    else:
                        # Erro na captura
                        self.root.after(0, lambda: self.quality_indicator.config(foreground='red'))
                        time.sleep(2)  # Pausa maior em caso de erro
                        
                    # Controle de taxa de atualização (aproximadamente 2 FPS)
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.root.after(0, lambda: self.quality_indicator.config(foreground='orange'))
                    time.sleep(3)
        
        # Iniciar thread
        thread = threading.Thread(target=streaming_thread, daemon=True)
        thread.start()
    
    def update_stream_display(self, photo, result):
        """Atualiza o display do streaming (executado na thread principal)"""
        self.stream_label.config(image=photo, text="")
        self.stream_label.image = photo  # Manter referência
        
        # Atualizar status
        size_kb = result['size'] / 1024
        self.stream_status_var.set(f"🎥 Streaming ativo - {size_kb:.0f}KB - Pronto para capturar")
    
    def toggle_streaming(self):
        """Liga/desliga o streaming"""
        if self.streaming_active:
            self.streaming_active = False
            self.status_label.config(text="🟡 Stream Pausado")
            self.stream_btn.config(text="▶️ Retomar Stream")
            self.quality_indicator.config(foreground='gray')
            self.stream_status_var.set("⏸️ Streaming pausado")
        else:
            self.start_streaming()
    
    def restart_streaming(self):
        """Reinicia o streaming"""
        self.streaming_active = False
        time.sleep(0.5)
        self.start_streaming()
        self.stream_status_var.set("🔄 Streaming reiniciado")
    
    def capture_current_frame(self):
        """Captura o frame atual (sob demanda)"""
        if not self.current_frame:
            messagebox.showwarning("Aviso", "Nenhum frame disponível! Aguarde o streaming conectar.")
            return
        
        # Verificar se há produto selecionado
        selection = self.product_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um produto antes de capturar!")
            return
        
        product = self.product_listbox.get(selection[0])
        
        try:
            # Criar pasta se não existir
            os.makedirs("capturas_streaming", exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}_{len(self.captured_images)+1:03d}.jpg"
            filepath = os.path.join("capturas_streaming", filename)
            
            # Salvar imagem
            with open(filepath, 'wb') as f:
                f.write(self.current_frame)
            
            # Registrar captura
            capture_data = {
                'id': len(self.captured_images) + 1,
                'produto': product,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': filename,
                'filepath': filepath,
                'source': 'Streaming Intelbras'
            }
            
            self.captured_images.append(capture_data)
            
            # Atualizar contador
            self.capture_count_var.set(f"Capturas: {len(self.captured_images)}")
            
            # Feedback visual
            self.capture_btn.config(text="✅ CAPTURADO!")
            self.root.after(1000, lambda: self.capture_btn.config(text="📸 CAPTURAR AGORA"))
            
            # Status
            self.stream_status_var.set(f"📸 Capturado: {product[:30]}...")
            
            messagebox.showinfo("Captura Realizada", f"✅ Foto salva!\n\nProduto: {product}\nArquivo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")
    
    def show_captures(self):
        """Mostra janela com todas as capturas"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura realizada ainda")
            return
        
        # Janela de capturas
        window = tk.Toplevel(self.root)
        window.title(f"Capturas Realizadas - {len(self.captured_images)} fotos")
        window.geometry("1000x600")
        
        # Treeview
        columns = ('ID', 'Produto', 'Data/Hora', 'Arquivo')
        tree = ttk.Treeview(window, columns=columns, show='headings', height=20)
        
        # Configurar colunas
        tree.heading('ID', text='ID')
        tree.heading('Produto', text='Produto')
        tree.heading('Data/Hora', text='Data/Hora')
        tree.heading('Arquivo', text='Arquivo')
        
        tree.column('ID', width=50)
        tree.column('Produto', width=400)
        tree.column('Data/Hora', width=150)
        tree.column('Arquivo', width=300)
        
        # Preencher dados
        for capture in self.captured_images:
            tree.insert('', 'end', values=(
                capture['id'],
                capture['produto'],
                capture['timestamp'],
                capture['filename']
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Botão para abrir pasta
        ttk.Button(window, text="📁 Abrir Pasta das Capturas", 
                  command=self.open_captures_folder).pack(pady=10)
    
    def export_captures(self):
        """Exporta dados das capturas para CSV"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura para exportar")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_capturas_{timestamp}.csv"
            
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write("ID,Produto,Data_Hora,Arquivo,Caminho_Completo\n")
                
                for capture in self.captured_images:
                    f.write(f'{capture["id"]},"{capture["produto"]}",{capture["timestamp"]},')
                    f.write(f'{capture["filename"]},"{capture["filepath"]}"\n')
            
            self.stream_status_var.set(f"📤 Exportado: {filename}")
            messagebox.showinfo("Exportação Concluída", f"Arquivo salvo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na exportação: {e}")
    
    def clear_captures(self):
        """Limpa todas as capturas"""
        if not self.captured_images:
            return
        
        if messagebox.askyesno("Confirmar", f"Limpar todas as {len(self.captured_images)} capturas?\n\n(Os arquivos não serão deletados)"):
            self.captured_images.clear()
            self.capture_count_var.set("Capturas: 0")
            self.stream_status_var.set("🗑️ Capturas limpas - continuando streaming")
    
    def open_captures_folder(self):
        """Abre pasta das capturas"""
        import subprocess
        import sys
        
        folder_path = os.path.abspath("capturas_streaming")
        
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")

def main():
    root = tk.Tk()
    
    # Estilo
    style = ttk.Style()
    if "Accent.TButton" not in style.theme_names():
        style.configure("Accent.TButton", font=('Arial', 10, 'bold'))
    
    app = StreamingIntelbras(root)
    
    # Configurar fechamento
    def on_closing():
        app.streaming_active = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()