#!/usr/bin/env python3
"""
VerifiK - Streaming com Reconhecimento Automático de Produtos
Sistema integrado: Câmera Intelbras + YOLO + OCR para detecção automática
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sqlite3
from datetime import datetime
import os
import io
import threading
import time
import cv2
import numpy as np
from pathlib import Path

# Imports para detecção
try:
    from ultralytics import YOLO
    import pytesseract
    YOLO_DISPONIVEL = True
    
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
except ImportError as e:
    print(f"⚠️ Dependências de IA não encontradas: {e}")
    YOLO_DISPONIVEL = False

class VerifiKStreamingReconhecimento:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Streaming + Reconhecimento Automático")
        self.root.geometry("1400x900")
        
        # Configuração da câmera
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # URLs de captura (funciona com Digest Auth)
        self.snapshot_urls = [
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi",
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi?channel=1&subtype=0",
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi?channel=1&subtype=1"
        ]
        
        # Variáveis de controle
        self.streaming = False
        self.reconhecimento_ativo = False
        self.current_frame = None
        self.deteccoes_atuais = []
        self.produtos_detectados = []
        self.produtos_database = []
        
        # Modelo YOLO e configurações
        self.modelo_yolo = None
        self.confianca_yolo = 0.15
        self.usar_ocr = True
        
        # Estatísticas
        self.total_frames = 0
        self.total_deteccoes = 0
        self.fps_atual = 0
        self.last_fps_time = time.time()
        
        # Interface
        self.setup_interface()
        self.carregar_modelo_yolo()
        self.carregar_produtos_database()
        
        # Iniciar streaming automático
        self.root.after(1000, self.iniciar_streaming)
    
    def setup_interface(self):
        """Interface completa com reconhecimento"""
        
        # Header - Informações
        header = ttk.LabelFrame(self.root, text="📹 VerifiK - Streaming + IA", padding="10")
        header.pack(fill='x', padx=10, pady=5)
        
        # Info grid
        info_frame = ttk.Frame(header)
        info_frame.pack(fill='x')
        
        ttk.Label(info_frame, text=f"📷 Câmera: {self.camera_ip}", font=('Arial', 9)).pack(side='left', padx=(0, 15))
        
        self.status_conexao = ttk.Label(info_frame, text="🔴 Conectando...", font=('Arial', 9, 'bold'))
        self.status_conexao.pack(side='left', padx=(0, 15))
        
        self.status_ia = ttk.Label(info_frame, text="🤖 IA: Carregando...", font=('Arial', 9))
        self.status_ia.pack(side='left', padx=(0, 15))
        
        self.fps_label = ttk.Label(info_frame, text="FPS: 0", font=('Arial', 9))
        self.fps_label.pack(side='right')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Lado esquerdo - Streaming com detecções
        left_panel = ttk.LabelFrame(main_frame, text="🎥 Visualização com Reconhecimento", padding="10")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Container do streaming
        self.streaming_frame = ttk.Frame(left_panel)
        self.streaming_frame.pack(fill='both', expand=True)
        
        # Label para imagem (maior)
        self.image_label = ttk.Label(
            self.streaming_frame,
            text="📹\n\nIniciando Sistema...\nCarregando Modelo IA...",
            justify=tk.CENTER,
            font=('Arial', 14),
            background='black',
            foreground='white'
        )
        self.image_label.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Controles de streaming
        controls_frame = ttk.Frame(left_panel)
        controls_frame.pack(fill='x', pady=(10, 0))
        
        # Primeira linha de controles
        controls_top = ttk.Frame(controls_frame)
        controls_top.pack(fill='x', pady=(0, 5))
        
        self.btn_stream = ttk.Button(controls_top, text="▶️ Iniciar Stream", command=self.toggle_streaming)
        self.btn_stream.pack(side='left', padx=(0, 10))
        
        self.btn_reconhecimento = ttk.Button(controls_top, text="🤖 Ativar IA", command=self.toggle_reconhecimento)
        self.btn_reconhecimento.pack(side='left', padx=(0, 10))
        
        ttk.Button(controls_top, text="📸 Capturar", command=self.capturar_manual).pack(side='left', padx=(0, 10))
        
        # Segunda linha - configurações
        controls_bottom = ttk.Frame(controls_frame)
        controls_bottom.pack(fill='x')
        
        ttk.Label(controls_bottom, text="Confiança:").pack(side='left', padx=(0, 5))
        
        self.confianca_var = tk.DoubleVar(value=0.15)
        confianca_scale = ttk.Scale(
            controls_bottom, 
            from_=0.05, 
            to=0.8, 
            variable=self.confianca_var,
            length=150,
            command=self.update_confianca
        )
        confianca_scale.pack(side='left', padx=(0, 10))
        
        self.confianca_label = ttk.Label(controls_bottom, text="15%")
        self.confianca_label.pack(side='left', padx=(0, 15))
        
        # OCR toggle
        self.ocr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_bottom, text="OCR", variable=self.ocr_var, 
                       command=self.toggle_ocr).pack(side='left')
        
        # Lado direito - Detecções e resultados
        right_panel = ttk.LabelFrame(main_frame, text="🎯 Produtos Detectados", padding="10")
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        
        # Notebook para organizar informações
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True)
        
        # Aba 1: Detecções em tempo real
        deteccoes_frame = ttk.Frame(notebook)
        notebook.add(deteccoes_frame, text="🔍 Tempo Real")
        
        # Lista de detecções atuais
        ttk.Label(deteccoes_frame, text="Produtos no Frame Atual:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Listbox para detecções atuais
        deteccoes_container = ttk.Frame(deteccoes_frame)
        deteccoes_container.pack(fill='both', expand=True, pady=(0, 10))
        
        self.deteccoes_listbox = tk.Listbox(deteccoes_container, height=12, font=('Arial', 9))
        scrollbar_det = ttk.Scrollbar(deteccoes_container, command=self.deteccoes_listbox.yview)
        
        self.deteccoes_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_det.pack(side='right', fill='y')
        self.deteccoes_listbox.config(yscrollcommand=scrollbar_det.set)
        
        # Botão para confirmar produto
        ttk.Button(deteccoes_frame, text="✅ Confirmar Produto", 
                  command=self.confirmar_produto_selecionado).pack(fill='x', pady=5)
        
        # Aba 2: Produtos confirmados
        confirmados_frame = ttk.Frame(notebook)
        notebook.add(confirmados_frame, text="✅ Confirmados")
        
        # Lista de produtos confirmados
        self.confirmados_listbox = tk.Listbox(confirmados_frame, height=15, font=('Arial', 9))
        scrollbar_conf = ttk.Scrollbar(confirmados_frame, command=self.confirmados_listbox.yview)
        
        self.confirmados_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_conf.pack(side='right', fill='y')
        self.confirmados_listbox.config(yscrollcommand=scrollbar_conf.set)
        
        # Aba 3: Base de produtos
        database_frame = ttk.Frame(notebook)
        notebook.add(database_frame, text="📦 Database")
        
        # Lista da base de dados
        self.database_listbox = tk.Listbox(database_frame, height=15, font=('Arial', 9))
        scrollbar_db = ttk.Scrollbar(database_frame, command=self.database_listbox.yview)
        
        self.database_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_db.pack(side='right', fill='y')
        self.database_listbox.config(yscrollcommand=scrollbar_db.set)
        
        # Footer - Estatísticas e status
        footer = ttk.LabelFrame(self.root, text="📊 Status e Estatísticas", padding="10")
        footer.pack(fill='x', padx=10, pady=(5, 10))
        
        # Grid de informações
        stats_frame = ttk.Frame(footer)
        stats_frame.pack(fill='x')
        
        # Status principal
        self.status_principal = ttk.Label(stats_frame, text="Iniciando sistema...", font=('Arial', 10))
        self.status_principal.pack(side='left')
        
        # Estatísticas
        stats_right = ttk.Frame(stats_frame)
        stats_right.pack(side='right')
        
        self.stats_frames = ttk.Label(stats_right, text="Frames: 0", font=('Arial', 9))
        self.stats_frames.pack(side='left', padx=(0, 15))
        
        self.stats_deteccoes = ttk.Label(stats_right, text="Detecções: 0", font=('Arial', 9))
        self.stats_deteccoes.pack(side='left', padx=(0, 15))
        
        self.stats_confirmados = ttk.Label(stats_right, text="Confirmados: 0", font=('Arial', 9))
        self.stats_confirmados.pack(side='left')
    
    def carregar_modelo_yolo(self):
        """Carrega modelo YOLO treinado"""
        if not YOLO_DISPONIVEL:
            self.status_ia.config(text="❌ IA: Não disponível")
            return
        
        # Procurar modelo treinado
        modelo_paths = [
            "verifik/verifik_yolov8.pt",
            "verifik/runs/treino_continuado/weights/best.pt",
            "runs/detect/train/weights/best.pt"
        ]
        
        modelo_encontrado = None
        for path in modelo_paths:
            if os.path.exists(path):
                modelo_encontrado = path
                break
        
        if modelo_encontrado:
            try:
                self.modelo_yolo = YOLO(modelo_encontrado)
                self.status_ia.config(text="✅ IA: Modelo Carregado")
                print(f"✅ Modelo YOLO carregado: {modelo_encontrado}")
                return True
            except Exception as e:
                print(f"❌ Erro ao carregar modelo: {e}")
        
        self.status_ia.config(text="⚠️ IA: Modelo não encontrado")
        return False
    
    def carregar_produtos_database(self):
        """Carrega produtos da base de dados"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT descricao_produto FROM produtos WHERE ativo = 1 ORDER BY descricao_produto")
            self.produtos_database = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Preencher lista
            for produto in self.produtos_database:
                self.database_listbox.insert(tk.END, produto)
            
            print(f"✅ {len(self.produtos_database)} produtos carregados da base")
            
        except Exception as e:
            print(f"❌ Erro ao carregar produtos: {e}")
    
    def iniciar_streaming(self):
        """Inicia streaming da câmera"""
        if self.streaming:
            return
        
        self.streaming = True
        self.status_conexao.config(text="🟡 Conectando...")
        self.btn_stream.config(text="⏸️ Pausar Stream")
        
        def streaming_thread():
            while self.streaming:
                try:
                    # Tentar capturar frame
                    frame_data = self.capturar_frame_camera()
                    
                    if frame_data:
                        # Processar frame
                        frame_processado = self.processar_frame(frame_data)
                        
                        # Atualizar UI na thread principal
                        self.root.after(0, self.atualizar_display, frame_processado, frame_data)
                        
                        # Controle de FPS
                        self.total_frames += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            self.fps_atual = self.total_frames / (current_time - self.last_fps_time)
                            self.root.after(0, lambda: self.fps_label.config(text=f"FPS: {self.fps_atual:.1f}"))
                            self.total_frames = 0
                            self.last_fps_time = current_time
                        
                        self.root.after(0, lambda: self.status_conexao.config(text="🟢 Stream Ativo"))
                    
                    else:
                        self.root.after(0, lambda: self.status_conexao.config(text="🔴 Erro Conexão"))
                        time.sleep(2)
                    
                    time.sleep(0.5)  # ~2 FPS
                    
                except Exception as e:
                    print(f"Erro no streaming: {e}")
                    time.sleep(3)
        
        # Iniciar thread
        thread = threading.Thread(target=streaming_thread, daemon=True)
        thread.start()
    
    def capturar_frame_camera(self):
        """Captura um frame da câmera Intelbras"""
        for url in self.snapshot_urls:
            try:
                response = requests.get(url, auth=self.auth, timeout=8)
                
                if response.status_code == 200 and len(response.content) > 5000:
                    return response.content
                    
            except Exception:
                continue
        
        return None
    
    def processar_frame(self, frame_data):
        """Processa frame para reconhecimento se ativo"""
        if not self.reconhecimento_ativo or not self.modelo_yolo:
            return frame_data
        
        try:
            # Converter para OpenCV
            nparr = np.frombuffer(frame_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Fazer predição YOLO
            results = self.modelo_yolo.predict(
                img_cv,
                conf=self.confianca_yolo,
                verbose=False
            )
            
            # Processar detecções
            deteccoes_frame = []
            
            if results and len(results) > 0:
                for r in results:
                    if r.boxes is not None:
                        for box in r.boxes:
                            # Extrair informações
                            xyxy = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            
                            if cls_id < len(self.modelo_yolo.names):
                                classe = self.modelo_yolo.names[cls_id]
                                
                                # OCR opcional
                                texto_ocr = ""
                                if self.usar_ocr:
                                    texto_ocr = self.extrair_texto_regiao(img_cv, xyxy)
                                
                                deteccoes_frame.append({
                                    'bbox': xyxy,
                                    'confianca': conf,
                                    'classe': classe,
                                    'texto_ocr': texto_ocr,
                                    'timestamp': datetime.now()
                                })
            
            # Atualizar detecções atuais
            self.deteccoes_atuais = deteccoes_frame
            self.total_deteccoes += len(deteccoes_frame)
            
            # Desenhar detecções no frame
            img_com_deteccoes = self.desenhar_deteccoes(img_cv, deteccoes_frame)
            
            # Converter de volta para bytes
            _, buffer = cv2.imencode('.jpg', img_com_deteccoes)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return frame_data
    
    def extrair_texto_regiao(self, img_cv, bbox):
        """Extrai texto de uma região usando OCR"""
        if not self.usar_ocr:
            return ""
        
        try:
            x1, y1, x2, y2 = bbox
            regiao = img_cv[y1:y2, x1:x2]
            
            # Processar para OCR
            cinza = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
            
            # Melhorar qualidade
            altura, largura = cinza.shape
            if altura < 200:
                escala = 200 / altura
                nova_largura = int(largura * escala)
                cinza = cv2.resize(cinza, (nova_largura, 200))
            
            # Threshold
            _, thresh = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR
            texto = pytesseract.image_to_string(thresh, lang='por+eng', config='--psm 6 --oem 3')
            return texto.strip().upper()
            
        except Exception as e:
            return ""
    
    def desenhar_deteccoes(self, img_cv, deteccoes):
        """Desenha detecções no frame"""
        img_resultado = img_cv.copy()
        
        for i, det in enumerate(deteccoes):
            x1, y1, x2, y2 = det['bbox']
            conf = det['confianca']
            classe = det['classe']
            texto_ocr = det['texto_ocr']
            
            # Cor baseada na confiança
            if conf > 0.5:
                cor = (0, 255, 0)  # Verde - alta confiança
            elif conf > 0.25:
                cor = (0, 255, 255)  # Amarelo - média confiança
            else:
                cor = (0, 0, 255)  # Vermelho - baixa confiança
            
            # Desenhar retângulo
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 2)
            
            # Texto da detecção
            label = f"{classe} {conf*100:.0f}%"
            if texto_ocr and len(texto_ocr) > 3:
                label += f" | {texto_ocr[:15]}..."
            
            # Background do texto
            (w_text, h_text), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(img_resultado, (x1, y1-h_text-10), (x1+w_text, y1), cor, -1)
            
            # Texto
            cv2.putText(img_resultado, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return img_resultado
    
    def atualizar_display(self, frame_processado, frame_original):
        """Atualiza display com frame processado"""
        try:
            # Converter para PIL
            image = Image.open(io.BytesIO(frame_processado))
            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Atualizar display
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
            
            # Armazenar frame atual
            self.current_frame = frame_original
            
            # Atualizar lista de detecções
            self.atualizar_lista_deteccoes()
            
            # Atualizar estatísticas
            self.atualizar_estatisticas()
            
        except Exception as e:
            print(f"Erro ao atualizar display: {e}")
    
    def atualizar_lista_deteccoes(self):
        """Atualiza lista de detecções em tempo real"""
        self.deteccoes_listbox.delete(0, tk.END)
        
        for i, det in enumerate(self.deteccoes_atuais, 1):
            conf = det['confianca']
            classe = det['classe']
            texto_ocr = det['texto_ocr']
            
            # Formato da linha
            linha = f"{i}. {classe} ({conf*100:.0f}%)"
            if texto_ocr and len(texto_ocr) > 3:
                linha += f" - OCR: {texto_ocr[:20]}..."
            
            self.deteccoes_listbox.insert(tk.END, linha)
    
    def atualizar_estatisticas(self):
        """Atualiza estatísticas na interface"""
        self.stats_deteccoes.config(text=f"Detecções: {self.total_deteccoes}")
        self.stats_confirmados.config(text=f"Confirmados: {len(self.produtos_detectados)}")
        
        if self.reconhecimento_ativo:
            self.status_principal.config(text=f"🤖 Reconhecimento ativo - {len(self.deteccoes_atuais)} produto(s) no frame")
        else:
            self.status_principal.config(text="📹 Streaming ativo - Reconhecimento pausado")
    
    def toggle_streaming(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.streaming = False
            self.btn_stream.config(text="▶️ Iniciar Stream")
            self.status_conexao.config(text="⏸️ Pausado")
        else:
            self.iniciar_streaming()
    
    def toggle_reconhecimento(self):
        """Liga/desliga reconhecimento"""
        if not self.modelo_yolo:
            messagebox.showwarning("Aviso", "Modelo YOLO não disponível!")
            return
        
        self.reconhecimento_ativo = not self.reconhecimento_ativo
        
        if self.reconhecimento_ativo:
            self.btn_reconhecimento.config(text="⏸️ Pausar IA")
            self.status_ia.config(text="🤖 IA: ATIVA")
        else:
            self.btn_reconhecimento.config(text="🤖 Ativar IA")
            self.status_ia.config(text="⏸️ IA: Pausada")
            self.deteccoes_atuais = []
            self.atualizar_lista_deteccoes()
    
    def update_confianca(self, value):
        """Atualiza threshold de confiança"""
        self.confianca_yolo = float(value)
        self.confianca_label.config(text=f"{self.confianca_yolo*100:.0f}%")
    
    def toggle_ocr(self):
        """Liga/desliga OCR"""
        self.usar_ocr = self.ocr_var.get()
    
    def confirmar_produto_selecionado(self):
        """Confirma produto selecionado na lista"""
        selection = self.deteccoes_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma detecção para confirmar!")
            return
        
        idx = selection[0]
        if idx < len(self.deteccoes_atuais):
            det = self.deteccoes_atuais[idx]
            
            # Adicionar à lista de confirmados
            produto_confirmado = {
                'id': len(self.produtos_detectados) + 1,
                'classe': det['classe'],
                'confianca': det['confianca'],
                'texto_ocr': det['texto_ocr'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'frame_salvo': self.salvar_frame_produto(det)
            }
            
            self.produtos_detectados.append(produto_confirmado)
            
            # Atualizar lista de confirmados
            self.confirmados_listbox.insert(tk.END, 
                f"{produto_confirmado['id']}. {produto_confirmado['classe']} ({produto_confirmado['confianca']*100:.0f}%) - {produto_confirmado['timestamp']}")
            
            messagebox.showinfo("Sucesso", f"Produto confirmado: {det['classe']}")
    
    def salvar_frame_produto(self, deteccao):
        """Salva frame com produto detectado"""
        if not self.current_frame:
            return None
        
        try:
            os.makedirs("produtos_detectados_ia", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"produto_ia_{timestamp}_{deteccao['classe']}.jpg"
            filepath = os.path.join("produtos_detectados_ia", filename)
            
            with open(filepath, 'wb') as f:
                f.write(self.current_frame)
            
            return filepath
            
        except Exception as e:
            print(f"Erro ao salvar frame: {e}")
            return None
    
    def capturar_manual(self):
        """Captura manual sem reconhecimento"""
        if not self.current_frame:
            messagebox.showwarning("Aviso", "Nenhum frame disponível!")
            return
        
        try:
            os.makedirs("capturas_manuais", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_{timestamp}.jpg"
            filepath = os.path.join("capturas_manuais", filename)
            
            with open(filepath, 'wb') as f:
                f.write(self.current_frame)
            
            messagebox.showinfo("Captura", f"Foto salva: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")

def main():
    root = tk.Tk()
    
    # Verificar dependências
    if not YOLO_DISPONIVEL:
        messagebox.showwarning(
            "Dependências",
            "Algumas funcionalidades de IA não estarão disponíveis.\n\n" +
            "Instale: pip install ultralytics pytesseract"
        )
    
    app = VerifiKStreamingReconhecimento(root)
    
    # Fechar corretamente
    def on_close():
        app.streaming = False
        app.reconhecimento_ativo = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()