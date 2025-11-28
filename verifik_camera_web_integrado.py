#!/usr/bin/env python3
"""
Sistema VerifiK + Câmera Intelbras - Versão Web Integrada
Interface web que conecta com a câmera IP para captura automática
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from requests.auth import HTTPBasicAuth
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os
import io
import threading
import webbrowser
import time

class VerifiKCameraWeb:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK + Câmera Intelbras - Sistema Web")
        self.root.geometry("900x700")
        
        # Configurações da câmera
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.camera_url = f"http://{self.camera_ip}"
        
        # Variáveis de controle
        self.captured_images = []
        self.current_image = None
        self.produtos = []
        self.continuous_capture = False
        self.session = requests.Session()
        self.authenticated = False
        
        # Carregar produtos
        self.load_products()
        
        # Interface
        self.setup_interface()
        
        # Testar câmera
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
            # Produtos de fallback
            self.produtos = [
                "CERVEJA HEINEKEN 473ML", "CERVEJA SKOL 473ML", "CERVEJA ANTARCTICA 473ML",
                "REFRIGERANTE COCA COLA 2L", "AGUA MINERAL 500ML", "BISCOITO CREAM CRACKER"
            ]
    
    def setup_interface(self):
        """Configura interface do sistema"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="VerifiK + Câmera Intelbras", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de informações da câmera
        camera_info_frame = ttk.LabelFrame(main_frame, text="Informações da Câmera", padding="10")
        camera_info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Info da câmera
        ttk.Label(camera_info_frame, text=f"📷 IP: {self.camera_ip}").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Label(camera_info_frame, text=f"👤 Usuário: {self.camera_user}").grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Status da câmera
        self.camera_status = ttk.Label(camera_info_frame, text="🔴 Verificando...")
        self.camera_status.grid(row=0, column=2, sticky=tk.W)
        
        # Botões de acesso
        access_frame = ttk.Frame(camera_info_frame)
        access_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(access_frame, text="📸 Capturar Automática", 
                  command=self.auto_capture_camera, style='Accent.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(access_frame, text="🎥 Stream Contínuo", 
                  command=self.start_continuous_capture).grid(row=0, column=1, padx=5)
        ttk.Button(access_frame, text="⏹️ Parar Stream", 
                  command=self.stop_continuous_capture).grid(row=0, column=2, padx=5)
        ttk.Button(access_frame, text="🔄 Testar Conexão", 
                  command=self.test_camera_connection).grid(row=0, column=3, padx=5)
        
        # Frame de captura manual
        manual_frame = ttk.LabelFrame(main_frame, text="Captura Manual", padding="10")
        manual_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Preview da imagem
        self.image_preview = ttk.Label(manual_frame, text="📷\nNenhuma imagem\ncapturada", 
                                     justify=tk.CENTER, font=('Arial', 12))
        self.image_preview.grid(row=0, column=0, pady=(0, 10))
        
        # Botões de captura
        ttk.Button(manual_frame, text="📁 Selecionar Arquivo", 
                  command=self.select_image_file).grid(row=1, column=0, pady=5)
        
        # Frame de produtos
        product_frame = ttk.LabelFrame(main_frame, text="Seleção de Produto", padding="10")
        product_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Busca de produto
        ttk.Label(product_frame, text="🔍 Buscar produto:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_products)
        search_entry = ttk.Entry(product_frame, textvariable=self.search_var, width=35)
        search_entry.grid(row=1, column=0, pady=(5, 10), sticky=(tk.W, tk.E))
        
        # Lista de produtos
        list_frame = ttk.Frame(product_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.product_listbox = tk.Listbox(list_frame, height=10, font=('Arial', 10))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        
        self.product_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.product_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.product_listbox.yview)
        
        # Configurar grid
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        product_frame.columnconfigure(0, weight=1)
        product_frame.rowconfigure(2, weight=1)
        
        # Preencher lista
        self.update_product_list(self.produtos)
        
        # Frame de controles
        control_frame = ttk.LabelFrame(main_frame, text="Controles Principais", padding="15")
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Botões principais em grid
        ttk.Button(control_frame, text="💾 Salvar Imagem + Produto", 
                  command=self.save_image_with_product).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="📋 Ver Capturas", 
                  command=self.show_captures).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="📤 Exportar CSV", 
                  command=self.export_csv).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="🗑️ Limpar Tudo", 
                  command=self.clear_all).grid(row=0, column=3, padx=5, pady=5)
        
        # Status e contador
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Sistema iniciado - Carregue uma imagem e selecione um produto")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10))
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.counter_var = tk.StringVar(value="Capturas: 0")
        counter_label = ttk.Label(status_frame, textvariable=self.counter_var, 
                                font=('Arial', 10, 'bold'), foreground='blue')
        counter_label.grid(row=0, column=1, sticky=tk.E)
        
        status_frame.columnconfigure(0, weight=1)
        
        # Configurar grid principal
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
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
        """Testa conexão com a câmera"""
        def test_in_thread():
            try:
                self.camera_status.config(text="🟡 Testando conexão...")
                self.root.update()
                
                response = requests.get(
                    self.camera_url,
                    auth=HTTPBasicAuth(self.camera_user, self.camera_pass),
                    timeout=8
                )
                
                if response.status_code == 200:
                    self.camera_status.config(text="🟢 Câmera conectada")
                    self.status_var.set("✅ Câmera acessível - Use 'Capturar da Câmera' ou 'Abrir Interface Web'")
                else:
                    self.camera_status.config(text="🟡 Câmera com problemas")
                    self.status_var.set(f"⚠️ Câmera respondeu com status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.camera_status.config(text="🔴 Timeout de conexão")
                self.status_var.set("❌ Timeout: Verifique se a câmera está ligada")
            except requests.exceptions.ConnectionError:
                self.camera_status.config(text="🔴 Câmera inacessível")
                self.status_var.set("❌ Erro de conexão: Verifique IP e rede")
            except Exception as e:
                self.camera_status.config(text="🔴 Erro de conexão")
                self.status_var.set(f"❌ Erro: {str(e)[:50]}...")
        
        # Executar em thread para não travar a interface
        thread = threading.Thread(target=test_in_thread)
        thread.daemon = True
        thread.start()
    
    def authenticate_camera(self):
        """Autentica automaticamente na câmera"""
        try:
            # Configurar sessão com autenticação
            self.session.auth = HTTPBasicAuth(self.camera_user, self.camera_pass)
            
            # Testar login
            response = self.session.get(f"{self.camera_url}/", timeout=10)
            
            if response.status_code == 200:
                self.authenticated = True
                return True
            else:
                self.authenticated = False
                return False
                
        except Exception as e:
            self.authenticated = False
            return False
    
    def auto_capture_camera(self):
        """Captura automática com login direto"""
        def capture_in_thread():
            try:
                self.status_var.set("🔐 Fazendo login automático na câmera...")
                self.root.update()
                
                # Autenticar primeiro
                if not self.authenticate_camera():
                    self.status_var.set("❌ Falha na autenticação automática")
                    return
                
                self.status_var.set("📸 Capturando imagem automaticamente...")
                self.root.update()
                
                # URLs para snapshot com sessão autenticada
                snapshot_urls = [
                    f"{self.camera_url}/cgi-bin/snapshot.cgi",
                    f"{self.camera_url}/cgi-bin/hi3510/snap.cgi", 
                    f"{self.camera_url}/web/cgi-bin/hi3510/snap.cgi",
                    f"{self.camera_url}/Streaming/Channels/1/picture",
                    f"{self.camera_url}/onvif-http/snapshot?Profile_1",
                    f"{self.camera_url}/cgi-bin/main-cgi?action=snapshot",
                    f"{self.camera_url}/picture/1/1"
                ]
                
                image_captured = False
                
                for url in snapshot_urls:
                    try:
                        # Usar sessão autenticada
                        response = self.session.get(url, timeout=15, stream=True)
                        
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if (response.status_code == 200 and 
                            ('image' in content_type or 'jpeg' in content_type or 'jpg' in content_type)):
                            
                            # Imagem capturada com sucesso
                            image_data = response.content
                            
                            if len(image_data) > 1000:  # Verificar se não é muito pequena
                                # Preview da imagem
                                image = Image.open(io.BytesIO(image_data))
                                
                                # Redimensionar para preview
                                image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                                photo = ImageTk.PhotoImage(image)
                                
                                # Atualizar preview
                                self.image_preview.config(image=photo, text="")
                                self.image_preview.image = photo
                                
                                # Armazenar imagem
                                self.current_image = image_data
                                
                                size_kb = len(image_data) / 1024
                                self.status_var.set(f"✅ Imagem capturada automaticamente! ({size_kb:.1f}KB) - Selecione produto")
                                image_captured = True
                                break
                            
                    except Exception as e:
                        print(f"Erro em {url}: {e}")
                        continue
                
                if not image_captured:
                    self.status_var.set("❌ Falha na captura automática - Verificando URLs alternativas...")
                    # Tentar URLs adicionais específicas da Intelbras
                    self.try_alternative_capture_methods()
                    
            except Exception as e:
                self.status_var.set(f"❌ Erro na captura automática: {str(e)[:50]}...")
        
        thread = threading.Thread(target=capture_in_thread)
        thread.daemon = True
        thread.start()
    
    def try_alternative_capture_methods(self):
        """Tenta métodos alternativos de captura"""
        try:
            # Método 1: Via CGI com parâmetros específicos
            alt_urls = [
                f"{self.camera_url}/cgi-bin/snapshot.cgi?channel=1",
                f"{self.camera_url}/cgi-bin/snapshot.cgi?chn=1&u={self.camera_user}&p={self.camera_pass}",
                f"{self.camera_url}/tmpfs/auto.jpg",
                f"{self.camera_url}/jpg/image.jpg",
                f"{self.camera_url}/cgi-bin/main-cgi?user={self.camera_user}&pwd={self.camera_pass}&action=snapshot"
            ]
            
            for url in alt_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if (response.status_code == 200 and 
                        len(response.content) > 1000 and
                        response.content[:4] == b'\xff\xd8\xff\xe0'):  # Header JPEG
                        
                        # Sucesso!
                        image = Image.open(io.BytesIO(response.content))
                        image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        self.image_preview.config(image=photo, text="")
                        self.image_preview.image = photo
                        self.current_image = response.content
                        
                        self.status_var.set("✅ Captura bem-sucedida via método alternativo!")
                        return True
                        
                except Exception as e:
                    continue
            
            self.status_var.set("❌ Todos os métodos de captura falharam - Use upload manual")
            return False
            
        except Exception as e:
            self.status_var.set(f"❌ Erro nos métodos alternativos: {str(e)[:40]}...")
            return False
    
    def select_image_file(self):
        """Seleciona arquivo de imagem"""
        file_path = filedialog.askopenfilename(
            title="Selecionar imagem capturada",
            filetypes=[
                ("Todas as imagens", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Todas", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Ler arquivo
                with open(file_path, 'rb') as f:
                    self.current_image = f.read()
                
                # Preview
                image = Image.open(file_path)
                image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.image_preview.config(image=photo, text="")
                self.image_preview.image = photo
                
                filename = os.path.basename(file_path)
                self.status_var.set(f"✅ Imagem carregada: {filename}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar imagem: {e}")
    
    def save_image_with_product(self):
        """Salva imagem associada ao produto selecionado"""
        if not self.current_image:
            messagebox.showwarning("Aviso", "Capture ou selecione uma imagem primeiro!")
            return
        
        selected_indices = self.product_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Selecione um produto da lista!")
            return
        
        selected_product = self.product_listbox.get(selected_indices[0])
        
        try:
            # Criar diretório se necessário
            os.makedirs("capturas_verifik", exist_ok=True)
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            capture_id = len(self.captured_images) + 1
            filename = f"verifik_{timestamp}_{capture_id:03d}.jpg"
            filepath = os.path.join("capturas_verifik", filename)
            
            # Salvar arquivo
            with open(filepath, 'wb') as f:
                f.write(self.current_image)
            
            # Registrar captura
            capture_data = {
                'id': capture_id,
                'produto': selected_product,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': filename,
                'filepath': filepath,
                'source': 'Câmera Automática' if self.authenticated else 'Upload Manual'
            }
            
            self.captured_images.append(capture_data)
            
            # Atualizar contadores
            self.counter_var.set(f"Capturas: {len(self.captured_images)}")
            self.status_var.set(f"✅ Salvo: {selected_product} → {filename}")
            
            # Limpar imagem atual
            self.current_image = None
            self.image_preview.config(image="", text="📷\nNenhuma imagem\ncapturada")
            
            messagebox.showinfo("Sucesso!", 
                f"Imagem salva com sucesso!\n\n"
                f"Produto: {selected_product}\n"
                f"Arquivo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
    
    def show_captures(self):
        """Mostra janela com capturas realizadas"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura realizada ainda")
            return
        
        # Janela de capturas
        captures_window = tk.Toplevel(self.root)
        captures_window.title("Capturas Realizadas - VerifiK")
        captures_window.geometry("1000x600")
        
        # Treeview
        columns = ('ID', 'Produto', 'Data/Hora', 'Arquivo', 'Origem')
        tree = ttk.Treeview(captures_window, columns=columns, show='headings', height=15)
        
        # Configurar colunas
        tree.heading('ID', text='ID')
        tree.heading('Produto', text='Produto')
        tree.heading('Data/Hora', text='Data/Hora')
        tree.heading('Arquivo', text='Arquivo')
        tree.heading('Origem', text='Origem')
        
        tree.column('ID', width=50)
        tree.column('Produto', width=300)
        tree.column('Data/Hora', width=150)
        tree.column('Arquivo', width=200)
        tree.column('Origem', width=100)
        
        # Adicionar dados
        for capture in self.captured_images:
            product_display = capture['produto'][:40] + '...' if len(capture['produto']) > 40 else capture['produto']
            tree.insert('', 'end', values=(
                capture['id'],
                product_display,
                capture['timestamp'],
                capture['filename'],
                capture.get('source', 'N/A')
            ))
        
        # Scrollbar
        scrollbar_tree = ttk.Scrollbar(captures_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_tree.set)
        
        # Layout
        tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar_tree.pack(side='right', fill='y', pady=10)
        
        # Info
        info_label = ttk.Label(captures_window, 
            text=f"Total de capturas: {len(self.captured_images)} | Pasta: capturas_verifik/",
            font=('Arial', 10))
        info_label.pack(pady=(0, 10))
    
    def export_csv(self):
        """Exporta dados para CSV"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura para exportar")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"verifik_export_{timestamp}.csv"
            
            with open(csv_filename, 'w', encoding='utf-8-sig') as f:
                f.write("ID,Produto,Data_Hora,Arquivo,Caminho_Completo,Origem\n")
                
                for capture in self.captured_images:
                    f.write(f"{capture['id']},\"{capture['produto']}\",{capture['timestamp']},")
                    f.write(f"{capture['filename']},\"{capture['filepath']}\",")
                    f.write(f"{capture.get('source', 'N/A')}\n")
            
            self.status_var.set(f"📤 Dados exportados para {csv_filename}")
            messagebox.showinfo("Exportação Concluída", 
                f"Dados exportados com sucesso!\n\n"
                f"Arquivo: {csv_filename}\n"
                f"Registros: {len(self.captured_images)}")
            
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Erro ao exportar: {e}")
    
    def start_continuous_capture(self):
        """Inicia captura contínua da câmera"""
        if self.continuous_capture:
            messagebox.showinfo("Info", "Captura contínua já está ativa")
            return
        
        self.continuous_capture = True
        self.status_var.set("🎥 Iniciando captura contínua...")
        
        def continuous_loop():
            while self.continuous_capture:
                try:
                    # Autenticar se necessário
                    if not self.authenticated:
                        if not self.authenticate_camera():
                            self.status_var.set("❌ Falha na autenticação para captura contínua")
                            break
                    
                    # Capturar imagem
                    response = self.session.get(f"{self.camera_url}/cgi-bin/snapshot.cgi", timeout=8)
                    
                    if (response.status_code == 200 and 
                        'image' in response.headers.get('content-type', '') and
                        len(response.content) > 1000):
                        
                        # Atualizar preview
                        image = Image.open(io.BytesIO(response.content))
                        image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        self.image_preview.config(image=photo, text="")
                        self.image_preview.image = photo
                        self.current_image = response.content
                        
                        self.status_var.set("🎥 Stream ativo - Selecione produto e salve quando desejar")
                    
                    # Aguardar antes da próxima captura (2 segundos)
                    for i in range(20):  # 20 x 0.1s = 2s
                        if not self.continuous_capture:
                            break
                        time.sleep(0.1)
                    
                except Exception as e:
                    self.status_var.set(f"⚠️ Erro no stream: {str(e)[:40]}...")
                    time.sleep(5)  # Aguardar mais em caso de erro
        
        # Iniciar thread de captura contínua
        thread = threading.Thread(target=continuous_loop)
        thread.daemon = True
        thread.start()
    
    def stop_continuous_capture(self):
        """Para captura contínua"""
        self.continuous_capture = False
        self.status_var.set("⏹️ Captura contínua interrompida")
    
    def clear_all(self):
        """Limpa todas as capturas"""
        if not self.captured_images:
            messagebox.showinfo("Info", "Nenhuma captura para limpar")
            return
        
        result = messagebox.askyesno("Confirmar Limpeza",
            f"Tem certeza que deseja limpar {len(self.captured_images)} capturas?\n\n"
            "Esta ação não pode ser desfeita!")
        
        if result:
            self.captured_images.clear()
            self.counter_var.set("Capturas: 0")
            self.status_var.set("🗑️ Todas as capturas foram removidas")
            messagebox.showinfo("Limpeza Concluída", "Todas as capturas foram removidas da memória")

def main():
    root = tk.Tk()
    app = VerifiKCameraWeb(root)
    root.mainloop()

if __name__ == "__main__":
    main()