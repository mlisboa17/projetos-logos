#!/usr/bin/env python3
"""
Sistema de captura integrado VerifiK + Câmera Intelbras
Combina a coleta manual com capturas automáticas da câmera IP
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from requests.auth import HTTPBasicAuth
import cv2
import numpy as np
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os
import threading
import time

class VerifiKCameraSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK + Câmera Intelbras - Sistema Integrado")
        self.root.geometry("1200x800")
        
        # Configurações da câmera
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.camera_url = f"http://{self.camera_ip}"
        
        # Variáveis de controle
        self.capturing = False
        self.captured_images = []
        self.current_image = None
        self.produtos = []
        
        # Carregar produtos
        self.load_products()
        
        # Interface
        self.setup_interface()
        
        # Testar conexão da câmera
        self.test_camera_connection()
    
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
        """Configura a interface do sistema"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="VerifiK + Câmera Intelbras", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame da câmera
        camera_frame = ttk.LabelFrame(main_frame, text="Câmera Intelbras", padding="10")
        camera_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Canvas para vídeo
        self.video_canvas = tk.Canvas(camera_frame, width=640, height=480, bg='black')
        self.video_canvas.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status da câmera
        self.camera_status = ttk.Label(camera_frame, text="🔴 Câmera desconectada")
        self.camera_status.grid(row=1, column=0, sticky=tk.W)
        
        # Botões da câmera
        ttk.Button(camera_frame, text="🔄 Conectar", command=self.connect_camera).grid(row=1, column=1, padx=5)
        ttk.Button(camera_frame, text="📸 Capturar", command=self.capture_from_camera).grid(row=1, column=2, padx=5)
        
        # Frame de produtos
        product_frame = ttk.LabelFrame(main_frame, text="Seleção de Produto", padding="10")
        product_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Busca de produto
        ttk.Label(product_frame, text="Buscar produto:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_products)
        search_entry = ttk.Entry(product_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=1, column=0, pady=(0, 10))
        
        # Lista de produtos
        self.product_listbox = tk.Listbox(product_frame, height=15)
        self.product_listbox.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para lista
        scrollbar = ttk.Scrollbar(product_frame, orient="vertical")
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.product_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.product_listbox.yview)
        
        # Preencher lista inicial
        self.update_product_list(self.produtos)
        
        # Frame de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Botões principais
        ttk.Button(control_frame, text="💾 Salvar Imagem", command=self.save_image).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="📁 Captura Manual", command=self.manual_capture).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="📊 Ver Capturas", command=self.show_captures).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="📤 Exportar CSV", command=self.export_csv).grid(row=0, column=3, padx=5)
        
        # Status geral
        self.status_var = tk.StringVar(value="Sistema iniciado - Conecte a câmera")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # Contador de imagens
        self.counter_var = tk.StringVar(value="Imagens capturadas: 0")
        counter_label = ttk.Label(control_frame, textvariable=self.counter_var)
        counter_label.grid(row=2, column=0, columnspan=4, pady=(5, 0))
    
    def filter_products(self, *args):
        """Filtra produtos conforme busca"""
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
    
    def test_camera_connection(self):
        """Testa conexão inicial com a câmera"""
        try:
            response = requests.get(
                self.camera_url,
                auth=HTTPBasicAuth(self.camera_user, self.camera_pass),
                timeout=5
            )
            if response.status_code == 200:
                self.camera_status.config(text="🟢 Câmera disponível")
                self.status_var.set("Câmera detectada - Pronto para captura")
            else:
                self.camera_status.config(text="🟡 Câmera com problemas")
        except Exception as e:
            self.camera_status.config(text="🔴 Câmera inacessível")
            print(f"Erro na câmera: {e}")
    
    def connect_camera(self):
        """Conecta ao stream da câmera"""
        try:
            # URL RTSP da câmera
            rtsp_url = f"rtsp://{self.camera_user}:{self.camera_pass}@{self.camera_ip}:554/cam/realmonitor?channel=1&subtype=0"
            
            self.cap = cv2.VideoCapture(rtsp_url)
            
            if self.cap.isOpened():
                self.camera_status.config(text="🟢 Stream conectado")
                self.status_var.set("Stream ativo - Clique em Capturar para obter imagem")
                self.capturing = True
                self.update_video_feed()
            else:
                self.camera_status.config(text="🔴 Falha no stream")
                self.status_var.set("Erro: Não foi possível conectar ao stream RTSP")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar câmera: {e}")
    
    def update_video_feed(self):
        """Atualiza feed de vídeo"""
        if self.capturing and hasattr(self, 'cap') and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Redimensionar frame
                frame = cv2.resize(frame, (640, 480))
                
                # Converter para RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Converter para PhotoImage
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # Atualizar canvas
                self.video_canvas.delete("all")
                self.video_canvas.create_image(320, 240, image=photo, anchor=tk.CENTER)
                self.video_canvas.image = photo  # Manter referência
                
                # Armazenar frame atual
                self.current_frame = frame_rgb
        
        # Agendar próxima atualização
        if self.capturing:
            self.root.after(50, self.update_video_feed)
    
    def capture_from_camera(self):
        """Captura imagem da câmera"""
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            self.current_image = self.current_frame.copy()
            self.status_var.set("Imagem capturada! Selecione um produto e clique em Salvar")
            
            # Adicionar borda verde para indicar captura
            self.video_canvas.config(highlightbackground="green", highlightthickness=3)
            self.root.after(1000, lambda: self.video_canvas.config(highlightthickness=0))
        else:
            messagebox.showwarning("Aviso", "Conecte a câmera primeiro!")
    
    def manual_capture(self):
        """Captura manual via arquivo"""
        file_path = filedialog.askopenfilename(
            title="Selecionar imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            try:
                image = Image.open(file_path)
                self.current_image = np.array(image)
                self.status_var.set("Imagem manual carregada! Selecione um produto e salve")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar imagem: {e}")
    
    def save_image(self):
        """Salva imagem com produto selecionado"""
        if self.current_image is None:
            messagebox.showwarning("Aviso", "Capture uma imagem primeiro!")
            return
        
        selected_indices = self.product_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        selected_product = self.product_listbox.get(selected_indices[0])
        
        # Criar dados da captura
        capture_data = {
            'id': len(self.captured_images) + 1,
            'produto': selected_product,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fonte': 'Câmera IP' if self.capturing else 'Manual',
            'imagem': self.current_image.copy()
        }
        
        # Salvar arquivo de imagem
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captura_{timestamp_str}_{capture_data['id']}.jpg"
        
        try:
            os.makedirs("capturas", exist_ok=True)
            image_path = os.path.join("capturas", filename)
            
            # Salvar imagem
            image_pil = Image.fromarray(self.current_image)
            image_pil.save(image_path, quality=95)
            
            capture_data['arquivo'] = filename
            capture_data['caminho'] = image_path
            
            # Adicionar à lista
            self.captured_images.append(capture_data)
            
            # Atualizar contadores
            self.counter_var.set(f"Imagens capturadas: {len(self.captured_images)}")
            self.status_var.set(f"✅ Salvo: {selected_product}")
            
            # Limpar seleção
            self.current_image = None
            
            messagebox.showinfo("Sucesso", f"Imagem salva como {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
    
    def show_captures(self):
        """Mostra janela com capturas realizadas"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura realizada ainda")
            return
        
        # Criar janela
        captures_window = tk.Toplevel(self.root)
        captures_window.title("Capturas Realizadas")
        captures_window.geometry("800x600")
        
        # Treeview para mostrar capturas
        columns = ('ID', 'Produto', 'Data/Hora', 'Fonte', 'Arquivo')
        tree = ttk.Treeview(captures_window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Adicionar dados
        for capture in self.captured_images:
            tree.insert('', 'end', values=(
                capture['id'],
                capture['produto'][:30] + '...' if len(capture['produto']) > 30 else capture['produto'],
                capture['timestamp'],
                capture['fonte'],
                capture['arquivo']
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def export_csv(self):
        """Exporta capturas para CSV"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura para exportar")
            return
        
        filename = f"verifik_capturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("ID,Produto,Data_Hora,Fonte,Arquivo,Caminho\n")
                
                for capture in self.captured_images:
                    f.write(f"{capture['id']},\"{capture['produto']}\",{capture['timestamp']},{capture['fonte']},{capture['arquivo']},{capture['caminho']}\n")
            
            messagebox.showinfo("Sucesso", f"Dados exportados para {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

def main():
    root = tk.Tk()
    app = VerifiKCameraSystem(root)
    
    def on_closing():
        if hasattr(app, 'cap') and app.cap.isOpened():
            app.cap.release()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()