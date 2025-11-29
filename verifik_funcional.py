#!/usr/bin/env python3
"""
VerifiK - Sistema de Streaming Funcional
Interface simples e eficaz para câmera Intelbras com análise automática
"""

import tkinter as tk
from tkinter import ttk
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image, ImageTk
import threading
import time
import sqlite3

class VerifiKStreaming:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 VerifiK - Streaming Funcional")
        self.root.geometry("1000x700")
        
        # Configurações da câmera
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # Estado do sistema
        self.streaming = False
        self.current_image = None
        
        # Carregar produtos
        self.carregar_produtos()
        
        # Criar interface
        self.criar_interface()
        
        print(f"✅ Sistema iniciado - {len(self.produtos)} produtos carregados")
    
    def carregar_produtos(self):
        """Carrega produtos da base de dados"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT descricao_produto FROM produtos WHERE ativo = 1 ORDER BY descricao_produto")
            self.produtos = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"⚠️ Erro ao carregar produtos: {e}")
            self.produtos = ["PRODUTO TESTE 1", "PRODUTO TESTE 2", "PRODUTO TESTE 3"]
    
    def criar_interface(self):
        """Cria a interface do usuário"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🎯 VerifiK - Sistema de Streaming", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Frame superior - controles
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Controles", padding="10")
        control_frame.pack(fill='x', pady=(0, 10))
        
        # Botões principais
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill='x')
        
        self.btn_stream = ttk.Button(buttons_frame, text="▶️ Iniciar Stream", 
                                   command=self.toggle_streaming)
        self.btn_stream.pack(side='left', padx=(0, 10))
        
        self.btn_captura = ttk.Button(buttons_frame, text="📸 Capturar", 
                                    command=self.capturar_imagem)
        self.btn_captura.pack(side='left', padx=(0, 10))
        
        # Status
        self.status_label = ttk.Label(buttons_frame, text="⚪ Pronto para iniciar")
        self.status_label.pack(side='left', padx=(20, 0))
        
        # Frame do meio - vídeo e informações
        video_frame = ttk.LabelFrame(main_frame, text="📹 Câmera", padding="10")
        video_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Canvas para vídeo
        self.video_canvas = tk.Canvas(video_frame, width=640, height=480, bg='black')
        self.video_canvas.pack()
        
        # Frame inferior - produtos
        product_frame = ttk.LabelFrame(main_frame, text="📦 Produtos Detectados", padding="10")
        product_frame.pack(fill='x')
        
        # Lista de produtos
        self.product_text = tk.Text(product_frame, height=5, wrap=tk.WORD)
        self.product_text.pack(fill='x')
        
        # Mensagem inicial
        self.product_text.insert('1.0', f"📊 Sistema carregado com {len(self.produtos)} produtos\n")
        self.product_text.insert('end', "🎯 Clique em 'Iniciar Stream' para começar")
    
    def toggle_streaming(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.parar_streaming()
        else:
            self.iniciar_streaming()
    
    def iniciar_streaming(self):
        """Inicia o streaming da câmera"""
        print("🚀 Iniciando streaming...")
        
        # Testar conectividade primeiro
        if not self.testar_camera():
            self.status_label.config(text="❌ Câmera inacessível")
            return
        
        self.streaming = True
        self.btn_stream.config(text="⏸️ Parar Stream")
        self.status_label.config(text="🟡 Conectando...")
        
        # Iniciar thread de captura
        thread = threading.Thread(target=self.loop_streaming, daemon=True)
        thread.start()
    
    def parar_streaming(self):
        """Para o streaming"""
        self.streaming = False
        self.btn_stream.config(text="▶️ Iniciar Stream")
        self.status_label.config(text="⏸️ Pausado")
        print("⏹️ Streaming parado")
    
    def testar_camera(self):
        """Testa conectividade com a câmera"""
        try:
            print(f"🔍 Testando câmera {self.camera_ip}...")
            
            # Teste básico
            url = f"http://{self.camera_ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
            response = requests.get(url, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Câmera conectada: {response.text.strip()}")
                
                # Teste de snapshot
                snapshot_url = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
                snap_resp = requests.get(snapshot_url, auth=self.auth, timeout=3)
                
                if snap_resp.status_code == 200 and len(snap_resp.content) > 5000:
                    print("✅ Snapshot funcionando")
                    return True
                else:
                    print(f"❌ Snapshot falhou: {snap_resp.status_code}")
            else:
                print(f"❌ Câmera inacessível: {response.status_code}")
                
        except Exception as e:
            print(f"💥 Erro: {e}")
        
        return False
    
    def loop_streaming(self):
        """Loop principal do streaming"""
        frame_count = 0
        
        while self.streaming:
            try:
                # Capturar frame
                image_data = self.capturar_frame()
                
                if image_data:
                    # Atualizar display
                    self.root.after(0, self.atualizar_display, image_data)
                    
                    frame_count += 1
                    
                    # Status a cada 30 frames
                    if frame_count % 30 == 0:
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"🟢 Ativo - Frame {frame_count}"
                        ))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="🔴 Erro captura"))
                
                time.sleep(0.2)  # ~5 FPS
                
            except Exception as e:
                print(f"❌ Erro no loop: {e}")
                time.sleep(1)
    
    def capturar_frame(self):
        """Captura um frame da câmera"""
        try:
            url = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
            response = requests.get(url, auth=self.auth, timeout=3)
            
            if response.status_code == 200 and len(response.content) > 5000:
                return response.content
                
        except Exception as e:
            print(f"⚠️ Erro captura: {e}")
        
        return None
    
    def atualizar_display(self, image_data):
        """Atualiza o display com nova imagem"""
        try:
            # Converter para PIL
            from io import BytesIO
            image = Image.open(BytesIO(image_data))
            
            # Redimensionar se necessário
            image = image.resize((640, 480), Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Atualizar canvas
            self.video_canvas.delete("all")
            self.video_canvas.create_image(320, 240, image=photo, anchor=tk.CENTER)
            self.video_canvas.image = photo  # Manter referência
            
            # Armazenar imagem atual
            self.current_image = image
            
        except Exception as e:
            print(f"❌ Erro display: {e}")
    
    def capturar_imagem(self):
        """Captura e salva imagem atual"""
        if self.current_image:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"captura_{timestamp}.jpg"
                
                self.current_image.save(filename, quality=95)
                
                self.product_text.insert('end', f"\n📸 Imagem salva: {filename}")
                self.product_text.see('end')
                
                print(f"✅ Imagem salva: {filename}")
                
            except Exception as e:
                print(f"❌ Erro ao salvar: {e}")
        else:
            print("⚠️ Nenhuma imagem para capturar")

def main():
    root = tk.Tk()
    app = VerifiKStreaming(root)
    
    def on_closing():
        app.streaming = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()