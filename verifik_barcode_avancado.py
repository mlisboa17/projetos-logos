#!/usr/bin/env python3
"""
VerifiK - Sistema Avançado com Código de Barras e Controles da Câmera
Recursos: YOLO + OCR + Barcode + Zoom + Focus + Exposição + Brilho + Íris
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
import re

# Imports para detecção
try:
    from ultralytics import YOLO
    import pytesseract
    from pyzbar import pyzbar
    import pyzbar.pyzbar as pyzbar_decode
    YOLO_DISPONIVEL = True
    BARCODE_DISPONIVEL = True
    
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
except ImportError as e:
    print(f"⚠️ Dependências não encontradas: {e}")
    YOLO_DISPONIVEL = False
    BARCODE_DISPONIVEL = False

class VerifiKBarcodeAvancado:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Sistema Avançado: YOLO + Barcode + Controles Câmera")
        self.root.geometry("1600x1000")
        
        # Configuração da câmera
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # URLs da câmera
        self.snapshot_url = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
        self.config_url = f"http://{self.camera_ip}/cgi-bin/configManager.cgi"
        
        # Estado do sistema
        self.streaming = False
        self.reconhecimento_ativo = False
        self.usar_yolo = True
        self.usar_ocr = True
        self.usar_barcode = True
        
        # Controles da câmera
        self.brilho_atual = 50
        self.contraste_atual = 50
        self.exposicao_atual = 50
        self.iris_atual = 50
        self.foco_atual = 50
        self.zoom_atual = 1.0
        
        # Modelo YOLO e dados
        self.modelo_yolo = None
        self.confianca_yolo = 0.15
        self.produtos_database = []
        
        # Estatísticas
        self.total_frames = 0
        self.total_deteccoes = 0
        self.total_barcodes = 0
        self.deteccoes_atuais = []
        self.barcodes_atuais = []
        self.fps_atual = 0
        self.last_fps_time = time.time()
        
        # Configurar interface
        self.configurar_interface()
        
        # Inicializar sistema
        self.carregar_modelo_yolo()
        self.carregar_produtos_database()
        self.obter_configuracoes_camera()
        
    def configurar_interface(self):
        """Configura interface gráfica completa"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🔍 VerifiK Avançado: YOLO + Barcode + Controles", 
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        # === PAINEL ESQUERDO: VÍDEO ===
        video_frame = ttk.LabelFrame(main_frame, text="📹 Streaming + Reconhecimento", padding="10")
        video_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Display de vídeo
        self.video_label = ttk.Label(video_frame, text="📷 Aguardando câmera...", 
                                    font=('Arial', 12), anchor='center',
                                    background='black', foreground='white')
        self.video_label.pack(pady=10)
        
        # Controles de streaming
        stream_controls = ttk.Frame(video_frame)
        stream_controls.pack(fill='x', pady=5)
        
        self.btn_stream = ttk.Button(stream_controls, text="▶️ Iniciar Stream", 
                                    command=self.toggle_streaming)
        self.btn_stream.pack(side='left', padx=(0, 5))
        
        self.btn_reconhecimento = ttk.Button(stream_controls, text="🧠 Ativar IA", 
                                           command=self.toggle_reconhecimento)
        self.btn_reconhecimento.pack(side='left', padx=5)
        
        self.btn_snapshot = ttk.Button(stream_controls, text="📸 Foto", 
                                     command=self.tirar_foto_manual)
        self.btn_snapshot.pack(side='left', padx=5)
        
        # Status
        status_frame = ttk.Frame(video_frame)
        status_frame.pack(fill='x', pady=5)
        
        self.status_conexao = ttk.Label(status_frame, text="⚪ Desconectado", font=('Arial', 9))
        self.status_conexao.pack(side='left')
        
        self.status_ia = ttk.Label(status_frame, text="⚪ IA: Inativa", font=('Arial', 9))
        self.status_ia.pack(side='left', padx=(20, 0))
        
        self.fps_label = ttk.Label(status_frame, text="FPS: 0.0", font=('Arial', 9))
        self.fps_label.pack(side='right')
        
        # === PAINEL CENTRO: CONTROLES DA CÂMERA ===
        controls_frame = ttk.LabelFrame(main_frame, text="🎛️ Controles da Câmera", padding="10")
        controls_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Controles de imagem
        img_controls = ttk.LabelFrame(controls_frame, text="🖼️ Qualidade de Imagem", padding="5")
        img_controls.pack(fill='x', pady=(0, 10))
        
        # Brilho
        ttk.Label(img_controls, text="☀️ Brilho:").grid(row=0, column=0, sticky='w', pady=2)
        self.brilho_scale = ttk.Scale(img_controls, from_=0, to=100, orient='horizontal',
                                     command=self.ajustar_brilho)
        self.brilho_scale.set(50)
        self.brilho_scale.grid(row=0, column=1, sticky='ew', padx=5)
        self.brilho_valor = ttk.Label(img_controls, text="50")
        self.brilho_valor.grid(row=0, column=2)
        
        # Contraste
        ttk.Label(img_controls, text="🔲 Contraste:").grid(row=1, column=0, sticky='w', pady=2)
        self.contraste_scale = ttk.Scale(img_controls, from_=0, to=100, orient='horizontal',
                                        command=self.ajustar_contraste)
        self.contraste_scale.set(50)
        self.contraste_scale.grid(row=1, column=1, sticky='ew', padx=5)
        self.contraste_valor = ttk.Label(img_controls, text="50")
        self.contraste_valor.grid(row=1, column=2)
        
        # Exposição
        ttk.Label(img_controls, text="📷 Exposição:").grid(row=2, column=0, sticky='w', pady=2)
        self.exposicao_scale = ttk.Scale(img_controls, from_=0, to=100, orient='horizontal',
                                        command=self.ajustar_exposicao)
        self.exposicao_scale.set(50)
        self.exposicao_scale.grid(row=2, column=1, sticky='ew', padx=5)
        self.exposicao_valor = ttk.Label(img_controls, text="50")
        self.exposicao_valor.grid(row=2, column=2)
        
        # Íris
        ttk.Label(img_controls, text="🔘 Íris:").grid(row=3, column=0, sticky='w', pady=2)
        self.iris_scale = ttk.Scale(img_controls, from_=0, to=100, orient='horizontal',
                                   command=self.ajustar_iris)
        self.iris_scale.set(50)
        self.iris_scale.grid(row=3, column=1, sticky='ew', padx=5)
        self.iris_valor = ttk.Label(img_controls, text="50")
        self.iris_valor.grid(row=3, column=2)
        
        img_controls.columnconfigure(1, weight=1)
        
        # Controles de foco e zoom
        focus_controls = ttk.LabelFrame(controls_frame, text="🔍 Foco e Zoom", padding="5")
        focus_controls.pack(fill='x', pady=(0, 10))
        
        # Foco
        focus_frame = ttk.Frame(focus_controls)
        focus_frame.pack(fill='x', pady=2)
        
        ttk.Label(focus_frame, text="🎯 Foco:").pack(side='left')
        self.btn_foco_auto = ttk.Button(focus_frame, text="AUTO", width=6,
                                       command=self.foco_automatico)
        self.btn_foco_auto.pack(side='left', padx=5)
        
        self.btn_foco_perto = ttk.Button(focus_frame, text="PERTO", width=6,
                                        command=self.foco_perto)
        self.btn_foco_perto.pack(side='left', padx=2)
        
        self.btn_foco_longe = ttk.Button(focus_frame, text="LONGE", width=6,
                                        command=self.foco_longe)
        self.btn_foco_longe.pack(side='left', padx=2)
        
        # Zoom
        zoom_frame = ttk.Frame(focus_controls)
        zoom_frame.pack(fill='x', pady=2)
        
        ttk.Label(zoom_frame, text="🔍 Zoom:").pack(side='left')
        
        self.btn_zoom_out = ttk.Button(zoom_frame, text="➖", width=4,
                                      command=self.zoom_out)
        self.btn_zoom_out.pack(side='left', padx=5)
        
        self.zoom_valor_label = ttk.Label(zoom_frame, text="1.0x", width=6)
        self.zoom_valor_label.pack(side='left', padx=5)
        
        self.btn_zoom_in = ttk.Button(zoom_frame, text="➕", width=4,
                                     command=self.zoom_in)
        self.btn_zoom_in.pack(side='left', padx=2)
        
        self.btn_zoom_reset = ttk.Button(zoom_frame, text="RESET", width=6,
                                        command=self.zoom_reset)
        self.btn_zoom_reset.pack(side='left', padx=5)
        
        # Modo de reconhecimento
        modo_frame = ttk.LabelFrame(controls_frame, text="🤖 Modos de Reconhecimento", padding="5")
        modo_frame.pack(fill='x', pady=(0, 10))
        
        self.var_yolo = tk.BooleanVar(value=True)
        self.check_yolo = ttk.Checkbutton(modo_frame, text="🧠 YOLO (Produtos Treinados)",
                                         variable=self.var_yolo, command=self.atualizar_modos)
        self.check_yolo.pack(anchor='w', pady=2)
        
        self.var_barcode = tk.BooleanVar(value=True)
        self.check_barcode = ttk.Checkbutton(modo_frame, text="📊 Código de Barras",
                                            variable=self.var_barcode, command=self.atualizar_modos)
        self.check_barcode.pack(anchor='w', pady=2)
        
        self.var_ocr = tk.BooleanVar(value=True)
        self.check_ocr = ttk.Checkbutton(modo_frame, text="📝 OCR (Texto)",
                                        variable=self.var_ocr, command=self.atualizar_modos)
        self.check_ocr.pack(anchor='w', pady=2)
        
        # Botão de reset
        ttk.Button(controls_frame, text="🔄 Resetar Configurações",
                  command=self.resetar_configuracoes).pack(pady=10)
        
        # === PAINEL DIREITO: DETECÇÕES ===
        detection_frame = ttk.LabelFrame(main_frame, text="📋 Detecções e Resultados", padding="10")
        detection_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Abas para diferentes tipos de detecção
        self.notebook = ttk.Notebook(detection_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Aba YOLO
        yolo_frame = ttk.Frame(self.notebook)
        self.notebook.add(yolo_frame, text="🧠 YOLO")
        
        ttk.Label(yolo_frame, text="Produtos Detectados (YOLO):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.yolo_listbox = tk.Listbox(yolo_frame, height=8, font=('Arial', 9))
        scrollbar_yolo = ttk.Scrollbar(yolo_frame, orient='vertical', command=self.yolo_listbox.yview)
        self.yolo_listbox.configure(yscrollcommand=scrollbar_yolo.set)
        self.yolo_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_yolo.pack(side='right', fill='y')
        
        # Aba Códigos de Barras
        barcode_frame = ttk.Frame(self.notebook)
        self.notebook.add(barcode_frame, text="📊 Barcode")
        
        ttk.Label(barcode_frame, text="Códigos de Barras Detectados:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.barcode_listbox = tk.Listbox(barcode_frame, height=8, font=('Arial', 9))
        scrollbar_barcode = ttk.Scrollbar(barcode_frame, orient='vertical', command=self.barcode_listbox.yview)
        self.barcode_listbox.configure(yscrollcommand=scrollbar_barcode.set)
        self.barcode_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_barcode.pack(side='right', fill='y')
        
        # Aba OCR
        ocr_frame = ttk.Frame(self.notebook)
        self.notebook.add(ocr_frame, text="📝 OCR")
        
        ttk.Label(ocr_frame, text="Texto Detectado (OCR):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.ocr_text = tk.Text(ocr_frame, height=8, width=30, font=('Arial', 9))
        scrollbar_ocr = ttk.Scrollbar(ocr_frame, orient='vertical', command=self.ocr_text.yview)
        self.ocr_text.configure(yscrollcommand=scrollbar_ocr.set)
        self.ocr_text.pack(side='left', fill='both', expand=True)
        scrollbar_ocr.pack(side='right', fill='y')
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(detection_frame, text="📊 Estatísticas", padding="5")
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_frames = ttk.Label(stats_frame, text="Frames: 0", font=('Arial', 9))
        self.stats_frames.pack(anchor='w')
        
        self.stats_yolo_det = ttk.Label(stats_frame, text="YOLO: 0", font=('Arial', 9))
        self.stats_yolo_det.pack(anchor='w')
        
        self.stats_barcode_det = ttk.Label(stats_frame, text="Barcodes: 0", font=('Arial', 9))
        self.stats_barcode_det.pack(anchor='w')
        
        # Configurar grid weights
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
    def carregar_modelo_yolo(self):
        """Carrega modelo YOLO treinado"""
        if not YOLO_DISPONIVEL:
            self.status_ia.config(text="❌ IA: YOLO não disponível")
            return False
        
        modelo_paths = [
            "verifik/verifik_yolov8.pt",
            "verifik/runs/treino_continuado/weights/best.pt",
            "runs/detect/train/weights/best.pt"
        ]
        
        for path in modelo_paths:
            if os.path.exists(path):
                try:
                    self.modelo_yolo = YOLO(path)
                    self.status_ia.config(text="✅ IA: YOLO Carregado")
                    print(f"✅ Modelo YOLO carregado: {path}")
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
            print(f"✅ {len(self.produtos_database)} produtos carregados da base")
        except Exception as e:
            print(f"❌ Erro ao carregar produtos: {e}")
    
    def obter_configuracoes_camera(self):
        """Obtém configurações atuais da câmera"""
        try:
            url = f"{self.config_url}?action=getConfig&name=VideoInOptions"
            response = requests.get(url, auth=self.auth, timeout=5)
            if response.status_code == 200:
                print("✅ Configurações da câmera obtidas")
            else:
                print("⚠️ Não foi possível obter configurações da câmera")
        except Exception as e:
            print(f"⚠️ Erro ao obter configurações: {e}")
    
    def toggle_streaming(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.parar_streaming()
        else:
            self.iniciar_streaming()
    
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
                    frame_data = self.capturar_frame_camera()
                    
                    if frame_data:
                        frame_processado = self.processar_frame(frame_data)
                        self.root.after(0, self.atualizar_display, frame_processado)
                        
                        # Controle de FPS
                        self.total_frames += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            self.fps_atual = self.total_frames / (current_time - self.last_fps_time)
                            self.root.after(0, self.atualizar_fps)
                            self.total_frames = 0
                            self.last_fps_time = current_time
                        
                        self.root.after(0, lambda: self.status_conexao.config(text="🟢 Stream Ativo"))
                    else:
                        self.root.after(0, lambda: self.status_conexao.config(text="🔴 Erro Conexão"))
                        time.sleep(2)
                    
                    time.sleep(0.3)  # ~3 FPS
                    
                except Exception as e:
                    print(f"Erro no streaming: {e}")
                    time.sleep(3)
        
        thread = threading.Thread(target=streaming_thread, daemon=True)
        thread.start()
    
    def parar_streaming(self):
        """Para o streaming"""
        self.streaming = False
        self.btn_stream.config(text="▶️ Iniciar Stream")
        self.status_conexao.config(text="⚪ Desconectado")
    
    def toggle_reconhecimento(self):
        """Liga/desliga reconhecimento"""
        self.reconhecimento_ativo = not self.reconhecimento_ativo
        if self.reconhecimento_ativo:
            self.btn_reconhecimento.config(text="🔴 Parar IA")
            self.status_ia.config(text="🟢 IA: Ativo")
        else:
            self.btn_reconhecimento.config(text="🧠 Ativar IA")
            self.status_ia.config(text="⚪ IA: Inativo")
    
    def capturar_frame_camera(self):
        """Captura frame da câmera"""
        try:
            response = requests.get(self.snapshot_url, auth=self.auth, timeout=3)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None
    
    def processar_frame(self, frame_data):
        """Processa frame com todos os tipos de reconhecimento"""
        if not self.reconhecimento_ativo:
            return frame_data
        
        try:
            # Converter para OpenCV
            nparr = np.frombuffer(frame_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            deteccoes_yolo = []
            deteccoes_barcode = []
            texto_ocr = ""
            
            # YOLO Detection
            if self.usar_yolo and self.modelo_yolo:
                deteccoes_yolo = self.detectar_yolo(img_cv)
            
            # Barcode Detection
            if self.usar_barcode and BARCODE_DISPONIVEL:
                deteccoes_barcode = self.detectar_barcodes(img_cv)
            
            # OCR Detection
            if self.usar_ocr:
                texto_ocr = self.detectar_ocr(img_cv)
            
            # Desenhar detecções
            img_resultado = self.desenhar_todas_deteccoes(img_cv, deteccoes_yolo, deteccoes_barcode)
            
            # Atualizar listas na UI
            self.root.after(0, self.atualizar_deteccoes_ui, deteccoes_yolo, deteccoes_barcode, texto_ocr)
            
            # Converter de volta
            _, buffer = cv2.imencode('.jpg', img_resultado)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return frame_data
    
    def detectar_yolo(self, img_cv):
        """Detecta objetos com YOLO"""
        try:
            results = self.modelo_yolo.predict(img_cv, conf=self.confianca_yolo, verbose=False)
            deteccoes = []
            
            if results and len(results) > 0:
                for r in results:
                    if r.boxes is not None:
                        for box in r.boxes:
                            xyxy = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            
                            if cls_id < len(self.modelo_yolo.names):
                                classe = self.modelo_yolo.names[cls_id]
                                deteccoes.append({
                                    'bbox': xyxy,
                                    'confianca': conf,
                                    'classe': classe,
                                    'tipo': 'YOLO'
                                })
            
            return deteccoes
        except Exception as e:
            return []
    
    def detectar_barcodes(self, img_cv):
        """Detecta códigos de barras"""
        try:
            # Converter para cinza
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Detectar códigos de barras
            barcodes = pyzbar_decode.decode(gray)
            deteccoes = []
            
            for barcode in barcodes:
                # Extrair dados
                x, y, w, h = barcode.rect
                data = barcode.data.decode('utf-8')
                tipo = barcode.type
                
                deteccoes.append({
                    'bbox': [x, y, x + w, y + h],
                    'data': data,
                    'tipo_barcode': tipo,
                    'tipo': 'BARCODE'
                })
                
                self.total_barcodes += 1
            
            return deteccoes
        except Exception as e:
            return []
    
    def detectar_ocr(self, img_cv):
        """Detecta texto com OCR"""
        try:
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            texto = pytesseract.image_to_string(gray, lang='por+eng', config='--psm 6 --oem 3')
            return texto.strip()
        except Exception as e:
            return ""
    
    def desenhar_todas_deteccoes(self, img_cv, deteccoes_yolo, deteccoes_barcode):
        """Desenha todas as detecções no frame"""
        img_resultado = img_cv.copy()
        
        # Desenhar YOLO (verde)
        for det in deteccoes_yolo:
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Label
            label = f"YOLO: {det['classe']} ({det['confianca']:.2f})"
            cv2.putText(img_resultado, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Desenhar Barcodes (azul)
        for det in deteccoes_barcode:
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Label
            label = f"BARCODE: {det['data'][:20]}..."
            cv2.putText(img_resultado, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        return img_resultado
    
    def atualizar_deteccoes_ui(self, deteccoes_yolo, deteccoes_barcode, texto_ocr):
        """Atualiza listas de detecções na UI"""
        # Limpar listas
        self.yolo_listbox.delete(0, tk.END)
        self.barcode_listbox.delete(0, tk.END)
        self.ocr_text.delete(1.0, tk.END)
        
        # YOLO
        for det in deteccoes_yolo:
            item = f"{det['classe']} ({det['confianca']:.2f})"
            self.yolo_listbox.insert(tk.END, item)
        
        # Barcodes
        for det in deteccoes_barcode:
            item = f"{det['tipo_barcode']}: {det['data']}"
            self.barcode_listbox.insert(tk.END, item)
        
        # OCR
        if texto_ocr:
            self.ocr_text.insert(tk.END, texto_ocr)
        
        # Estatísticas
        self.stats_frames.config(text=f"Frames: {self.total_frames}")
        self.stats_yolo_det.config(text=f"YOLO: {len(deteccoes_yolo)}")
        self.stats_barcode_det.config(text=f"Barcodes: {len(deteccoes_barcode)}")
    
    def atualizar_display(self, frame_data):
        """Atualiza display de vídeo"""
        try:
            # Converter para PIL
            image = Image.open(io.BytesIO(frame_data))
            
            # Redimensionar se necessário
            display_size = (640, 480)
            image = image.resize(display_size, Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo
            
        except Exception as e:
            print(f"Erro ao atualizar display: {e}")
    
    def atualizar_fps(self):
        """Atualiza contador FPS"""
        self.fps_label.config(text=f"FPS: {self.fps_atual:.1f}")
    
    # === CONTROLES DA CÂMERA ===
    
    def ajustar_brilho(self, valor):
        """Ajusta brilho da câmera"""
        self.brilho_atual = int(float(valor))
        self.brilho_valor.config(text=str(self.brilho_atual))
        self.aplicar_configuracao_camera("Brightness", self.brilho_atual)
    
    def ajustar_contraste(self, valor):
        """Ajusta contraste da câmera"""
        self.contraste_atual = int(float(valor))
        self.contraste_valor.config(text=str(self.contraste_atual))
        self.aplicar_configuracao_camera("Contrast", self.contraste_atual)
    
    def ajustar_exposicao(self, valor):
        """Ajusta exposição da câmera"""
        self.exposicao_atual = int(float(valor))
        self.exposicao_valor.config(text=str(self.exposicao_atual))
        self.aplicar_configuracao_camera("ExposureValue", self.exposicao_atual)
    
    def ajustar_iris(self, valor):
        """Ajusta íris da câmera"""
        self.iris_atual = int(float(valor))
        self.iris_valor.config(text=str(self.iris_atual))
        self.aplicar_configuracao_camera("IrisValue", self.iris_atual)
    
    def aplicar_configuracao_camera(self, parametro, valor):
        """Aplica configuração na câmera via API"""
        try:
            url = f"{self.config_url}?action=setConfig&{parametro}[0]={valor}"
            response = requests.get(url, auth=self.auth, timeout=3)
            if response.status_code == 200:
                print(f"✅ {parametro} ajustado para {valor}")
        except Exception as e:
            print(f"⚠️ Erro ao ajustar {parametro}: {e}")
    
    def foco_automatico(self):
        """Ativa foco automático"""
        self.aplicar_configuracao_camera("FocusMode", "Auto")
        print("🎯 Foco automático ativado")
    
    def foco_perto(self):
        """Ajusta foco para perto"""
        if self.foco_atual > 0:
            self.foco_atual -= 10
            self.aplicar_configuracao_camera("FocusValue", self.foco_atual)
            print(f"🎯 Foco ajustado: {self.foco_atual}")
    
    def foco_longe(self):
        """Ajusta foco para longe"""
        if self.foco_atual < 100:
            self.foco_atual += 10
            self.aplicar_configuracao_camera("FocusValue", self.foco_atual)
            print(f"🎯 Foco ajustado: {self.foco_atual}")
    
    def zoom_in(self):
        """Aumenta zoom"""
        if self.zoom_atual < 5.0:
            self.zoom_atual += 0.2
            self.zoom_valor_label.config(text=f"{self.zoom_atual:.1f}x")
            self.aplicar_configuracao_camera("ZoomValue", int(self.zoom_atual * 20))
            print(f"🔍 Zoom: {self.zoom_atual:.1f}x")
    
    def zoom_out(self):
        """Diminui zoom"""
        if self.zoom_atual > 1.0:
            self.zoom_atual -= 0.2
            self.zoom_valor_label.config(text=f"{self.zoom_atual:.1f}x")
            self.aplicar_configuracao_camera("ZoomValue", int(self.zoom_atual * 20))
            print(f"🔍 Zoom: {self.zoom_atual:.1f}x")
    
    def zoom_reset(self):
        """Reseta zoom para 1x"""
        self.zoom_atual = 1.0
        self.zoom_valor_label.config(text=f"{self.zoom_atual:.1f}x")
        self.aplicar_configuracao_camera("ZoomValue", 20)
        print("🔍 Zoom resetado para 1x")
    
    def atualizar_modos(self):
        """Atualiza modos de reconhecimento"""
        self.usar_yolo = self.var_yolo.get()
        self.usar_barcode = self.var_barcode.get()
        self.usar_ocr = self.var_ocr.get()
        
        modos = []
        if self.usar_yolo: modos.append("YOLO")
        if self.usar_barcode: modos.append("Barcode")
        if self.usar_ocr: modos.append("OCR")
        
        print(f"🤖 Modos ativos: {', '.join(modos) if modos else 'Nenhum'}")
    
    def resetar_configuracoes(self):
        """Reseta todas as configurações para padrão"""
        # Resetar controles
        self.brilho_scale.set(50)
        self.contraste_scale.set(50)
        self.exposicao_scale.set(50)
        self.iris_scale.set(50)
        
        # Resetar zoom
        self.zoom_reset()
        
        # Aplicar configurações padrão
        self.ajustar_brilho(50)
        self.ajustar_contraste(50)
        self.ajustar_exposicao(50)
        self.ajustar_iris(50)
        
        print("🔄 Configurações resetadas para padrão")
    
    def tirar_foto_manual(self):
        """Tira foto manual e salva"""
        try:
            frame_data = self.capturar_frame_camera()
            if frame_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"foto_verifik_{timestamp}.jpg"
                
                with open(filename, 'wb') as f:
                    f.write(frame_data)
                
                messagebox.showinfo("Foto Salva", f"Foto salva: {filename}")
                print(f"📸 Foto salva: {filename}")
            else:
                messagebox.showerror("Erro", "Não foi possível capturar foto")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar foto: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VerifiKBarcodeAvancado(root)
    root.mainloop()