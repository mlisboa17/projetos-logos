#!/usr/bin/env python3
"""
VerifiK - Sistema Avançado com Rastreamento de Múltiplos Objetos (MOT)
Recursos: YOLO + Multi-Object Tracking + Barcode + Controles da Câmera
Detecta e rastreia múltiplos produtos simultaneamente na frente da câmera
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
import uuid
from collections import defaultdict, deque
import math

# Imports para detecção e rastreamento
try:
    from ultralytics import YOLO
    import pytesseract
    # Para códigos de barras - usando cv2 se pyzbar não disponível
    try:
        from pyzbar import pyzbar
        import pyzbar.pyzbar as pyzbar_decode
        BARCODE_DISPONIVEL = True
    except ImportError:
        BARCODE_DISPONIVEL = False
        print("⚠️ pyzbar não disponível, usando detecção básica de padrões")
    
    YOLO_DISPONIVEL = True
    
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
except ImportError as e:
    print(f"⚠️ Dependências não encontradas: {e}")
    YOLO_DISPONIVEL = False
    BARCODE_DISPONIVEL = False

class TrackedObject:
    """Classe para objetos rastreados"""
    def __init__(self, obj_id, bbox, classe, confianca, tipo='YOLO'):
        self.id = obj_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.classe = classe
        self.confianca = confianca
        self.tipo = tipo
        self.historico_posicoes = deque(maxlen=30)  # Últimas 30 posições
        self.tempo_criacao = time.time()
        self.ultima_deteccao = time.time()
        self.frames_sem_deteccao = 0
        self.confirmado = False
        self.cor = self._gerar_cor_unica()
        self.texto_adicional = ""
        
        # Controle de passagem
        self.passou_pela_camera = False
        self.entrou_zona = False
        self.saiu_zona = False
        self.status_passagem = "DETECTADO"  # DETECTADO, PASSOU, NAO_PASSOU
        
        # Adicionar posição inicial
        self.historico_posicoes.append(self._centro_bbox(bbox))
    
    def _gerar_cor_unica(self):
        """Gera cor única para o objeto baseada no ID"""
        # Hash do ID para cor consistente
        hash_id = hash(self.id) % 1000000
        r = (hash_id * 137) % 255
        g = (hash_id * 241) % 255
        b = (hash_id * 193) % 255
        return (b, g, r)  # BGR para OpenCV
    
    def _centro_bbox(self, bbox):
        """Calcula centro da bbox"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def atualizar(self, bbox, confianca, texto_adicional=""):
        """Atualiza posição e dados do objeto"""
        self.bbox = bbox
        self.confianca = confianca
        self.ultima_deteccao = time.time()
        self.frames_sem_deteccao = 0
        self.texto_adicional = texto_adicional
        
        # Adicionar nova posição ao histórico
        centro = self._centro_bbox(bbox)
        self.historico_posicoes.append(centro)
        
        # Confirmar objeto se detectado por alguns frames
        if len(self.historico_posicoes) >= 5:
            self.confirmado = True
    
    def perdeu_deteccao(self):
        """Marca que objeto não foi detectado neste frame"""
        self.frames_sem_deteccao += 1
    
    def deve_remover(self, max_frames_perdidos=30):
        """Verifica se objeto deve ser removido do rastreamento"""
        return self.frames_sem_deteccao > max_frames_perdidos
    
    def obter_velocidade(self):
        """Calcula velocidade de movimento"""
        if len(self.historico_posicoes) < 2:
            return 0
        
        pos_atual = self.historico_posicoes[-1]
        pos_anterior = self.historico_posicoes[-2]
        
        dx = pos_atual[0] - pos_anterior[0]
        dy = pos_atual[1] - pos_anterior[1]
        
        return math.sqrt(dx*dx + dy*dy)
    
    def obter_trajetoria(self):
        """Retorna pontos da trajetória para desenhar"""
        return list(self.historico_posicoes)
    
    def verificar_passagem_zona_central(self, largura_frame, altura_frame):
        """Verifica se objeto passou pela zona central da câmera"""
        if len(self.historico_posicoes) < 5:
            return
        
        # Definir zona central (30% do centro da tela)
        centro_x = largura_frame // 2
        centro_y = altura_frame // 2
        zona_largura = largura_frame * 0.3
        zona_altura = altura_frame * 0.3
        
        zona_x1 = centro_x - zona_largura // 2
        zona_x2 = centro_x + zona_largura // 2
        zona_y1 = centro_y - zona_altura // 2
        zona_y2 = centro_y + zona_altura // 2
        
        # Verificar se entrou na zona
        posicao_atual = self.historico_posicoes[-1]
        x, y = posicao_atual
        
        esta_na_zona = (zona_x1 <= x <= zona_x2 and zona_y1 <= y <= zona_y2)
        
        if esta_na_zona and not self.entrou_zona:
            self.entrou_zona = True
        elif not esta_na_zona and self.entrou_zona and not self.saiu_zona:
            self.saiu_zona = True
            self.passou_pela_camera = True
            self.status_passagem = "PASSOU"
    
    def marcar_nao_passou(self):
        """Marca manualmente que o produto não passou"""
        self.status_passagem = "NAO_PASSOU"
        self.passou_pela_camera = False

