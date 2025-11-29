#!/usr/bin/env python3
"""
VerifiK - Streaming Simplificado Intelbras
Versão otimizada para garantir funcionamento das imagens
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

class StreamingSimples:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Streaming Intelbras SIMPLIFICADO")
        self.root.geometry("1000x700")
        
        # Config câmera
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"  
        self.camera_pass = "C@sa3863"
        
        # Usar Digest Auth (conforme diagnóstico)
        from requests.auth import HTTPDigestAuth
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # Variáveis
        self.streaming = False
        self.current_image = None
        self.capturas = []
        self.produtos = []
        
        # URLs de teste
        self.urls = [
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi?channel=1&subtype=0",
            f"http://{self.camera_ip}/cgi-bin/magicBox.cgi?action=getSnapshot&channel=1&subtype=0",
            f"http://{self.camera_ip}/Streaming/Channels/101/picture"
        ]
        
        self.setup_ui()
        self.carregar_produtos()
        
        # Testar conexão imediatamente
        self.root.after(500, self.testar_conexao)
    
    def setup_ui(self):
        """Interface simples e funcional"""
        
        # Header
        header = ttk.LabelFrame(self.root, text="📹 Câmera Intelbras", padding="10")
        header.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(header, text=f"IP: {self.camera_ip} | User: {self.camera_user}", 
                 font=('Arial', 10)).pack(side='left')
        
        self.status_conexao = ttk.Label(header, text="🔴 Testando...", font=('Arial', 10, 'bold'))
        self.status_conexao.pack(side='right')
        
        # Frame principal
        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Streaming (esquerda)
        stream_frame = ttk.LabelFrame(main, text="📺 Visualização", padding="10")
        stream_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Área da imagem
        self.image_label = ttk.Label(stream_frame, 
                                   text="📷\n\nTeste de Conexão...\nAguarde...", 
                                   justify=tk.CENTER, 
                                   font=('Arial', 12),
                                   background='lightgray')
        self.image_label.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Controles
        controles = ttk.Frame(stream_frame)
        controles.pack(fill='x', pady=5)
        
        self.btn_testar = ttk.Button(controles, text="🔍 Testar Conexão", 
                                   command=self.testar_conexao_manual)
        self.btn_testar.pack(side='left', padx=5)
        
        self.btn_stream = ttk.Button(controles, text="▶️ Iniciar Stream", 
                                   command=self.toggle_stream)
        self.btn_stream.pack(side='left', padx=5)
        
        self.btn_capturar = ttk.Button(controles, text="📸 CAPTURAR", 
                                     command=self.capturar_agora,
                                     style='Accent.TButton')
        self.btn_capturar.pack(side='left', padx=5)
        
        # Produtos (direita)
        produtos_frame = ttk.LabelFrame(main, text="📦 Produtos", padding="10")
        produtos_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # Lista simples
        self.lista_produtos = tk.Listbox(produtos_frame, width=30, height=25, font=('Arial', 9))
        scroll = ttk.Scrollbar(produtos_frame, command=self.lista_produtos.yview)
        
        self.lista_produtos.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.lista_produtos.config(yscrollcommand=scroll.set)
        
        # Status
        self.status_label = ttk.Label(self.root, text="Iniciando sistema...", font=('Arial', 10))
        self.status_label.pack(pady=5)
    
    def carregar_produtos(self):
        """Carrega produtos da base"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT descricao_produto FROM produtos WHERE ativo = 1 ORDER BY descricao_produto")
            self.produtos = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Preencher lista
            for produto in self.produtos:
                self.lista_produtos.insert(tk.END, produto)
            
            if self.produtos:
                self.lista_produtos.selection_set(0)
            
            self.status_label.config(text=f"✅ {len(self.produtos)} produtos carregados")
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erro produtos: {e}")
            self.produtos = ["TESTE 1", "TESTE 2"]
            for produto in self.produtos:
                self.lista_produtos.insert(tk.END, produto)
    
    def testar_conexao(self):
        """Testa conexão e primeira captura"""
        def teste_thread():
            self.status_label.config(text="🔍 Testando conexão com câmera...")
            
            for i, url in enumerate(self.urls, 1):
                try:
                    self.status_label.config(text=f"🔍 Testando URL {i}/{len(self.urls)}...")
                    
                    response = requests.get(
                        url,
                        auth=self.auth,
                        timeout=10
                    )
                    
                    if response.status_code == 200 and len(response.content) > 5000:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'image' in content_type or 'jpeg' in content_type:
                            # Sucesso! Mostrar imagem
                            self.root.after(0, self.mostrar_primeira_imagem, response.content, url)
                            return
                
                except Exception as e:
                    print(f"Erro URL {url}: {e}")
                    continue
            
            # Se chegou aqui, falhou
            self.root.after(0, self.conexao_falhada)
        
        thread = threading.Thread(target=teste_thread, daemon=True)
        thread.start()
    
    def mostrar_primeira_imagem(self, image_data, url_sucesso):
        """Mostra primeira imagem capturada"""
        try:
            # Processar imagem
            image = Image.open(io.BytesIO(image_data))
            
            # Redimensionar
            image.thumbnail((600, 450), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Mostrar
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
            self.current_image = image_data
            
            # Status
            self.status_conexao.config(text="🟢 Conectado")
            self.status_label.config(text=f"✅ Conectado! URL: {url_sucesso}")
            
            # Ativar streaming automático
            self.btn_stream.config(text="⏸️ Pausar Stream")
            self.iniciar_streaming_automatico(url_sucesso)
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erro ao processar imagem: {e}")
    
    def conexao_falhada(self):
        """Quando não consegue conectar"""
        self.status_conexao.config(text="🔴 Falhou")
        self.status_label.config(text="❌ Não foi possível conectar à câmera")
        self.image_label.config(text="❌\n\nConexão Falhada\n\nVerifique:\n• IP da câmera\n• Usuário/senha\n• Rede")
    
    def testar_conexao_manual(self):
        """Teste manual"""
        self.testar_conexao()
    
    def iniciar_streaming_automatico(self, url_sucesso):
        """Inicia streaming com a URL que funcionou"""
        self.streaming = True
        self.url_ativa = url_sucesso
        
        def stream_loop():
            frame_count = 0
            while self.streaming:
                try:
                    response = requests.get(
                        self.url_ativa,
                        auth=self.auth,
                        timeout=8
                    )
                    
                    if response.status_code == 200 and len(response.content) > 5000:
                        # Processar
                        image = Image.open(io.BytesIO(response.content))
                        image.thumbnail((600, 450), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        # Atualizar UI na thread principal
                        self.root.after(0, self.atualizar_frame, photo, response.content)
                        
                        frame_count += 1
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"🎥 Streaming ativo - Frame {frame_count} - Clique CAPTURAR para fotografar"))
                    
                    time.sleep(1)  # 1 FPS
                    
                except Exception as e:
                    self.root.after(0, lambda: self.status_label.config(text=f"⚠️ Erro stream: {str(e)[:50]}"))
                    time.sleep(3)
        
        thread = threading.Thread(target=stream_loop, daemon=True)
        thread.start()
    
    def atualizar_frame(self, photo, image_data):
        """Atualiza frame na UI (thread principal)"""
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo
        self.current_image = image_data
    
    def toggle_stream(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.streaming = False
            self.btn_stream.config(text="▶️ Iniciar Stream")
            self.status_label.config(text="⏸️ Streaming pausado")
        else:
            if hasattr(self, 'url_ativa'):
                self.iniciar_streaming_automatico(self.url_ativa)
                self.btn_stream.config(text="⏸️ Pausar Stream")
            else:
                self.testar_conexao()
    
    def capturar_agora(self):
        """Captura a imagem atual"""
        if not self.current_image:
            messagebox.showwarning("Aviso", "Nenhuma imagem disponível!")
            return
        
        selection = self.lista_produtos.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        produto = self.lista_produtos.get(selection[0])
        
        try:
            # Criar pasta
            os.makedirs("capturas_streaming_simples", exist_ok=True)
            
            # Salvar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cap_{timestamp}_{len(self.capturas)+1:03d}.jpg"
            filepath = os.path.join("capturas_streaming_simples", filename)
            
            with open(filepath, 'wb') as f:
                f.write(self.current_image)
            
            # Registrar
            captura = {
                'id': len(self.capturas) + 1,
                'produto': produto,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': filename,
                'filepath': filepath
            }
            
            self.capturas.append(captura)
            
            # Feedback
            self.btn_capturar.config(text="✅ SALVO!")
            self.root.after(1500, lambda: self.btn_capturar.config(text="📸 CAPTURAR"))
            
            self.status_label.config(text=f"💾 Capturado: {produto[:40]}... | Total: {len(self.capturas)}")
            
            messagebox.showinfo("Sucesso", f"📸 Captura realizada!\n\nProduto: {produto}\nArquivo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")

def main():
    root = tk.Tk()
    
    # Configurar estilo
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = StreamingSimples(root)
    
    # Fechar corretamente
    def on_close():
        app.streaming = False
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()