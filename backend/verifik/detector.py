"""
VerifiK - Sistema de Detecção por IA
Módulo de visão computacional
"""
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict

class ObjectDetector:
    """Detector de objetos usando YOLOv8"""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Inicializa o detector
        
        Args:
            model_path: Caminho para o modelo YOLO
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = 0.75
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detecta objetos no frame
        
        Args:
            frame: Frame da câmera (numpy array)
            
        Returns:
            Lista de objetos detectados com [classe, confiança, bbox]
        """
        results = self.model(frame, conf=self.confidence_threshold)
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Extrai informações
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
                detections.append({
                    "class_id": cls,
                    "class_name": self.model.names[cls],
                    "confidence": conf,
                    "bbox": bbox
                })
        
        return detections
    
    def count_products(self, detections: List[Dict], product_name: str) -> int:
        """
        Conta quantidade de produtos detectados
        
        Args:
            detections: Lista de detecções
            product_name: Nome do produto (ex: "Skol 350ml")
            
        Returns:
            Quantidade detectada
        """
        count = sum(1 for d in detections if d["class_name"] == product_name)
        return count


class PDVComparator:
    """Compara detecções da câmera com registros do PDV"""
    
    @staticmethod
    def compare(camera_items: Dict[str, int], pdv_items: Dict[str, int]) -> Dict:
        """
        Compara itens da câmera vs PDV
        
        Args:
            camera_items: {"produto": quantidade} detectado pela câmera
            pdv_items: {"produto": quantidade} registrado no PDV
            
        Returns:
            {
                "has_divergence": bool,
                "missing_items": {"produto": quantidade_faltante},
                "total_loss": float
            }
        """
        divergence = {}
        
        for product, camera_qty in camera_items.items():
            pdv_qty = pdv_items.get(product, 0)
            
            if camera_qty > pdv_qty:
                divergence[product] = camera_qty - pdv_qty
        
        has_divergence = len(divergence) > 0
        
        return {
            "has_divergence": has_divergence,
            "missing_items": divergence,
            "total_loss": 0.0  # Calcular baseado em preços
        }


if __name__ == "__main__":
    # Teste básico
    detector = ObjectDetector()
    print("✅ Detector inicializado com sucesso")