class MultiObjectTracker:
    """Rastreador de múltiplos objetos"""
    def __init__(self, max_distance=100):
        self.objetos_rastreados = {}
        self.proximo_id = 1
        self.max_distance = max_distance
    
    def calcular_distancia(self, bbox1, bbox2):
        """Calcula distância entre duas bboxes (centros)"""
        def centro(bbox):
            x1, y1, x2, y2 = bbox
            return ((x1 + x2) / 2, (y1 + y2) / 2)
        
        c1 = centro(bbox1)
        c2 = centro(bbox2)
        
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
    
    def atualizar(self, deteccoes):
        """
        Atualiza rastreamento com novas detecções
        deteccoes: lista de dicts com 'bbox', 'classe', 'confianca', 'tipo'
        """
        # Marcar todos os objetos como perdidos inicialmente
        for obj in self.objetos_rastreados.values():
            obj.perdeu_deteccao()
        
        # Associar detecções com objetos existentes
        deteccoes_nao_associadas = []
        
        for deteccao in deteccoes:
            melhor_obj = None
            menor_distancia = float('inf')
            
            # Encontrar objeto mais próximo da mesma classe
            for obj_id, obj in self.objetos_rastreados.items():
                if obj.classe == deteccao['classe']:
                    distancia = self.calcular_distancia(obj.bbox, deteccao['bbox'])
                    
                    if distancia < self.max_distance and distancia < menor_distancia:
                        melhor_obj = obj
                        menor_distancia = distancia
            
            # Se encontrou objeto próximo, atualizar
            if melhor_obj:
                texto_extra = deteccao.get('texto_adicional', '')
                melhor_obj.atualizar(deteccao['bbox'], deteccao['confianca'], texto_extra)
            else:
                # Nova detecção - adicionar à lista de não associadas
                deteccoes_nao_associadas.append(deteccao)
        
        # Criar novos objetos para detecções não associadas
        for deteccao in deteccoes_nao_associadas:
            obj_id = f"obj_{self.proximo_id:04d}"
            self.proximo_id += 1
            
            novo_objeto = TrackedObject(
                obj_id, 
                deteccao['bbox'], 
                deteccao['classe'], 
                deteccao['confianca'],
                deteccao['tipo']
            )
            
            if 'texto_adicional' in deteccao:
                novo_objeto.texto_adicional = deteccao['texto_adicional']
            
            self.objetos_rastreados[obj_id] = novo_objeto
        
        # Remover objetos que perderam rastreamento
        objetos_para_remover = []
        for obj_id, obj in self.objetos_rastreados.items():
            if obj.deve_remover():
                objetos_para_remover.append(obj_id)
        
        for obj_id in objetos_para_remover:
            del self.objetos_rastreados[obj_id]
        
        return list(self.objetos_rastreados.values())
    
    def obter_objetos_confirmados(self):
        """Retorna apenas objetos confirmados (detectados por vários frames)"""
        return [obj for obj in self.objetos_rastreados.values() if obj.confirmado]
    
    def limpar(self):
        """Limpa todos os objetos rastreados"""
        self.objetos_rastreados.clear()
        self.proximo_id = 1

