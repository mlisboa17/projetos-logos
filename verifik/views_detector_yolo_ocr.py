"""
Django Views para Sistema YOLOv8 + OCR
Detector Copilot V1 - Integração com Django
"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import cv2
import numpy as np

# Importações condicionais para evitar erros se as bibliotecas não estiverem instaladas
try:
    from ultralytics import YOLO
    import easyocr
    LIBS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Bibliotecas não encontradas: {e}")
    LIBS_AVAILABLE = False

class DetectorYOLOOCR:
    """
    Classe principal para detecção YOLOv8 + OCR integrada com Django
    """
    
    def __init__(self):
        self.modelo_yolo = None
        self.reader_ocr = None
        self.camera = None
        self.detectando = False
        self.estatisticas = {
            'total_deteccoes': 0,
            'fps': 0,
            'produtos_detectados': [],
            'textos_lidos': [],
            'tempo_inicio': None
        }
        self.frame_atual = None
        self.lock = threading.Lock()
        
        # Inicializar modelos se as bibliotecas estiverem disponíveis
        if LIBS_AVAILABLE:
            self.inicializar_modelos()
    
    def inicializar_modelos(self):
        """Inicializa os modelos YOLOv8 e EasyOCR"""
        try:
            print("🔥 Carregando modelo YOLOv8...")
            
            # Tentar carregar modelo personalizado primeiro
            modelo_personalizado = Path(__file__).parent / "verifik_yolov8.pt"
            if modelo_personalizado.exists():
                self.modelo_yolo = YOLO(str(modelo_personalizado))
                print(f"✅ Modelo personalizado carregado: {modelo_personalizado}")
            else:
                # Fallback para modelo pré-treinado
                self.modelo_yolo = YOLO('yolov8n.pt')
                print("✅ Modelo YOLOv8n padrão carregado")
            
            print("📖 Inicializando EasyOCR...")
            self.reader_ocr = easyocr.Reader(['pt', 'en'], gpu=False)
            print("✅ EasyOCR inicializado")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar modelos: {e}")
            raise e
    
    def iniciar_camera(self):
        """Inicia a câmera"""
        try:
            if self.camera is not None:
                self.camera.release()
            
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Não foi possível acessar a câmera")
            
            # Configurar resolução
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar câmera: {e}")
            return False
    
    def processar_frame(self, frame):
        """Processa um frame com YOLOv8 + OCR"""
        try:
            if not LIBS_AVAILABLE or self.modelo_yolo is None:
                return frame, []
            
            # Detecção YOLOv8
            resultados = self.modelo_yolo(frame, verbose=False)
            deteccoes = []
            
            for resultado in resultados:
                boxes = resultado.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extrair informações da detecção
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confianca = float(box.conf[0])
                        classe_id = int(box.cls[0])
                        classe_nome = self.modelo_yolo.names[classe_id]
                        
                        # Filtrar detecções com baixa confiança
                        if confianca < 0.5:
                            continue
                        
                        # Desenhar caixa no frame
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        
                        # Recortar região para OCR
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        regiao_ocr = frame[y1:y2, x1:x2]
                        
                        # Processar OCR na região
                        texto_detectado = ""
                        if regiao_ocr.size > 0 and self.reader_ocr is not None:
                            try:
                                # Melhorar contraste da região
                                regiao_melhorada = cv2.convertScaleAbs(regiao_ocr, alpha=1.5, beta=10)
                                
                                # OCR
                                resultados_ocr = self.reader_ocr.readtext(regiao_melhorada)
                                textos = [resultado[1] for resultado in resultados_ocr if resultado[2] > 0.5]
                                texto_detectado = " ".join(textos)
                                
                            except Exception as e:
                                print(f"⚠️ Erro no OCR: {e}")
                        
                        # Texto para exibir no frame
                        label = f"{classe_nome}: {confianca:.2f}"
                        if texto_detectado:
                            label += f" | {texto_detectado[:20]}..."
                        
                        # Desenhar label
                        cv2.putText(frame, label, (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        
                        # Adicionar à lista de detecções
                        deteccao = {
                            'classe': classe_nome,
                            'confianca': confianca,
                            'bbox': [x1, y1, x2, y2],
                            'texto': texto_detectado,
                            'timestamp': datetime.now().isoformat()
                        }
                        deteccoes.append(deteccao)
                        
                        # Atualizar estatísticas
                        with self.lock:
                            self.estatisticas['total_deteccoes'] += 1
                            if classe_nome not in self.estatisticas['produtos_detectados']:
                                self.estatisticas['produtos_detectados'].append(classe_nome)
                            if texto_detectado and texto_detectado not in self.estatisticas['textos_lidos']:
                                self.estatisticas['textos_lidos'].append(texto_detectado)
            
            return frame, deteccoes
            
        except Exception as e:
            print(f"❌ Erro ao processar frame: {e}")
            return frame, []
    
    def gerar_frames(self):
        """Gerador de frames para streaming"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.detectando:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Processar frame
                frame_processado, deteccoes = self.processar_frame(frame)
                
                # Calcular FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps_end_time = time.time()
                    fps = 30 / (fps_end_time - fps_start_time)
                    with self.lock:
                        self.estatisticas['fps'] = round(fps, 1)
                    fps_start_time = fps_end_time
                
                # Adicionar informações no frame
                cv2.putText(frame_processado, f"FPS: {self.estatisticas['fps']}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame_processado, f"Deteccoes: {self.estatisticas['total_deteccoes']}", 
                          (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Armazenar frame atual
                with self.lock:
                    self.frame_atual = frame_processado.copy()
                
                # Codificar frame para JPEG
                ret, buffer = cv2.imencode('.jpg', frame_processado)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.01)  # Pequena pausa para evitar sobrecarga
                
            except Exception as e:
                print(f"❌ Erro no streaming: {e}")
                break
    
    def iniciar_deteccao(self):
        """Inicia o processo de detecção"""
        if not LIBS_AVAILABLE:
            return False, "Bibliotecas YOLOv8/OCR não instaladas"
        
        if self.detectando:
            return False, "Detecção já está ativa"
        
        if not self.iniciar_camera():
            return False, "Erro ao iniciar câmera"
        
        self.detectando = True
        with self.lock:
            self.estatisticas['tempo_inicio'] = datetime.now()
        
        return True, "Detecção iniciada com sucesso"
    
    def parar_deteccao(self):
        """Para o processo de detecção"""
        self.detectando = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        return True, "Detecção parada com sucesso"
    
    def get_estatisticas(self):
        """Retorna estatísticas atuais"""
        with self.lock:
            return self.estatisticas.copy()

# Instância global do detector
detector_global = DetectorYOLOOCR()

# Views Django

# @login_required  # Removido temporariamente para teste
def detector_interface(request):
    """Página principal da interface do detector"""
    context = {
        'titulo': 'Detector YOLOv8 + OCR V1',
        'libs_available': LIBS_AVAILABLE,
        'detector_status': 'Pronto' if LIBS_AVAILABLE else 'Bibliotecas não instaladas'
    }
    return render(request, 'verifik/detector_yolo_ocr_simples.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def iniciar_deteccao(request):
    """API para iniciar detecção"""
    try:
        sucesso, mensagem = detector_global.iniciar_deteccao()
        return JsonResponse({
            'success': sucesso,
            'message': mensagem,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def parar_deteccao(request):
    """API para parar detecção"""
    try:
        sucesso, mensagem = detector_global.parar_deteccao()
        return JsonResponse({
            'success': sucesso,
            'message': mensagem,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, status=500)

def estatisticas_deteccao(request):
    """API para obter estatísticas"""
    try:
        stats = detector_global.get_estatisticas()
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({
            'error': f'Erro: {str(e)}'
        }, status=500)

def video_feed(request):
    """Stream de vídeo em tempo real"""
    try:
        if not detector_global.detectando:
            # Retornar imagem estática se não estiver detectando
            return StreamingHttpResponse(
                iter([b'--frame\r\n'
                     b'Content-Type: image/jpeg\r\n\r\n'
                     b'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjY2NjIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMThweCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkPDom1lcmEgRGVzY29uZWN0YWRhPC90ZXh0Pjwvc3ZnPg=='
                     b'\r\n']),
                content_type='multipart/x-mixed-replace; boundary=frame'
            )
        
        return StreamingHttpResponse(
            detector_global.gerar_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        print(f"❌ Erro no video feed: {e}")
        return JsonResponse({'error': f'Erro: {str(e)}'}, status=500)

def status_detector(request):
    """Status do sistema detector"""
    return JsonResponse({
        'libs_available': LIBS_AVAILABLE,
        'detectando': detector_global.detectando,
        'camera_conectada': detector_global.camera is not None and detector_global.camera.isOpened() if detector_global.camera else False,
        'yolo_carregado': detector_global.modelo_yolo is not None,
        'ocr_carregado': detector_global.reader_ocr is not None,
        'timestamp': datetime.now().isoformat()
    })

# View para testes (debug)
def teste_detector(request):
    """Página de teste para desenvolvimento"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    context = {
        'libs_available': LIBS_AVAILABLE,
        'detector': detector_global,
        'stats': detector_global.get_estatisticas()
    }
    return render(request, 'verifik/teste_detector.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def processar_imagem_upload(request):
    """Processa imagem enviada via upload"""
    if not LIBS_AVAILABLE:
        return JsonResponse({
            'success': False,
            'message': 'Bibliotecas YOLOv8/OCR não estão instaladas'
        })
    
    try:
        if 'imagem' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma imagem foi enviada'
            })
        
        imagem_file = request.FILES['imagem']
        
        # Ler imagem diretamente da memória
        import numpy as np
        from PIL import Image
        import io
        
        # Converter para array numpy
        img_pil = Image.open(imagem_file)
        img_array = np.array(img_pil)
        
        # Converter RGB para BGR (OpenCV usa BGR)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Processar com YOLOv8
        resultados = detector_global.modelo_yolo(img_array)
        
        produtos_detectados = []
        textos_lidos = []
        
        # Processar detecções
        for resultado in resultados:
            if resultado.boxes is not None:
                for box in resultado.boxes:
                    # Extrair coordenadas da bbox
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confianca = float(box.conf[0])
                    classe_id = int(box.cls[0])
                    
                    if confianca > 0.5:  # Threshold de confiança
                        # Recortar região da detecção
                        regiao = img_array[y1:y2, x1:x2]
                        
                        # Aplicar OCR na região
                        try:
                            texto_resultado = detector_global.reader_ocr.readtext(regiao)
                            for deteccao_texto in texto_resultado:
                                texto = deteccao_texto[1].strip()
                                if len(texto) > 3:  # Texto mínimo
                                    textos_lidos.append(texto)
                        except:
                            pass
                        
                        produtos_detectados.append({
                            'bbox': [x1, y1, x2, y2],
                            'confianca': confianca,
                            'classe': classe_id
                        })
        
        return JsonResponse({
            'success': True,
            'produtos_detectados': produtos_detectados,
            'textos_lidos': textos_lidos,
            'total_deteccoes': len(produtos_detectados),
            'total_textos': len(textos_lidos)
        })
        
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar imagem: {str(e)}'
        })