#!/usr/bin/env python3
"""
VerifiK - Teste de Sistema com Controle de Passagem
Versão simplificada para teste
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image, ImageTk
import time
import threading
import cv2
import numpy as np
import os

# Teste de YOLO e OCR
try:
    from ultralytics import YOLO
    import pytesseract
    import sqlite3
    import re
    import json
    import requests
    from collections import defaultdict, deque
    from datetime import datetime, timedelta
    import uuid
    YOLO_DISPONIVEL = True
    OCR_DISPONIVEL = True
    
    # Configurar Tesseract (apenas inglês para melhor performance)
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Tentar importar pyzbar, mas não é obrigatório
    try:
        from pyzbar import pyzbar
        BARCODE_DISPONIVEL = True
        print("✅ YOLO + OCR + BARCODE disponíveis")
    except (ImportError, FileNotFoundError) as e:
        BARCODE_DISPONIVEL = False
        print("✅ YOLO + OCR disponíveis (BARCODE via OCR)")
        # Criar módulo pyzbar fictício para evitar erros
        class FakePyzbar:
            def decode(self, img):
                return []
        pyzbar = FakePyzbar()
        
except ImportError as e:
    YOLO_DISPONIVEL = False
    OCR_DISPONIVEL = False
    BARCODE_DISPONIVEL = False
    print(f"❌ Dependências não encontradas: {e}")

class ProductTracker:
    """Classe para rastrear um produto individual"""
    def __init__(self, track_id, deteccao_inicial, timestamp):
        self.track_id = track_id
        self.classe = deteccao_inicial['classe']
        self.fonte_deteccao = deteccao_inicial['fonte']
        
        # Histórico de posições
        self.historico_bbox = deque(maxlen=50)
        self.historico_centros = deque(maxlen=50)
        self.historico_confiancas = deque(maxlen=50)
        
        # Estado atual
        self.bbox_atual = deteccao_inicial['bbox']
        self.centro_atual = self.calcular_centro(self.bbox_atual)
        self.confianca_atual = deteccao_inicial['confianca']
        
        # Timestamps
        self.timestamp_criacao = timestamp
        self.timestamp_ultima_deteccao = timestamp
        self.timestamp_ultima_atualizacao = timestamp
        
        # Estado de rastreamento
        self.frames_sem_deteccao = 0
        self.ativo = True
        self.perdido = False
        self.passou_zona = False
        
        # Identificação única
        self.uuid = str(uuid.uuid4())[:8]
        
        # Adicionar primeira detecção
        self.adicionar_deteccao(deteccao_inicial, timestamp)
        
        # Cor de rastreamento
        self.cor_track = None
        
        # Características do produto
        self.caracteristicas = {
            'area_media': 0,
            'velocidade_media': 0,
            'direcao_movimento': None,
            'tempo_na_tela': 0
        }
    
    def calcular_centro(self, bbox):
        """Calcula centro da bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def adicionar_deteccao(self, deteccao, timestamp):
        """Adiciona nova detecção ao track"""
        self.bbox_atual = deteccao['bbox']
        self.centro_atual = self.calcular_centro(self.bbox_atual)
        self.confianca_atual = deteccao['confianca']
        self.timestamp_ultima_deteccao = timestamp
        self.timestamp_ultima_atualizacao = timestamp
        
        # Adicionar ao histórico
        self.historico_bbox.append(deteccao['bbox'])
        self.historico_centros.append(self.centro_atual)
        self.historico_confiancas.append(deteccao['confianca'])
        
        # Reset contador
        self.frames_sem_deteccao = 0
        self.perdido = False
        
        # Atualizar características
        self.atualizar_caracteristicas()
    
    def atualizar_caracteristicas(self):
        """Atualiza características do produto rastreado"""
        if len(self.historico_bbox) < 2:
            return
        
        # Calcular área média
        areas = []
        for bbox in self.historico_bbox:
            x1, y1, x2, y2 = bbox
            area = (x2 - x1) * (y2 - y1)
            areas.append(area)
        self.caracteristicas['area_media'] = sum(areas) / len(areas)
        
        # Calcular velocidade média
        if len(self.historico_centros) >= 2:
            velocidades = []
            for i in range(1, len(self.historico_centros)):
                centro_ant = self.historico_centros[i-1]
                centro_atual = self.historico_centros[i]
                
                dist = ((centro_atual[0] - centro_ant[0])**2 + 
                       (centro_atual[1] - centro_ant[1])**2)**0.5
                velocidades.append(dist)
            
            if velocidades:
                self.caracteristicas['velocidade_media'] = sum(velocidades) / len(velocidades)
        
        # Calcular direção do movimento
        if len(self.historico_centros) >= 5:
            primeiro_centro = self.historico_centros[0]
            ultimo_centro = self.historico_centros[-1]
            
            dx = ultimo_centro[0] - primeiro_centro[0]
            dy = ultimo_centro[1] - primeiro_centro[1]
            
            if abs(dx) > abs(dy):
                self.caracteristicas['direcao_movimento'] = 'HORIZONTAL'
            else:
                self.caracteristicas['direcao_movimento'] = 'VERTICAL'
        
        # Tempo na tela
        self.caracteristicas['tempo_na_tela'] = (
            self.timestamp_ultima_atualizacao - self.timestamp_criacao
        )
    
    def marcar_perdido(self):
        """Marca o track como perdido"""
        self.frames_sem_deteccao += 1
        self.timestamp_ultima_atualizacao = time.time()
        
        if self.frames_sem_deteccao > 15:  # 15 frames sem detecção
            self.perdido = True
    
    def calcular_distancia(self, deteccao):
        """Calcula distância entre track atual e nova detecção"""
        centro_deteccao = self.calcular_centro(deteccao['bbox'])
        
        dist_centro = ((self.centro_atual[0] - centro_deteccao[0])**2 + 
                      (self.centro_atual[1] - centro_deteccao[1])**2)**0.5
        
        return dist_centro
    
    def compativel_com_deteccao(self, deteccao, max_distancia):
        """Verifica se detecção é compatível com este track"""
        # Verificar distância
        distancia = self.calcular_distancia(deteccao)
        if distancia > max_distancia:
            return False
        
        # Verificar classe (opcional - produtos podem mudar de classe)
        # if deteccao['classe'] != self.classe:
        #     return False
        
        return True
    
    def deve_ser_removido(self, max_frames_perdido, max_tempo_vida):
        """Verifica se o track deve ser removido"""
        tempo_vida = time.time() - self.timestamp_criacao
        
        return (self.frames_sem_deteccao > max_frames_perdido or 
                tempo_vida > max_tempo_vida)

