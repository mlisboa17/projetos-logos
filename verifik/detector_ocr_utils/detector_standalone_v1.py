"""
🎯 DETECTOR COPILOT YOLO + OCR V1 - STANDALONE
Sistema de detecção em tempo real usando YOLOv8 + EasyOCR
Versão independente do Django para teste rápido
"""
import cv2
import time
import numpy as np
from pathlib import Path
import threading

# Importações condicionais
try:
    from ultralytics import YOLO
    import easyocr
    LIBS_OK = True
    print("✅ YOLOv8 e EasyOCR importados com sucesso")
except ImportError as e:
    print(f"❌ Erro: {e}")
    print("💡 Execute: pip install ultralytics easyocr opencv-python")
    LIBS_OK = False

class DetectorStandalone:
    """Detector YOLOv8 + OCR standalone para teste rápido"""
    
    def __init__(self):
        self.modelo_yolo = None
        self.reader_ocr = None
        self.camera = None
        self.detectando = False
        self.stats = {
            'total_deteccoes': 0,
            'fps': 0,
            'produtos_detectados': set(),
            'textos_lidos': set()
        }
        
        if LIBS_OK:
            self.inicializar()
    
    def inicializar(self):
        """Inicializa os modelos"""
        print("🔥 Carregando YOLOv8...")
        
        # Tentar modelo personalizado primeiro
        modelo_personalizado = Path("verifik/verifik_yolov8.pt")
        if modelo_personalizado.exists():
            self.modelo_yolo = YOLO(str(modelo_personalizado))
            print(f"✅ Modelo personalizado: {modelo_personalizado}")
        else:
            self.modelo_yolo = YOLO('yolov8n.pt')  # Modelo padrão
            print("✅ Modelo YOLOv8n padrão carregado")
        
        print("📖 Carregando EasyOCR...")
        self.reader_ocr = easyocr.Reader(['pt', 'en'], gpu=False)
        print("✅ EasyOCR carregado")
    
    def processar_frame(self, frame):
        """Processa um frame com YOLOv8 + OCR"""
        if not LIBS_OK:
            return frame
        
        # YOLOv8 Detection
        results = self.modelo_yolo(frame, verbose=False)
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    # Extrair dados da detecção
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confianca = float(box.conf[0])
                    classe_id = int(box.cls[0])
                    classe_nome = self.modelo_yolo.names[classe_id]
                    
                    # Filtrar detecções fracas
                    if confianca < 0.5:
                        continue
                    
                    # Atualizar estatísticas
                    self.stats['total_deteccoes'] += 1
                    self.stats['produtos_detectados'].add(classe_nome)
                    
                    # Desenhar caixa
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # OCR na região detectada
                    roi = frame[y1:y2, x1:x2]
                    texto_detectado = ""
                    
                    if roi.size > 0:
                        try:
                            # Melhorar contraste
                            roi_melhorado = cv2.convertScaleAbs(roi, alpha=1.5, beta=10)
                            
                            # Executar OCR
                            resultados_ocr = self.reader_ocr.readtext(roi_melhorado)
                            textos = [r[1] for r in resultados_ocr if r[2] > 0.5]
                            texto_detectado = " ".join(textos)
                            
                            if texto_detectado:
                                self.stats['textos_lidos'].add(texto_detectado)
                        
                        except Exception as e:
                            pass  # Ignorar erros de OCR
                    
                    # Label para exibir
                    label = f"{classe_nome}: {confianca:.2f}"
                    if texto_detectado:
                        label += f" | {texto_detectado[:15]}..."
                    
                    # Desenhar texto
                    cv2.putText(frame, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return frame
    
    def executar(self):
        """Executa o detector em tempo real"""
        if not LIBS_OK:
            print("❌ Bibliotecas não disponíveis")
            return
        
        print("🎥 Iniciando câmera...")
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            print("❌ Erro: Não foi possível acessar a câmera")
            return
        
        # Configurar câmera
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("🚀 Detector iniciado!")
        print("📋 Controles:")
        print("   'q' - Sair")
        print("   's' - Mostrar estatísticas")
        print("   'r' - Reset estatísticas")
        
        self.detectando = True
        fps_counter = 0
        fps_start = time.time()
        
        try:
            while self.detectando:
                ret, frame = self.camera.read()
                if not ret:
                    print("❌ Erro ao capturar frame")
                    break
                
                # Processar frame
                frame_processado = self.processar_frame(frame)
                
                # Calcular FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps_end = time.time()
                    self.stats['fps'] = round(30 / (fps_end - fps_start), 1)
                    fps_start = fps_end
                
                # Adicionar informações no frame
                cv2.putText(frame_processado, f"FPS: {self.stats['fps']}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.putText(frame_processado, f"Deteccoes: {self.stats['total_deteccoes']}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.putText(frame_processado, f"Produtos: {len(self.stats['produtos_detectados'])}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Exibir frame
                cv2.imshow('🎯 Detector YOLOv8 + OCR V1', frame_processado)
                
                # Processar teclas
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("🛑 Saindo...")
                    break
                elif key == ord('s'):
                    self.mostrar_estatisticas()
                elif key == ord('r'):
                    self.reset_estatisticas()
        
        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
        
        finally:
            self.parar()
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas na console"""
        print("\n" + "="*50)
        print("📊 ESTATÍSTICAS")
        print("="*50)
        print(f"Total de Detecções: {self.stats['total_deteccoes']}")
        print(f"FPS Atual: {self.stats['fps']}")
        print(f"Produtos Únicos: {len(self.stats['produtos_detectados'])}")
        print(f"Textos Únicos: {len(self.stats['textos_lidos'])}")
        
        if self.stats['produtos_detectados']:
            print(f"\nProdutos Detectados:")
            for produto in sorted(self.stats['produtos_detectados']):
                print(f"  • {produto}")
        
        if self.stats['textos_lidos']:
            print(f"\nTextos Lidos:")
            for texto in sorted(list(self.stats['textos_lidos'])[:10]):  # Só os primeiros 10
                print(f"  📝 {texto}")
        
        print("="*50 + "\n")
    
    def reset_estatisticas(self):
        """Reset das estatísticas"""
        self.stats = {
            'total_deteccoes': 0,
            'fps': 0,
            'produtos_detectados': set(),
            'textos_lidos': set()
        }
        print("🔄 Estatísticas resetadas")
    
    def parar(self):
        """Para o detector"""
        self.detectando = False
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Detector finalizado")

def main():
    """Função principal"""
    print("="*60)
    print("🎯 DETECTOR COPILOT YOLO + OCR V1")
    print("="*60)
    print("Sistema de detecção inteligente em tempo real")
    print("YOLOv8 (objetos) + EasyOCR (texto) + OpenCV (processamento)")
    print("="*60)
    
    if not LIBS_OK:
        print("\n❌ Sistema não pode ser executado")
        print("\n💡 Para instalar as dependências:")
        print("pip install ultralytics easyocr opencv-python torch torchvision")
        return
    
    # Criar e executar detector
    detector = DetectorStandalone()
    
    try:
        detector.executar()
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        detector.mostrar_estatisticas()

if __name__ == "__main__":
    main()