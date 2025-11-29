#!/usr/bin/env python3
"""
Sistema VerifiK com API Oficial Intelbras
Utiliza comandos CGI e ONVIF nativos da Intelbras
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os
import io
import threading
import time
import json
import xml.etree.ElementTree as ET

class IntelbrasAPI:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}"
        self.session = requests.Session()
        self.auth_basic = HTTPBasicAuth(username, password)
        self.auth_digest = HTTPDigestAuth(username, password)
        self.device_info = {}
        
    def get_device_info(self):
        """Obtém informações do dispositivo via API Intelbras"""
        endpoints = [
            "/cgi-bin/magicBox.cgi?action=getDeviceType",
            "/cgi-bin/magicBox.cgi?action=getMachineName", 
            "/cgi-bin/magicBox.cgi?action=getSystemInfo",
            "/cgi-bin/configManager.cgi?action=getConfig&name=General",
            "/cgi-bin/global.cgi?action=getCurrentTime"
        ]
        
        device_data = {}
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    auth=self.auth_basic,
                    timeout=10
                )
                
                if response.status_code == 200:
                    content = response.text.strip()
                    if "=" in content:
                        # Formato key=value da Intelbras
                        for line in content.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                device_data[key.strip()] = value.strip()
                                
            except Exception as e:
                continue
        
        self.device_info = device_data
        return device_data
    
    def get_channels_info(self):
        """Obtém informações dos canais de vídeo"""
        try:
            response = self.session.get(
                f"{self.base_url}/cgi-bin/configManager.cgi?action=getConfig&name=VideoInOptions",
                auth=self.auth_basic,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            pass
        return None
    
    def capture_snapshot(self, channel=1, quality='high'):
        """Captura snapshot via API oficial Intelbras"""
        
        # URLs específicas da API Intelbras por prioridade
        snapshot_endpoints = [
            # API Intelbras padrão
            f"/cgi-bin/snapshot.cgi?channel={channel}&subtype=0",
            f"/cgi-bin/snapshot.cgi?chn={channel}&u={self.username}&p={self.password}",
            
            # API magicBox (mais recente)
            f"/cgi-bin/magicBox.cgi?action=getSnapshot&channel={channel}&subtype=0",
            
            # API configManager 
            f"/cgi-bin/configManager.cgi?action=attachFileProc&name=Snap&channel={channel}&subtype=0",
            
            # APIs alternativas
            f"/Streaming/Channels/{channel}01/picture",
            f"/cgi-bin/hi3510/snap.cgi?&-usr={self.username}&-pwd={self.password}",
            
            # ONVIF padrão
            f"/onvif-http/snapshot?Profile_{channel}",
        ]
        
        for endpoint in snapshot_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Tentar diferentes métodos de autenticação
                for auth_method in [self.auth_basic, self.auth_digest]:
                    try:
                        response = self.session.get(
                            url, 
                            auth=auth_method,
                            timeout=15,
                            stream=True
                        )
                        
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if (response.status_code == 200 and 
                            ('image' in content_type or 'jpeg' in content_type) and
                            len(response.content) > 2000):
                            
                            return {
                                'success': True,
                                'data': response.content,
                                'endpoint': endpoint,
                                'auth_method': type(auth_method).__name__,
                                'content_type': content_type,
                                'size': len(response.content)
                            }
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        return {'success': False, 'error': 'Todos os endpoints falharam'}
    
    def get_rtsp_urls(self, channel=1):
        """Gera URLs RTSP para diferentes qualidades"""
        rtsp_urls = [
            # Formato Intelbras padrão
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel={channel}&subtype=0",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel={channel}&subtype=1",
            
            # Formato alternativo
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_0{channel}_main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_0{channel}_sub",
            
            # ONVIF
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/{channel}/main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/{channel}/sub"
        ]
        
        return rtsp_urls
    
    def control_ptz(self, action, channel=1, speed=5):
        """Controla PTZ se disponível"""
        ptz_commands = {
            'up': f"/cgi-bin/ptz.cgi?action=start&channel={channel}&code=Up&arg1={speed}&arg2={speed}",
            'down': f"/cgi-bin/ptz.cgi?action=start&channel={channel}&code=Down&arg1={speed}&arg2={speed}",
            'left': f"/cgi-bin/ptz.cgi?action=start&channel={channel}&code=Left&arg1={speed}&arg2={speed}",
            'right': f"/cgi-bin/ptz.cgi?action=start&channel={channel}&code=Right&arg1={speed}&arg2={speed}",
            'stop': f"/cgi-bin/ptz.cgi?action=stop&channel={channel}"
        }
        
        if action in ptz_commands:
            try:
                response = self.session.get(
                    f"{self.base_url}{ptz_commands[action]}",
                    auth=self.auth_basic,
                    timeout=5
                )
                return response.status_code == 200
            except:
                return False
        return False

class VerifiKIntelbrasAPI:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK + API Intelbras Oficial")
        self.root.geometry("1000x750")
        
        # Configuração da câmera
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        
        # API Intelbras
        self.intelbras_api = IntelbrasAPI(self.camera_ip, self.camera_user, self.camera_pass)
        
        # Variáveis de controle
        self.captured_images = []
        self.current_image = None
        self.produtos = []
        self.device_connected = False
        self.auto_capture_active = False
        
        # Carregar produtos
        self.load_products()
        
        # Interface
        self.setup_interface()
        
        # Conectar à câmera
        self.connect_to_device()
    
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
            self.produtos = ["PRODUTO EXEMPLO 1", "PRODUTO EXEMPLO 2"]
    
    def setup_interface(self):
        """Configura interface com recursos da API Intelbras"""
        
        # Notebook para organizar abas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Aba principal - Captura
        capture_frame = ttk.Frame(notebook)
        notebook.add(capture_frame, text="📸 Captura")
        
        # Aba de configurações
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ Configurações")
        
        # === ABA CAPTURA ===
        
        # Header com informações da câmera
        header_frame = ttk.LabelFrame(capture_frame, text="Câmera Intelbras", padding="10")
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Info da câmera em grid
        ttk.Label(header_frame, text=f"📷 IP: {self.camera_ip}", font=('Arial', 10)).grid(row=0, column=0, sticky='w', padx=(0, 20))
        ttk.Label(header_frame, text=f"👤 Usuário: {self.camera_user}", font=('Arial', 10)).grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        self.connection_status = ttk.Label(header_frame, text="🔴 Desconectado", font=('Arial', 10, 'bold'))
        self.connection_status.grid(row=0, column=2, sticky='w')
        
        # Frame principal dividido
        main_content = ttk.Frame(capture_frame)
        main_content.pack(fill='both', expand=True)
        
        # Lado esquerdo - Preview e controles
        left_frame = ttk.LabelFrame(main_content, text="Visualização", padding="10")
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Preview da imagem
        self.image_preview = ttk.Label(left_frame, text="📷\nPressione 'Capturar' para\nobter imagem da câmera", 
                                     justify=tk.CENTER, font=('Arial', 12))
        self.image_preview.pack(pady=20)
        
        # Controles de captura
        capture_controls = ttk.Frame(left_frame)
        capture_controls.pack(fill='x', pady=10)
        
        ttk.Button(capture_controls, text="📸 Capturar Via API", 
                  command=self.capture_via_api, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(capture_controls, text="🎥 Auto-Captura", 
                  command=self.toggle_auto_capture).pack(side='left', padx=5)
        ttk.Button(capture_controls, text="📁 Arquivo", 
                  command=self.select_file).pack(side='left', padx=5)
        
        # Lado direito - Produtos
        right_frame = ttk.LabelFrame(main_content, text="Produtos", padding="10")
        right_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # Busca
        ttk.Label(right_frame, text="🔍 Buscar:", font=('Arial', 10)).pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_products)
        ttk.Entry(right_frame, textvariable=self.search_var, width=30).pack(fill='x', pady=(5, 10))
        
        # Lista de produtos
        list_container = ttk.Frame(right_frame)
        list_container.pack(fill='both', expand=True)
        
        self.product_listbox = tk.Listbox(list_container, width=35, height=15, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.product_listbox.yview)
        
        self.product_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.product_listbox.config(yscrollcommand=scrollbar.set)
        
        self.update_product_list(self.produtos)
        
        # Botões principais
        action_frame = ttk.LabelFrame(capture_frame, text="Ações", padding="10")
        action_frame.pack(fill='x', pady=(10, 0))
        
        # Grid de botões
        ttk.Button(action_frame, text="💾 Salvar Captura", 
                  command=self.save_capture).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(action_frame, text="📋 Ver Capturas", 
                  command=self.show_captures).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(action_frame, text="📤 Exportar", 
                  command=self.export_data).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(action_frame, text="🗑️ Limpar", 
                  command=self.clear_data).grid(row=0, column=3, padx=5, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Iniciando conexão com API Intelbras...")
        self.counter_var = tk.StringVar(value="Capturas: 0")
        
        status_frame = ttk.Frame(action_frame)
        status_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=(10, 0))
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side='left')
        ttk.Label(status_frame, textvariable=self.counter_var, font=('Arial', 10, 'bold')).pack(side='right')
        
        # === ABA CONFIGURAÇÕES ===
        
        # Device info
        device_info_frame = ttk.LabelFrame(config_frame, text="Informações do Dispositivo", padding="10")
        device_info_frame.pack(fill='x', pady=(0, 10))
        
        self.device_info_text = tk.Text(device_info_frame, height=8, width=80, font=('Consolas', 9))
        scrollbar_info = ttk.Scrollbar(device_info_frame, orient="vertical", command=self.device_info_text.yview)
        
        self.device_info_text.pack(side='left', fill='both', expand=True)
        scrollbar_info.pack(side='right', fill='y')
        self.device_info_text.config(yscrollcommand=scrollbar_info.set)
        
        # URLs RTSP
        rtsp_frame = ttk.LabelFrame(config_frame, text="URLs RTSP", padding="10")
        rtsp_frame.pack(fill='x', pady=(0, 10))
        
        self.rtsp_text = tk.Text(rtsp_frame, height=6, width=80, font=('Consolas', 9))
        self.rtsp_text.pack(fill='both', expand=True)
        
        # Botões de configuração
        config_buttons = ttk.Frame(config_frame)
        config_buttons.pack(fill='x')
        
        ttk.Button(config_buttons, text="🔄 Atualizar Info", command=self.update_device_info).pack(side='left', padx=5)
        ttk.Button(config_buttons, text="🌐 Abrir Interface Web", command=self.open_web_interface).pack(side='left', padx=5)
    
    def connect_to_device(self):
        """Conecta à câmera via API Intelbras"""
        def connect_thread():
            try:
                self.status_var.set("🔄 Conectando via API Intelbras...")
                
                # Obter informações do dispositivo
                device_info = self.intelbras_api.get_device_info()
                
                if device_info:
                    self.device_connected = True
                    self.connection_status.config(text="🟢 API Conectada")
                    self.status_var.set("✅ Conectado via API oficial Intelbras")
                    
                    # Atualizar informações na interface
                    self.update_device_info_display(device_info)
                else:
                    self.connection_status.config(text="🟡 Conectado (Info limitada)")
                    self.status_var.set("⚠️ Conectado mas com informações limitadas")
                    
            except Exception as e:
                self.connection_status.config(text="🔴 Falha na API")
                self.status_var.set(f"❌ Erro na API: {str(e)[:40]}...")
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()
    
    def capture_via_api(self):
        """Captura usando API oficial"""
        def capture_thread():
            try:
                self.status_var.set("📸 Capturando via API Intelbras...")
                
                result = self.intelbras_api.capture_snapshot()
                
                if result['success']:
                    # Processar imagem
                    image_data = result['data']
                    
                    # Preview
                    image = Image.open(io.BytesIO(image_data))
                    image.thumbnail((300, 225), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.image_preview.config(image=photo, text="")
                    self.image_preview.image = photo
                    self.current_image = image_data
                    
                    size_kb = len(image_data) / 1024
                    self.status_var.set(f"✅ Capturado via {result['endpoint']} ({size_kb:.1f}KB)")
                    
                else:
                    self.status_var.set("❌ Falha na captura via API")
                    
            except Exception as e:
                self.status_var.set(f"❌ Erro na API: {str(e)[:40]}...")
        
        thread = threading.Thread(target=capture_thread)
        thread.daemon = True
        thread.start()
    
    def toggle_auto_capture(self):
        """Ativa/desativa captura automática"""
        if self.auto_capture_active:
            self.auto_capture_active = False
            self.status_var.set("⏹️ Auto-captura desativada")
        else:
            self.auto_capture_active = True
            self.status_var.set("🎥 Auto-captura ativada (3s)")
            self.start_auto_capture()
    
    def start_auto_capture(self):
        """Loop de captura automática"""
        def auto_loop():
            while self.auto_capture_active:
                try:
                    result = self.intelbras_api.capture_snapshot()
                    if result['success']:
                        # Atualizar preview
                        image = Image.open(io.BytesIO(result['data']))
                        image.thumbnail((300, 225), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        self.image_preview.config(image=photo, text="")
                        self.image_preview.image = photo
                        self.current_image = result['data']
                    
                    # Aguardar 3 segundos
                    for i in range(30):
                        if not self.auto_capture_active:
                            break
                        time.sleep(0.1)
                        
                except Exception as e:
                    time.sleep(5)
        
        thread = threading.Thread(target=auto_loop)
        thread.daemon = True
        thread.start()
    
    def update_device_info_display(self, info):
        """Atualiza display de informações do dispositivo"""
        self.device_info_text.delete(1.0, tk.END)
        
        info_text = "=== INFORMAÇÕES DA CÂMERA INTELBRAS ===\n\n"
        
        for key, value in info.items():
            info_text += f"{key}: {value}\n"
        
        if not info:
            info_text += "Informações não disponíveis via API\n"
        
        # URLs RTSP
        rtsp_urls = self.intelbras_api.get_rtsp_urls()
        rtsp_text = "=== URLs RTSP DISPONÍVEIS ===\n\n"
        for i, url in enumerate(rtsp_urls, 1):
            rtsp_text += f"{i}. {url}\n"
        
        self.device_info_text.insert(1.0, info_text)
        self.rtsp_text.delete(1.0, tk.END)
        self.rtsp_text.insert(1.0, rtsp_text)
    
    def filter_products(self, *args):
        """Filtra produtos"""
        query = self.search_var.get().lower()
        filtered = [p for p in self.produtos if query in p.lower()] if query else self.produtos
        self.update_product_list(filtered)
    
    def update_product_list(self, products):
        """Atualiza lista de produtos"""
        self.product_listbox.delete(0, tk.END)
        for product in products:
            self.product_listbox.insert(tk.END, product)
    
    def select_file(self):
        """Seleciona arquivo de imagem"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Selecionar imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png"), ("Todos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    self.current_image = f.read()
                
                image = Image.open(file_path)
                image.thumbnail((300, 225), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.image_preview.config(image=photo, text="")
                self.image_preview.image = photo
                
                self.status_var.set(f"📁 Arquivo carregado: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar: {e}")
    
    def save_capture(self):
        """Salva captura com produto"""
        if not self.current_image:
            messagebox.showwarning("Aviso", "Capture uma imagem primeiro!")
            return
        
        selection = self.product_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        product = self.product_listbox.get(selection[0])
        
        try:
            os.makedirs("capturas_intelbras_api", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intelbras_api_{timestamp}_{len(self.captured_images)+1:03d}.jpg"
            filepath = os.path.join("capturas_intelbras_api", filename)
            
            with open(filepath, 'wb') as f:
                f.write(self.current_image)
            
            capture_data = {
                'id': len(self.captured_images) + 1,
                'produto': product,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': filename,
                'filepath': filepath,
                'source': 'API Intelbras'
            }
            
            self.captured_images.append(capture_data)
            self.counter_var.set(f"Capturas: {len(self.captured_images)}")
            self.status_var.set(f"💾 Salvo: {product}")
            
            self.current_image = None
            self.image_preview.config(image="", text="📷\nCapturar nova imagem")
            
            messagebox.showinfo("Sucesso", f"Salvo via API Intelbras!\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
    
    def show_captures(self):
        """Mostra janela de capturas"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura realizada")
            return
        
        window = tk.Toplevel(self.root)
        window.title("Capturas - API Intelbras")
        window.geometry("900x500")
        
        columns = ('ID', 'Produto', 'Data/Hora', 'Arquivo', 'Fonte')
        tree = ttk.Treeview(window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column('ID', width=50)
        tree.column('Produto', width=300)
        tree.column('Data/Hora', width=150)
        tree.column('Arquivo', width=200)
        tree.column('Fonte', width=100)
        
        for capture in self.captured_images:
            tree.insert('', 'end', values=(
                capture['id'],
                capture['produto'][:40] + '...' if len(capture['produto']) > 40 else capture['produto'],
                capture['timestamp'],
                capture['filename'],
                capture['source']
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def export_data(self):
        """Exporta dados"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nada para exportar")
            return
        
        try:
            filename = f"export_intelbras_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write("ID,Produto,Data_Hora,Arquivo,Caminho,Fonte\n")
                for capture in self.captured_images:
                    f.write(f"{capture['id']},\"{capture['produto']}\",{capture['timestamp']},")
                    f.write(f"{capture['filename']},\"{capture['filepath']}\",{capture['source']}\n")
            
            self.status_var.set(f"📤 Exportado: {filename}")
            messagebox.showinfo("Exportado", f"Arquivo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na exportação: {e}")
    
    def clear_data(self):
        """Limpa dados"""
        if not self.captured_images:
            return
        
        if messagebox.askyesno("Confirmar", "Limpar todas as capturas?"):
            self.captured_images.clear()
            self.counter_var.set("Capturas: 0")
            self.status_var.set("🗑️ Dados limpos")
    
    def update_device_info(self):
        """Atualiza informações do dispositivo"""
        self.connect_to_device()
    
    def open_web_interface(self):
        """Abre interface web da câmera"""
        import webbrowser
        webbrowser.open(f"http://{self.camera_ip}")

def main():
    root = tk.Tk()
    app = VerifiKIntelbrasAPI(root)
    root.mainloop()

if __name__ == "__main__":
    main()