class VerifiKTesteProdutos:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Teste: Controle de Passagem de Produtos")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Configurar responsividade
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configuração da câmera
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        self.snapshot_url = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
        
        # Estado do sistema
        self.streaming = False
        self.deteccao_ativa = False
        
        # Modelo YOLO
        self.modelo_yolo = None
        
        # Produtos detectados
        self.produtos_detectados = []
        self.produtos_passaram = 0
        self.produtos_nao_passaram = 0
        
        # Configurações de validação (otimizadas para diferentes distâncias)
        self.tamanho_minimo = 300    # pixels² mínimos (produto pequeno distante)
        self.tamanho_maximo = 80000  # pixels² máximos (produto grande próximo)
        self.aspect_ratio_min = 0.15 # proporção mínima (objetos muito largos)
        self.aspect_ratio_max = 6.0  # proporção máxima (barras longas)
        self.confianca_minima = 0.25 # confiança mínima (mais sensível)
        self.deteccoes_recentes = {}  # cache para evitar duplicatas
        
        # BASE DE CONHECIMENTO DE TAMANHOS REAIS DE PRODUTOS
        self.conhecimento_produtos = {
            # BEBIDAS
            'lata_refrigerante': {
                'altura_real_mm': 123,  # altura real em mm
                'diametro_real_mm': 66,  # diâmetro real em mm
                'aspect_ratio_ideal': 1.86,  # altura/largura ideal
                'tolerancia_aspect': 0.4,  # ±40% de tolerância
                'area_min_pixels': 400,    # menor para câmera distante
                'area_max_pixels': 15000,  # maior para câmera próxima
                'nomes_alternativos': ['coca_cola', 'pepsi', 'refrigerante', 'lata', 'soda']
            },
            'lata_cerveja': {
                'altura_real_mm': 123,
                'diametro_real_mm': 66,
                'aspect_ratio_ideal': 1.86,
                'tolerancia_aspect': 0.3,
                'area_min_pixels': 1500,
                'area_max_pixels': 8000,
                'nomes_alternativos': ['cerveja', 'beer', 'brahma', 'skol', 'heineken']
            },
            'garrafa_agua': {
                'altura_real_mm': 200,
                'diametro_real_mm': 65,
                'aspect_ratio_ideal': 3.08,
                'tolerancia_aspect': 0.4,
                'area_min_pixels': 2000,
                'area_max_pixels': 12000,
                'nomes_alternativos': ['agua', 'water', 'garrafa', 'crystal']
            },
            'garrafa_refrigerante': {
                'altura_real_mm': 240,
                'diametro_real_mm': 70,
                'aspect_ratio_ideal': 3.43,
                'tolerancia_aspect': 0.5,
                'area_min_pixels': 1000,   # flexível para distâncias
                'area_max_pixels': 25000,  # cobrir câmeras próximas
                'nomes_alternativos': ['coca_cola_garrafa', 'pepsi_garrafa', 'refrigerante_garrafa']
            },
            'caixa_leite': {
                'altura_real_mm': 195,
                'largura_real_mm': 95,
                'aspect_ratio_ideal': 2.05,
                'tolerancia_aspect': 0.4,
                'area_min_pixels': 800,    # menor para longe
                'area_max_pixels': 22000,  # maior para perto
                'nomes_alternativos': ['leite', 'milk', 'longa_vida', 'tetra_pak']
            },
            'energetico': {
                'altura_real_mm': 168,
                'diametro_real_mm': 53,
                'aspect_ratio_ideal': 3.17,
                'tolerancia_aspect': 0.4,
                'area_min_pixels': 300,    # muito menor (lata fina distante)
                'area_max_pixels': 12000,  # maior alcance
                'nomes_alternativos': ['red_bull', 'monster', 'energetico', 'energy_drink']
            },
            # ALIMENTOS
            'pacote_biscoito': {
                'altura_real_mm': 150,
                'largura_real_mm': 110,
                'aspect_ratio_ideal': 1.36,
                'tolerancia_aspect': 0.5,
                'area_min_pixels': 600,    # menor para distância
                'area_max_pixels': 18000,  # maior para proximidade
                'nomes_alternativos': ['biscoito', 'bolacha', 'cookie', 'oreo']
            },
            'chocolate_barra': {
                'altura_real_mm': 120,
                'largura_real_mm': 25,
                'aspect_ratio_ideal': 4.8,
                'tolerancia_aspect': 0.7,  # maior tolerância para barras
                'area_min_pixels': 200,    # muito pequeno (barra distante)
                'area_max_pixels': 8000,   # maior alcance
                'nomes_alternativos': ['chocolate', 'barra', 'kit_kat', 'snickers']
            },
            # PRODUTOS GERAIS
            'produto_generico': {
                'aspect_ratio_ideal': 1.5,
                'tolerancia_aspect': 1.2,  # maior tolerância
                'area_min_pixels': 200,    # muito flexível
                'area_max_pixels': 50000,  # cobertura total
                'nomes_alternativos': ['produto', 'item', 'object']
            }
        }
        
        # Calibração automática de escala
        self.pixels_por_mm = None
        self.referencia_calibrada = False
        
        # SISTEMA DE APRENDIZADO DE FORMATOS
        self.formatos_aprendidos = {}  # {classe: [lista_de_formatos_válidos]}
        self.historico_deteccoes = {}  # Para aprendizado contínuo
        
        # BASE DE DADOS DE PRODUTOS TREINADOS
        self.produtos_treinados = []
        self.produtos_ocr_cache = {}  # Cache de reconhecimento OCR
        
        # CONFIGURAÇÕES HÍBRIDAS
        self.usar_yolo = True
        self.usar_ocr = True
        self.usar_aprendizado = True
        self.usar_base_treinada = True
        
        # THRESHOLDS DE COMBINAÇÃO
        self.confianca_yolo_min = 0.3
        self.confianca_ocr_min = 0.7  # OCR precisa ser mais confiável
        self.similaridade_texto_min = 0.6
        
        # CONFIGURAÇÕES DE CÓDIGO DE BARRAS
        self.usar_barcode = True
        self.barcode_cache = {}  # Cache de códigos já processados
        self.produtos_nao_treinados = []  # Produtos encontrados por código de barras
        
        # BIBLIOTECAS EXTERNAS DE VAREJO
        self.usar_openfoodfacts = True
        self.usar_base_conhecimento = True
        self.openfoodfacts_cache = {}
        self.base_conhecimento_varejo = {}
        self.produtos_descobertos_online = []
        
        # SISTEMA MOT (MULTI-OBJECT TRACKING) AVANÇADO
        self.mot_ativo = True
        self.produtos_rastreados = {}  # {track_id: ProductTracker}
        self.proximo_track_id = 1
        
        # SISTEMA DE MENSAGENS
        self.produtos_anunciados = set()  # Para evitar repetições
        self.ultima_mensagem = 0
        self.mensagens_ativas = True
        self.historico_rastreamento = deque(maxlen=1000)
        self.zona_passagem = None  # Será definida dinamicamente
        
        # CONFIGURAÇÕES DE TRACKING
        self.max_distancia_tracking = 150  # pixels
        self.frames_sem_deteccao_max = 30  # frames
        self.confianca_tracking_min = 0.4
        self.tempo_vida_track_max = 300  # segundos
        
        # MARCAÇÃO INTELIGENTE
        self.cores_tracking = [
            (255, 0, 0),    # Vermelho
            (0, 255, 0),    # Verde  
            (0, 0, 255),    # Azul
            (255, 255, 0),  # Ciano
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Amarelo
            (128, 0, 128),  # Roxo
            (255, 165, 0),  # Laranja
            (0, 128, 128),  # Teal
            (128, 128, 0)   # Olive
        ]
        
        # ESTATÍSTICAS DE RASTREAMENTO
        self.stats_mot = {
            'total_tracks': 0,
            'tracks_ativos': 0,
            'produtos_identificados': 0,
            'passagens_detectadas': 0,
            'tempo_inicio': time.time()
        }
        
        # Configurar interface
        self.configurar_interface()
        
        # Inicializar sistemas
        if YOLO_DISPONIVEL:
            self.carregar_modelo()
        
        if OCR_DISPONIVEL:
            self.carregar_base_produtos_treinados()
            self.inicializar_aprendizado_formatos()
            self.carregar_base_conhecimento_varejo()
            self.carregar_cache_openfoodfacts()
        

    
    def configurar_interface(self):
        """Interface responsiva com layout grid"""
        # Frame principal com grid
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configurar peso das linhas e colunas
        main_frame.grid_rowconfigure(2, weight=1)  # Área do vídeo
        main_frame.grid_rowconfigure(3, weight=1)  # Área da lista
        main_frame.grid_columnconfigure(0, weight=2)  # Coluna esquerda (vídeo)
        main_frame.grid_columnconfigure(1, weight=1)  # Coluna direita (controles)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        ttk.Label(title_frame, text="🎯 VerifiK - Controle de Passagem com IA Inteligente", 
                 font=('Arial', 16, 'bold')).pack()
        
        # Frame de controles principais
        controls_frame = ttk.LabelFrame(main_frame, text="🎮 Controles Principais", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        
        # Botões principais em linha
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(fill='x')
        
        self.btn_stream = ttk.Button(btn_frame, text="▶️ Iniciar Câmera", 
                                   command=self.toggle_streaming, width=15)
        self.btn_stream.pack(side='left', padx=5)
        
        self.btn_deteccao = ttk.Button(btn_frame, text="🧠 Ativar IA", 
                                     command=self.toggle_deteccao, width=15)
        self.btn_deteccao.pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📸 Foto Teste", 
                  command=self.teste_foto, width=12).pack(side='left', padx=5)
        
        # Status na mesma linha
        self.status_label = ttk.Label(btn_frame, text="⚪ Sistema Iniciado", font=('Arial', 10))
        self.status_label.pack(side='right', padx=10)
        
        # === COLUNA ESQUERDA: VÍDEO ===
        video_frame = ttk.LabelFrame(main_frame, text="📹 Streaming + Detecção IA", padding="10")
        video_frame.grid(row=2, column=0, sticky='nsew', padx=(0, 5))
        
        # Display de vídeo responsivo
        self.video_label = ttk.Label(video_frame, text="📷 Aguardando câmera...\n\nClique 'Iniciar Câmera' e depois 'Ativar IA'", 
                                   font=('Arial', 12), background='black', foreground='white',
                                   anchor='center', justify='center')
        self.video_label.pack(expand=True, fill='both', padx=5, pady=5)
        
        # === LISTA DE PRODUTOS (SPAN 2 COLUNAS) ===
        list_frame = ttk.LabelFrame(main_frame, text="🛍️ Produtos Detectados pela IA", padding="10")
        list_frame.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=(10, 0))
        
        # Container com scrollbar responsivo
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill='both', expand=True)
        
        # Listbox responsiva
        self.produtos_listbox = tk.Listbox(list_container, height=6, font=('Arial', 10),
                                         selectmode='single')
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.produtos_listbox.yview)
        self.produtos_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.produtos_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Controles de passagem organizados
        passagem_frame = ttk.LabelFrame(list_frame, text="🚪 Controle de Passagem", padding="5")
        passagem_frame.pack(fill='x', pady=(10, 0))
        
        # Linha de botões
        btn_line = ttk.Frame(passagem_frame)
        btn_line.pack(fill='x')
        
        ttk.Label(btn_line, text="Selecione um produto e marque:", font=('Arial', 9)).pack(side='left')
        
        self.btn_passou = ttk.Button(btn_line, text="✅ Passou", 
                                   command=self.marcar_passou, state='disabled', width=10)
        self.btn_passou.pack(side='right', padx=5)
        
        self.btn_nao_passou = ttk.Button(btn_line, text="❌ Não Passou", 
                                        command=self.marcar_nao_passou, state='disabled', width=12)
        self.btn_nao_passou.pack(side='right', padx=5)
        
        # Bind para seleção
        self.produtos_listbox.bind('<<ListboxSelect>>', self.on_produto_select)
        
        # === COLUNA DIREITA: CONTROLES E CONFIGURAÇÕES ===
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=2, column=1, sticky='nsew', padx=(5, 0))
        
        # Configurações de validação IA
        config_frame = ttk.LabelFrame(right_frame, text="🧠 Configurações IA", padding="8")
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Tamanho mínimo
        size_frame = ttk.Frame(config_frame)
        size_frame.pack(fill='x', pady=3)
        ttk.Label(size_frame, text="📏 Tamanho Mín:", width=12).pack(side='left')
        self.size_var = tk.StringVar(value="2000")
        size_entry = ttk.Entry(size_frame, textvariable=self.size_var, width=8)
        size_entry.pack(side='left', padx=3)
        ttk.Label(size_frame, text="px²").pack(side='left')
        
        # Confiança mínima
        conf_frame = ttk.Frame(config_frame)
        conf_frame.pack(fill='x', pady=3)
        ttk.Label(conf_frame, text="🎯 Confiança:", width=12).pack(side='left')
        self.conf_var = tk.StringVar(value="0.4")
        conf_entry = ttk.Entry(conf_frame, textvariable=self.conf_var, width=8)
        conf_entry.pack(side='left', padx=3)
        ttk.Label(conf_frame, text="(0-1)").pack(side='left')
        
        # Botão aplicar
        ttk.Button(config_frame, text="✅ Aplicar Configurações", 
                  command=self.atualizar_config).pack(pady=5)
        
        # Controles do sistema híbrido
        hibrido_frame = ttk.LabelFrame(right_frame, text="🤖 Sistema Híbrido", padding="8")
        hibrido_frame.pack(fill='x', pady=(0, 10))
        
        self.var_yolo = tk.BooleanVar(value=True)
        ttk.Checkbutton(hibrido_frame, text="🧠 YOLO", variable=self.var_yolo, 
                       command=self.atualizar_sistema_hibrido).pack(anchor='w')
        
        self.var_ocr = tk.BooleanVar(value=True)
        ttk.Checkbutton(hibrido_frame, text="📚 OCR + Base", variable=self.var_ocr, 
                       command=self.atualizar_sistema_hibrido).pack(anchor='w')
        
        self.var_aprendizado = tk.BooleanVar(value=True)
        ttk.Checkbutton(hibrido_frame, text="🌱 Aprendizado", variable=self.var_aprendizado, 
                       command=self.atualizar_sistema_hibrido).pack(anchor='w')
        
        self.var_barcode = tk.BooleanVar(value=True)
        ttk.Checkbutton(hibrido_frame, text="📱 Código Barras", variable=self.var_barcode, 
                       command=self.atualizar_sistema_hibrido).pack(anchor='w')
        
        # Informações da base
        info_frame = ttk.LabelFrame(right_frame, text="📊 Informações", padding="8")
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_base = ttk.Label(info_frame, text="Base: Carregando...", font=('Arial', 8))
        self.info_base.pack(anchor='w')
        
        self.info_aprendizado = ttk.Label(info_frame, text="Formatos: 0", font=('Arial', 8))
        self.info_aprendizado.pack(anchor='w')
        
        # Estatísticas compactas
        stats_frame = ttk.LabelFrame(right_frame, text="📊 Estatísticas", padding="8")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.stats_detectados = ttk.Label(stats_frame, text="🔍 Detectados: 0", font=('Arial', 9))
        self.stats_detectados.pack(anchor='w', pady=1)
        
        self.stats_passou = ttk.Label(stats_frame, text="✅ Passaram: 0", font=('Arial', 9), foreground='green')
        self.stats_passou.pack(anchor='w', pady=1)
        
        self.stats_nao_passou = ttk.Label(stats_frame, text="❌ Não Passaram: 0", font=('Arial', 9), foreground='red')
        self.stats_nao_passou.pack(anchor='w', pady=1)

    
    def carregar_base_produtos_treinados(self):
        """Carrega base de dados de produtos treinados"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            
            # Verificar colunas existentes na tabela
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = [col[1] for col in cursor.fetchall()]
            print(f"📋 Colunas disponíveis: {colunas}")
            
            # Query adaptativa baseada nas colunas disponíveis
            campos = ['descricao_produto']
            if 'categoria' in colunas: campos.append('categoria')
            if 'marca' in colunas: campos.append('marca')
            if 'id' in colunas: campos.append('id')
            
            # Carregar todos os produtos (sem limit)
            query = f"SELECT DISTINCT {', '.join(campos)} FROM produtos WHERE descricao_produto IS NOT NULL AND descricao_produto != '' ORDER BY descricao_produto"
            cursor.execute(query)
            
            # Contar total de produtos na base
            cursor_count = conn.cursor()
            cursor_count.execute("SELECT COUNT(*) FROM produtos WHERE descricao_produto IS NOT NULL AND descricao_produto != ''")
            total_produtos = cursor_count.fetchone()[0]
            print(f"📊 Total de produtos na base: {total_produtos}")
            
            self.produtos_treinados = []
            for row in cursor.fetchall():
                produto = {
                    'descricao': row[0] if row[0] else '',
                    'categoria': row[1] if len(row) > 1 and row[1] else '',
                    'marca': row[2] if len(row) > 2 and row[2] else '',
                    'id': row[3] if len(row) > 3 and row[3] else '',
                    'palavras_chave': self.extrair_palavras_chave(row[0] if row[0] else '')
                }
                self.produtos_treinados.append(produto)
            
            conn.close()
            
            print(f"✅ {len(self.produtos_treinados)} produtos carregados da base treinada")
            self.status_label.config(text=f"📚 Base carregada: {len(self.produtos_treinados)} produtos")
            
            # Mapear produtos com classes do YOLO se disponível
            if self.modelo_yolo and hasattr(self.modelo_yolo, 'names'):
                self.mapear_classes_yolo_com_base()
            
            # Mostrar guia de tamanhos
            self.mostrar_guia_tamanhos()
            
        except Exception as e:
            print(f"❌ Erro ao carregar base de produtos: {e}")
            self.produtos_treinados = []
    
    def mapear_classes_yolo_com_base(self):
        """Mapeia classes do YOLO com produtos da base de dados"""
        if not self.modelo_yolo or not hasattr(self.modelo_yolo, 'names'):
            return
        
        self.mapa_yolo_base = {}
        classes_yolo = list(self.modelo_yolo.names.values())
        
        print(f"🔗 Mapeando {len(classes_yolo)} classes YOLO com {len(self.produtos_treinados)} produtos da base...")
        
        mapeamentos_encontrados = 0
        for classe_yolo in classes_yolo:
            # Procurar correspondências na base
            classe_limpa = self.limpar_texto_para_comparacao(classe_yolo)
            
            for produto in self.produtos_treinados:
                descricao_limpa = self.limpar_texto_para_comparacao(produto['descricao'])
                
                # Verificar similaridade
                if self.calcular_similaridade_texto(classe_limpa, descricao_limpa) > 0.6:
                    if classe_yolo not in self.mapa_yolo_base:
                        self.mapa_yolo_base[classe_yolo] = []
                    
                    self.mapa_yolo_base[classe_yolo].append(produto)
                    mapeamentos_encontrados += 1
                    break  # Pegar apenas a melhor correspondência
        
        print(f"✅ {mapeamentos_encontrados} mapeamentos YOLO ↔ Base criados")
        
        # Mostrar alguns exemplos
        contador = 0
        for classe, produtos in self.mapa_yolo_base.items():
            if contador < 5:  # Mostrar apenas 5 exemplos
                produto = produtos[0] if produtos else {}
                print(f"   🔗 '{classe}' → '{produto.get('descricao', 'N/A')}'")
                contador += 1

    def extrair_palavras_chave(self, descricao):
        """Extrai palavras-chave de uma descrição de produto"""
        if not descricao:
            return []
        
        # Limpar e dividir em palavras
        palavras = descricao.upper().replace(',', ' ').replace('-', ' ').split()
        
        # Filtrar palavras muito pequenas
        palavras_filtradas = [p for p in palavras if len(p) >= 3]
        
        return palavras_filtradas
    
    def limpar_texto_para_comparacao(self, texto):
        """Limpa texto para comparação"""
        if not texto:
            return ""
        
        # Converter para minúsculas e remover caracteres especiais
        import re
        texto_limpo = re.sub(r'[^a-zA-Z0-9\s]', ' ', texto.lower())
        # Remover espaços extras
        texto_limpo = ' '.join(texto_limpo.split())
        return texto_limpo
    
    def calcular_similaridade_texto(self, texto1, texto2):
        """Calcula similaridade entre dois textos"""
        if not texto1 or not texto2:
            return 0.0
        
        palavras1 = set(texto1.split())
        palavras2 = set(texto2.split())
        
        if not palavras1 or not palavras2:
            return 0.0
        
        # Jaccard similarity
        intersecao = palavras1.intersection(palavras2)
        uniao = palavras1.union(palavras2)
        
        return len(intersecao) / len(uniao) if uniao else 0.0
    
    def mostrar_guia_tamanhos(self):
        """Mostra guia prático de tamanhos para diferentes distâncias"""
        print("\n📏 GUIA DE TAMANHOS CONFIGURADOS:")
        print(f"   ⚙️ Tamanho mínimo geral: {self.tamanho_minimo} pixels²")
        print(f"   ⚙️ Tamanho máximo geral: {self.tamanho_maximo} pixels²")
        print("\n📦 PRODUTOS ESPECÍFICOS:")
        print("   🥫 Lata refrigerante: 400 - 15.000 px² (chocolate à 6m → lata à 1m)")
        print("   🍼 Garrafa PET: 1.000 - 25.000 px² (pequena à 5m → grande à 1m)")
        print("   📋 Caixa leite: 800 - 22.000 px² (longe → muito próximo)")
        print("   🍫 Chocolate barra: 200 - 8.000 px² (fino distante → próximo)")
        print("   📦 Pacote biscoito: 600 - 18.000 px² (médio alcance)")
        print("   ⚡ Energético: 300 - 12.000 px² (lata fina → próxima)")
        print("\n💡 DICA: Valores baixos detectam produtos distantes, altos evitam detecções gigantes\n")
    
    def inicializar_aprendizado_formatos(self):
        """Inicializa sistema de aprendizado de formatos"""
        # Carregar formatos já aprendidos se existir arquivo
        try:
            import json
            with open('formatos_aprendidos.json', 'r') as f:
                self.formatos_aprendidos = json.load(f)
            print(f"✅ {len(self.formatos_aprendidos)} formatos aprendidos carregados")
        except:
            print("📊 Iniciando aprendizado de formatos do zero")
            self.formatos_aprendidos = {}
    
    def salvar_formatos_aprendidos(self):
        """Salva formatos aprendidos em arquivo"""
        try:
            with open('formatos_aprendidos.json', 'w', encoding='utf-8') as f:
                json.dump(self.formatos_aprendidos, f, indent=2, ensure_ascii=False)
            print("💾 Formatos aprendidos salvos")
        except Exception as e:
            print(f"❌ Erro ao salvar formatos: {e}")
    
    def carregar_base_conhecimento_varejo(self):
        """Carrega base de conhecimento sobre produtos de varejo"""
        self.base_conhecimento_varejo = {
            'marcas_conhecidas': {
                'coca_cola': {'cores': ['vermelho', 'branco'], 'palavras': ['COCA', 'COLA', 'COKE']},
                'pepsi': {'cores': ['azul', 'vermelho'], 'palavras': ['PEPSI', 'COLA']},
                'guarana': {'cores': ['verde', 'vermelho'], 'palavras': ['GUARANÁ', 'ANTARCTICA']},
                'skol': {'cores': ['azul', 'branco'], 'palavras': ['SKOL', 'CERVEJA']},
                'brahma': {'cores': ['vermelho', 'dourado'], 'palavras': ['BRAHMA', 'CERVEJA']},
                'nestle': {'cores': ['azul', 'branco'], 'palavras': ['NESTLE', 'LEITE']},
                'doritos': {'cores': ['laranja', 'vermelho'], 'palavras': ['DORITOS', 'NACHO']},
                'oreo': {'cores': ['azul', 'branco'], 'palavras': ['OREO', 'BISCOITO']}
            }
        }
        
        print(f"🏪 Base conhecimento carregada: {len(self.base_conhecimento_varejo['marcas_conhecidas'])} marcas")
    
    def carregar_cache_openfoodfacts(self):
        """Carrega cache do OpenFoodFacts"""
        try:
            with open('openfoodfacts_cache.json', 'r', encoding='utf-8') as f:
                self.openfoodfacts_cache = json.load(f)
            print(f"🌍 OpenFoodFacts cache: {len(self.openfoodfacts_cache)} produtos")
        except:
            print("🌍 OpenFoodFacts cache vazio - iniciando")
            self.openfoodfacts_cache = {}
    
    def salvar_cache_openfoodfacts(self):
        """Salva cache do OpenFoodFacts"""
        try:
            with open('openfoodfacts_cache.json', 'w', encoding='utf-8') as f:
                json.dump(self.openfoodfacts_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar cache OpenFoodFacts: {e}")
    

    
    def identificar_formato_produto(self, nome_produto):
        """Identifica o formato do produto (lata, garrafa, barra, etc.)"""
        nome_lower = nome_produto.lower()
        
        # Latas (refrigerantes, cervejas)
        if any(word in nome_lower for word in ['coca', 'pepsi', 'skol', 'brahma', 'cerveja', 'refrigerante', 'guaraná']):
            if any(word in nome_lower for word in ['lata', '350ml', '269ml']):
                return 'lata'
            elif any(word in nome_lower for word in ['garrafa', 'pet', '600ml', '1l', '2l']):
                return 'garrafa'
        
        # Garrafas (água, sucos, leite)
        if any(word in nome_lower for word in ['água', 'suco', 'leite', 'garrafa', 'pet']):
            return 'garrafa'
        
        # Barras (chocolates, cereais)
        if any(word in nome_lower for word in ['chocolate', 'barra', 'cereal', 'granola']):
            return 'barra'
        
        # Pacotes/caixas
        if any(word in nome_lower for word in ['biscoito', 'bolacha', 'chips', 'pacote']):
            return 'pacote'
        
        # Caixas (leite longa vida)
        if any(word in nome_lower for word in ['leite', 'caixa', 'longa vida']):
            return 'caixa'
        
        return None
    
    def informar_produto_detectado(self, nome_produto, formato):
        """Informa por escrito quando detecta produto específico"""
        if not self.mensagens_ativas:
            return
        
        # Evitar mensagens muito frequentes
        tempo_atual = time.time()
        if tempo_atual - self.ultima_mensagem < 2:  # Mínimo 2 segundos entre mensagens
            return
        
        # Criar chave única para o produto
        chave_produto = f"{nome_produto}_{formato}"
        
        # Evitar repetições do mesmo produto
        if chave_produto in self.produtos_anunciados:
            return
        
        # Preparar texto da mensagem
        if formato:
            if formato == 'lata':
                texto_mensagem = f"🥫 LATA DETECTADA: {nome_produto}"
            elif formato == 'garrafa':
                texto_mensagem = f"🍼 GARRAFA DETECTADA: {nome_produto}"
            elif formato == 'barra':
                texto_mensagem = f"🍫 BARRA DETECTADA: {nome_produto}"
            elif formato == 'pacote':
                texto_mensagem = f"📦 PACOTE DETECTADO: {nome_produto}"
            elif formato == 'caixa':
                texto_mensagem = f"📋 CAIXA DETECTADA: {nome_produto}"
            else:
                texto_mensagem = f"📍 {formato.upper()} DETECTADA: {nome_produto}"
        else:
            texto_mensagem = f"🔍 PRODUTO DETECTADO: {nome_produto}"
        
        # Exibir mensagem no console e na interface
        print(texto_mensagem)
        
        # Atualizar status na interface se disponível
        if hasattr(self, 'status_label'):
            self.status_label.config(text=texto_mensagem)
        
        # Atualizar controles
        self.produtos_anunciados.add(chave_produto)
        self.ultima_mensagem = tempo_atual
        
        # Limpar cache de mensagens periodicamente (manter apenas últimos 10)
        if len(self.produtos_anunciados) > 10:
            # Remove os 5 mais antigos (aproximadamente)
            lista_produtos = list(self.produtos_anunciados)
            for i in range(5):
                if i < len(lista_produtos):
                    self.produtos_anunciados.discard(lista_produtos[i])
    
    def carregar_modelo(self):
        """Carrega modelo YOLO"""
        modelos = [
            "verifik/verifik_yolov8.pt",
            "verifik/runs/treino_continuado/weights/best.pt"
        ]
        
        for modelo_path in modelos:
            if os.path.exists(modelo_path):
                try:
                    self.modelo_yolo = YOLO(modelo_path)
                    
                    # Mostrar informações sobre o modelo treinado
                    if hasattr(self.modelo_yolo, 'names') and self.modelo_yolo.names:
                        nomes_classes = list(self.modelo_yolo.names.values())
                        print(f"✅ Modelo carregado: {modelo_path}")
                        print(f"🎯 Classes treinadas: {len(nomes_classes)} produtos")
                        print(f"📝 Primeiras 10 classes: {nomes_classes[:10]}")
                        
                        self.status_label.config(text=f"✅ YOLO: {len(nomes_classes)} classes")
                    else:
                        print(f"⚠️ Modelo carregado sem nomes de classes: {modelo_path}")
                        self.status_label.config(text="⚠️ Modelo sem classes")
                    
                    return True
                except Exception as e:
                    print(f"❌ Erro: {e}")
        
        self.status_label.config(text="⚠️ Modelo YOLO não encontrado")
        return False
    
    def toggle_streaming(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.streaming = False
            self.btn_stream.config(text="▶️ Iniciar Câmera")
            self.status_label.config(text="⚪ Câmera parada")
        else:
            self.streaming = True
            self.btn_stream.config(text="⏸️ Parar Câmera")
            self.status_label.config(text="🟡 Iniciando câmera...")
            threading.Thread(target=self.streaming_thread, daemon=True).start()
    
    def toggle_deteccao(self):
        """Liga/desliga detecção"""
        self.deteccao_ativa = not self.deteccao_ativa
        if self.deteccao_ativa:
            self.btn_deteccao.config(text="🔴 Parar Detecção")
            self.status_label.config(text="🟢 Detecção ativa")
        else:
            self.btn_deteccao.config(text="🧠 Ativar Detecção")
            self.status_label.config(text="⚪ Detecção inativa")
    
    def streaming_thread(self):
        """Thread de streaming"""
        while self.streaming:
            try:
                # Capturar frame
                response = requests.get(self.snapshot_url, auth=self.auth, timeout=3)
                
                if response.status_code == 200:
                    frame_data = response.content
                    
                    # Processar se detecção ativa
                    if self.deteccao_ativa:
                        frame_data = self.processar_frame_hibrido(frame_data)
                    
                    # Atualizar display
                    self.root.after(0, self.atualizar_display, frame_data)
                    self.root.after(0, lambda: self.status_label.config(text="🟢 Câmera ativa"))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="🔴 Erro de conexão"))
                
                time.sleep(0.5)  # 2 FPS
                
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"❌ Erro: {str(e)[:20]}"))
                time.sleep(2)
    
    def processar_frame_hibrido(self, frame_data):
        """Processa frame com YOLO + OCR + Base Treinada + Aprendizado"""
        try:
            # Converter para OpenCV
            nparr = np.frombuffer(frame_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            altura_frame, largura_frame = img_cv.shape[:2]
            
            deteccoes_finais = []
            
            # 1. DETECÇÃO YOLO (se disponível e habilitado)
            deteccoes_yolo = []
            if self.usar_yolo and self.modelo_yolo:
                deteccoes_yolo = self.detectar_com_yolo(img_cv)
                print(f"🧠 YOLO detectou {len(deteccoes_yolo)} objetos")
            
            # 2. RECONHECIMENTO OCR GLOBAL (se habilitado)
            texto_ocr_global = ""
            produtos_ocr = []
            if self.usar_ocr:
                texto_ocr_global = self.extrair_texto_ocr(img_cv)
                produtos_ocr = self.reconhecer_produtos_por_ocr(texto_ocr_global, img_cv)
                print(f"🔍 OCR encontrou {len(produtos_ocr)} produtos")
            
            # 3. DETECÇÃO DE CÓDIGOS DE BARRAS (para produtos não treinados)
            produtos_barcode = []
            if self.usar_barcode and BARCODE_DISPONIVEL:
                produtos_barcode = self.detectar_produtos_por_barcode(img_cv)
                print(f"📱 BARCODE encontrou {len(produtos_barcode)} produtos")
            
            # 4. COMBINAR E VALIDAR DETECÇÕES
            deteccoes_finais = self.combinar_deteccoes(deteccoes_yolo, produtos_ocr, produtos_barcode, img_cv)
            
            # 5. APLICAR APRENDIZADO DE FORMATOS
            if self.usar_aprendizado:
                deteccoes_finais = self.aplicar_aprendizado_formatos(deteccoes_finais, img_cv)
            
            # 6. DESENHAR RESULTADOS
            img_resultado = self.desenhar_deteccoes_hibridas(img_cv, deteccoes_finais)
            
            # 7. APLICAR SISTEMA MOT (MULTI-OBJECT TRACKING)
            if self.mot_ativo:
                deteccoes_finais = self.aplicar_mot(deteccoes_finais, img_cv)
            
            # 8. ATUALIZAR LISTA DE PRODUTOS
            self.atualizar_produtos_detectados(deteccoes_finais)
            
            # 9. INFORMAR PRODUTOS DETECTADOS (LATA, GARRAFA, BARRA)
            for det in deteccoes_finais:
                if 'classe' in det and det['classe']:
                    formato = self.identificar_formato_produto(det['classe'])
                    if formato:  # Só informa se identificou um formato específico
                        self.informar_produto_detectado(det['classe'], formato)
            
            # Converter de volta
            _, buffer = cv2.imencode('.jpg', img_resultado)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"❌ Erro no processamento híbrido: {e}")
            return frame_data
    
    def detectar_com_yolo(self, img_cv):
        """Detecta objetos usando YOLO"""
        try:
            results = self.modelo_yolo.predict(img_cv, conf=self.confianca_yolo_min, verbose=False)
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
                                
                                # Buscar informações adicionais na base mapeada
                                produto_base = None
                                if hasattr(self, 'mapa_yolo_base') and classe in self.mapa_yolo_base:
                                    produtos_mapeados = self.mapa_yolo_base[classe]
                                    if produtos_mapeados:
                                        produto_base = produtos_mapeados[0]
                                
                                deteccao = {
                                    'fonte': 'YOLO',
                                    'classe': classe,
                                    'confianca': conf,
                                    'bbox': xyxy,
                                    'validado': False
                                }
                                
                                # Adicionar informações da base se disponível
                                if produto_base:
                                    deteccao.update({
                                        'nome': produto_base.get('descricao', classe),
                                        'marca': produto_base.get('marca', ''),
                                        'categoria': produto_base.get('categoria', ''),
                                        'id_base': produto_base.get('id', ''),
                                        'fonte_enriquecida': 'YOLO+Base'
                                    })
                                else:
                                    deteccao['nome'] = classe
                                
                                deteccoes.append(deteccao)
            
            return deteccoes
        except Exception as e:
            print(f"❌ Erro YOLO: {e}")
            return []
    
    def detectar_produtos_por_barcode(self, img_cv):
        """Detecta produtos usando códigos de barras e busca no banco"""
        produtos_encontrados = []
        
        try:
            # Método 1: Usar pyzbar se disponível
            if BARCODE_DISPONIVEL:
                produtos_encontrados.extend(self.detectar_com_pyzbar(img_cv))
            
            # Método 2: Usar OCR para detectar códigos numéricos
            produtos_encontrados.extend(self.detectar_codigos_com_ocr(img_cv))
                
        except Exception as e:
            print(f"❌ Erro na detecção de código de barras: {e}")
        
        return produtos_encontrados
    
    def detectar_com_pyzbar(self, img_cv):
        """Detecta códigos usando pyzbar"""
        produtos_encontrados = []
        
        try:
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(gray)
            
            for barcode in barcodes:
                codigo_barras = barcode.data.decode('utf-8')
                tipo_barcode = barcode.type
                
                print(f"📱 Código pyzbar: {codigo_barras} (Tipo: {tipo_barcode})")
                
                produto_info = self.obter_produto_por_codigo(codigo_barras)
                if produto_info:
                    # Calcular bbox do código de barras
                    pontos = barcode.polygon
                    if pontos:
                        x_coords = [p.x for p in pontos]
                        y_coords = [p.y for p in pontos]
                        x1, y1 = min(x_coords), min(y_coords)
                        x2, y2 = max(x_coords), max(y_coords)
                        
                        # Expandir bbox
                        margem = 50
                        altura_img, largura_img = img_cv.shape[:2]
                        x1 = max(0, x1 - margem)
                        y1 = max(0, y1 - margem)
                        x2 = min(largura_img, x2 + margem)
                        y2 = min(altura_img, y2 + margem)
                        
                        produtos_encontrados.append({
                            'fonte': 'BARCODE',
                            'classe': produto_info['descricao'],
                            'confianca': 0.95,
                            'bbox': [x1, y1, x2, y2],
                            'codigo_barras': codigo_barras,
                            'tipo_barcode': tipo_barcode,
                            'produto_completo': produto_info,
                            'validado': True
                        })
        except Exception as e:
            print(f"❌ Erro pyzbar: {e}")
        
        return produtos_encontrados
    
    def detectar_codigos_com_ocr(self, img_cv):
        """Detecta códigos numéricos usando OCR"""
        produtos_encontrados = []
        
        try:
            # Extrair texto da imagem
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # OCR configurado para números
            texto = pytesseract.image_to_string(
                gray, 
                lang='eng',
                config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
            )
            
            # Procurar padrões de código de barras
            codigos_encontrados = self.extrair_codigos_numericos(texto)
            
            for codigo in codigos_encontrados:
                print(f"📱 Código OCR: {codigo}")
                
                produto_info = self.obter_produto_por_codigo(codigo)
                if produto_info:
                    altura_img, largura_img = img_cv.shape[:2]
                    
                    # bbox estimada (centro da imagem)
                    x1 = largura_img // 4
                    y1 = altura_img // 4
                    x2 = 3 * largura_img // 4
                    y2 = 3 * altura_img // 4
                    
                    produtos_encontrados.append({
                        'fonte': 'BARCODE-OCR',
                        'classe': produto_info['descricao'],
                        'confianca': 0.85,  # Menos confiável que detecção direta
                        'bbox': [x1, y1, x2, y2],
                        'codigo_barras': codigo,
                        'tipo_barcode': 'OCR',
                        'produto_completo': produto_info,
                        'validado': True
                    })
                    
        except Exception as e:
            print(f"❌ Erro OCR códigos: {e}")
        
        return produtos_encontrados
    
    def extrair_codigos_numericos(self, texto):
        """Extrai códigos numéricos válidos do texto"""
        codigos = []
        
        # Padrões para diferentes tipos de códigos
        padroes = [
            r'\b\d{13}\b',   # EAN-13
            r'\b\d{12}\b',   # UPC-A
            r'\b\d{8}\b',    # EAN-8
            r'\b\d{10,14}\b' # Outros códigos longos
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, texto)
            for match in matches:
                if len(match) >= 8:  # Códigos válidos têm pelo menos 8 dígitos
                    codigos.append(match)
        
        # Remover duplicatas
        return list(set(codigos))
    
    def obter_produto_por_codigo(self, codigo_barras):
        """Obtém produto por código - cache + busca + base conhecida"""
        # Verificar cache primeiro
        if codigo_barras in self.barcode_cache:
            return self.barcode_cache[codigo_barras]
        
        # Buscar usando método melhorado
        produto_info = self.buscar_produto_melhorado(codigo_barras)
        
        if produto_info:
            self.barcode_cache[codigo_barras] = produto_info
            print(f"🎯 Produto encontrado: {produto_info['descricao'][:30]}")
        
        return produto_info
    
    def buscar_produto_melhorado(self, codigo_barras):
        """Busca produto usando todas as fontes disponíveis"""
        # 1. Buscar no banco local primeiro (mais rápido)
        produto_local = self.buscar_produto_local(codigo_barras)
        if produto_local:
            return produto_local
        
        # 2. Buscar no OpenFoodFacts se habilitado
        if self.usar_openfoodfacts:
            produto_off = self.buscar_openfoodfacts(codigo_barras)
            if produto_off:
                return produto_off
        
        # 3. Fallback para base conhecida local
        return self.buscar_produto_online(codigo_barras)
    
    def buscar_produto_local(self, codigo_barras):
        """Busca no banco de dados local"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            
            queries = [
                "SELECT * FROM produtos WHERE descricao_produto LIKE ? OR descricao_produto = ?",
                "SELECT * FROM produtos WHERE id = ? OR descricao_produto LIKE ?"
            ]
            
            for query in queries:
                cursor.execute(query, (f"%{codigo_barras}%", codigo_barras))
                resultado = cursor.fetchone()
                
                if resultado:
                    cursor.execute("PRAGMA table_info(produtos)")
                    colunas = [col[1] for col in cursor.fetchall()]
                    
                    produto = {}
                    for i, valor in enumerate(resultado):
                        if i < len(colunas):
                            produto[colunas[i]] = valor
                    
                    produto_padronizado = {
                        'descricao': produto.get('descricao_produto', 'Produto Desconhecido'),
                        'categoria': produto.get('categoria', ''),
                        'marca': produto.get('marca', ''),
                        'id': produto.get('id', ''),
                        'codigo_barras': codigo_barras,
                        'fonte_busca': 'BANCO_LOCAL'
                    }
                    
                    conn.close()
                    return produto_padronizado
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Erro busca local: {e}")
            return None
    
    def buscar_produto_por_codigo(self, codigo_barras):
        """Busca produto no banco de dados pelo código de barras"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            
            # Tentar diferentes campos que podem conter código de barras
            queries = [
                "SELECT * FROM produtos WHERE descricao_produto LIKE ? OR descricao_produto = ?",
                "SELECT * FROM produtos WHERE id = ? OR descricao_produto LIKE ?"
            ]
            
            for query in queries:
                cursor.execute(query, (f"%{codigo_barras}%", codigo_barras))
                resultado = cursor.fetchone()
                
                if resultado:
                    # Verificar colunas disponíveis
                    cursor.execute("PRAGMA table_info(produtos)")
                    colunas = [col[1] for col in cursor.fetchall()]
                    
                    produto = {}
                    for i, valor in enumerate(resultado):
                        if i < len(colunas):
                            produto[colunas[i]] = valor
                    
                    # Padronizar campos
                    produto_padronizado = {
                        'descricao': produto.get('descricao_produto', 'Produto Desconhecido'),
                        'categoria': produto.get('categoria', ''),
                        'marca': produto.get('marca', ''),
                        'id': produto.get('id', ''),
                        'codigo_barras': codigo_barras,
                        'fonte_busca': 'BANCO_DADOS'
                    }
                    
                    conn.close()
                    return produto_padronizado
            
            # Se não encontrou no banco, tentar busca online (simulada)
            produto_online = self.buscar_produto_online(codigo_barras)
            conn.close()
            return produto_online
            
        except Exception as e:
            print(f"❌ Erro ao buscar produto por código: {e}")
            return None
    
    def buscar_openfoodfacts(self, codigo_barras):
        """Busca produto no OpenFoodFacts"""
        try:
            # Verificar cache primeiro
            if codigo_barras in self.openfoodfacts_cache:
                print(f"💾 OpenFoodFacts cache hit: {codigo_barras}")
                return self.openfoodfacts_cache[codigo_barras]
            
            # Buscar online
            url = f"https://world.openfoodfacts.org/api/v0/product/{codigo_barras}.json"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1:
                    produto = data['product']
                    
                    produto_padronizado = {
                        'descricao': produto.get('product_name', f'Produto {codigo_barras}'),
                        'marca': produto.get('brands', 'Marca Desconhecida'),
                        'categoria': produto.get('categories', 'Alimento'),
                        'ingredientes': produto.get('ingredients_text', ''),
                        'codigo_barras': codigo_barras,
                        'fonte_busca': 'OPENFOODFACTS',
                        'pais': produto.get('countries', ''),
                        'nutriscore': produto.get('nutriscore_grade', '')
                    }
                    
                    # Salvar no cache
                    self.openfoodfacts_cache[codigo_barras] = produto_padronizado
                    self.salvar_cache_openfoodfacts()
                    
                    print(f"🌍 OpenFoodFacts: {produto_padronizado['descricao'][:30]}")
                    return produto_padronizado
            
            return None
            
        except Exception as e:
            print(f"❌ Erro OpenFoodFacts: {e}")
            return None
    
    def buscar_produto_online(self, codigo_barras):
        """Simula busca online de produto por código de barras"""
        # Base de produtos conhecidos por código
        produtos_conhecidos = {
            '7891000100103': {'descricao': 'Coca-Cola 350ml', 'categoria': 'Refrigerante', 'marca': 'Coca-Cola'},
            '7891000053904': {'descricao': 'Pepsi Cola 350ml', 'categoria': 'Refrigerante', 'marca': 'PepsiCo'},
            '7891991010016': {'descricao': 'Guaraná Antarctica 350ml', 'categoria': 'Refrigerante', 'marca': 'Antarctica'},
            '7891149105342': {'descricao': 'Skol Lata 350ml', 'categoria': 'Cerveja', 'marca': 'Skol'},
            '7891991234567': {'descricao': 'Água Mineral Crystal 500ml', 'categoria': 'Água', 'marca': 'Crystal'}
        }
        
        # Busca por padrões conhecidos
        for codigo_conhecido, produto in produtos_conhecidos.items():
            if codigo_barras == codigo_conhecido or codigo_barras in codigo_conhecido:
                produto['codigo_barras'] = codigo_barras
                produto['fonte_busca'] = 'BASE_CONHECIDA'
                print(f"🌐 Produto encontrado na base conhecida: {produto['descricao']}")
                return produto
        
        # Se não encontrou, criar entrada genérica
        if len(codigo_barras) >= 8:  # Códigos válidos têm pelo menos 8 dígitos
            produto_generico = {
                'descricao': f'Produto Código {codigo_barras}',
                'categoria': 'Não Identificada',
                'marca': 'Desconhecida',
                'codigo_barras': codigo_barras,
                'fonte_busca': 'GENERICO'
            }
            print(f"❓ Produto genérico criado para código: {codigo_barras}")
            return produto_generico
        
        return None
    
    def extrair_texto_ocr(self, img_cv):
        """Extrai texto da imagem usando OCR"""
        try:
            # Converter para cinza
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Melhorar qualidade para OCR
            altura, largura = gray.shape
            if altura < 600:
                escala = 600 / altura
                nova_largura = int(largura * escala)
                gray = cv2.resize(gray, (nova_largura, 600))
            
            # Filtros para melhorar OCR
            gray = cv2.medianBlur(gray, 3)
            
            # OCR apenas em inglês para melhor performance
            texto = pytesseract.image_to_string(
                gray, 
                lang='eng', 
                config='--psm 6 --oem 3'
            )
            
            return texto.strip().upper()
            
        except Exception as e:
            print(f"❌ Erro OCR: {e}")
            return ""
    
    def reconhecer_produtos_por_ocr(self, texto_ocr, img_cv):
        """Reconhece produtos baseado no texto OCR e base treinada"""
        if not texto_ocr or not self.usar_base_treinada:
            return []
        
        produtos_encontrados = []
        altura_img, largura_img = img_cv.shape[:2]
        
        # Comparar com base de produtos treinados
        for produto in self.produtos_treinados:
            similaridade = self.calcular_similaridade_produto(texto_ocr, produto)
            
            if similaridade >= self.similaridade_texto_min:
                # Criar detecção OCR (bbox estimada)
                bbox_estimada = [largura_img//4, altura_img//4, 3*largura_img//4, 3*altura_img//4]
                
                produtos_encontrados.append({
                    'fonte': 'OCR+BASE',
                    'classe': produto['descricao'],
                    'confianca': similaridade,
                    'bbox': bbox_estimada,
                    'produto_completo': produto,
                    'texto_ocr': texto_ocr,
                    'validado': False
                })
                
                print(f"📚 OCR reconheceu: {produto['descricao'][:30]} (sim: {similaridade:.2f})")
        
        return produtos_encontrados
    
    def calcular_similaridade_produto(self, texto_ocr, produto):
        """Calcula similaridade entre texto OCR e produto da base"""
        score_total = 0
        comparacoes = 0
        
        # Comparar com descrição
        if produto['descricao']:
            score_desc = self.calcular_similaridade_texto(texto_ocr, produto['descricao'])
            score_total += score_desc * 0.4  # Peso 40%
            comparacoes += 1
        
        # Comparar com marca
        if produto['marca']:
            score_marca = self.calcular_similaridade_texto(texto_ocr, produto['marca'])
            score_total += score_marca * 0.3  # Peso 30%
            comparacoes += 1
        
        # Comparar com palavras-chave
        if produto['palavras_chave']:
            score_palavras = 0
            for palavra in produto['palavras_chave']:
                if palavra in texto_ocr:
                    score_palavras += 1
            
            if len(produto['palavras_chave']) > 0:
                score_palavras = score_palavras / len(produto['palavras_chave'])
                score_total += score_palavras * 0.3  # Peso 30%
                comparacoes += 1
        
        return score_total / max(comparacoes, 1)
    
    def calcular_similaridade_texto(self, texto1, texto2):
        """Calcula similaridade entre dois textos"""
        texto1 = texto1.upper().strip()
        texto2 = texto2.upper().strip()
        
        # Similaridade simples baseada em palavras comuns
        palavras1 = set(texto1.split())
        palavras2 = set(texto2.split())
        
        if not palavras1 or not palavras2:
            return 0
        
        intersecao = palavras1.intersection(palavras2)
        uniao = palavras1.union(palavras2)
        
        return len(intersecao) / len(uniao) if uniao else 0
    
    def processar_frame(self, frame_data):
        """Método de compatibilidade - redireciona para híbrido"""
        return self.processar_frame_hibrido(frame_data)
        try:
            # Converter para OpenCV
            nparr = np.frombuffer(frame_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            altura_frame, largura_frame = img_cv.shape[:2]
            
            # Detectar com YOLO
            results = self.modelo_yolo.predict(img_cv, conf=self.confianca_minima, verbose=False)
            
            if results and len(results) > 0:
                for r in results:
                    if r.boxes is not None:
                        for box in r.boxes:
                            # Extrair dados
                            xyxy = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            
                            if cls_id < len(self.modelo_yolo.names):
                                classe = self.modelo_yolo.names[cls_id]
                                x1, y1, x2, y2 = xyxy
                                
                                # VALIDAÇÃO INTELIGENTE BASEADA NO TIPO DE PRODUTO
                                valido, motivo_validacao = self.validar_objeto_inteligente(x1, y1, x2, y2, conf, classe, largura_frame, altura_frame)
                                
                                if valido:
                                    # Verificar se é detecção nova (evitar duplicatas)
                                    chave_deteccao = f"{classe}_{x1}_{y1}_{x2}_{y2}"
                                    tempo_atual = time.time()
                                    
                                    # Limpar detecções antigas (mais de 3 segundos)
                                    self.deteccoes_recentes = {k: v for k, v in self.deteccoes_recentes.items() 
                                                              if tempo_atual - v < 3.0}
                                    
                                    # Se é nova detecção ou já passou tempo suficiente
                                    if (chave_deteccao not in self.deteccoes_recentes or 
                                        tempo_atual - self.deteccoes_recentes[chave_deteccao] > 2.0):
                                        
                                        self.deteccoes_recentes[chave_deteccao] = tempo_atual
                                        
                                        # Calcular informações do objeto
                                        largura_obj = x2 - x1
                                        altura_obj = y2 - y1
                                        area_obj = largura_obj * altura_obj
                                        aspect_ratio = altura_obj / largura_obj if largura_obj > 0 else 0
                                        
                                        # Adicionar à lista se não existe produto similar recente
                                        if not self.produto_ja_detectado_recentemente(classe, x1, y1, x2, y2):
                                            tipo_produto = self.identificar_tipo_produto(classe)
                                            produto_info = {
                                                'id': f"{classe}_{int(tempo_atual)}",
                                                'classe': classe,
                                                'confianca': conf,
                                                'timestamp': tempo_atual,
                                                'status': 'DETECTADO',
                                                'bbox': [x1, y1, x2, y2],
                                                'area': area_obj,
                                                'aspect_ratio': aspect_ratio,
                                                'tipo_produto': tipo_produto,
                                                'validacao': motivo_validacao,
                                                'validado': True
                                            }
                                            self.produtos_detectados.append(produto_info)
                                            self.root.after(0, self.atualizar_lista_produtos)
                                            print(f"✅ Produto válido detectado: {classe} (área: {area_obj}px², conf: {conf:.2f})")
                                        
                                        # Desenhar detecção VÁLIDA (verde)
                                        cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 3)
                                        
                                        # Label detalhado com validação inteligente
                                        tipo_produto = self.identificar_tipo_produto(classe)
                                        label = f"{classe} ({conf:.2f}) ✅"
                                        info_label = f"{motivo_validacao} | {area_obj}px²"
                                        tipo_label = f"Tipo: {tipo_produto.replace('_', ' ').title()}"
                                        
                                        cv2.putText(img_cv, label, (x1, y1 - 50), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                        cv2.putText(img_cv, tipo_label, (x1, y1 - 30), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                                        cv2.putText(img_cv, info_label, (x1, y1 - 10), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                                        
                                else:
                                    # Desenhar detecção INVÁLIDA (vermelho)
                                    cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                    
                                    # Mostrar motivo da rejeição inteligente
                                    tipo_produto = self.identificar_tipo_produto(classe)
                                    label = f"{classe} - REJEITADO ❌"
                                    tipo_label = f"Esperado: {tipo_produto.replace('_', ' ').title()}"
                                    motivo_label = f"Motivo: {motivo_validacao}"
                                    
                                    cv2.putText(img_cv, label, (x1, y1 - 40), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                    cv2.putText(img_cv, tipo_label, (x1, y1 - 20), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                                    cv2.putText(img_cv, motivo_label, (x1, y1), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
            # Converter de volta para bytes
            _, buffer = cv2.imencode('.jpg', img_cv)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return frame_data
    
    def atualizar_display(self, frame_data):
        """Atualiza display de vídeo"""
        try:
            # Converter para PIL com dimensões responsivas
            image = Image.open(io.BytesIO(frame_data))
            
            # Calcular dimensões responsivas (mantendo proporção)
            original_width, original_height = image.size
            max_width = 800
            max_height = 600
            
            # Calcular proporção
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo
            
        except Exception as e:
            print(f"Erro no display: {e}")
    
    def atualizar_lista_produtos(self):
        """Atualiza lista de produtos"""
        # Limpar lista
        self.produtos_listbox.delete(0, tk.END)
        
        # Adicionar cabeçalho se houver produtos
        if self.produtos_detectados:
            self.produtos_listbox.insert(tk.END, "━━━ PRODUTOS DETECTADOS PELA IA ━━━")
            self.produtos_listbox.insert(tk.END, "")
        
        # Adicionar produtos
        for i, produto in enumerate(self.produtos_detectados):
            # Ícone baseado no status
            if produto['status'] == 'PASSOU':
                icone = "✅"
            elif produto['status'] == 'NAO_PASSOU':
                icone = "❌"
            else:
                icone = "🔍"
            
            # Informações detalhadas com fonte e aprendizado
            info_extra = ""
            if 'fonte' in produto:
                fonte_icon = "🧠" if produto['fonte'] == 'YOLO' else "📚" if produto['fonte'] == 'OCR+BASE' else "📱" if produto['fonte'] == 'BARCODE' else "🤖"
                info_extra += f" | {fonte_icon}{produto['fonte']}"
            
            # Mostrar código de barras se disponível
            if 'codigo_barras' in produto:
                info_extra += f" | 📱{produto['codigo_barras'][-6:]}"  # Últimos 6 dígitos
            
            if 'aprendizado' in produto:
                aprend_icon = "🌱" if produto['aprendizado'] == 'APRENDENDO' else "✅" if produto['aprendizado'] == 'COMPATÍVEL' else "⚠️"
                info_extra += f" | {aprend_icon}"
            
            # Mostrar se é da base treinada ou encontrado por código
            if 'produto_completo' in produto:
                if produto.get('fonte') == 'BARCODE':
                    info_extra += " | 🔍 DESCOBERTO"
                else:
                    info_extra += " | 🎯 TREINADO"
            
            item = f"{icone} {produto['classe'][:25]} - {produto['status']} ({produto['confianca']:.2f}){info_extra}"
            self.produtos_listbox.insert(tk.END, item)
        
        # Atualizar estatísticas
        total = len(self.produtos_detectados)
        self.stats_detectados.config(text=f"Detectados: {total}")
        self.stats_passou.config(text=f"Passaram: {self.produtos_passaram}")
        self.stats_nao_passou.config(text=f"Não Passaram: {self.produtos_nao_passaram}")
    
    def on_produto_select(self, event):
        """Quando produto é selecionado"""
        if self.produtos_listbox.curselection():
            self.btn_passou.config(state='normal')
            self.btn_nao_passou.config(state='normal')
        else:
            self.btn_passou.config(state='disabled')
            self.btn_nao_passou.config(state='disabled')
    
    def marcar_passou(self):
        """Marca produto como passou"""
        selection = self.produtos_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        produto = self.produtos_detectados[index]
        
        if produto['status'] != 'PASSOU':
            produto['status'] = 'PASSOU'
            if produto['status'] != 'PASSOU':  # Evitar dupla contagem
                self.produtos_passaram += 1
            
            self.atualizar_lista_produtos()
            messagebox.showinfo("Confirmado", f"Produto {produto['classe']} marcado como PASSOU")
            print(f"✅ {produto['classe']} marcado como PASSOU")
    
    def marcar_nao_passou(self):
        """Marca produto como não passou"""
        selection = self.produtos_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        produto = self.produtos_detectados[index]
        
        if produto['status'] != 'NAO_PASSOU':
            produto['status'] = 'NAO_PASSOU'
            self.produtos_nao_passaram += 1
            
            self.atualizar_lista_produtos()
            messagebox.showinfo("Marcado", f"Produto {produto['classe']} marcado como NÃO PASSOU")
            print(f"❌ {produto['classe']} marcado como NÃO PASSOU")
    
    def identificar_tipo_produto(self, classe_detectada):
        """Identifica tipo de produto baseado no nome da classe"""
        classe_lower = classe_detectada.lower()
        
        for tipo_produto, info in self.conhecimento_produtos.items():
            # Verificar se o nome da classe corresponde aos nomes alternativos
            for nome_alt in info['nomes_alternativos']:
                if nome_alt.lower() in classe_lower or classe_lower in nome_alt.lower():
                    return tipo_produto
        
        # Se não encontrou correspondência específica, usar produto genérico
        return 'produto_generico'
    
    def validar_objeto_inteligente(self, x1, y1, x2, y2, confianca, classe, largura_frame, altura_frame):
        """Valida objeto usando conhecimento da IA sobre tamanhos reais"""
        # Identificar tipo de produto
        tipo_produto = self.identificar_tipo_produto(classe)
        info_produto = self.conhecimento_produtos[tipo_produto]
        
        # Calcular dimensões
        largura_obj = x2 - x1
        altura_obj = y2 - y1
        area_obj = largura_obj * altura_obj
        
        print(f"🔍 Analisando {classe} como {tipo_produto}")
        
        # Verificar se está dentro dos limites da imagem
        if x1 < 0 or y1 < 0 or x2 > largura_frame or y2 > altura_frame:
            print(f"❌ {classe}: Fora dos limites da imagem")
            return False, "Fora dos limites"
        
        # Verificar confiança mínima
        if confianca < self.confianca_minima:
            print(f"❌ {classe}: Confiança muito baixa ({confianca:.2f})")
            return False, f"Confiança baixa: {confianca:.2f}"
        
        # Verificar área baseada no conhecimento do produto
        area_min = info_produto['area_min_pixels']
        area_max = info_produto['area_max_pixels']
        
        if area_obj < area_min:
            print(f"❌ {classe}: Muito pequeno para ser um {tipo_produto} real ({area_obj}px² < {area_min}px²)")
            return False, f"Muito pequeno: {area_obj}px²"
            
        if area_obj > area_max:
            print(f"❌ {classe}: Muito grande para ser um {tipo_produto} real ({area_obj}px² > {area_max}px²)")
            return False, f"Muito grande: {area_obj}px²"
        
        # Verificar proporção (aspect ratio) baseada no conhecimento do produto
        if largura_obj <= 0 or altura_obj <= 0:
            return False, "Dimensões inválidas"
            
        aspect_ratio_atual = altura_obj / largura_obj
        aspect_ratio_ideal = info_produto['aspect_ratio_ideal']
        tolerancia = info_produto['tolerancia_aspect']
        
        # Calcular faixa aceitável
        aspect_min = aspect_ratio_ideal * (1 - tolerancia)
        aspect_max = aspect_ratio_ideal * (1 + tolerancia)
        
        if aspect_ratio_atual < aspect_min or aspect_ratio_atual > aspect_max:
            print(f"❌ {classe}: Proporção incorreta para {tipo_produto} ({aspect_ratio_atual:.2f}, esperado: {aspect_ratio_ideal:.2f}±{tolerancia*100:.0f}%)")
            return False, f"Proporção incorreta: {aspect_ratio_atual:.2f}"
        
        # Verificar se não é muito pequeno em relação ao frame
        porcentagem_frame = (area_obj / (largura_frame * altura_frame)) * 100
        if porcentagem_frame < 0.05:  # Menor que 0.05% do frame
            print(f"❌ {classe}: Muito pequeno na imagem ({porcentagem_frame:.2f}% do frame)")
            return False, f"Muito pequeno no frame: {porcentagem_frame:.2f}%"
        
        if porcentagem_frame > 60:  # Maior que 60% do frame
            print(f"❌ {classe}: Ocupa muito espaço na imagem ({porcentagem_frame:.2f}% do frame)")
            return False, f"Muito grande no frame: {porcentagem_frame:.2f}%"
        
        print(f"✅ {classe}: Validado como {tipo_produto} real (área: {area_obj}px², prop: {aspect_ratio_atual:.2f}, {porcentagem_frame:.1f}% do frame)")
        return True, f"Válido como {tipo_produto}"
    
    def validar_objeto(self, x1, y1, x2, y2, confianca, largura_frame, altura_frame):
        """Método de compatibilidade - usa validação básica"""
        # Calcular dimensões
        largura_obj = x2 - x1
        altura_obj = y2 - y1
        area_obj = largura_obj * altura_obj
        
        # Verificar se está dentro dos limites da imagem
        if x1 < 0 or y1 < 0 or x2 > largura_frame or y2 > altura_frame:
            return False
        
        # Verificar tamanho mínimo e máximo
        if area_obj < self.tamanho_minimo or area_obj > self.tamanho_maximo:
            return False
        
        # Verificar proporção (aspect ratio)
        if largura_obj <= 0 or altura_obj <= 0:
            return False
            
        aspect_ratio = altura_obj / largura_obj
        if aspect_ratio < self.aspect_ratio_min or aspect_ratio > self.aspect_ratio_max:
            return False
        
        # Verificar confiança
        if confianca < self.confianca_minima:
            return False
        
        # Verificar se não é muito pequeno em relação ao frame
        porcentagem_frame = (area_obj / (largura_frame * altura_frame)) * 100
        if porcentagem_frame < 0.1 or porcentagem_frame > 50:  # Entre 0.1% e 50% do frame
            return False
        
        return True
    
    def obter_motivo_rejeicao(self, x1, y1, x2, y2, confianca, largura_frame, altura_frame):
        """Retorna motivo da rejeição do objeto"""
        largura_obj = x2 - x1
        altura_obj = y2 - y1
        area_obj = largura_obj * altura_obj
        
        if area_obj < self.tamanho_minimo:
            return f"Muito pequeno: {area_obj}px²"
        elif area_obj > self.tamanho_maximo:
            return f"Muito grande: {area_obj}px²"
        
        if largura_obj > 0:
            aspect_ratio = altura_obj / largura_obj
            if aspect_ratio < self.aspect_ratio_min:
                return f"Muito largo: {aspect_ratio:.2f}"
            elif aspect_ratio > self.aspect_ratio_max:
                return f"Muito alto: {aspect_ratio:.2f}"
        
        if confianca < self.confianca_minima:
            return f"Confiança baixa: {confianca:.2f}"
        
        porcentagem_frame = (area_obj / (largura_frame * altura_frame)) * 100
        if porcentagem_frame < 0.1:
            return f"Muito pequeno no frame: {porcentagem_frame:.1f}%"
        elif porcentagem_frame > 50:
            return f"Muito grande no frame: {porcentagem_frame:.1f}%"
        
        return "Fora dos limites"
    
    def produto_ja_detectado_recentemente(self, classe, x1, y1, x2, y2):
        """Verifica se produto similar já foi detectado recentemente"""
        tempo_atual = time.time()
        
        for produto in self.produtos_detectados:
            if produto['classe'] == classe and 'bbox' in produto:
                # Verificar se foi detectado nos últimos 5 segundos
                if tempo_atual - produto['timestamp'] < 5.0:
                    # Calcular sobreposição das bounding boxes
                    px1, py1, px2, py2 = produto['bbox']
                    
                    # Área de interseção
                    inter_x1 = max(x1, px1)
                    inter_y1 = max(y1, py1)
                    inter_x2 = min(x2, px2)
                    inter_y2 = min(y2, py2)
                    
                    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
                        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                        area_atual = (x2 - x1) * (y2 - y1)
                        area_produto = (px2 - px1) * (py2 - py1)
                        
                        # Se sobreposição é maior que 50%, considera como mesmo produto
                        overlap_ratio = inter_area / min(area_atual, area_produto)
                        if overlap_ratio > 0.5:
                            return True
        
        return False
    
    def combinar_deteccoes(self, deteccoes_yolo, produtos_ocr, produtos_barcode, img_cv):
        """Combina detecções de YOLO, OCR e BARCODE de forma inteligente"""
        deteccoes_combinadas = []
        altura, largura = img_cv.shape[:2]
        
        # Adicionar detecções YOLO validadas
        for det_yolo in deteccoes_yolo:
            x1, y1, x2, y2 = det_yolo['bbox']
            valido, motivo = self.validar_objeto_inteligente(x1, y1, x2, y2, 
                                                           det_yolo['confianca'], 
                                                           det_yolo['classe'], 
                                                           largura, altura)
            if valido:
                det_yolo['validado'] = True
                det_yolo['motivo_validacao'] = motivo
                deteccoes_combinadas.append(det_yolo)
        
        # Adicionar produtos OCR se não conflitarem com YOLO
        for prod_ocr in produtos_ocr:
            conflito = False
            for det_yolo in deteccoes_combinadas:
                if self.bbox_overlap(prod_ocr['bbox'], det_yolo['bbox']) > 0.3:
                    conflito = True
                    if det_yolo['confianca'] < 0.5 and prod_ocr['confianca'] > 0.8:
                        deteccoes_combinadas.remove(det_yolo)
                        conflito = False
                    break
            
            if not conflito:
                prod_ocr['validado'] = True
                deteccoes_combinadas.append(prod_ocr)
        
        # Adicionar produtos de código de barras (alta prioridade)
        for prod_barcode in produtos_barcode:
            # Códigos de barras têm prioridade sobre outras detecções
            conflito_resolvido = False
            
            # Verificar sobreposições e resolver conflitos
            for i, det_existente in enumerate(deteccoes_combinadas[:]):
                if self.bbox_overlap(prod_barcode['bbox'], det_existente['bbox']) > 0.2:
                    # Código de barras tem prioridade - substituir detecção existente
                    deteccoes_combinadas[i] = prod_barcode
                    conflito_resolvido = True
                    print(f"🔄 Substituindo {det_existente['fonte']} por BARCODE: {prod_barcode['classe'][:30]}")
                    break
            
            if not conflito_resolvido:
                deteccoes_combinadas.append(prod_barcode)
        
        return deteccoes_combinadas
    
    def bbox_overlap(self, bbox1, bbox2):
        """Calcula porcentagem de sobreposição entre duas bounding boxes"""
        x1a, y1a, x2a, y2a = bbox1
        x1b, y1b, x2b, y2b = bbox2
        
        # Calcular interseção
        x1i = max(x1a, x1b)
        y1i = max(y1a, y1b)
        x2i = min(x2a, x2b)
        y2i = min(y2a, y2b)
        
        if x1i >= x2i or y1i >= y2i:
            return 0
        
        area_intersecao = (x2i - x1i) * (y2i - y1i)
        area_bbox1 = (x2a - x1a) * (y2a - y1a)
        area_bbox2 = (x2b - x1b) * (y2b - y1b)
        
        area_uniao = area_bbox1 + area_bbox2 - area_intersecao
        
        return area_intersecao / area_uniao if area_uniao > 0 else 0
    
    def aplicar_mot(self, deteccoes, img_cv):
        """Aplica sistema MOT (Multi-Object Tracking) às detecções"""
        timestamp_atual = time.time()
        altura_img, largura_img = img_cv.shape[:2]
        
        # Definir zona de passagem se não existir
        if self.zona_passagem is None:
            self.definir_zona_passagem(largura_img, altura_img)
        
        # 1. ASSOCIAR DETECÇÕES COM TRACKS EXISTENTES
        deteccoes_associadas = []
        deteccoes_nao_associadas = deteccoes.copy()
        
        for track_id, tracker in list(self.produtos_rastreados.items()):
            melhor_deteccao = None
            menor_distancia = float('inf')
            
            for deteccao in deteccoes_nao_associadas:
                if tracker.compativel_com_deteccao(deteccao, self.max_distancia_tracking):
                    distancia = tracker.calcular_distancia(deteccao)
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        melhor_deteccao = deteccao
            
            if melhor_deteccao:
                # Associar detecção ao track existente
                tracker.adicionar_deteccao(melhor_deteccao, timestamp_atual)
                deteccoes_nao_associadas.remove(melhor_deteccao)
                
                # Adicionar informações de tracking
                melhor_deteccao['track_id'] = track_id
                melhor_deteccao['track_info'] = {
                    'uuid': tracker.uuid,
                    'tempo_vida': timestamp_atual - tracker.timestamp_criacao,
                    'velocidade': tracker.caracteristicas['velocidade_media'],
                    'direcao': tracker.caracteristicas['direcao_movimento'],
                    'passou_zona': tracker.passou_zona
                }
                
                deteccoes_associadas.append(melhor_deteccao)
                
                # Verificar passagem pela zona
                self.verificar_passagem_zona(tracker)
                
            else:
                # Track sem detecção - marcar como perdido
                tracker.marcar_perdido()
        
        # 2. CRIAR NOVOS TRACKS PARA DETECÇÕES NÃO ASSOCIADAS
        for deteccao in deteccoes_nao_associadas:
            if deteccao['confianca'] >= self.confianca_tracking_min:
                novo_track_id = self.proximo_track_id
                self.proximo_track_id += 1
                
                novo_tracker = ProductTracker(novo_track_id, deteccao, timestamp_atual)
                novo_tracker.cor_track = self.cores_tracking[novo_track_id % len(self.cores_tracking)]
                
                self.produtos_rastreados[novo_track_id] = novo_tracker
                
                # Adicionar informações de tracking
                deteccao['track_id'] = novo_track_id
                deteccao['track_info'] = {
                    'uuid': novo_tracker.uuid,
                    'tempo_vida': 0,
                    'velocidade': 0,
                    'direcao': None,
                    'passou_zona': False
                }
                
                deteccoes_associadas.append(deteccao)
                
                self.stats_mot['total_tracks'] += 1
                print(f"🆕 Novo track criado: ID {novo_track_id} para {deteccao['classe'][:20]}")
        
        # 3. REMOVER TRACKS PERDIDOS
        self.limpar_tracks_perdidos()
        
        # 4. ATUALIZAR ESTATÍSTICAS
        self.atualizar_estatisticas_mot()
        
        return deteccoes_associadas
    
    def definir_zona_passagem(self, largura, altura):
        """Define zona de passagem central da imagem"""
        margem_x = largura // 4
        margem_y = altura // 4
        
        self.zona_passagem = {
            'x1': margem_x,
            'y1': margem_y,
            'x2': largura - margem_x,
            'y2': altura - margem_y,
            'centro_x': largura // 2,
            'centro_y': altura // 2
        }
        
        print(f"🎯 Zona de passagem definida: {margem_x},{margem_y} -> {largura-margem_x},{altura-margem_y}")
    
    def verificar_passagem_zona(self, tracker):
        """Verifica se o produto passou pela zona de controle"""
        if not self.zona_passagem or tracker.passou_zona:
            return
        
        centro = tracker.centro_atual
        zona = self.zona_passagem
        
        # Verificar se está dentro da zona
        if (zona['x1'] <= centro[0] <= zona['x2'] and 
            zona['y1'] <= centro[1] <= zona['y2']):
            
            # Verificar se realmente atravessou (baseado no histórico)
            if len(tracker.historico_centros) >= 3:
                centros_anteriores = list(tracker.historico_centros)[-3:]
                
                # Verificar se veio de fora da zona
                veio_de_fora = any(
                    not (zona['x1'] <= c[0] <= zona['x2'] and zona['y1'] <= c[1] <= zona['y2'])
                    for c in centros_anteriores[:-1]
                )
                
                if veio_de_fora:
                    tracker.passou_zona = True
                    self.stats_mot['passagens_detectadas'] += 1
                    
                    # Registrar passagem
                    passagem_info = {
                        'timestamp': time.time(),
                        'track_id': tracker.track_id,
                        'classe': tracker.classe,
                        'uuid': tracker.uuid,
                        'fonte': tracker.fonte_deteccao,
                        'tempo_vida': time.time() - tracker.timestamp_criacao,
                        'centro': centro
                    }
                    
                    self.historico_rastreamento.append(passagem_info)
                    
                    print(f"🚪 PASSAGEM DETECTADA: {tracker.classe[:20]} (ID: {tracker.track_id})")
    
    def limpar_tracks_perdidos(self):
        """Remove tracks perdidos ou muito antigos"""
        tracks_para_remover = []
        
        for track_id, tracker in self.produtos_rastreados.items():
            if tracker.deve_ser_removido(self.frames_sem_deteccao_max, self.tempo_vida_track_max):
                tracks_para_remover.append(track_id)
                print(f"🗑️ Removendo track perdido: ID {track_id} ({tracker.classe[:20]})")
        
        for track_id in tracks_para_remover:
            del self.produtos_rastreados[track_id]
    
    def atualizar_estatisticas_mot(self):
        """Atualiza estatísticas do sistema MOT"""
        self.stats_mot['tracks_ativos'] = len(self.produtos_rastreados)
        
        produtos_identificados = set()
        for tracker in self.produtos_rastreados.values():
            produtos_identificados.add(tracker.classe)
        self.stats_mot['produtos_identificados'] = len(produtos_identificados)
    
    def aplicar_aprendizado_formatos(self, deteccoes, img_cv):
        """Aplica aprendizado de formatos aos produtos detectados"""
        deteccoes_aprendidas = []
        
        for det in deteccoes:
            classe = det['classe']
            x1, y1, x2, y2 = det['bbox']
            
            # Calcular características do formato
            largura_obj = x2 - x1
            altura_obj = y2 - y1
            area_obj = largura_obj * altura_obj
            aspect_ratio = altura_obj / largura_obj if largura_obj > 0 else 0
            
            formato_atual = {
                'area': area_obj,
                'aspect_ratio': aspect_ratio,
                'largura': largura_obj,
                'altura': altura_obj
            }
            
            # Verificar se formato é compatível com formatos aprendidos
            if classe in self.formatos_aprendidos:
                compativel = self.verificar_compatibilidade_formato(formato_atual, self.formatos_aprendidos[classe])
                if compativel:
                    det['aprendizado'] = 'COMPATÍVEL'
                    deteccoes_aprendidas.append(det)
                else:
                    det['aprendizado'] = 'INCOMPATÍVEL'
                    print(f"⚠️ {classe}: Formato não compatível com aprendizado")
            else:
                # Primeira vez vendo este produto - iniciar aprendizado
                self.formatos_aprendidos[classe] = [formato_atual]
                det['aprendizado'] = 'APRENDENDO'
                deteccoes_aprendidas.append(det)
                print(f"🌱 Iniciando aprendizado de formato para: {classe}")
            
            # Adicionar formato ao aprendizado se válido
            if det.get('validado', False) and classe not in self.formatos_aprendidos:
                self.formatos_aprendidos[classe] = []
            
            if det.get('validado', False) and len(self.formatos_aprendidos[classe]) < 10:
                self.formatos_aprendidos[classe].append(formato_atual)
        
        # Salvar aprendizado periodicamente
        if len(deteccoes_aprendidas) > 0:
            self.salvar_formatos_aprendidos()
        
        return deteccoes_aprendidas
    
    def verificar_compatibilidade_formato(self, formato_atual, formatos_aprendidos):
        """Verifica se formato atual é compatível com formatos aprendidos"""
        if not formatos_aprendidos:
            return True
        
        # Calcular médias dos formatos aprendidos
        areas = [f['area'] for f in formatos_aprendidos]
        aspect_ratios = [f['aspect_ratio'] for f in formatos_aprendidos]
        
        area_media = sum(areas) / len(areas)
        aspect_media = sum(aspect_ratios) / len(aspect_ratios)
        
        # Tolerâncias baseadas na variação dos dados aprendidos
        tolerancia_area = 0.5  # 50% de tolerância
        tolerancia_aspect = 0.3  # 30% de tolerância
        
        # Verificar se está dentro das tolerâncias
        area_ok = (area_media * (1 - tolerancia_area)) <= formato_atual['area'] <= (area_media * (1 + tolerancia_area))
        aspect_ok = (aspect_media * (1 - tolerancia_aspect)) <= formato_atual['aspect_ratio'] <= (aspect_media * (1 + tolerancia_aspect))
        
        return area_ok and aspect_ok
    
    def desenhar_deteccoes_hibridas(self, img_cv, deteccoes):
        """Desenha detecções com informações da fonte + MOT (YOLO/OCR/BARCODE/Tracking)"""
        img_resultado = img_cv.copy()
        
        # Desenhar zona de passagem
        if self.zona_passagem:
            zona = self.zona_passagem
            cv2.rectangle(img_resultado, 
                         (zona['x1'], zona['y1']), 
                         (zona['x2'], zona['y2']), 
                         (0, 255, 255), 2)  # Amarelo
            cv2.putText(img_resultado, "ZONA CONTROLE", 
                       (zona['x1'], zona['y1'] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        for det in deteccoes:
            x1, y1, x2, y2 = det['bbox']
            fonte = det['fonte']
            classe = det['classe']
            confianca = det['confianca']
            
            # Cor baseada no tracking (se disponível) ou fonte
            if 'track_id' in det and det['track_id'] in self.produtos_rastreados:
                tracker = self.produtos_rastreados[det['track_id']]
                cor = tracker.cor_track
                espessura = 3  # Mais grosso para produtos rastreados
            else:
                # Cor baseada na fonte para produtos não rastreados
                if fonte == 'YOLO':
                    cor = (0, 255, 0)  # Verde para YOLO
                elif fonte == 'OCR+BASE':
                    cor = (255, 0, 0)  # Azul para OCR
                elif fonte == 'OCR+MARCA':
                    cor = (255, 100, 0)  # Azul escuro para marca
                elif fonte == 'BARCODE':
                    cor = (0, 165, 255)  # Laranja para código de barras
                else:
                    cor = (0, 255, 255)  # Amarelo para outros
                espessura = 2
            
            # Desenhar retângulo
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, espessura)
            
            # Desenhar trajeto do tracking (se disponível)
            if 'track_id' in det and det['track_id'] in self.produtos_rastreados:
                tracker = self.produtos_rastreados[det['track_id']]
                
                # Desenhar trilha de movimento
                if len(tracker.historico_centros) > 1:
                    pontos = list(tracker.historico_centros)
                    for i in range(1, len(pontos)):
                        cv2.line(img_resultado, pontos[i-1], pontos[i], cor, 2)
                    
                    # Desenhar círculo no centro atual
                    cv2.circle(img_resultado, tracker.centro_atual, 8, cor, -1)
                
                # Indicador de passagem
                if tracker.passou_zona:
                    cv2.circle(img_resultado, (x2-15, y1+15), 10, (0, 255, 0), -1)  # Verde
                    cv2.putText(img_resultado, "✓", (x2-20, y1+20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Labels com informações completas incluindo tracking
            if 'track_id' in det:
                track_info = det.get('track_info', {})
                label_principal = f"ID:{det['track_id']} {classe[:15]} ({confianca:.2f})"
                label_fonte = f"Fonte: {fonte} | Tempo: {track_info.get('tempo_vida', 0):.1f}s"
                
                # Label de velocidade e direção
                label_tracking = ""
                if track_info.get('velocidade', 0) > 0:
                    label_tracking = f"Vel: {track_info['velocidade']:.1f}px/f"
                    if track_info.get('direcao'):
                        label_tracking += f" | {track_info['direcao'][:4]}"
            else:
                label_principal = f"{classe[:20]} ({confianca:.2f})"
                label_fonte = f"Fonte: {fonte}"
                label_tracking = ""
            
            # Label de código de barras se disponível
            label_barcode = ""
            if 'codigo_barras' in det:
                label_barcode = f"Código: {det['codigo_barras'][-8:]}"  # Últimos 8 dígitos
            
            # Label de aprendizado se disponível
            label_aprendizado = ""
            if 'aprendizado' in det:
                label_aprendizado = f"Aprend: {det['aprendizado']}"
            
            # Desenhar labels com fundo semi-transparente
            y_offset = y1 - 80
            
            # Label principal
            cv2.putText(img_resultado, label_principal, (x1, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
            
            y_offset += 20
            cv2.putText(img_resultado, label_fonte, (x1, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor, 1)
            
            # Label de tracking
            if label_tracking:
                y_offset += 15
                cv2.putText(img_resultado, label_tracking, (x1, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor, 1)
            
            if label_barcode:
                y_offset += 15
                cv2.putText(img_resultado, label_barcode, (x1, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor, 1)
            
            if label_aprendizado:
                y_offset += 15
                cv2.putText(img_resultado, label_aprendizado, (x1, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor, 1)
        
        # Desenhar estatísticas MOT no canto da imagem
        if self.mot_ativo:
            self.desenhar_estatisticas_mot(img_resultado)
        
        return img_resultado
    
    def desenhar_estatisticas_mot(self, img):
        """Desenha estatísticas do sistema MOT na imagem"""
        altura_img = img.shape[0]
        
        # Fundo semi-transparente para estatísticas
        overlay = img.copy()
        cv2.rectangle(overlay, (10, altura_img-120), (300, altura_img-10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Estatísticas
        stats_text = [
            f"MOT Stats:",
            f"Tracks Ativos: {self.stats_mot['tracks_ativos']}",
            f"Total Tracks: {self.stats_mot['total_tracks']}",
            f"Passagens: {self.stats_mot['passagens_detectadas']}",
            f"Produtos ID: {self.stats_mot['produtos_identificados']}"
        ]
        
        for i, text in enumerate(stats_text):
            y_pos = altura_img - 100 + (i * 20)
            cor_text = (0, 255, 255) if i == 0 else (255, 255, 255)
            cv2.putText(img, text, (15, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor_text, 1)
        
        return img_resultado
    
    def atualizar_produtos_detectados(self, deteccoes):
        """Atualiza lista de produtos com detecções híbridas"""
        for det in deteccoes:
            # Evitar duplicatas recentes
            produto_similar = self.buscar_produto_similar(det)
            if not produto_similar:
                tempo_atual = time.time()
                produto_info = {
                    'id': f"{det['classe'][:10]}_{int(tempo_atual)}",
                    'classe': det['classe'],
                    'confianca': det['confianca'],
                    'timestamp': tempo_atual,
                    'status': 'DETECTADO',
                    'bbox': det['bbox'],
                    'fonte': det['fonte'],
                    'validado': det.get('validado', False)
                }
                
                # Adicionar informações extras se disponível
                if 'produto_completo' in det:
                    produto_info['produto_completo'] = det['produto_completo']
                if 'aprendizado' in det:
                    produto_info['aprendizado'] = det['aprendizado']
                if 'codigo_barras' in det:
                    produto_info['codigo_barras'] = det['codigo_barras']
                if 'tipo_barcode' in det:
                    produto_info['tipo_barcode'] = det['tipo_barcode']
                if 'track_id' in det:
                    produto_info['track_id'] = det['track_id']
                    produto_info['track_info'] = det.get('track_info', {})
                if 'marca_detectada' in det:
                    produto_info['marca_detectada'] = det['marca_detectada']
                
                self.produtos_detectados.append(produto_info)
                self.root.after(0, self.atualizar_lista_produtos)
                
                print(f"✅ Produto adicionado: {det['classe'][:30]} (Fonte: {det['fonte']})")
    
    def buscar_produto_similar(self, deteccao):
        """Busca produto similar na lista recente"""
        tempo_atual = time.time()
        classe = deteccao['classe']
        
        for produto in self.produtos_detectados:
            if (produto['classe'] == classe and 
                tempo_atual - produto['timestamp'] < 3.0):  # 3 segundos
                return produto
        
        return None
    
    def atualizar_config(self):
        """Atualiza configurações de validação"""
        try:
            self.tamanho_minimo = int(self.size_var.get())
            self.confianca_minima = float(self.conf_var.get())
            
            self.status_label.config(text=f"✅ IA Configurada: Tamanho≥{self.tamanho_minimo}px² | Confiança≥{self.confianca_minima}")
            # Flash visual de confirmação
            self.root.after(3000, lambda: self.status_label.config(text="🧠 IA Ativa e Configurada"))
            print(f"✅ Configurações atualizadas: Tamanho mín: {self.tamanho_minimo}px², Confiança: {self.confianca_minima}")
            
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos nas configurações")
    
    def atualizar_sistema_hibrido(self):
        """Atualiza configurações do sistema híbrido"""
        self.usar_yolo = self.var_yolo.get()
        self.usar_ocr = self.var_ocr.get()
        self.usar_aprendizado = self.var_aprendizado.get()
        self.usar_barcode = self.var_barcode.get()
        
        # Atualizar informações
        if hasattr(self, 'info_base'):
            total_cache = len(self.barcode_cache) if hasattr(self, 'barcode_cache') else 0
            self.info_base.config(text=f"Base: {len(self.produtos_treinados)}+{total_cache} produtos")
        
        if hasattr(self, 'info_aprendizado'):
            self.info_aprendizado.config(text=f"Formatos: {len(self.formatos_aprendidos)}")
        
        sistemas_ativos = []
        if self.usar_yolo: sistemas_ativos.append("YOLO")
        if self.usar_ocr: sistemas_ativos.append("OCR")
        if self.usar_barcode: sistemas_ativos.append("BARCODE")
        if self.usar_aprendizado: sistemas_ativos.append("APREND")
        
        self.status_label.config(text=f"🤖 Híbrido: {'+'.join(sistemas_ativos)}")
        print(f"🤖 Sistema híbrido atualizado: {', '.join(sistemas_ativos)}")
    
    def teste_foto(self):
        """Testa captura de foto"""
        try:
            response = requests.get(self.snapshot_url, auth=self.auth, timeout=5)
            if response.status_code == 200:
                # Salvar foto de teste
                filename = f"teste_foto_{int(time.time())}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                messagebox.showinfo("Sucesso", f"Foto teste salva: {filename}")
                print(f"📸 Foto teste salva: {filename}")
            else:
                messagebox.showerror("Erro", f"Erro ao capturar: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na captura: {e}")

if __name__ == "__main__":
    import io
    root = tk.Tk()
    app = VerifiKTesteProdutos(root)
    root.mainloop()