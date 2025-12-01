"""
Exemplo de uso das câmeras do VerifiK para detecção de produtos
Demonstra como integrar câmera + IA + banco de dados
"""

import os
import django
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import Camera, DeteccaoProduto, ProdutoMae
from accounts.models import User


class DetectorProdutosCamara:
    """
    Sistema de detecção de produtos via câmera
    
    Funcionalidades:
    - Conecta à câmera IP
    - Captura frames em tempo real
    - Detecta produtos (bounding boxes)
    - Registra detecções no banco de dados
    - Exibe estatísticas
    """
    
    def __init__(self, camera_id):
        """
        Args:
            camera_id: ID da câmera no banco de dados
        """
        self.camera = Camera.objects.get(id=camera_id)
        self.cap = None
        self.deteccoes_count = 0
        self.frames_processados = 0
        
        print(f"🎥 Detector inicializado para: {self.camera.nome}")
        print(f"   Local: {self.camera.localizacao}")
        print(f"   URL: {self.camera.url_stream}")
    
    def conectar(self):
        """Conecta à câmera"""
        print(f"\n⏳ Conectando à câmera...")
        self.cap = cv2.VideoCapture(self.camera.url_stream)
        
        if not self.cap.isOpened():
            raise Exception(f"❌ Não foi possível conectar à câmera {self.camera.nome}")
        
        # Atualizar status
        self.camera.ultima_conexao = datetime.now()
        self.camera.status = 'ATIVA'
        self.camera.save()
        
        print("✅ Conectado!")
        return True
    
    def detectar_produtos_frame(self, frame):
        """
        Detecta produtos em um frame
        
        NOTA: Este é um exemplo simplificado.
        Em produção, você usaria um modelo de IA real (YOLO, Faster R-CNN, etc.)
        
        Args:
            frame: Frame capturado da câmera
            
        Returns:
            list: Lista de detecções [{produto, confianca, bbox}, ...]
        """
        deteccoes = []
        
        # ========================================
        # EXEMPLO SIMPLIFICADO DE DETECÇÃO
        # ========================================
        # Em produção, substituir por:
        # - Modelo YOLO treinado
        # - TensorFlow/PyTorch
        # - API de detecção de objetos
        
        # Para demonstração, vamos simular detecção por cores
        # (produtos com embalagem vermelha, azul, etc.)
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detectar objetos vermelhos (exemplo: Coca-Cola)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red, upper_red)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Ignorar objetos muito pequenos
            if area < 1000:
                continue
            
            # Obter bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Simular confiança da detecção
            confianca = min(0.95, area / 10000)
            
            deteccoes.append({
                'produto_nome': 'Coca-Cola 2L',  # Em produção, vem do modelo IA
                'confianca': confianca,
                'bbox': (x, y, w, h),
                'area': area
            })
        
        return deteccoes
    
    def registrar_deteccao(self, produto_nome, confianca, bbox, frame):
        """
        Registra uma detecção no banco de dados
        
        Args:
            produto_nome: Nome do produto detectado
            confianca: Confiança da detecção (0-1)
            bbox: Bounding box (x, y, w, h)
            frame: Frame onde foi detectado
        """
        try:
            # Buscar produto no banco
            produto = ProdutoMae.objects.filter(nome__icontains=produto_nome).first()
            
            if not produto:
                print(f"⚠️ Produto '{produto_nome}' não encontrado no catálogo")
                return None
            
            # Salvar recorte do produto
            x, y, w, h = bbox
            recorte = frame[y:y+h, x:x+w]
            
            pasta_deteccoes = Path(__file__).parent / 'deteccoes_camera'
            pasta_deteccoes.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            arquivo = f"det_{self.camera.id}_{timestamp}.jpg"
            caminho = pasta_deteccoes / arquivo
            
            cv2.imwrite(str(caminho), recorte)
            
            # Criar registro de detecção
            deteccao = DeteccaoProduto.objects.create(
                camera=self.camera,
                produto_identificado=produto,
                confianca=confianca,
                imagem_deteccao=str(caminho),
                metodo_deteccao='YOLO',  # Ou seu modelo
                bbox_x=x,
                bbox_y=y,
                bbox_largura=w,
                bbox_altura=h
            )
            
            self.deteccoes_count += 1
            
            print(f"✅ Detecção registrada: {produto.nome} ({confianca*100:.1f}%)")
            
            # Atualizar última detecção da câmera
            self.camera.ultima_deteccao = datetime.now()
            self.camera.save()
            
            return deteccao
            
        except Exception as e:
            print(f"❌ Erro ao registrar detecção: {e}")
            return None
    
    def processar_stream(self, duracao_segundos=60, exibir_video=True):
        """
        Processa o stream da câmera detectando produtos
        
        Args:
            duracao_segundos: Tempo de processamento (0 = infinito)
            exibir_video: Se True, exibe vídeo com bounding boxes
        """
        if not self.cap or not self.cap.isOpened():
            self.conectar()
        
        print(f"\n🔄 Iniciando detecção de produtos...")
        print(f"   Duração: {'Infinito' if duracao_segundos == 0 else f'{duracao_segundos}s'}")
        print(f"   Pressione 'q' para sair")
        print(f"   Pressione 's' para salvar frame")
        print()
        
        inicio = datetime.now()
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("⚠️ Erro ao ler frame")
                    break
                
                self.frames_processados += 1
                
                # Detectar produtos no frame
                deteccoes = self.detectar_produtos_frame(frame)
                
                # Desenhar bounding boxes
                frame_display = frame.copy()
                
                for det in deteccoes:
                    x, y, w, h = det['bbox']
                    confianca = det['confianca']
                    produto = det['produto_nome']
                    
                    # Desenhar retângulo
                    cor = (0, 255, 0) if confianca > 0.7 else (0, 255, 255)
                    cv2.rectangle(frame_display, (x, y), (x+w, y+h), cor, 2)
                    
                    # Texto com produto e confiança
                    texto = f"{produto} {confianca*100:.0f}%"
                    cv2.putText(frame_display, texto, (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
                    
                    # Registrar no banco (apenas se confiança > 70%)
                    if confianca > 0.7:
                        self.registrar_deteccao(produto, confianca, det['bbox'], frame)
                
                # Informações no frame
                tempo_decorrido = (datetime.now() - inicio).total_seconds()
                fps = self.frames_processados / tempo_decorrido if tempo_decorrido > 0 else 0
                
                info_texto = f"{self.camera.nome} | FPS: {fps:.1f} | Deteccoes: {self.deteccoes_count}"
                cv2.putText(frame_display, info_texto, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if exibir_video:
                    cv2.imshow('VerifiK - Detecção de Produtos', frame_display)
                
                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n👋 Encerrando...")
                    break
                elif key == ord('s'):
                    # Salvar frame
                    pasta_capturas = Path(__file__).parent / 'capturas_deteccao'
                    pasta_capturas.mkdir(exist_ok=True)
                    
                    arquivo = f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(str(pasta_capturas / arquivo), frame_display)
                    print(f"📸 Frame salvo: {arquivo}")
                
                # Verificar tempo limite
                if duracao_segundos > 0 and tempo_decorrido >= duracao_segundos:
                    print(f"\n⏱️ Tempo limite atingido")
                    break
            
            # Estatísticas finais
            tempo_total = (datetime.now() - inicio).total_seconds()
            print(f"\n{'='*70}")
            print("📊 ESTATÍSTICAS DA SESSÃO")
            print(f"{'='*70}")
            print(f"⏱️  Tempo total: {tempo_total:.1f}s")
            print(f"🎞️  Frames processados: {self.frames_processados}")
            print(f"📊 FPS médio: {self.frames_processados/tempo_total:.1f}")
            print(f"🎯 Detecções: {self.deteccoes_count}")
            print(f"📈 Taxa de detecção: {self.deteccoes_count/self.frames_processados*100:.2f}%")
            print(f"{'='*70}\n")
            
        finally:
            self.desconectar()
    
    def desconectar(self):
        """Desconecta da câmera"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("👋 Desconectado da câmera")


def exemplo_uso():
    """Exemplo de uso do detector"""
    
    # Listar câmeras disponíveis
    print("="*70)
    print("🎥 CÂMERAS DISPONÍVEIS")
    print("="*70)
    
    cameras = Camera.objects.filter(ativa=True)
    
    if not cameras.exists():
        print("❌ Nenhuma câmera cadastrada")
        print("\nCadastre uma câmera primeiro:")
        print("  python conectar_camera_verifik.py")
        return
    
    for i, cam in enumerate(cameras, 1):
        print(f"{i}. {cam.nome} - {cam.localizacao}")
        print(f"   Status: {cam.get_status_display()}")
        print()
    
    try:
        escolha = int(input("Escolha uma câmera: ")) - 1
        
        if escolha < 0 or escolha >= len(cameras):
            print("❌ Opção inválida")
            return
        
        camera = cameras[escolha]
        
        # Criar detector
        detector = DetectorProdutosCamara(camera.id)
        
        # Processar stream
        detector.processar_stream(duracao_segundos=0, exibir_video=True)
        
    except ValueError:
        print("❌ Digite um número válido")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == '__main__':
    exemplo_uso()
