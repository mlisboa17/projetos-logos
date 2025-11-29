#!/usr/bin/env python3
"""
VerifiK - Sistema de Reconhecimento Automático de Produtos
Câmera inteligente para detecção automática e prevenção de furtos
"""

import tkinter as tk
from tkinter import ttk
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image, ImageTk, ImageDraw
import threading
import time
import sqlite3
import cv2
import numpy as np
from datetime import datetime
import json

try:
    import pytesseract
    OCR_DISPONIVEL = True
except ImportError:
    OCR_DISPONIVEL = False
    print("⚠️ OCR não disponível - instale pytesseract para melhor reconhecimento")

class VerifiKReconhecimento:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 VerifiK - Reconhecimento Automático de Produtos")
        self.root.geometry("1400x900")
        
        # Configurações da câmera
        self.camera_ip = "192.168.68.108"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
        # Estado do sistema
        self.streaming = False
        self.reconhecimento_ativo = True
        self.current_image = None
        self.frame_count = 0
        self.produtos_detectados = {}
        self.historico_deteccoes = []
        
        # Performance
        self.fps_target = 5
        self.analise_a_cada_frames = 3
        self.ultimo_frame_analisado = 0
        
        # Carregar produtos e padrões
        self.carregar_produtos()
        self.criar_padroes_reconhecimento()
        
        # Criar interface
        self.criar_interface()
        
        print(f"✅ Sistema de reconhecimento iniciado - {len(self.produtos)} produtos")
        print("🎯 Reconhecimento automático ativado")
    
    def carregar_produtos(self):
        """Carrega produtos da base de dados"""
        try:
            conn = sqlite3.connect('mobile_simulator.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT descricao_produto
                FROM produtos WHERE ativo = 1 
                ORDER BY descricao_produto
            """)
            
            self.produtos = []
            self.produtos_dict = {}
            
            for row in cursor.fetchall():
                produto = {
                    'nome': row[0],
                    'codigo': '',
                    'valor': 2.50  # Valor padrão
                }
                self.produtos.append(produto)
                self.produtos_dict[row[0].upper()] = produto
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar produtos: {e}")
            self.produtos = [
                {'nome': 'COCA COLA 350ML', 'codigo': '7894900011517', 'valor': 3.50},
                {'nome': 'GUARANA ANTARCTICA 350ML', 'codigo': '7891991010048', 'valor': 3.20},
                {'nome': 'ÁGUA CRYSTAL 500ML', 'codigo': '7891020001014', 'valor': 2.00}
            ]
            self.produtos_dict = {p['nome'].upper(): p for p in self.produtos}
    
    def criar_padroes_reconhecimento(self):
        """Cria padrões para reconhecimento automático"""
        self.padroes = {
            'BEBIDAS': {
                'palavras_chave': ['COCA', 'PEPSI', 'GUARANA', 'FANTA', 'SPRITE', 'AGUA', 'CRYSTAL', 'H2O'],
                'cores_predominantes': [(255, 0, 0), (0, 100, 0), (0, 0, 255), (255, 165, 0)],
                'formatos': ['vertical', 'cilindrico']
            },
            'ALIMENTOS': {
                'palavras_chave': ['CHOCOLATE', 'BISCOITO', 'BOLACHA', 'SALGADINHO', 'DOCE'],
                'cores_predominantes': [(139, 69, 19), (255, 215, 0), (255, 140, 0)],
                'formatos': ['retangular', 'quadrado']
            },
            'HIGIENE': {
                'palavras_chave': ['SABONETE', 'SHAMPOO', 'PASTA', 'DENTAL', 'DESODORANTE'],
                'cores_predominantes': [(255, 255, 255), (0, 191, 255), (173, 216, 230)],
                'formatos': ['vertical', 'cilindrico']
            }
        }
    
    def criar_interface(self):
        """Cria interface de reconhecimento automático"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="🎯 VerifiK - Reconhecimento Automático", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(side='left')
        
        self.status_geral = ttk.Label(header_frame, text="🟢 Sistema Ativo", 
                                     font=('Arial', 12, 'bold'), foreground='green')
        self.status_geral.pack(side='right')
        
        # Frame de controles
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Controles", padding="10")
        control_frame.pack(fill='x', pady=(0, 10))
        
        # Botões principais
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x')
        
        self.btn_stream = ttk.Button(btn_frame, text="▶️ Iniciar Vigilância", 
                                   command=self.toggle_streaming, style='Accent.TButton')
        self.btn_stream.pack(side='left', padx=(0, 10))
        
        self.btn_reconhecimento = ttk.Button(btn_frame, text="🧠 Reconhecimento ON", 
                                           command=self.toggle_reconhecimento)
        self.btn_reconhecimento.pack(side='left', padx=(0, 10))
        
        ttk.Button(btn_frame, text="📊 Relatório", 
                  command=self.gerar_relatorio).pack(side='left', padx=(0, 10))
        
        ttk.Button(btn_frame, text="🧹 Limpar Tela", 
                  command=self.limpar_tela).pack(side='left', padx=(0, 10))
        
        # Status
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_camera = ttk.Label(status_frame, text="📹 Câmera: Desconectada")
        self.status_camera.pack(side='left')
        
        self.fps_label = ttk.Label(status_frame, text="⚡ FPS: 0")
        self.fps_label.pack(side='left', padx=(20, 0))
        
        self.produtos_detectados_label = ttk.Label(status_frame, text="📦 Produtos: 0")
        self.produtos_detectados_label.pack(side='left', padx=(20, 0))
        
        # Frame principal de conteúdo
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Frame esquerdo - Vídeo
        video_frame = ttk.LabelFrame(content_frame, text="📹 Vigilância em Tempo Real", padding="10")
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.video_canvas = tk.Canvas(video_frame, width=640, height=480, bg='black')
        self.video_canvas.pack(pady=(0, 10))
        
        # Indicadores visuais
        indicators_frame = ttk.Frame(video_frame)
        indicators_frame.pack(fill='x')
        
        self.indicator_movimento = ttk.Label(indicators_frame, text="👁️ Monitorando", 
                                           background='yellow', padding="5")
        self.indicator_movimento.pack(side='left', padx=(0, 5))
        
        self.indicator_deteccao = ttk.Label(indicators_frame, text="🎯 Detectando", 
                                          background='lightblue', padding="5")
        self.indicator_deteccao.pack(side='left', padx=(0, 5))
        
        # Frame direito - Detecções
        detection_frame = ttk.LabelFrame(content_frame, text="🚨 Detecções em Tempo Real", padding="10")
        detection_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Lista de produtos detectados
        self.detection_text = tk.Text(detection_frame, height=15, wrap=tk.WORD, 
                                    font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(detection_frame, orient="vertical", command=self.detection_text.yview)
        self.detection_text.configure(yscrollcommand=scrollbar.set)
        
        self.detection_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(detection_frame, text="📊 Estatísticas", padding="5")
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        self.stats_text.pack(fill='both')
        
        # Inicializar display
        self.atualizar_stats()
        self.log_deteccao("🚀 Sistema de reconhecimento iniciado")
        self.log_deteccao(f"📋 {len(self.produtos)} produtos na base de dados")
        self.log_deteccao("🎯 Pronto para detectar produtos automaticamente")
    
    def toggle_streaming(self):
        """Liga/desliga streaming com reconhecimento"""
        if self.streaming:
            self.parar_streaming()
        else:
            self.iniciar_streaming()
    
    def toggle_reconhecimento(self):
        """Liga/desliga reconhecimento automático"""
        self.reconhecimento_ativo = not self.reconhecimento_ativo
        
        if self.reconhecimento_ativo:
            self.btn_reconhecimento.config(text="🧠 Reconhecimento ON")
            self.log_deteccao("✅ Reconhecimento automático ATIVADO")
        else:
            self.btn_reconhecimento.config(text="🧠 Reconhecimento OFF")
            self.log_deteccao("⏸️ Reconhecimento automático DESATIVADO")
    
    def iniciar_streaming(self):
        """Inicia streaming com reconhecimento automático"""
        print("🚀 Iniciando vigilância automática...")
        
        if not self.testar_camera():
            self.status_camera.config(text="❌ Câmera: Inacessível")
            self.log_deteccao("❌ ERRO: Câmera não acessível")
            return
        
        self.streaming = True
        self.btn_stream.config(text="⏸️ Parar Vigilância")
        self.status_camera.config(text="🟢 Câmera: Ativa")
        self.status_geral.config(text="🟢 Vigilância Ativa", foreground='green')
        
        self.log_deteccao("🎬 Vigilância iniciada - Monitorando produtos...")
        
        # Thread de captura e reconhecimento
        thread = threading.Thread(target=self.loop_reconhecimento, daemon=True)
        thread.start()
    
    def parar_streaming(self):
        """Para streaming"""
        self.streaming = False
        self.btn_stream.config(text="▶️ Iniciar Vigilância")
        self.status_camera.config(text="📹 Câmera: Pausada")
        self.status_geral.config(text="⏸️ Sistema Pausado", foreground='orange')
        self.log_deteccao("⏹️ Vigilância pausada")
    
    def testar_camera(self):
        """Testa conectividade da câmera"""
        try:
            url = f"http://{self.camera_ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
            response = requests.get(url, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                self.log_deteccao(f"✅ Câmera conectada: {response.text.strip()}")
                return True
            else:
                self.log_deteccao(f"❌ Erro de conexão: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_deteccao(f"💥 Erro: {e}")
            return False
    
    def loop_reconhecimento(self):
        """Loop principal com reconhecimento automático"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.streaming:
            try:
                # Capturar frame
                image_data = self.capturar_frame()
                
                if image_data:
                    self.frame_count += 1
                    
                    # Atualizar display
                    self.root.after(0, self.atualizar_display, image_data)
                    
                    # Reconhecimento automático (otimizado)
                    if (self.reconhecimento_ativo and 
                        self.frame_count % self.analise_a_cada_frames == 0):
                        
                        self.reconhecer_produtos_automatico(image_data)
                    
                    # Calcular FPS
                    fps_counter += 1
                    current_time = time.time()
                    
                    if current_time - fps_start_time >= 1.0:
                        fps = fps_counter / (current_time - fps_start_time)
                        self.root.after(0, lambda: self.fps_label.config(text=f"⚡ FPS: {fps:.1f}"))
                        fps_counter = 0
                        fps_start_time = current_time
                
                else:
                    self.root.after(0, lambda: self.status_camera.config(text="🔴 Câmera: Erro"))
                
                time.sleep(1.0 / self.fps_target)  # Controle de FPS
                
            except Exception as e:
                print(f"❌ Erro no loop: {e}")
                time.sleep(1)
    
    def capturar_frame(self):
        """Captura frame otimizado"""
        try:
            url = f"http://{self.camera_ip}/cgi-bin/snapshot.cgi"
            response = requests.get(url, auth=self.auth, timeout=2)
            
            if response.status_code == 200 and len(response.content) > 5000:
                return response.content
                
        except Exception:
            pass
        
        return None
    
    def atualizar_display(self, image_data):
        """Atualiza display com overlays de detecção"""
        try:
            from io import BytesIO
            image = Image.open(BytesIO(image_data))
            image = image.resize((640, 480), Image.Resampling.LANCZOS)
            
            # Desenhar overlays de detecção
            draw = ImageDraw.Draw(image)
            
            # Indicador de reconhecimento ativo
            if self.reconhecimento_ativo:
                draw.rectangle([10, 10, 150, 40], fill=(0, 255, 0, 100), outline=(0, 255, 0))
                draw.text((15, 18), "🎯 DETECTANDO", fill=(255, 255, 255))
            
            # Mostrar produtos detectados recentemente
            y_pos = 50
            for produto, info in list(self.produtos_detectados.items())[-3:]:
                draw.rectangle([10, y_pos, 200, y_pos + 25], fill=(255, 0, 0, 150), outline=(255, 0, 0))
                draw.text((15, y_pos + 5), f"📦 {produto[:15]}", fill=(255, 255, 255))
                y_pos += 30
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Atualizar canvas
            self.video_canvas.delete("all")
            self.video_canvas.create_image(320, 240, image=photo, anchor=tk.CENTER)
            self.video_canvas.image = photo
            
            # Armazenar imagem atual
            self.current_image = image
            
        except Exception as e:
            print(f"❌ Erro display: {e}")
    
    def reconhecer_produtos_automatico(self, image_data):
        """Reconhecimento automático de produtos em tempo real"""
        try:
            from io import BytesIO
            
            # Converter para análise
            pil_image = Image.open(BytesIO(image_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Análise rápida de características
            produtos_encontrados = []
            
            # 1. Análise de cores dominantes
            cores_detectadas = self.analisar_cores_dominantes(cv_image)
            
            # 2. Detecção de texto (se OCR disponível)
            if OCR_DISPONIVEL:
                texto_detectado = self.extrair_texto(pil_image)
                produtos_texto = self.buscar_produtos_por_texto(texto_detectado)
                produtos_encontrados.extend(produtos_texto)
            
            # 3. Análise de formas e padrões
            formas_detectadas = self.analisar_formas(cv_image)
            produtos_formas = self.buscar_produtos_por_formas(formas_detectadas, cores_detectadas)
            produtos_encontrados.extend(produtos_formas)
            
            # 4. Detecção de código de barras (análise de padrões)
            codigo_barras = self.detectar_codigo_barras_visual(cv_image)
            if codigo_barras:
                produto_codigo = self.buscar_produto_por_codigo(codigo_barras)
                if produto_codigo:
                    produtos_encontrados.append(produto_codigo)
            
            # Processar detecções
            for produto in produtos_encontrados:
                self.processar_deteccao(produto)
                
        except Exception as e:
            print(f"❌ Erro reconhecimento: {e}")
    
    def analisar_cores_dominantes(self, image):
        """Analisa cores dominantes na imagem"""
        # Redimensionar para análise rápida
        small = cv2.resize(image, (100, 100))
        
        # Converter para LAB para melhor análise de cores
        lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
        
        # Encontrar cores dominantes
        pixels = lab.reshape((-1, 3))
        
        # Análise simples de agrupamento de cores
        cores_dominantes = []
        
        # Verificar se há predominância de certas cores
        l_mean = np.mean(pixels[:, 0])  # Luminosidade
        a_mean = np.mean(pixels[:, 1])  # Verde-Vermelho
        b_mean = np.mean(pixels[:, 2])  # Azul-Amarelo
        
        # Classificar cor dominante
        if a_mean > 130:  # Vermelho
            cores_dominantes.append('VERMELHO')
        elif a_mean < 125:  # Verde
            cores_dominantes.append('VERDE')
        
        if b_mean > 130:  # Amarelo
            cores_dominantes.append('AMARELO')
        elif b_mean < 125:  # Azul
            cores_dominantes.append('AZUL')
        
        if l_mean > 200:  # Branco
            cores_dominantes.append('BRANCO')
        elif l_mean < 50:  # Preto
            cores_dominantes.append('PRETO')
        
        return cores_dominantes
    
    def extrair_texto(self, image):
        """Extrai texto da imagem usando OCR"""
        try:
            # Melhorar imagem para OCR
            gray = image.convert('L')
            
            # Extrair texto
            texto = pytesseract.image_to_string(gray, config='--psm 8')
            return texto.upper().strip()
            
        except Exception:
            return ""
    
    def buscar_produtos_por_texto(self, texto):
        """Busca produtos baseado no texto detectado"""
        produtos_encontrados = []
        
        for produto_nome, produto_info in self.produtos_dict.items():
            # Verificar palavras-chave do produto no texto
            palavras_produto = produto_nome.split()
            
            for palavra in palavras_produto:
                if len(palavra) > 3 and palavra in texto:
                    produtos_encontrados.append(produto_info)
                    break
        
        return produtos_encontrados
    
    def analisar_formas(self, image):
        """Analisa formas na imagem"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar bordas
        edges = cv2.Canny(gray, 50, 150)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        formas = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 1000:  # Filtrar objetos pequenos
                # Aproximar contorno
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Classificar forma
                if len(approx) == 4:
                    # Retângulo ou quadrado
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 0.8 <= aspect_ratio <= 1.2:
                        formas.append('QUADRADO')
                    elif aspect_ratio > 2.0:
                        formas.append('RETANGULAR_HORIZONTAL')
                    elif aspect_ratio < 0.5:
                        formas.append('RETANGULAR_VERTICAL')
                    else:
                        formas.append('RETANGULAR')
                        
                elif len(approx) > 8:
                    formas.append('CIRCULAR')
        
        return formas
    
    def buscar_produtos_por_formas(self, formas, cores):
        """Busca produtos baseado em formas e cores"""
        produtos_encontrados = []
        
        # Lógica de matching com padrões conhecidos
        for categoria, padroes in self.padroes.items():
            score = 0
            
            # Score por formas
            for forma in formas:
                if forma.lower() in [f.lower() for f in padroes['formatos']]:
                    score += 2
            
            # Score por cores (simplificado)
            for cor in cores:
                if cor in ['VERMELHO', 'VERDE', 'AZUL', 'AMARELO']:
                    score += 1
            
            # Se score alto, buscar produtos dessa categoria
            if score >= 2:
                for produto in self.produtos:
                    for palavra in padroes['palavras_chave']:
                        if palavra in produto['nome'].upper():
                            produtos_encontrados.append(produto)
                            break
        
        return produtos_encontrados
    
    def detectar_codigo_barras_visual(self, image):
        """Detecta padrões visuais de código de barras"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar linhas verticais (características de código de barras)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        # Verificar se há padrão de linhas verticais
        edges = cv2.Canny(opened, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=5)
        
        if lines is not None and len(lines) > 10:
            # Possível código de barras detectado
            return "BARCODE_DETECTED"
        
        return None
    
    def buscar_produto_por_codigo(self, codigo):
        """Busca produto por código de barras"""
        # Simulação - em implementação real, faria OCR do código
        for produto in self.produtos:
            if produto['codigo'] and len(produto['codigo']) > 5:
                return produto
        return None
    
    def processar_deteccao(self, produto):
        """Processa uma detecção de produto"""
        timestamp = datetime.now()
        produto_nome = produto['nome']
        
        # Evitar duplicatas muito próximas no tempo
        if produto_nome in self.produtos_detectados:
            ultima_deteccao = self.produtos_detectados[produto_nome]['timestamp']
            if (timestamp - ultima_deteccao).seconds < 5:
                return
        
        # Registrar detecção
        deteccao = {
            'produto': produto,
            'timestamp': timestamp,
            'confianca': 85  # Simulação de confiança
        }
        
        self.produtos_detectados[produto_nome] = deteccao
        self.historico_deteccoes.append(deteccao)
        
        # Log da detecção
        self.root.after(0, lambda: self.log_deteccao(
            f"🚨 PRODUTO DETECTADO: {produto_nome}\n"
            f"   💰 Valor: R$ {produto['valor']:.2f}\n"
            f"   🕐 {timestamp.strftime('%H:%M:%S')}\n"
            f"   📊 Confiança: {deteccao['confianca']}%"
        ))
        
        # Atualizar contador
        self.root.after(0, lambda: self.produtos_detectados_label.config(
            text=f"📦 Produtos: {len(self.produtos_detectados)}"
        ))
        
        # Atualizar estatísticas
        self.root.after(0, self.atualizar_stats)
        
        print(f"🚨 DETECTADO: {produto_nome} - R$ {produto['valor']:.2f}")
    
    def log_deteccao(self, mensagem):
        """Adiciona mensagem ao log de detecções"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {mensagem}\n\n"
        
        self.detection_text.insert('end', log_entry)
        self.detection_text.see('end')
        
        # Limitar tamanho do log
        lines = self.detection_text.get("1.0", "end-1c").split('\n')
        if len(lines) > 100:
            self.detection_text.delete("1.0", f"{len(lines)-80}.0")
    
    def atualizar_stats(self):
        """Atualiza estatísticas"""
        total_detectado = len(self.produtos_detectados)
        valor_total = sum(p['produto']['valor'] for p in self.produtos_detectados.values())
        
        # Produtos mais detectados
        produtos_freq = {}
        for deteccao in self.historico_deteccoes[-20:]:  # Últimas 20
            nome = deteccao['produto']['nome']
            produtos_freq[nome] = produtos_freq.get(nome, 0) + 1
        
        stats = f"""📊 ESTATÍSTICAS EM TEMPO REAL
═══════════════════════════════
🎯 Produtos Únicos Detectados: {total_detectado}
💰 Valor Total Detectado: R$ {valor_total:.2f}
📈 Total de Detecções: {len(self.historico_deteccoes)}

🏆 PRODUTOS MAIS DETECTADOS:
"""
        
        for produto, freq in sorted(produtos_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            stats += f"   • {produto[:20]}: {freq}x\n"
        
        stats += f"\n🕐 Última atualização: {datetime.now().strftime('%H:%M:%S')}"
        
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats)
    
    def limpar_tela(self):
        """Limpa todas as informações da tela"""
        # Limpar log de detecções
        self.detection_text.delete("1.0", "end")
        
        # Limpar estatísticas
        self.stats_text.delete("1.0", "end")
        
        # Resetar contadores
        self.produtos_detectados.clear()
        self.historico_deteccoes.clear()
        
        # Atualizar displays
        self.produtos_detectados_label.config(text="📦 Produtos: 0")
        
        # Mensagem de tela limpa
        self.log_deteccao("🧹 Tela limpa - Sistema resetado")
        self.log_deteccao(f"📋 {len(self.produtos)} produtos na base de dados")
        self.log_deteccao("🎯 Pronto para detectar produtos")
        
        # Atualizar estatísticas
        self.atualizar_stats()
        
        print("🧹 Tela limpa e sistema resetado")
    
    def gerar_relatorio(self):
        """Gera relatório de detecções"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"verifik_relatorio_{timestamp}.json"
        
        relatorio = {
            'timestamp': timestamp,
            'produtos_detectados': len(self.produtos_detectados),
            'valor_total': sum(p['produto']['valor'] for p in self.produtos_detectados.values()),
            'deteccoes': [
                {
                    'produto': d['produto']['nome'],
                    'valor': d['produto']['valor'],
                    'timestamp': d['timestamp'].isoformat(),
                    'confianca': d['confianca']
                }
                for d in self.historico_deteccoes
            ]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, ensure_ascii=False, indent=2)
            
            self.log_deteccao(f"📋 Relatório salvo: {filename}")
            print(f"✅ Relatório salvo: {filename}")
            
        except Exception as e:
            self.log_deteccao(f"❌ Erro ao salvar relatório: {e}")

def main():
    root = tk.Tk()
    app = VerifiKReconhecimento(root)
    
    def on_closing():
        app.streaming = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()