class VerifiKMultiTracking:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Rastreamento de Múltiplos Objetos (MOT)")
        self.root.geometry("1700x1000")
        
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
        self.rastreamento_ativo = False
        self.usar_yolo = True
        self.usar_barcode = True
        self.mostrar_trajetoria = True
        self.mostrar_historico = True
        
        # Rastreador de objetos
        self.tracker = MultiObjectTracker(max_distance=80)
        
        # Controles da câmera
        self.brilho_atual = 50
        self.exposicao_atual = 50
        self.zoom_atual = 1.0
        
        # Modelo YOLO e dados
        self.modelo_yolo = None
        self.confianca_yolo = 0.25  # Aumentada para detecções mais estáveis
        self.produtos_database = []
        
        # Estatísticas
        self.total_frames = 0
        self.objetos_detectados_total = 0
        self.fps_atual = 0
        self.last_fps_time = time.time()
        
        # Controle de passagem
        self.produtos_passaram = 0
        self.produtos_nao_passaram = 0
        self.mostrar_zona_central = True
        
        # Configurar interface
        self.configurar_interface()
        
        # Inicializar sistema
        self.carregar_modelo_yolo()
        self.carregar_produtos_database()
        
    def configurar_interface(self):
        """Configura interface gráfica para multi-tracking"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🎯 VerifiK Multi-Tracking: Rastreamento de Múltiplos Produtos", 
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        # === PAINEL ESQUERDO: VÍDEO ===
        video_frame = ttk.LabelFrame(main_frame, text="📹 Streaming + Rastreamento", padding="10")
        video_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Display de vídeo (maior para ver múltiplos objetos)
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
        
        self.btn_tracking = ttk.Button(stream_controls, text="🎯 Ativar Tracking", 
                                      command=self.toggle_rastreamento)
        self.btn_tracking.pack(side='left', padx=5)
        
        self.btn_limpar = ttk.Button(stream_controls, text="🧹 Limpar Objetos", 
                                    command=self.limpar_rastreamento)
        self.btn_limpar.pack(side='left', padx=5)
        
        self.btn_snapshot = ttk.Button(stream_controls, text="📸 Foto", 
                                     command=self.tirar_foto_manual)
        self.btn_snapshot.pack(side='left', padx=5)
        
        # Controles de passagem
        passagem_controls = ttk.Frame(video_frame)
        passagem_controls.pack(fill='x', pady=5)
        
        ttk.Label(passagem_controls, text="🚪 Controle de Passagem:", font=('Arial', 10, 'bold')).pack(side='left')
        
        self.btn_marcar_nao_passou = ttk.Button(passagem_controls, text="❌ Não Passou", 
                                               command=self.marcar_produto_nao_passou, state='disabled')
        self.btn_marcar_nao_passou.pack(side='left', padx=5)
        
        self.btn_confirmar_passou = ttk.Button(passagem_controls, text="✅ Confirmou Passagem", 
                                              command=self.confirmar_produto_passou, state='disabled')
        self.btn_confirmar_passou.pack(side='left', padx=5)
        
        self.btn_resetar_passagem = ttk.Button(passagem_controls, text="🔄 Reset Passagem", 
                                              command=self.resetar_controle_passagem)
        self.btn_resetar_passagem.pack(side='left', padx=5)
        
        # Opções de visualização
        view_options = ttk.Frame(video_frame)
        view_options.pack(fill='x', pady=5)
        
        self.var_trajetoria = tk.BooleanVar(value=True)
        ttk.Checkbutton(view_options, text="Mostrar Trajetórias", 
                       variable=self.var_trajetoria).pack(side='left', padx=5)
        
        self.var_historico = tk.BooleanVar(value=True)
        ttk.Checkbutton(view_options, text="Histórico de IDs", 
                       variable=self.var_historico).pack(side='left', padx=5)
        
        self.var_zona_central = tk.BooleanVar(value=True)
        ttk.Checkbutton(view_options, text="Zona de Passagem", 
                       variable=self.var_zona_central).pack(side='left', padx=5)
        
        # Status
        status_frame = ttk.Frame(video_frame)
        status_frame.pack(fill='x', pady=5)
        
        self.status_conexao = ttk.Label(status_frame, text="⚪ Desconectado", font=('Arial', 9))
        self.status_conexao.pack(side='left')
        
        self.status_tracking = ttk.Label(status_frame, text="⚪ Tracking: Inativo", font=('Arial', 9))
        self.status_tracking.pack(side='left', padx=(20, 0))
        
        self.fps_label = ttk.Label(status_frame, text="FPS: 0.0", font=('Arial', 9))
        self.fps_label.pack(side='right')
        
        # === PAINEL CENTRO: CONTROLES ===
        controls_frame = ttk.LabelFrame(main_frame, text="🎛️ Controles de Detecção", padding="10")
        controls_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Configurações de YOLO
        yolo_frame = ttk.LabelFrame(controls_frame, text="🧠 Configurações YOLO", padding="5")
        yolo_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(yolo_frame, text="Confiança YOLO:").grid(row=0, column=0, sticky='w', pady=2)
        self.confianca_scale = ttk.Scale(yolo_frame, from_=0.1, to=0.9, orient='horizontal',
                                        command=self.ajustar_confianca)
        self.confianca_scale.set(0.25)
        self.confianca_scale.grid(row=0, column=1, sticky='ew', padx=5)
        self.confianca_valor = ttk.Label(yolo_frame, text="0.25")
        self.confianca_valor.grid(row=0, column=2)
        
        yolo_frame.columnconfigure(1, weight=1)
        
        # Configurações de Tracking
        tracking_frame = ttk.LabelFrame(controls_frame, text="🎯 Configurações de Rastreamento", padding="5")
        tracking_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(tracking_frame, text="Distância Máxima:").grid(row=0, column=0, sticky='w', pady=2)
        self.distancia_scale = ttk.Scale(tracking_frame, from_=30, to=150, orient='horizontal',
                                        command=self.ajustar_distancia_tracking)
        self.distancia_scale.set(80)
        self.distancia_scale.grid(row=0, column=1, sticky='ew', padx=5)
        self.distancia_valor = ttk.Label(tracking_frame, text="80")
        self.distancia_valor.grid(row=0, column=2)
        
        tracking_frame.columnconfigure(1, weight=1)
        
        # Controles da câmera simplificados
        camera_frame = ttk.LabelFrame(controls_frame, text="📷 Controles da Câmera", padding="5")
        camera_frame.pack(fill='x', pady=(0, 10))
        
        # Brilho
        ttk.Label(camera_frame, text="☀️ Brilho:").grid(row=0, column=0, sticky='w', pady=2)
        self.brilho_scale = ttk.Scale(camera_frame, from_=0, to=100, orient='horizontal',
                                     command=self.ajustar_brilho)
        self.brilho_scale.set(50)
        self.brilho_scale.grid(row=0, column=1, sticky='ew', padx=5)
        
        # Exposição
        ttk.Label(camera_frame, text="📷 Exposição:").grid(row=1, column=0, sticky='w', pady=2)
        self.exposicao_scale = ttk.Scale(camera_frame, from_=0, to=100, orient='horizontal',
                                        command=self.ajustar_exposicao)
        self.exposicao_scale.set(50)
        self.exposicao_scale.grid(row=1, column=1, sticky='ew', padx=5)
        
        # Zoom
        zoom_frame = ttk.Frame(camera_frame)
        zoom_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Label(zoom_frame, text="🔍 Zoom:").pack(side='left')
        ttk.Button(zoom_frame, text="➖", width=3, command=self.zoom_out).pack(side='left', padx=2)
        self.zoom_label = ttk.Label(zoom_frame, text="1.0x", width=6)
        self.zoom_label.pack(side='left', padx=5)
        ttk.Button(zoom_frame, text="➕", width=3, command=self.zoom_in).pack(side='left', padx=2)
        
        camera_frame.columnconfigure(1, weight=1)
        
        # === PAINEL DIREITO: OBJETOS RASTREADOS ===
        objects_frame = ttk.LabelFrame(main_frame, text="🎯 Objetos Rastreados", padding="10")
        objects_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Lista de objetos ativos
        ttk.Label(objects_frame, text="Objetos Ativos:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Frame com scrollbar para lista de objetos
        list_frame = ttk.Frame(objects_frame)
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.objects_listbox = tk.Listbox(list_frame, height=12, font=('Arial', 9))
        scrollbar_objects = ttk.Scrollbar(list_frame, orient='vertical', command=self.objects_listbox.yview)
        self.objects_listbox.configure(yscrollcommand=scrollbar_objects.set)
        self.objects_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_objects.pack(side='right', fill='y')
        
        # Detalhes do objeto selecionado
        details_frame = ttk.LabelFrame(objects_frame, text="📋 Detalhes do Objeto", padding="5")
        details_frame.pack(fill='x', pady=(0, 10))
        
        self.details_text = tk.Text(details_frame, height=6, width=30, font=('Arial', 8))
        details_scroll = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        self.details_text.pack(side='left', fill='both', expand=True)
        details_scroll.pack(side='right', fill='y')
        
        # Bind para seleção de objeto
        self.objects_listbox.bind('<<ListboxSelect>>', self.mostrar_detalhes_objeto)
        self.objects_listbox.bind('<<ListboxSelect>>', self.atualizar_botoes_passagem, add='+')
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(objects_frame, text="📊 Estatísticas", padding="5")
        stats_frame.pack(fill='x')
        
        self.stats_frames = ttk.Label(stats_frame, text="Frames: 0", font=('Arial', 9))
        self.stats_frames.pack(anchor='w')
        
        self.stats_objetos_ativos = ttk.Label(stats_frame, text="Objetos Ativos: 0", font=('Arial', 9))
        self.stats_objetos_ativos.pack(anchor='w')
        
        self.stats_total_detectado = ttk.Label(stats_frame, text="Total Detectado: 0", font=('Arial', 9))
        self.stats_total_detectado.pack(anchor='w')
        
        # Estatísticas de passagem
        passagem_stats = ttk.LabelFrame(objects_frame, text="🚪 Controle de Passagem", padding="5")
        passagem_stats.pack(fill='x', pady=(10, 0))
        
        self.stats_passou = ttk.Label(passagem_stats, text="Passaram: 0", font=('Arial', 9), foreground='green')
        self.stats_passou.pack(anchor='w')
        
        self.stats_nao_passou = ttk.Label(passagem_stats, text="Não Passaram: 0", font=('Arial', 9), foreground='red')
        self.stats_nao_passou.pack(anchor='w')
        
        self.stats_detectando = ttk.Label(passagem_stats, text="Detectando: 0", font=('Arial', 9), foreground='orange')
        self.stats_detectando.pack(anchor='w')
        
        # Configurar grid weights
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def carregar_modelo_yolo(self):
        """Carrega modelo YOLO treinado"""
        if not YOLO_DISPONIVEL:
            messagebox.showerror("Erro", "YOLO não disponível")
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
                    print(f"✅ Modelo YOLO carregado: {path}")
                    return True
                except Exception as e:
                    print(f"❌ Erro ao carregar modelo: {e}")
        
        messagebox.showerror("Erro", "Modelo YOLO não encontrado")
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
                        frame_processado = self.processar_frame_com_tracking(frame_data)
                        self.root.after(0, self.atualizar_display, frame_processado)
                        
                        # Controle de FPS
                        self.total_frames += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            self.fps_atual = self.total_frames / (current_time - self.last_fps_time)
                            self.root.after(0, self.atualizar_estatisticas)
                            self.total_frames = 0
                            self.last_fps_time = current_time
                        
                        self.root.after(0, lambda: self.status_conexao.config(text="🟢 Stream Ativo"))
                    else:
                        self.root.after(0, lambda: self.status_conexao.config(text="🔴 Erro Conexão"))
                        time.sleep(2)
                    
                    time.sleep(0.2)  # ~5 FPS para melhor tracking
                    
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
    
    def toggle_rastreamento(self):
        """Liga/desliga rastreamento"""
        self.rastreamento_ativo = not self.rastreamento_ativo
        if self.rastreamento_ativo:
            self.btn_tracking.config(text="🔴 Parar Tracking")
            self.status_tracking.config(text="🟢 Tracking: Ativo")
        else:
            self.btn_tracking.config(text="🎯 Ativar Tracking")
            self.status_tracking.config(text="⚪ Tracking: Inativo")
            self.tracker.limpar()
    
    def limpar_rastreamento(self):
        """Limpa todos os objetos rastreados"""
        self.tracker.limpar()
        self.objects_listbox.delete(0, tk.END)
        self.details_text.delete(1.0, tk.END)
        print("🧹 Rastreamento limpo")
    
    def capturar_frame_camera(self):
        """Captura frame da câmera"""
        try:
            response = requests.get(self.snapshot_url, auth=self.auth, timeout=3)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None
    
    def processar_frame_com_tracking(self, frame_data):
        """Processa frame com rastreamento de múltiplos objetos"""
        if not self.rastreamento_ativo or not self.modelo_yolo:
            return frame_data
        
        try:
            # Converter para OpenCV
            nparr = np.frombuffer(frame_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Detectar objetos com YOLO
            deteccoes = self.detectar_objetos_yolo(img_cv)
            
            # Detectar códigos de barras se habilitado
            if self.usar_barcode:
                deteccoes_barcode = self.detectar_barcodes_basico(img_cv)
                deteccoes.extend(deteccoes_barcode)
            
            # Atualizar rastreamento
            objetos_rastreados = self.tracker.atualizar(deteccoes)
            
            # Verificar passagem pela zona central
            altura, largura = img_cv.shape[:2]
            for obj in objetos_rastreados:
                obj.verificar_passagem_zona_central(largura, altura)
            
            # Desenhar objetos rastreados
            img_resultado = self.desenhar_objetos_rastreados(img_cv, objetos_rastreados)
            
            # Atualizar UI
            self.root.after(0, self.atualizar_lista_objetos, objetos_rastreados)
            
            # Converter de volta
            _, buffer = cv2.imencode('.jpg', img_resultado)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return frame_data
    
    def detectar_objetos_yolo(self, img_cv):
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
                                    'classe': classe,
                                    'confianca': conf,
                                    'tipo': 'YOLO'
                                })
            
            return deteccoes
        except Exception as e:
            return []
    
    def detectar_barcodes_basico(self, img_cv):
        """Detecta códigos de barras usando padrões básicos"""
        try:
            deteccoes = []
            
            # Se pyzbar disponível, usar
            if BARCODE_DISPONIVEL:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                barcodes = pyzbar_decode.decode(gray)
                
                for barcode in barcodes:
                    x, y, w, h = barcode.rect
                    data = barcode.data.decode('utf-8')
                    tipo = barcode.type
                    
                    deteccoes.append({
                        'bbox': [x, y, x + w, y + h],
                        'classe': f'BARCODE_{tipo}',
                        'confianca': 0.9,
                        'tipo': 'BARCODE',
                        'texto_adicional': data
                    })
            else:
                # Detecção básica de padrões de barcode
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Filtro para realçar linhas verticais (códigos de barras)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
                morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
                
                # Encontrar contornos
                contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Filtrar por proporções típicas de códigos de barras
                    if w > 50 and h > 20 and w/h > 2:
                        deteccoes.append({
                            'bbox': [x, y, x + w, y + h],
                            'classe': 'BARCODE_PATTERN',
                            'confianca': 0.7,
                            'tipo': 'BARCODE_PATTERN'
                        })
            
            return deteccoes
        except Exception as e:
            return []
    
    def desenhar_objetos_rastreados(self, img_cv, objetos_rastreados):
        """Desenha objetos rastreados com IDs, trajetórias e zona central"""
        img_resultado = img_cv.copy()
        altura, largura = img_cv.shape[:2]
        
        # Desenhar zona central se habilitada
        if self.var_zona_central.get():
            centro_x = largura // 2
            centro_y = altura // 2
            zona_largura = int(largura * 0.3)
            zona_altura = int(altura * 0.3)
            
            x1 = centro_x - zona_largura // 2
            y1 = centro_y - zona_altura // 2
            x2 = centro_x + zona_largura // 2
            y2 = centro_y + zona_altura // 2
            
            # Desenhar retângulo da zona central
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(img_resultado, "ZONA DE PASSAGEM", (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        for obj in objetos_rastreados:
            x1, y1, x2, y2 = obj.bbox
            cor = obj.cor
            
            # Desenhar bbox
            thickness = 3 if obj.confirmado else 2
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, thickness)
            
            # Preparar label com status de passagem
            label = f"ID:{obj.id[-4:]} {obj.classe}"
            if obj.confianca:
                label += f" ({obj.confianca:.2f})"
            
            # Status de passagem
            if obj.status_passagem == "PASSOU":
                status_label = "✅ PASSOU"
                cor_status = (0, 255, 0)  # Verde
            elif obj.status_passagem == "NAO_PASSOU":
                status_label = "❌ NAO PASSOU"
                cor_status = (0, 0, 255)  # Vermelho
            else:
                status_label = "🔍 DETECTANDO"
                cor_status = (0, 165, 255)  # Laranja
            
            # Background do label principal
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(img_resultado, (x1, y1 - 50), (x1 + max(label_size[0], 150), y1), cor, -1)
            
            # Texto do label principal
            cv2.putText(img_resultado, label, (x1, y1 - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Label de status
            cv2.putText(img_resultado, status_label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor_status, 2)
            
            # Mostrar trajetória se habilitado
            if self.var_trajetoria.get() and len(obj.historico_posicoes) > 1:
                pontos = obj.obter_trajetoria()
                for i in range(1, len(pontos)):
                    alpha = i / len(pontos)  # Fade da trajetória
                    cor_fade = tuple(int(c * alpha) for c in cor)
                    cv2.line(img_resultado, pontos[i-1], pontos[i], cor_fade, 2)
            
            # Mostrar informações adicionais
            if obj.texto_adicional:
                info_y = y2 + 20
                cv2.putText(img_resultado, obj.texto_adicional[:30], (x1, info_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
        
        return img_resultado
    
    def atualizar_lista_objetos(self, objetos_rastreados):
        """Atualiza lista de objetos na interface"""
        # Salvar seleção atual
        selecao_atual = None
        if self.objects_listbox.curselection():
            selecao_atual = self.objects_listbox.get(self.objects_listbox.curselection()[0])
        
        # Limpar e repovoar lista
        self.objects_listbox.delete(0, tk.END)
        
        # Separar por confirmados e não confirmados
        confirmados = [obj for obj in objetos_rastreados if obj.confirmado]
        nao_confirmados = [obj for obj in objetos_rastreados if not obj.confirmado]
        
        # Adicionar confirmados primeiro
        for obj in confirmados:
            tempo_vida = time.time() - obj.tempo_criacao
            velocidade = obj.obter_velocidade()
            
            # Ícone baseado no status de passagem
            if obj.status_passagem == "PASSOU":
                icone = "✅"
            elif obj.status_passagem == "NAO_PASSOU":
                icone = "❌"
            else:
                icone = "🔍"
            
            item = f"{icone} ID:{obj.id[-4:]} | {obj.classe} | {obj.status_passagem} | {tempo_vida:.1f}s"
            self.objects_listbox.insert(tk.END, item)
        
        # Adicionar não confirmados
        for obj in nao_confirmados:
            item = f"⏳ ID:{obj.id[-4:]} | {obj.classe} | DETECTANDO..."
            self.objects_listbox.insert(tk.END, item)
        
        # Habilitar/desabilitar botões baseado na seleção
        if self.objects_listbox.curselection():
            self.btn_marcar_nao_passou.config(state='normal')
            self.btn_confirmar_passou.config(state='normal')
        else:
            self.btn_marcar_nao_passou.config(state='disabled')
            self.btn_confirmar_passou.config(state='disabled')
        
        # Restaurar seleção se possível
        if selecao_atual:
            for i in range(self.objects_listbox.size()):
                if selecao_atual in self.objects_listbox.get(i):
                    self.objects_listbox.selection_set(i)
                    break
    
    def mostrar_detalhes_objeto(self, event):
        """Mostra detalhes do objeto selecionado"""
        if not self.objects_listbox.curselection():
            return
        
        # Extrair ID do item selecionado
        item_selecionado = self.objects_listbox.get(self.objects_listbox.curselection()[0])
        id_match = re.search(r'ID:(\w+)', item_selecionado)
        
        if not id_match:
            return
        
        id_curto = id_match.group(1)
        
        # Encontrar objeto completo
        objeto_encontrado = None
        for obj_id, obj in self.tracker.objetos_rastreados.items():
            if obj.id.endswith(id_curto):
                objeto_encontrado = obj
                break
        
        if not objeto_encontrado:
            return
        
        # Mostrar detalhes
        self.details_text.delete(1.0, tk.END)
        
        detalhes = f"""ID Completo: {objeto_encontrado.id}
