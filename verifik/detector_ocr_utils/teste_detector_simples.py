"""
Teste simples do Detector YOLOv8 + OCR
Para testar rapidamente sem toda a estrutura Django
"""
import os
import sys
import cv2
import time
from pathlib import Path

# Adicionar o diretório do projeto ao path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')

# Importações condicionais
try:
    from ultralytics import YOLO
    import easyocr
    print("✅ Bibliotecas YOLOv8 e EasyOCR importadas com sucesso")
    LIBS_OK = True
except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas: {e}")
    LIBS_OK = False

def teste_camera():
    """Teste básico da câmera"""
    print("\n🎥 TESTANDO CÂMERA...")
    
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ Não foi possível acessar a câmera")
        return False
    
    print("✅ Câmera acessível")
    
    # Capturar alguns frames
    for i in range(5):
        ret, frame = camera.read()
        if ret:
            print(f"  📸 Frame {i+1}: {frame.shape}")
        else:
            print(f"  ❌ Erro ao capturar frame {i+1}")
    
    camera.release()
    return True

def teste_yolo():
    """Teste básico do YOLOv8"""
    if not LIBS_OK:
        print("\n❌ Bibliotecas não disponíveis")
        return False
    
    print("\n🤖 TESTANDO YOLOv8...")
    
    try:
        # Tentar carregar modelo personalizado primeiro
        modelo_personalizado = BASE_DIR / "verifik" / "verifik_yolov8.pt"
        if modelo_personalizado.exists():
            model = YOLO(str(modelo_personalizado))
            print(f"✅ Modelo personalizado carregado: {modelo_personalizado}")
        else:
            model = YOLO('yolov8n.pt')
            print("✅ Modelo YOLOv8n padrão carregado")
        
        # Teste com imagem dummy
        import numpy as np
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = model(test_image, verbose=False)
        
        print(f"✅ Detecção test realizada: {len(results)} resultado(s)")
        return True
        
    except Exception as e:
        print(f"❌ Erro no YOLOv8: {e}")
        return False

def teste_ocr():
    """Teste básico do EasyOCR"""
    if not LIBS_OK:
        print("\n❌ Bibliotecas não disponíveis")
        return False
    
    print("\n📖 TESTANDO EasyOCR...")
    
    try:
        reader = easyocr.Reader(['pt', 'en'], gpu=False)
        print("✅ EasyOCR inicializado")
        
        # Criar imagem de teste com texto
        import numpy as np
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "TESTE OCR", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        results = reader.readtext(test_image)
        print(f"✅ OCR test realizado: {len(results)} resultado(s)")
        
        for result in results:
            print(f"  📝 Texto detectado: '{result[1]}' (confiança: {result[2]:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no EasyOCR: {e}")
        return False

def teste_detector_completo():
    """Teste do detector completo com câmera"""
    if not LIBS_OK:
        print("\n❌ Bibliotecas não disponíveis")
        return False
    
    print("\n🎯 TESTANDO DETECTOR COMPLETO...")
    
    try:
        # Inicializar modelos
        modelo_personalizado = BASE_DIR / "verifik" / "verifik_yolov8.pt"
        if modelo_personalizado.exists():
            model = YOLO(str(modelo_personalizado))
            print(f"✅ Modelo YOLO carregado: {modelo_personalizado}")
        else:
            model = YOLO('yolov8n.pt')
            print("✅ Modelo YOLO padrão carregado")
        
        reader = easyocr.Reader(['pt', 'en'], gpu=False)
        print("✅ EasyOCR carregado")
        
        # Tentar câmera
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("❌ Câmera não disponível - usando imagem estática")
            return False
        
        print("✅ Iniciando detecção em tempo real (pressione 'q' para sair)")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = camera.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Processar apenas alguns frames para teste
            if frame_count % 30 == 0:  # A cada 30 frames
                # YOLOv8 detection
                results = model(frame, verbose=False)
                detections = 0
                
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            
                            if conf > 0.5:
                                detections += 1
                                
                                # Desenhar caixa
                                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                                
                                # Recortar região para OCR
                                roi = frame[int(y1):int(y2), int(x1):int(x2)]
                                if roi.size > 0:
                                    try:
                                        ocr_results = reader.readtext(roi)
                                        text = ' '.join([r[1] for r in ocr_results if r[2] > 0.5])
                                        if text:
                                            cv2.putText(frame, text[:20], (int(x1), int(y1)-10),
                                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                                    except:
                                        pass
                
                # Calcular FPS
                fps = frame_count / (time.time() - start_time)
                cv2.putText(frame, f"FPS: {fps:.1f} | Det: {detections}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostrar frame
            cv2.imshow('Detector YOLOv8 + OCR - Teste', frame)
            
            # Sair com 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        camera.release()
        cv2.destroyAllWindows()
        
        print(f"✅ Teste concluído - Processados {frame_count} frames")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste completo: {e}")
        return False

def main():
    """Função principal de teste"""
    print("="*60)
    print("🎯 TESTE DO SISTEMA DETECTOR YOLOv8 + OCR")
    print("="*60)
    
    # Status das bibliotecas
    print(f"\n📦 Bibliotecas YOLOv8/OCR: {'✅ OK' if LIBS_OK else '❌ ERRO'}")
    
    if not LIBS_OK:
        print("\n💡 Para instalar as bibliotecas:")
        print("   pip install ultralytics easyocr opencv-python")
        return
    
    # Executar testes
    testes = [
        ("Câmera", teste_camera),
        ("YOLOv8", teste_yolo),
        ("EasyOCR", teste_ocr)
    ]
    
    resultados = {}
    
    for nome, func in testes:
        print(f"\n{'='*40}")
        resultado = func()
        resultados[nome] = resultado
    
    # Resumo
    print(f"\n{'='*60}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    for nome, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"  {nome:15} : {status}")
    
    # Teste completo se todos passaram
    if all(resultados.values()):
        print(f"\n🚀 Todos os testes passaram! Executando teste completo...")
        input("\nPressione ENTER para iniciar o teste com câmera (ou Ctrl+C para cancelar)")
        teste_detector_completo()
    else:
        print(f"\n⚠️ Alguns testes falharam. Verifique as dependências.")

if __name__ == "__main__":
    main()