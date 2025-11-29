#!/usr/bin/env python3
"""
VerifiK - Streaming Básico com Detecção Simples
Versão simplificada sem OpenCV, usando apenas PIL para processamento
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import sqlite3
from datetime import datetime
import os
import io
import threading
import time
import re
import base64
from collections import Counter
import math

# Tentar importar OCR
try:
    import pytesseract
    # Configurar Tesseract se disponível
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_DISPONIVEL = True
except ImportError:
    OCR_DISPONIVEL = False
    print("⚠️ OCR não disponível - instale pytesseract para reconhecimento de texto")

class VerifiKStreamingBasico:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Streaming com Detecção Básica")
        self.root.geometry("1200x800")
        
    def criar_tooltip(self, widget, texto):
        """Cria tooltip explicativo para um widget"""
        def mostrar_tooltip(event):
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=texto, justify='left',
                           background="#ffffe0", relief='solid', borderwidth=1,
                           font=("tahoma", "8", "normal"))
            label.pack()
            
        def esconder_tooltip(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', mostrar_tooltip)
        widget.bind('<Leave>', esconder_tooltip)
        
        # Configuração da câmera  
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # URLs de captura otimizadas (baseado na API)
        self.snapshot_urls = [
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi",                     # URL principal que funciona
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi?subtype=0",          # Alta resolução 
            f"http://{self.camera_ip}/cgi-bin/snapshot.cgi?subtype=1",          # Resolução média
            f"http://{self.camera_ip}/cgi-bin/mjpeg?channel=0&subtype=1"        # MJPEG alternativo
        ]
        
        # Variáveis de controle
        self.streaming = False
        self.deteccao_ativa = False
        self.current_frame = None
        self.produtos_detectados = []
        self.produtos_database = []
        
        # Controles de performance
        self.frame_skip_counter = 0
        self.max_frame_skip = 2  # Analisar 1 a cada 3 frames
        self.ultimo_tempo_analise = 0
        self.intervalo_analise_minimo = 1.5  # Mínimo 1.5s entre análises completas
        self.analisando_frame = False
        
        # Feedback para usuário
        self.tempo_ultima_deteccao = 0
        self.tempo_ultimo_feedback = 0
        self.produtos_detectados_sessao = set()
        self.tentativas_deteccao = 0
        
        # APIs da câmera
        self.usar_deteccao_movimento = True
        self.qualidade_adaptativa = True
        
        # Controle de foco automático inteligente
        self.foco_automatico = True
        self.foco_atual = 5000  # Valor médio (0-8191)
        self.foco_para_barcode = 6500  # Foco otimizado para códigos de barras
        self.ultimo_ajuste_foco = 0
        self.tentativas_foco = 0
        self.historico_qualidade = []  # Histórico da qualidade de códigos
        self.foco_otimo_encontrado = False
        self.melhor_foco = 6500
        self.modo_busca_foco = False
        
        # Padrões avançados de produtos para reconhecimento detalhado
        self.padroes_produtos = {
            'CERVEJA': {
                'cores_predominantes': [(255, 215, 0), (255, 140, 0), (34, 139, 34), (139, 69, 19)],  # Dourado, laranja, verde, marrom
                'cores_secundarias': [(255, 255, 255), (0, 0, 0), (255, 255, 0)],  # Branco, preto, amarelo
                'formatos': ['vertical', 'cilindrico', 'garrafa'],
                'textos_esperados': ['CERVEJA', 'BEER', 'LAGER', 'PILSEN', 'ALE', 'HEINEKEN', 'BUDWEISER', 'STELLA', 'AMSTEL'],
                'padroes_rotulo': ['circular', 'oval', 'retangular_vertical'],
                'codigo_barras_prefixos': ['789', '780', '775'],  # Prefixos comuns para bebidas no Brasil
                'aspect_ratio_range': (2.0, 4.5),  # Altura/largura típica de garrafas
                'area_minima': 1000  # Pixels mínimos
            },
            'REFRIGERANTE': {
                'cores_predominantes': [(255, 0, 0), (0, 100, 0), (0, 0, 255), (255, 165, 0)],  # Vermelho, verde, azul, laranja
                'cores_secundarias': [(255, 255, 255), (0, 0, 0), (255, 255, 0)],
                'formatos': ['vertical', 'cilindrico', 'lata', 'garrafa'],
                'textos_esperados': ['COCA', 'PEPSI', 'GUARANA', 'FANTA', 'SPRITE', 'REFRIGERANTE', 'SODA'],
                'padroes_rotulo': ['circular', 'wave', 'retangular_horizontal'],
                'codigo_barras_prefixos': ['789', '780', '775'],
                'aspect_ratio_range': (1.5, 3.0),
                'area_minima': 800
            },
            'AGUA': {
                'cores_predominantes': [(135, 206, 235), (255, 255, 255), (0, 191, 255), (173, 216, 230)],  # Azul claro, branco, azul
                'cores_secundarias': [(0, 100, 200), (100, 149, 237)],
                'formatos': ['vertical', 'garrafa'],
                'textos_esperados': ['AGUA', 'WATER', 'CRYSTAL', 'BONAFONT', 'NESTLE', 'PUREZA'],
                'padroes_rotulo': ['circular', 'oval', 'minimalista'],
                'codigo_barras_prefixos': ['789', '780'],
                'aspect_ratio_range': (2.5, 4.0),
                'area_minima': 600
            },
            'ENERGETICO': {
                'cores_predominantes': [(255, 0, 0), (0, 0, 0), (255, 215, 0), (128, 0, 128)],  # Vermelho, preto, dourado, roxo
                'cores_secundarias': [(255, 255, 255), (0, 255, 0)],
                'formatos': ['vertical', 'lata_fina'],
                'textos_esperados': ['RED BULL', 'MONSTER', 'ENERGETICO', 'ENERGY', 'BURN'],
                'padroes_rotulo': ['agressivo', 'metalico', 'neon'],
                'codigo_barras_prefixos': ['789', '780'],
                'aspect_ratio_range': (2.8, 3.5),
                'area_minima': 500
            }
        }
        
        # Banco de códigos de barras conhecidos (simulado)
        self.codigos_barras_conhecidos = {
            '7891234567890': {'produto': 'CERVEJA HEINEKEN 350ML', 'categoria': 'CERVEJA'},
            '7891234567891': {'produto': 'COCA-COLA 350ML', 'categoria': 'REFRIGERANTE'},
            '7891234567892': {'produto': 'AGUA CRYSTAL 500ML', 'categoria': 'AGUA'}
        }
        
        # Estatísticas
        self.total_frames = 0
        self.fps_atual = 0
        self.last_fps_time = time.time()
        
        # Interface
        self.setup_interface()
        self.carregar_produtos_database()
        
        # Iniciar sistema
        # Inicializar timestamp da sessão
        self.tempo_inicio_sessao = time.time()
        
        # Inicializar timestamp da sessão
        self.tempo_inicio_sessao = time.time()
        
        self.root.after(1000, self.iniciar_streaming)
    
    def setup_interface(self):
        """Interface simplificada mas funcional"""
        
        # Header
        header = ttk.LabelFrame(self.root, text="📹 VerifiK - Streaming + Detecção Básica", padding="10")
        header.pack(fill='x', padx=10, pady=5)
        
        # Info linha superior
        info_top = ttk.Frame(header)
        info_top.pack(fill='x')
        
        ttk.Label(info_top, text=f"📷 Câmera: {self.camera_ip}", font=('Arial', 9)).pack(side='left', padx=(0, 15))
        
        self.status_conexao = ttk.Label(info_top, text="🔴 Conectando...", font=('Arial', 9, 'bold'))
        self.status_conexao.pack(side='left', padx=(0, 15))
        
        self.status_deteccao = ttk.Label(info_top, text="🤖 Detecção: Inativa", font=('Arial', 9))
        self.status_deteccao.pack(side='left', padx=(0, 15))
        
        self.fps_label = ttk.Label(info_top, text="FPS: 0", font=('Arial', 9))
        self.fps_label.pack(side='right')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Lado esquerdo - Streaming
        left_panel = ttk.LabelFrame(main_frame, text="📺 Visualização", padding="10")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Área da imagem (maior)
        self.image_label = ttk.Label(
            left_panel,
            text="📹\n\nIniciando Sistema...\nConectando à câmera...",
            justify=tk.CENTER,
            font=('Arial', 14),
            background='black',
            foreground='white'
        )
        self.image_label.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Controles
        controls = ttk.Frame(left_panel)
        controls.pack(fill='x', pady=(10, 0))
        
        # Primeira linha
        controls_top = ttk.Frame(controls)
        controls_top.pack(fill='x', pady=(0, 5))
        
        self.btn_stream = ttk.Button(controls_top, text="▶️ Stream", command=self.toggle_streaming)
        self.btn_stream.pack(side='left', padx=(0, 10))
        
        self.btn_deteccao = ttk.Button(controls_top, text="🤖 Detecção", command=self.toggle_deteccao)
        self.btn_deteccao.pack(side='left', padx=(0, 10))
        
        ttk.Button(controls_top, text="📸 Capturar", command=self.capturar_frame).pack(side='left', padx=(0, 10))
        
        ttk.Button(controls_top, text="🔍 Analisar Frame", command=self.analisar_frame_atual).pack(side='left')
        
        # Segunda linha - configurações
        controls_bottom = ttk.Frame(controls)
        controls_bottom.pack(fill='x')
        
        ttk.Label(controls_bottom, text="Sensibilidade:").pack(side='left', padx=(0, 5))
        
        self.sensibilidade_var = tk.DoubleVar(value=0.3)
        sensibilidade_scale = ttk.Scale(
            controls_bottom,
            from_=0.1,
            to=0.9,
            variable=self.sensibilidade_var,
            length=120
        )
        sensibilidade_scale.pack(side='left', padx=(0, 10))
        
        self.sensibilidade_label = ttk.Label(controls_bottom, text="30%")
        self.sensibilidade_label.pack(side='left', padx=(0, 15))
        
        # Opções de análise
        self.auto_analise_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls_bottom, text="Auto", variable=self.auto_analise_var).pack(side='left', padx=(0, 10))
        
        self.ocr_var = tk.BooleanVar(value=OCR_DISPONIVEL)
        ttk.Checkbutton(controls_bottom, text="OCR", variable=self.ocr_var).pack(side='left', padx=(0, 10))
        
        self.barcode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_bottom, text="Código Barras", variable=self.barcode_var).pack(side='left', padx=(0, 10))
        
        self.forma_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_bottom, text="Formas", variable=self.forma_var).pack(side='left')
        
        # Controles de foco automático
        ttk.Separator(controls_bottom, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Label(controls_bottom, text="Foco Auto:").pack(side='left', padx=(5, 5))
        
        # Botões de foco com tooltips
        self.btn_foco_auto = ttk.Button(controls_bottom, text="🤖", width=3,
                  command=self.ativar_foco_automatico_inteligente)
        self.btn_foco_auto.pack(side='left')
        self.criar_tooltip(self.btn_foco_auto, "Foco Automático Inteligente\nAjusta automaticamente para códigos de barras")
        
        self.btn_teste_manual = ttk.Button(controls_bottom, text="🔧", width=3,
                  command=self.testar_foco_manual)
        self.btn_teste_manual.pack(side='left')
        self.criar_tooltip(self.btn_teste_manual, "Teste Manual do Foco\nTesta diferentes valores de foco")
        
        self.btn_reset_foco = ttk.Button(controls_bottom, text="🔄", width=3,
                  command=self.resetar_aprendizado_foco)
        self.btn_reset_foco.pack(side='left')
        self.criar_tooltip(self.btn_reset_foco, "Reset do Aprendizado\nReinicia o sistema de foco inteligente")
        
        # Lado direito - Resultados
        right_panel = ttk.LabelFrame(main_frame, text="🎯 Detecções e Produtos", padding="10")
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        
        # Notebook para organizar
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True)
        
        # Aba 1: Análise atual
        analise_frame = ttk.Frame(notebook)
        notebook.add(analise_frame, text="🔍 Análise")
        
        ttk.Label(analise_frame, text="Última Análise:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Text widget para análise
        self.analise_text = tk.Text(analise_frame, height=15, width=35, font=('Arial', 9))
        scroll_analise = ttk.Scrollbar(analise_frame, command=self.analise_text.yview)
        
        self.analise_text.pack(side='left', fill='both', expand=True)
        scroll_analise.pack(side='right', fill='y')
        self.analise_text.config(yscrollcommand=scroll_analise.set)
        
        # Aba 2: Produtos confirmados
        produtos_frame = ttk.Frame(notebook)
        notebook.add(produtos_frame, text="✅ Produtos")
        
        # Lista de produtos detectados
        self.produtos_listbox = tk.Listbox(produtos_frame, font=('Arial', 9))
        scroll_produtos = ttk.Scrollbar(produtos_frame, command=self.produtos_listbox.yview)
        
        self.produtos_listbox.pack(side='left', fill='both', expand=True)
        scroll_produtos.pack(side='right', fill='y')
        self.produtos_listbox.config(yscrollcommand=scroll_produtos.set)
        
        # Aba 3: Database
        database_frame = ttk.Frame(notebook)
        notebook.add(database_frame, text="📦 Database")
        
        # Lista da base
        self.database_listbox = tk.Listbox(database_frame, font=('Arial', 9))
        scroll_db = ttk.Scrollbar(database_frame, command=self.database_listbox.yview)
        
        self.database_listbox.pack(side='left', fill='both', expand=True)
        scroll_db.pack(side='right', fill='y')
        self.database_listbox.config(yscrollcommand=scroll_db.set)
        
        # Footer - Status
        footer = ttk.LabelFrame(self.root, text="📊 Status", padding="10")
        footer.pack(fill='x', padx=10, pady=(5, 10))
        
        self.status_principal = ttk.Label(footer, text="Iniciando sistema...", font=('Arial', 10))
        self.status_principal.pack(side='left')
        
        # Stats
        stats_frame = ttk.Frame(footer)
        stats_frame.pack(side='right')
        
        self.stats_frames = ttk.Label(stats_frame, text="Frames: 0", font=('Arial', 9))
        self.stats_frames.pack(side='left', padx=(0, 15))
        
        self.stats_deteccoes = ttk.Label(stats_frame, text="Produtos: 0", font=('Arial', 9))
        self.stats_deteccoes.pack(side='left')
    
    def carregar_produtos_database(self):
        """Carrega produtos da base"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT descricao_produto FROM produtos WHERE ativo = 1 ORDER BY descricao_produto")
            self.produtos_database = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Preencher lista
            for produto in self.produtos_database:
                self.database_listbox.insert(tk.END, produto)
            
            print(f"✅ {len(self.produtos_database)} produtos na base")
            
        except Exception as e:
            print(f"❌ Erro produtos: {e}")
    
    def iniciar_streaming(self):
        """Inicia streaming"""
        if self.streaming:
            return
        
        # Testar conexão primeiro
        print("🔍 Testando conexão com câmera antes de iniciar stream...")
        if not self.testar_conexao_inicial():
            self.status_conexao.config(text="❌ Câmera inacessível")
            return
        
        self.streaming = True
        self.status_conexao.config(text="🟡 Conectando...")
        self.btn_stream.config(text="⏸️ Pausar")
        print("✅ Iniciando streaming...")
        
        def stream_thread():
            while self.streaming:
                try:
                    # Capturar frame
                    frame_data = self.capturar_frame_camera()
                    
                    if frame_data:
                        # Análise otimizada - apenas quando necessário
                        if self.deteccao_ativa and self.auto_analise_var.get():
                            self.frame_skip_counter += 1
                            tempo_atual = time.time()
                            
                            # Só analisar se passou o intervalo e não está analisando
                            if (not self.analisando_frame and 
                                tempo_atual - self.ultimo_tempo_analise > self.intervalo_analise_minimo and
                                self.frame_skip_counter > self.max_frame_skip):
                                
                                self.processar_frame_deteccao_rapido(frame_data)
                                self.frame_skip_counter = 0
                                self.ultimo_tempo_analise = tempo_atual
                        
                        # Atualizar display
                        self.root.after(0, self.atualizar_display, frame_data)
                        
                        # FPS
                        self.total_frames += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            self.fps_atual = self.total_frames / (current_time - self.last_fps_time)
                            self.root.after(0, lambda: self.fps_label.config(text=f"FPS: {self.fps_atual:.1f}"))
                            self.total_frames = 0
                            self.last_fps_time = current_time
                        
                        self.root.after(0, lambda: self.status_conexao.config(text="🟢 Ativo"))
                    
                    else:
                        self.root.after(0, lambda: self.status_conexao.config(text="🔴 Erro"))
                        time.sleep(2)
                    
                    time.sleep(0.2)  # ~5 FPS otimizado
                    
                except Exception as e:
                    print(f"Erro stream: {e}")
                    time.sleep(3)
        
        thread = threading.Thread(target=stream_thread, daemon=True)
        thread.start()
    
    def testar_conexao_inicial(self):
        """Testa conexão inicial com a câmera"""
        try:
            print(f"📡 Testando câmera em {self.camera_ip}...")
            
            # Teste básico de conectividade
            url_teste = f"http://{self.camera_ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
            response = requests.get(url_teste, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Câmera conectada: {response.text.strip()}")
                
                # Testar URL de snapshot
                url_snapshot = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
                resp = requests.get(url_snapshot, auth=self.auth, timeout=3)
                
                if resp.status_code == 200 and len(resp.content) > 5000:
                    print("✅ Snapshot funcionando")
                    return True
                else:
                    print(f"❌ Snapshot falhou: {resp.status_code}")
                    return False
            else:
                print(f"❌ Câmera inacessível: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"💥 Erro de conexão: {e}")
            return False

    def capturar_frame_camera(self):
        """Captura frame da câmera"""
        for i, url in enumerate(self.snapshot_urls):
            try:
                response = requests.get(url, auth=self.auth, timeout=3)
                
                if response.status_code == 200 and len(response.content) > 5000:
                    # Log apenas na primeira captura ou mudança de URL
                    if not hasattr(self, 'url_funcionando') or self.url_funcionando != i:
                        print(f"✅ Usando URL {i+1}: {url}")
                        self.url_funcionando = i
                    return response.content
                    
            except Exception as e:
                if i == 0:  # Log erro apenas na primeira URL
                    print(f"⚠️ Erro URL {i+1}: {e}")
                continue
        
        # Se chegou aqui, nenhuma URL funcionou
        print("❌ Todas as URLs falharam")
        return None
    
    def ajustar_foco_camera(self, valor_foco):
        """Ajusta o foco da câmera para melhor leitura de códigos de barras"""
        try:
            diferenca = abs(valor_foco - (self.foco_atual or 6000))
            print(f"🎯 FOCO: {self.foco_atual or 'AUTO'} → {valor_foco} (Δ={diferenca})")
            
            # API para ajustar foco manual
            url = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusMode=1"
            
            response = requests.get(url, auth=self.auth, timeout=5)
            
            if response.status_code == 200 and "OK" in response.text:
                # Definir valor do foco (0-8191)
                url_foco = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusRect.Value={valor_foco}"
                
                response_foco = requests.get(url_foco, auth=self.auth, timeout=5)
                
                if response_foco.status_code == 200 and "OK" in response_foco.text:
                    self.foco_atual = valor_foco
                    print(f"✅ FOCO APLICADO: {valor_foco} {'🔍' if diferenca > 500 else '🎯'}")
                    
                    # Aguardar câmera processar mudança
                    if diferenca > 500:
                        time.sleep(1.5)
                    else:
                        time.sleep(0.5)
                    
                    return True
                else:
                    print(f"❌ FOCO REJEITADO: {response_foco.text.strip()}")
            else:
                print(f"❌ MODO MANUAL FALHOU: {response.text.strip()}")
            
            return False
        except Exception as e:
            print(f"💥 ERRO FOCO: {e}")
            return False
    
    def detectar_codigo_barras_area(self, image):
        """Detecta áreas com possíveis códigos de barras na imagem"""
        try:
            # Converter para escala de cinza
            gray = image.convert('L')
            small = gray.resize((200, 150))
            
            # Análise de contraste por regiões
            pixels = list(small.getdata())
            width = 200
            
            barcode_areas = []
            
            # Verificar variação horizontal em cada linha
            for y in range(0, 150, 10):
                if y * width + width < len(pixels):
                    row_pixels = pixels[y * width:(y + 1) * width]
                    
                    # Calcular variação na linha
                    variations = []
                    for i in range(len(row_pixels) - 1):
                        diff = abs(row_pixels[i] - row_pixels[i + 1])
                        variations.append(diff)
                    
                    avg_variation = sum(variations) / len(variations) if variations else 0
                    
                    if avg_variation > 12:  # Ainda mais sensível
                        barcode_areas.append({
                            'y': y,
                            'variation': avg_variation,
                            'quality': min(avg_variation / 40, 1.0)  # Escala melhorada
                        })
                        if avg_variation > 25:  # Log apenas detecções fortes
                            print(f"📊 BARCODE detectado: linha {y}, variação {avg_variation:.1f}")
            
            return sorted(barcode_areas, key=lambda x: x['variation'], reverse=True)[:3]
            
        except Exception:
            return []
    
    def foco_automatico_inteligente(self, barcode_areas):
        """Sistema de foco automático que aprende o melhor foco para códigos"""
        if not barcode_areas:
            return
        
        tempo_atual = time.time()
        
        # Evitar ajustes muito frequentes (reduzido para ser mais ativo)
        if tempo_atual - self.ultimo_ajuste_foco < 1.5:
            return
        
        melhor_area = barcode_areas[0]
        qualidade_atual = melhor_area.get('quality', 0)
        
        # Adicionar ao histórico
        self.historico_qualidade.append({
            'foco': self.foco_atual,
            'qualidade': qualidade_atual,
            'timestamp': tempo_atual
        })
        
        # Manter apenas últimas 10 medições
        if len(self.historico_qualidade) > 10:
            self.historico_qualidade.pop(0)
        
        # Se qualidade está boa, salvar como melhor foco (limiar reduzido)
        if qualidade_atual > 0.6:
            self.melhor_foco = self.foco_atual
            self.foco_otimo_encontrado = True
            self.modo_busca_foco = False
            print(f"🎯 FOCO ÓTIMO: {self.melhor_foco} (qualidade: {qualidade_atual:.2f}) ✅")
            
            self.root.after(0, lambda: self.status_deteccao.config(
                text=f"🎯 Foco automático otimizado ({qualidade_atual*100:.0f}%) ✅"
            ))
            return
        
        # Se qualidade está baixa, iniciar busca inteligente (limiar aumentado)
        if qualidade_atual < 0.5 and not self.modo_busca_foco:
            self.modo_busca_foco = True
            self.tentativas_foco = 0
            print(f"🔍 INICIANDO BUSCA FOCO: qualidade atual {qualidade_atual:.2f} está baixa")
            
            self.root.after(0, lambda: self.status_deteccao.config(
                text="🔍 Buscando melhor foco automaticamente..."
            ))
        
        # Busca automática inteligente
        if self.modo_busca_foco:
            self.buscar_melhor_foco_automatico(qualidade_atual)
    
    def buscar_melhor_foco_automatico(self, qualidade_atual):
        """Busca automática do melhor foco usando algoritmo inteligente"""
        self.tentativas_foco += 1
        
        # Estratégia: começar pelo melhor foco conhecido, depois expandir
        if self.foco_otimo_encontrado:
            # Usar foco ótimo conhecido como base
            focos_teste = [
                self.melhor_foco,
                self.melhor_foco + 200,
                self.melhor_foco - 200,
                self.melhor_foco + 400,
                self.melhor_foco - 400
            ]
        else:
            # Busca inicial em pontos estratégicos
            focos_teste = [6500, 6800, 6200, 7000, 6000, 7300, 5800]
        
        if self.tentativas_foco <= len(focos_teste):
            novo_foco = focos_teste[self.tentativas_foco - 1]
            
            # Garantir que está dentro dos limites
            novo_foco = max(1000, min(8000, novo_foco))
            
            if self.ajustar_foco_camera(novo_foco):
                self.ultimo_ajuste_foco = time.time()
                print(f"🔍 Testando foco {novo_foco} (tentativa {self.tentativas_foco}, qualidade: {qualidade_atual:.2f})")
        else:
            # Analisar histórico e escolher melhor
            self.analisar_melhor_foco_do_historico()
    
    def analisar_melhor_foco_do_historico(self):
        """Analisa histórico e define o melhor foco encontrado"""
        if not self.historico_qualidade:
            self.modo_busca_foco = False
            return
        
        # Encontrar o foco com melhor qualidade
        melhor = max(self.historico_qualidade, key=lambda x: x['qualidade'])
        
        if melhor['qualidade'] > 0.3:  # Se encontrou algo minimamente útil
            self.melhor_foco = melhor['foco']
            self.foco_otimo_encontrado = True
            
            # Aplicar melhor foco encontrado
            self.ajustar_foco_camera(self.melhor_foco)
            
            print(f"📊 Melhor foco do histórico: {self.melhor_foco} (qualidade: {melhor['qualidade']:.2f})")
            
            self.root.after(0, lambda: self.status_deteccao.config(
                text=f"📊 Foco automático aprendido ({melhor['qualidade']*100:.0f}%)"
            ))
        else:
            # Se não encontrou nada bom, usar foco padrão
            self.ajustar_foco_camera(self.foco_para_barcode)
            print("❓ Usando foco padrão para códigos de barras")
            
            self.root.after(0, lambda: self.status_deteccao.config(
                text="❓ Foco padrão para códigos"
            ))
        
        # Finalizar busca
        self.modo_busca_foco = False
        self.tentativas_foco = 0
    
    def processar_frame_deteccao_rapido(self, frame_data):
        """Análise super rápida para streaming contínuo"""
        if self.analisando_frame:
            return
            
        def analise_rapida():
            self.analisando_frame = True
            try:
                # Converter para PIL Image
                image = Image.open(BytesIO(frame_data))
                
                # Redimensionar drasticamente para análise rápida
                small_image = image.resize((60, 45), Image.Resampling.NEAREST)
                pixels = list(small_image.getdata())
                
                # Análise super rápida de cores dominantes
                cores_count = {'vermelho': 0, 'verde': 0, 'azul': 0, 'dourado': 0}
                
                for pixel in pixels[::2]:  # Pegar apenas 1 a cada 2 pixels
                    if isinstance(pixel, tuple) and len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        
                        if r > 120 and g < 80 and b < 80:  # Vermelho
                            cores_count['vermelho'] += 1
                        elif g > 120 and r < 80:  # Verde
                            cores_count['verde'] += 1
                        elif b > 120 and r < 80:  # Azul
                            cores_count['azul'] += 1
                        elif r > 180 and g > 150:  # Dourado
                            cores_count['dourado'] += 1
                
                # Determinar categoria mais provável
                if max(cores_count.values()) > 20:  # Pelo menos 20 pixels da cor
                    cor_dominante = max(cores_count, key=cores_count.get)
                    
                    categorias = {
                        'vermelho': 'REFRIGERANTE',
                        'verde': 'CERVEJA', 
                        'azul': 'AGUA',
                        'dourado': 'CERVEJA'
                    }
                    
                    if cor_dominante in categorias:
                        # Detectar possíveis códigos de barras
                        barcode_areas = self.detectar_codigo_barras_area(image)
                        
                        # Sistema de foco automático inteligente - SEMPRE ATIVO
                        if barcode_areas:
                            # Forçar ajuste de foco quando detectar código
                            tempo_atual = time.time()
                            melhor_barcode = barcode_areas[0]
                            qualidade = melhor_barcode.get('quality', 0)
                            
                            print(f"🔍 Código detectado! Qualidade: {qualidade:.2f}")
                            
                            # Se qualidade baixa, ajustar foco imediatamente
                            if qualidade < 0.6 and tempo_atual - self.ultimo_ajuste_foco > 1.0:
                                self.tentativas_foco += 1
                                
                                # Focos para teste rápido
                                focos_rapidos = [6800, 6200, 7000, 6000, 5500]
                                
                                if self.tentativas_foco <= len(focos_rapidos):
                                    novo_foco = focos_rapidos[self.tentativas_foco - 1]
                                    
                                    print(f"🎯 AJUSTANDO FOCO: {self.foco_atual} → {novo_foco}")
                                    
                                    if self.ajustar_foco_camera(novo_foco):
                                        self.ultimo_ajuste_foco = tempo_atual
                                        
                                        # Feedback visual imediato
                                        self.root.after(0, lambda f=novo_foco, q=qualidade: 
                                            self.status_deteccao.config(
                                                text=f"🔍 FOCO: {f} (qual: {q*100:.0f}%)"
                                            ))
                                else:
                                    self.tentativas_foco = 0
                        
                        # Atualizar status e estatísticas
                        categoria = categorias[cor_dominante]
                        confianca = min(cores_count[cor_dominante] / 100, 0.8)
                        
                        # Bonus de confiança se código de barras detectado
                        if barcode_areas and barcode_areas[0].get('quality', 0) > 0.5:
                            confianca = min(confianca + 0.15, 1.0)  # +15% confiança
                            categoria += " 📱"  # Ícone de código de barras
                        
                        # Registrar detecção
                        self.tempo_ultima_deteccao = time.time()
                        self.produtos_detectados_sessao.add(categoria.replace(" 📱", ""))
                        
                        self.root.after(0, lambda: self.atualizar_status_deteccao(
                            categoria, confianca, "streaming"
                        ))
                else:
                    # Nenhum produto detectado - continuar analisando
                    self.tentativas_deteccao += 1
                    
                    # Feedback menos frequente para não incomodar
                    if self.tentativas_deteccao % 20 == 0:  # A cada 20 tentativas
                        self.root.after(0, lambda: self.feedback_nenhuma_deteccao())
                    
                    # Resetar histórico se muitas tentativas sem sucesso (produto saiu de cena)
                    if self.tentativas_deteccao % 50 == 0:
                        print("🔄 Resetando análise - possível mudança de produto")
                        self.produtos_detectados_sessao.clear()
                        self.tentativas_deteccao = 0
                        
                    # Continuar analisando com foco automático se necessário
                    if self.foco_automatico and self.tentativas_deteccao % 15 == 0:
                        threading.Thread(target=self.buscar_melhor_foco_automatico, daemon=True).start()
                
            except Exception as e:
                print(f"Erro análise rápida: {e}")
            finally:
                self.analisando_frame = False
        
        # Thread leve para análise
        import threading
        thread = threading.Thread(target=analise_rapida, daemon=True)
        thread.start()
    
    def atualizar_display(self, frame_data):
        """Atualiza display"""
        try:
            # PIL
            image = Image.open(io.BytesIO(frame_data))
            image.thumbnail((480, 360), Image.Resampling.NEAREST)  # Menor e mais rápido
            photo = ImageTk.PhotoImage(image)
            
            # Atualizar
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
            
            # Armazenar
            self.current_frame = frame_data
            
            # Stats
            self.stats_frames.config(text=f"Frames: {self.total_frames}")
            
            if self.deteccao_ativa:
                self.status_principal.config(text="🤖 Detecção ativa - Analisando produtos em tempo real")
            else:
                self.status_principal.config(text="📹 Streaming ativo")
            
        except Exception as e:
            print(f"Erro display: {e}")
    
    def processar_frame_deteccao(self, frame_data):
        """Processo básico de detecção usando análise de imagem"""
        try:
            # Converter para PIL
            image = Image.open(io.BytesIO(frame_data))
            
            # Análise básica
            resultados = self.analisar_imagem_produtos(image)
            
            if resultados:
                # Atualizar análise na interface
                self.root.after(0, self.atualizar_analise_text, resultados)
            
        except Exception as e:
            print(f"Erro detecção: {e}")
    
    def analisar_imagem_produtos(self, image):
        """Análise avançada: cores, formas, OCR, códigos de barras"""
        try:
            resultados = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'analises': [],
                'detalhes_analise': {
                    'cores_detectadas': [],
                    'formas_detectadas': [],
                    'textos_encontrados': [],
                    'codigos_barras': []
                }
            }
            
            width, height = image.size
            
            # 1. ANÁLISE AVANÇADA DE CORES
            cores_detalhadas = self.analisar_cores_detalhadas(image)
            resultados['detalhes_analise']['cores_detectadas'] = cores_detalhadas
            
            # 2. ANÁLISE DE FORMAS E CONTORNOS
            if self.forma_var.get():
                formas_detectadas = self.analisar_formas_produtos(image)
                resultados['detalhes_analise']['formas_detectadas'] = formas_detectadas
            
            # 3. OCR - RECONHECIMENTO DE TEXTO EM RÓTULOS
            if self.ocr_var.get() and OCR_DISPONIVEL:
                textos_encontrados = self.extrair_textos_rotulos(image)
                resultados['detalhes_analise']['textos_encontrados'] = textos_encontrados
            
            # 4. DETECÇÃO DE CÓDIGOS DE BARRAS
            if self.barcode_var.get():
                codigos_detectados = self.detectar_codigos_barras(image)
                resultados['detalhes_analise']['codigos_barras'] = codigos_detectados
            
            # 5. ANÁLISE INTEGRADA - COMBINAR TODAS AS INFORMAÇÕES
            for categoria, padroes in self.padroes_produtos.items():
                confianca_total = self.calcular_confianca_integrada(
                    cores_detalhadas,
                    formas_detectadas if self.forma_var.get() else [],
                    textos_encontrados if self.ocr_var.get() and OCR_DISPONIVEL else [],
                    codigos_detectados if self.barcode_var.get() else [],
                    padroes
                )
                
                if confianca_total > self.sensibilidade_var.get():
                    # Determinar qual evidência foi mais forte
                    evidencias = []
                    if any(texto in padroes['textos_esperados'] for texto in textos_encontrados):
                        evidencias.append("Texto do rótulo")
                    if codigos_detectados:
                        evidencias.append("Código de barras")
                    if cores_detalhadas:
                        evidencias.append("Padrão de cores")
                    if formas_detectadas:
                        evidencias.append("Forma do produto")
                    
                    resultados['analises'].append({
                        'categoria': categoria,
                        'confianca': confianca_total,
                        'detalhes': f"Evidências: {', '.join(evidencias)}",
                        'evidencias': evidencias
                    })
            
            return resultados
            
        except Exception as e:
            print(f"Erro na análise: {e}")
            return None
    
    def analisar_cores_detalhadas(self, image):
        """Análise detalhada de cores e padrões cromáticos"""
        try:
            # Análise em múltiplas resoluções
            cores_encontradas = []
            
            # 1. Análise geral da imagem
            small_image = image.resize((100, 100))
            colors = list(small_image.getdata())
            
            # Agrupar cores por famílias
            familias_cores = {
                'vermelho': [], 'verde': [], 'azul': [], 'amarelo': [],
                'branco': [], 'preto': [], 'dourado': [], 'prateado': []
            }
            
            for color in colors:
                if isinstance(color, tuple) and len(color) >= 3:
                    r, g, b = color[:3]
                    
                    # Classificar cor por família
                    if r > 180 and g < 100 and b < 100:  # Vermelho
                        familias_cores['vermelho'].append(color)
                    elif g > 150 and r < 100 and b < 100:  # Verde
                        familias_cores['verde'].append(color)
                    elif b > 150 and r < 100 and g < 100:  # Azul
                        familias_cores['azul'].append(color)
                    elif r > 200 and g > 200 and b < 100:  # Amarelo/Dourado
                        if r > 220 and g > 180:  # Dourado
                            familias_cores['dourado'].append(color)
                        else:
                            familias_cores['amarelo'].append(color)
                    elif r > 240 and g > 240 and b > 240:  # Branco
                        familias_cores['branco'].append(color)
                    elif r < 50 and g < 50 and b < 50:  # Preto
                        familias_cores['preto'].append(color)
                    elif abs(r-g) < 20 and abs(g-b) < 20 and r > 150:  # Prateado
                        familias_cores['prateado'].append(color)
            
            # Calcular predominância de cada família
            total_pixels = len(colors)
            for familia, cores in familias_cores.items():
                if cores:
                    percentual = len(cores) / total_pixels
                    if percentual > 0.05:  # Mais de 5% da imagem
                        cores_encontradas.append({
                            'familia': familia,
                            'percentual': percentual,
                            'cores_amostra': cores[:3]  # Primeiras 3 cores da família
                        })
            
            # 2. Análise de gradientes (para rótulos com degradê)
            gradientes = self.detectar_gradientes_cores(image)
            
            return {
                'familias': cores_encontradas,
                'gradientes': gradientes,
                'dominante': max(cores_encontradas, key=lambda x: x['percentual'])['familia'] if cores_encontradas else 'indefinido'
            }
            
        except Exception as e:
            return {'familias': [], 'gradientes': [], 'dominante': 'erro'}
    
    def detectar_regioes_verticais(self, image):
        """Detecta possíveis regiões de produtos (formas verticais)"""
        try:
            # Simplificado: procura por regiões mais escuras/claras que podem ser produtos
            width, height = image.size
            
            # Dividir em grid e analisar contraste
            grid_size = 20
            regioes = []
            
            for i in range(0, width-grid_size, grid_size):
                for j in range(0, height-grid_size, grid_size):
                    # Extrair região
                    regiao = image.crop((i, j, i+grid_size, j+grid_size))
                    
                    # Calcular brilho médio
                    grayscale = regiao.convert('L')
                    pixels = list(grayscale.getdata())
                    brilho_medio = sum(pixels) / len(pixels)
                    
                    # Se região tem contraste interessante (possível produto)
                    if 50 < brilho_medio < 200:  # Nem muito escuro nem muito claro
                        aspect_ratio = grid_size / grid_size  # Para produtos verticais seria height/width > 1
                        regioes.append({
                            'x': i, 'y': j,
                            'width': grid_size, 'height': grid_size,
                            'brilho': brilho_medio,
                            'aspect_ratio': aspect_ratio
                        })
            
            return regioes
            
        except Exception as e:
            return []
    
    def calcular_similaridade_produto(self, cores_imagem, regioes_imagem, padroes_produto):
        """Calcula similaridade entre imagem e padrões de produto"""
        try:
            similaridade = 0.0
            
            # Comparar cores
            cores_produto = padroes_produto['cores_predominantes']
            for cor_img in cores_imagem[:3]:  # Pegar apenas 3 principais
                for cor_produto in cores_produto:
                    # Calcular distância euclidiana entre cores
                    dist = sum((a-b)**2 for a, b in zip(cor_img, cor_produto))**0.5
                    if dist < 100:  # Cores similares
                        similaridade += 0.2
            
            # Analisar regiões (se tem formas verticais para produtos)
            if len(regioes_imagem) > 0:
                similaridade += 0.1
                
                # Bonus se muitas regiões (indica produtos)
                if len(regioes_imagem) > 5:
                    similaridade += 0.1
            
            return min(similaridade, 1.0)  # Max 1.0
            
        except Exception as e:
            return 0.0
    
    def atualizar_analise_text(self, resultados):
        """Atualiza texto de análise"""
        self.analise_text.delete(1.0, tk.END)
        
        texto = f"⏰ {resultados['timestamp']}\n"
        texto += "="*40 + "\n\n"
        
        if resultados['analises']:
            texto += "🎯 PRODUTOS DETECTADOS:\n\n"
            
            for analise in resultados['analises']:
                texto += f"📦 {analise['categoria']}\n"
                texto += f"   Confiança: {analise['confianca']*100:.1f}%\n"
                texto += f"   {analise['detalhes']}\n\n"
        else:
            texto += "❌ Nenhum produto detectado\n\n"
        
        texto += f"⚙️ Sensibilidade: {self.sensibilidade_var.get()*100:.0f}%\n"
        
        self.analise_text.insert(1.0, texto)
    
    def toggle_streaming(self):
        """Liga/desliga streaming"""
        if self.streaming:
            self.streaming = False
            self.btn_stream.config(text="▶️ Stream")
            self.status_conexao.config(text="⏸️ Pausado")
        else:
            self.iniciar_streaming()
    
    def ajustar_foco_manual(self, valor_foco, mensagem):
        """Ajusta foco manualmente"""
        if self.ajustar_foco_camera(valor_foco):
            self.foco_automatico = False
            self.status_deteccao.config(text=mensagem)
        else:
            self.status_deteccao.config(text="⚠️ Erro ao ajustar foco")
    
    def ativar_foco_automatico_inteligente(self):
        """Ativa sistema de foco automático inteligente"""
        self.foco_automatico = True
        self.modo_busca_foco = False
        self.tentativas_foco = 0
        
        # Se já tem um foco ótimo, usar ele
        if self.foco_otimo_encontrado:
            self.ajustar_foco_camera(self.melhor_foco)
            self.status_deteccao.config(text=f"🤖 Foco automático: {self.melhor_foco}")
        else:
            # Começar com foco padrão para códigos
            self.ajustar_foco_camera(self.foco_para_barcode)
            self.status_deteccao.config(text="🤖 Foco automático ativo - aprendendo...")
    
    def resetar_aprendizado_foco(self):
        """Reseta o aprendizado de foco para recomeçar"""
        self.historico_qualidade = []
        self.foco_otimo_encontrado = False
        self.melhor_foco = 6500
        self.modo_busca_foco = False
        self.tentativas_foco = 0
        
        # Voltar ao foco padrão
        self.ajustar_foco_camera(self.foco_para_barcode)
        self.status_deteccao.config(text="🔄 Aprendizado resetado - buscando melhor foco...")
        
        print("🔄 Sistema de foco resetado. Iniciando nova busca automática...")
    
    def feedback_nenhuma_deteccao(self):
        """Feedback quando nenhum produto é detectado por um tempo"""
        mensagens = [
            "🔍 Analisando continuamente...",
            "👀 Aguardando produto na câmera", 
            "🎯 Sistema ativo - posicione produto",
            "🔄 Análise contínua ativa"
        ]
        import random
        mensagem = random.choice(mensagens)
        self.status_deteccao.config(text=mensagem)
        
        # Log para mostrar que está funcionando
        print(f"📊 Análise contínua: {self.tentativas_deteccao} tentativas")
    
    def buscar_melhor_foco_automatico(self):
        """Busca automaticamente o melhor foco quando não detecta produtos"""
        if not self.foco_automatico or self.modo_busca_foco:
            return
            
        print("🔍 Buscando melhor foco automaticamente...")
        self.modo_busca_foco = True
        
        try:
            # Testar 3 valores diferentes rapidamente
            valores_rapidos = [5500, 6500, 7000]
            
            for valor in valores_rapidos:
                if self.ajustar_foco_camera(valor):
                    time.sleep(1)  # Tempo reduzido para busca rápida
                    
            print("✅ Busca automática de foco concluída")
        except Exception as e:
            print(f"❌ Erro na busca automática: {e}")
        finally:
            self.modo_busca_foco = False
    
    def testar_foco_manual(self):
        """Testa ajuste de foco manualmente para debug"""
        import threading
        
        def teste_foco():
            print("🧪 INICIANDO TESTE MANUAL DE FOCO")
            
            # Testar diferentes valores de foco
            focos_teste = [5000, 6000, 6500, 7000, 7500]
            
            for i, foco in enumerate(focos_teste):
                print(f"🎯 Teste {i+1}/5: Ajustando para {foco}")
                
                # Atualizar interface
                self.root.after(0, lambda f=foco: self.status_deteccao.config(
                    text=f"🔧 Testando foco: {f}"
                ))
                
                # Tentar ajustar
                sucesso = self.ajustar_foco_camera(foco)
                
                if sucesso:
                    print(f"✅ Foco {foco} aplicado com sucesso")
                    time.sleep(2)  # Aguardar câmera ajustar
                else:
                    print(f"❌ Falha ao aplicar foco {foco}")
                
                time.sleep(1)  # Pausa entre testes
            
            # Finalizar teste
            self.root.after(0, lambda: self.status_deteccao.config(
                text="🧪 Teste de foco concluído"
            ))
            
            print("🧪 TESTE DE FOCO CONCLUÍDO")
        
        # Executar em thread separada
        thread = threading.Thread(target=teste_foco, daemon=True)
        thread.start()
    
    def ativar_foco_automatico(self):
        """Ativa foco automático (função legacy mantida)"""
        self.ativar_foco_automatico_inteligente()
    
    def toggle_deteccao(self):
        """Liga/desliga detecção"""
        self.deteccao_ativa = not self.deteccao_ativa
        
        if self.deteccao_ativa:
            self.btn_deteccao.config(text="⏸️ Parar IA")
            self.status_deteccao.config(text="🤖 Detecção: ATIVA")
        else:
            self.btn_deteccao.config(text="🤖 Detecção")
            self.status_deteccao.config(text="🤖 Detecção: Inativa")
    
    def capturar_frame(self):
        """Captura frame atual"""
        if not self.current_frame:
            messagebox.showwarning("Aviso", "Nenhum frame disponível!")
            return
        
        try:
            os.makedirs("capturas_verifik", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"verifik_{timestamp}.jpg"
            filepath = os.path.join("capturas_verifik", filename)
            
            with open(filepath, 'wb') as f:
                f.write(self.current_frame)
            
            messagebox.showinfo("Captura", f"Salvo: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")
    
    def analisar_frame_atual(self):
        """Analisa frame atual manualmente"""
        if not self.current_frame:
            messagebox.showwarning("Aviso", "Nenhum frame para analisar!")
            return
        
        try:
            # Converter e analisar
            image = Image.open(io.BytesIO(self.current_frame))
            resultados = self.analisar_imagem_produtos(image)
            
            if resultados:
                self.atualizar_analise_text(resultados)
                
                # Se encontrou produtos, perguntar se quer confirmar
                if resultados['analises']:
                    resposta = messagebox.askyesno(
                        "Produtos Detectados",
                        f"Detectados {len(resultados['analises'])} produto(s)!\n\nConfirmar detecções?"
                    )
                    
                    if resposta:
                        # Adicionar à lista de confirmados
                        for analise in resultados['analises']:
                            produto_confirmado = f"{analise['categoria']} ({analise['confianca']*100:.0f}%) - {datetime.now().strftime('%H:%M:%S')}"
                            self.produtos_listbox.insert(tk.END, produto_confirmado)
                            self.produtos_detectados.append(analise)
                        
                        self.stats_deteccoes.config(text=f"Produtos: {len(self.produtos_detectados)}")
                
            else:
                self.analise_text.delete(1.0, tk.END)
                self.analise_text.insert(1.0, "❌ Erro na análise ou nenhum produto detectado")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na análise: {e}")

def main():
    root = tk.Tk()
    app = VerifiKStreamingBasico(root)
    
    def on_close():
        app.streaming = False
        root.destroy()
    
    # Adicionar botões de foco
    app.foco_para_barcode_manual = lambda: app.ajustar_foco_manual(app.foco_para_barcode, "🔍 Foco para códigos de barras")
    app.foco_automatico_manual = lambda: app.ativar_foco_automatico()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()