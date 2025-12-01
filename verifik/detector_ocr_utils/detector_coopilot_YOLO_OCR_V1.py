#!/usr/bin/env python3
"""
VerifiK - Detector Copilot YOLO + OCR V1
Sistema de detecção de produtos usando YOLOv8 + EasyOCR
Combina detecção de objetos com reconhecimento de texto
"""

import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
import time
from datetime import datetime
import threading
import base64
from flask import Flask, render_template, Response, jsonify
import json

class DetectorCopilotYOLO:
    def __init__(self):
        print("🚀 Inicializando Detector Copilot YOLO + OCR V1...")
        
        # Configurações
        self.camera_index = 0
        self.confidence_threshold = 0.5
        self.ocr_confidence_threshold = 0.6
        
        # Inicializar modelos
        self.inicializar_modelos()
        
        # Inicializar câmera
        self.cap = None
        self.frame_atual = None
        self.detectores_ativos = False
        
        # Estatísticas
        self.stats = {
            'total_deteccoes': 0,
            'produtos_detectados': [],
            'textos_lidos': [],
            'fps': 0,
            'tempo_inicio': time.time()
        }
        
        # Flask app
        self.app = Flask(__name__)
        self.configurar_rotas()
    
    def inicializar_modelos(self):
        """Inicializa os modelos YOLO e EasyOCR"""
        try:
            print("📦 Carregando modelo YOLOv8...")
            self.model = YOLO('yolov8n.pt')  # Modelo nano (mais rápido)
            print("✅ YOLOv8 carregado com sucesso!")
            
            print("🔤 Inicializando EasyOCR (PT + EN)...")
            self.reader = easyocr.Reader(['pt', 'en'], gpu=False)  # GPU=False para compatibilidade
            print("✅ EasyOCR inicializado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar modelos: {e}")
            raise e
    
    def inicializar_camera(self):
        """Inicializa a câmera"""
        try:
            print(f"📹 Conectando à câmera {self.camera_index}...")
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise Exception("Não foi possível abrir a câmera")
            
            # Configurar resolução
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Câmera inicializada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar câmera: {e}")
            return False
    
    def processar_frame(self, frame):
        """Processa um frame com YOLO + OCR"""
        frame_processado = frame.copy()
        deteccoes_frame = []
        
        try:
            # 1. Detecção com YOLOv8
            results = self.model(frame, conf=self.confidence_threshold)
            
            # 2. Para cada detecção
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Coordenadas da caixa
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        
                        # Validar coordenadas
                        h, w = frame.shape[:2]
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)
                        
                        if x2 > x1 and y2 > y1:
                            # 3. Recortar região da detecção
                            roi = frame[y1:y2, x1:x2]
                            
                            # 4. OCR na região (se for um produto relevante)
                            texto_detectado = ""
                            if self.eh_produto_relevante(class_name):
                                texto_detectado = self.extrair_texto_roi(roi)
                            
                            # 5. Desenhar caixa e informações
                            self.desenhar_deteccao(frame_processado, x1, y1, x2, y2, 
                                                 class_name, confidence, texto_detectado)
                            
                            # 6. Armazenar detecção
                            deteccao = {
                                'classe': class_name,
                                'confianca': confidence,
                                'bbox': [x1, y1, x2, y2],
                                'texto': texto_detectado,
                                'timestamp': datetime.now().isoformat()
                            }
                            deteccoes_frame.append(deteccao)
            
            # Atualizar estatísticas
            self.stats['total_deteccoes'] += len(deteccoes_frame)
            
        except Exception as e:
            print(f"⚠️ Erro no processamento: {e}")
        
        return frame_processado, deteccoes_frame
    
    def eh_produto_relevante(self, class_name):
        """Verifica se a classe é relevante para OCR"""
        classes_relevantes = [
            'bottle', 'cup', 'bowl', 'wine glass',
            'banana', 'apple', 'orange', 'cake',
            'pizza', 'donut', 'sandwich', 'hot dog'
        ]
        return class_name.lower() in classes_relevantes
    
    def extrair_texto_roi(self, roi):
        """Extrai texto da região usando EasyOCR"""
        try:
            if roi.shape[0] < 20 or roi.shape[1] < 20:  # ROI muito pequena
                return ""
            
            # Melhorar qualidade da imagem
            roi_melhorada = self.melhorar_imagem_ocr(roi)
            
            # OCR
            results = self.reader.readtext(roi_melhorada)
            
            # Filtrar resultados com boa confiança
            textos = []
            for (bbox, text, conf) in results:
                if conf > self.ocr_confidence_threshold:
                    textos.append(text.strip())
            
            return " ".join(textos) if textos else ""
            
        except Exception as e:
            return ""
    
    def melhorar_imagem_ocr(self, roi):
        """Melhora a qualidade da imagem para OCR"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Aumentar contraste
            gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
            
            # Reduzir ruído
            gray = cv2.medianBlur(gray, 3)
            
            # Redimensionar se muito pequena
            h, w = gray.shape
            if h < 50 or w < 50:
                scale = max(50/h, 50/w, 2.0)
                new_h, new_w = int(h * scale), int(w * scale)
                gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            return gray
            
        except:
            return roi
    
    def desenhar_deteccao(self, frame, x1, y1, x2, y2, class_name, confidence, texto):
        """Desenha a detecção no frame"""
        # Cor baseada na classe
        cores = {
            'bottle': (0, 255, 0),    # Verde
            'cup': (255, 0, 0),       # Azul
            'bowl': (0, 255, 255),    # Amarelo
            'default': (255, 255, 0)   # Ciano
        }
        cor = cores.get(class_name, cores['default'])
        
        # Desenhar caixa
        cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)
        
        # Label principal
        label = f"{class_name} ({confidence:.2f})"
        
        # Tamanho do texto
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        # Fundo do texto
        cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 10, y1), cor, -1)
        
        # Texto da classe
        cv2.putText(frame, label, (x1 + 5, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Texto OCR (se houver)
        if texto:
            cv2.putText(frame, texto, (x1, y2 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
    
    def loop_deteccao(self):
        """Loop principal de detecção"""
        if not self.inicializar_camera():
            return
        
        self.detectores_ativos = True
        fps_counter = 0
        tempo_fps = time.time()
        
        print("🎯 Iniciando detecção em tempo real...")
        print("Pressione 'q' para sair ou use a interface web")
        
        while self.detectores_ativos:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ Erro ao ler frame da câmera")
                break
            
            # Processar frame
            frame_processado, deteccoes = self.processar_frame(frame)
            
            # Atualizar frame atual para web interface
            self.frame_atual = frame_processado
            
            # Calcular FPS
            fps_counter += 1
            if time.time() - tempo_fps >= 1.0:
                self.stats['fps'] = fps_counter
                fps_counter = 0
                tempo_fps = time.time()
            
            # Desenhar FPS
            cv2.putText(frame_processado, f"FPS: {self.stats['fps']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Mostrar frame
            cv2.imshow('VerifiK - Detector Copilot YOLO + OCR V1', frame_processado)
            
            # Verificar tecla de saída
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.parar_deteccao()
    
    def parar_deteccao(self):
        """Para a detecção"""
        self.detectores_ativos = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🛑 Detecção parada")
    
    def configurar_rotas(self):
        """Configura as rotas Flask"""
        
        @self.app.route('/')
        def index():
            return render_template('detector_interface.html')
        
        @self.app.route('/video_feed')
        def video_feed():
            return Response(self.gerar_frames(), 
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/stats')
        def get_stats():
            return jsonify(self.stats)
        
        @self.app.route('/start')
        def start_detection():
            if not self.detectores_ativos:
                threading.Thread(target=self.loop_deteccao, daemon=True).start()
                return jsonify({'status': 'started'})
            return jsonify({'status': 'already_running'})
        
        @self.app.route('/stop')
        def stop_detection():
            self.parar_deteccao()
            return jsonify({'status': 'stopped'})
    
    def gerar_frames(self):
        """Gera frames para streaming web"""
        while True:
            if self.frame_atual is not None:
                ret, buffer = cv2.imencode('.jpg', self.frame_atual)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    def executar_web_interface(self):
        """Executa a interface web"""
        print("🌐 Iniciando interface web em http://localhost:5000")
        self.app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    try:
        detector = DetectorCopilotYOLO()
        
        print("\n" + "="*60)
        print("🎯 VERIFIK - DETECTOR COPILOT YOLO + OCR V1")
        print("="*60)
        print("1. YOLOv8 detecta produtos e desenha caixas")
        print("2. OpenCV recorta e melhora as regiões")  
        print("3. EasyOCR lê textos dentro das regiões")
        print("4. Interface web exibe resultados em tempo real")
        print("="*60)
        
        # Opção de execução
        modo = input("\nEscolha o modo:\n1. Terminal (pressione 1)\n2. Web Interface (pressione 2)\nEscolha: ").strip()
        
        if modo == "1":
            detector.loop_deteccao()
        else:
            # Iniciar detecção em background
            threading.Thread(target=detector.loop_deteccao, daemon=True).start()
            # Executar interface web
            detector.executar_web_interface()
            
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        import traceback
        traceback.print_exc()