Classe: {objeto_encontrado.classe}
Tipo: {objeto_encontrado.tipo}
Confiança: {objeto_encontrado.confianca:.3f}
Status: {'✅ Confirmado' if objeto_encontrado.confirmado else '⏳ Detectando'}
Passagem: {objeto_encontrado.status_passagem}

Posição: {objeto_encontrado.bbox}
Tempo de Vida: {time.time() - objeto_encontrado.tempo_criacao:.1f}s
Última Detecção: {time.time() - objeto_encontrado.ultima_deteccao:.1f}s atrás
Frames sem Detecção: {objeto_encontrado.frames_sem_deteccao}

Velocidade: {objeto_encontrado.obter_velocidade():.2f} pixels/frame
Trajetória: {len(objeto_encontrado.historico_posicoes)} pontos

Controle de Passagem:
- Entrou na Zona: {'Sim' if objeto_encontrado.entrou_zona else 'Não'}
- Saiu da Zona: {'Sim' if objeto_encontrado.saiu_zona else 'Não'}
- Passou pela Câmera: {'Sim' if objeto_encontrado.passou_pela_camera else 'Não'}

Informações Adicionais:
{objeto_encontrado.texto_adicional if objeto_encontrado.texto_adicional else 'Nenhuma'}"""
        
        self.details_text.insert(tk.END, detalhes)
    
    def atualizar_estatisticas(self):
        """Atualiza estatísticas na interface"""
        objetos_ativos = len(self.tracker.objetos_rastreados)
        self.objetos_detectados_total = max(self.objetos_detectados_total, objetos_ativos)
        
        # Contar status de passagem atuais
        detectando = 0
        passou_automatico = 0
        
        for obj in self.tracker.objetos_rastreados.values():
            if obj.status_passagem == "DETECTADO":
                detectando += 1
            elif obj.status_passagem == "PASSOU" and obj.passou_pela_camera:
                passou_automatico += 1
        
        # Atualizar labels
        self.fps_label.config(text=f"FPS: {self.fps_atual:.1f}")
        self.stats_frames.config(text=f"Frames: {self.total_frames}")
        self.stats_objetos_ativos.config(text=f"Objetos Ativos: {objetos_ativos}")
        self.stats_total_detectado.config(text=f"Total Detectado: {self.objetos_detectados_total}")
        
        # Estatísticas de passagem
        total_passou = self.produtos_passaram + passou_automatico
        self.stats_passou.config(text=f"Passaram: {total_passou}")
        self.stats_nao_passou.config(text=f"Não Passaram: {self.produtos_nao_passaram}")
        self.stats_detectando.config(text=f"Detectando: {detectando}")
    
    def atualizar_display(self, frame_data):
        """Atualiza display de vídeo"""
        try:
            # Converter para PIL
            image = Image.open(io.BytesIO(frame_data))
            
            # Redimensionar mantendo proporção (maior para ver múltiplos objetos)
            display_size = (800, 600)
            image = image.resize(display_size, Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo
            
        except Exception as e:
            print(f"Erro ao atualizar display: {e}")
    
    # === CONTROLES DE CONFIGURAÇÃO ===
    
    def ajustar_confianca(self, valor):
        """Ajusta confiança do YOLO"""
        self.confianca_yolo = float(valor)
        self.confianca_valor.config(text=f"{self.confianca_yolo:.2f}")
    
    def ajustar_distancia_tracking(self, valor):
        """Ajusta distância máxima para tracking"""
        nova_distancia = int(float(valor))
        self.tracker.max_distance = nova_distancia
        self.distancia_valor.config(text=str(nova_distancia))
    
    def ajustar_brilho(self, valor):
        """Ajusta brilho da câmera"""
        self.brilho_atual = int(float(valor))
        self.aplicar_configuracao_camera("Brightness", self.brilho_atual)
    
    def ajustar_exposicao(self, valor):
        """Ajusta exposição da câmera"""
        self.exposicao_atual = int(float(valor))
        self.aplicar_configuracao_camera("ExposureValue", self.exposicao_atual)
    
    def zoom_in(self):
        """Aumenta zoom"""
        if self.zoom_atual < 5.0:
            self.zoom_atual += 0.2
            self.zoom_label.config(text=f"{self.zoom_atual:.1f}x")
            self.aplicar_configuracao_camera("ZoomValue", int(self.zoom_atual * 20))
    
    def zoom_out(self):
        """Diminui zoom"""
        if self.zoom_atual > 1.0:
            self.zoom_atual -= 0.2
            self.zoom_label.config(text=f"{self.zoom_atual:.1f}x")
            self.aplicar_configuracao_camera("ZoomValue", int(self.zoom_atual * 20))
    
    def aplicar_configuracao_camera(self, parametro, valor):
        """Aplica configuração na câmera via API"""
        try:
            url = f"{self.config_url}?action=setConfig&{parametro}[0]={valor}"
            response = requests.get(url, auth=self.auth, timeout=3)
            if response.status_code == 200:
                print(f"✅ {parametro} ajustado para {valor}")
        except Exception as e:
            print(f"⚠️ Erro ao ajustar {parametro}: {e}")
    
    def marcar_produto_nao_passou(self):
        """Marca produto selecionado como 'não passou'"""
        if not self.objects_listbox.curselection():
            messagebox.showwarning("Seleção", "Selecione um produto da lista primeiro")
            return
        
        # Extrair ID do item selecionado
        item_selecionado = self.objects_listbox.get(self.objects_listbox.curselection()[0])
        id_match = re.search(r'ID:(\w+)', item_selecionado)
        
        if not id_match:
            return
        
        id_curto = id_match.group(1)
        
        # Encontrar objeto e marcar
        for obj_id, obj in self.tracker.objetos_rastreados.items():
            if obj.id.endswith(id_curto):
                obj.marcar_nao_passou()
                self.produtos_nao_passaram += 1
                print(f"❌ Produto {obj.classe} (ID:{id_curto}) marcado como NÃO PASSOU")
                messagebox.showinfo("Marcado", f"Produto {obj.classe} marcado como NÃO PASSOU")
                break
    
    def confirmar_produto_passou(self):
        """Confirma manualmente que produto passou"""
        if not self.objects_listbox.curselection():
            messagebox.showwarning("Seleção", "Selecione um produto da lista primeiro")
            return
        
        # Extrair ID do item selecionado
        item_selecionado = self.objects_listbox.get(self.objects_listbox.curselection()[0])
        id_match = re.search(r'ID:(\w+)', item_selecionado)
        
        if not id_match:
            return
        
        id_curto = id_match.group(1)
        
        # Encontrar objeto e confirmar passagem
        for obj_id, obj in self.tracker.objetos_rastreados.items():
            if obj.id.endswith(id_curto):
                obj.status_passagem = "PASSOU"
                obj.passou_pela_camera = True
                if obj.status_passagem != "PASSOU":  # Só conta se não estava marcado
                    self.produtos_passaram += 1
                print(f"✅ Produto {obj.classe} (ID:{id_curto}) confirmado como PASSOU")
                messagebox.showinfo("Confirmado", f"Produto {obj.classe} confirmado como PASSOU")
                break
    
    def resetar_controle_passagem(self):
        """Reseta todas as estatísticas de passagem"""
        resultado = messagebox.askyesno("Resetar", "Resetar todas as estatísticas de passagem?")
        if resultado:
            self.produtos_passaram = 0
            self.produtos_nao_passaram = 0
            
            # Resetar status de todos os objetos
            for obj in self.tracker.objetos_rastreados.values():
                obj.status_passagem = "DETECTADO"
                obj.passou_pela_camera = False
                obj.entrou_zona = False
                obj.saiu_zona = False
            
            print("🔄 Controle de passagem resetado")
            messagebox.showinfo("Resetado", "Controle de passagem resetado com sucesso")
    
    def tirar_foto_manual(self):
        """Tira foto manual com objetos rastreados"""
        try:
            frame_data = self.capturar_frame_camera()
            if frame_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"foto_multitracking_{timestamp}.jpg"
                
                with open(filename, 'wb') as f:
                    f.write(frame_data)
                
                # Salvar informações dos objetos detectados
                info_filename = f"objetos_{timestamp}.txt"
                with open(info_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Foto: {filename}\n")
                    f.write(f"Timestamp: {datetime.now()}\n")
                    f.write(f"Objetos Rastreados: {len(self.tracker.objetos_rastreados)}\n\n")
                    
                    for obj_id, obj in self.tracker.objetos_rastreados.items():
                        f.write(f"ID: {obj.id}\n")
                        f.write(f"Classe: {obj.classe}\n")
                        f.write(f"Confiança: {obj.confianca}\n")
                        f.write(f"Posição: {obj.bbox}\n")
                        f.write(f"Status: {'Confirmado' if obj.confirmado else 'Detectando'}\n")
                        f.write("-" * 30 + "\n")
                
                messagebox.showinfo("Foto Salva", f"Foto: {filename}\nInfo: {info_filename}")
                print(f"📸 Foto salva com informações de {len(self.tracker.objetos_rastreados)} objetos")
            else:
                messagebox.showerror("Erro", "Não foi possível capturar foto")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar foto: {e}")
    
    def atualizar_botoes_passagem(self, event=None):
        """Atualiza estado dos botões baseado na seleção"""
        if self.objects_listbox.curselection():
            self.btn_marcar_nao_passou.config(state='normal')
            self.btn_confirmar_passou.config(state='normal')
        else:
            self.btn_marcar_nao_passou.config(state='disabled')
            self.btn_confirmar_passou.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = VerifiKMultiTracking(root)
    root.mainloop()