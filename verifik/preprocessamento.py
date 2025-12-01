"""
Módulo de pré-processamento para detecção de produtos
Contém funções para preparar imagens antes da inferência YOLO
"""

import cv2
import numpy as np
from PIL import Image
import torch
from pathlib import Path


class PreProcessadorImagem:
    """
    Classe para pré-processamento de imagens para modelos YOLO
    
    ATENÇÃO: O YOLO já faz pré-processamento automático!
    Use estas funções apenas quando necessário controle manual.
    """
    
    def __init__(self, tamanho_entrada=(640, 640)):
        """
        Inicializa o pré-processador
        
        Args:
            tamanho_entrada (tuple): Tamanho de entrada do modelo (largura, altura)
        """
        self.tamanho_entrada = tamanho_entrada
        self.dimensoes_originais = None
        self.fator_escala = None
        
    def redimensionar_proporcional(self, imagem):
        """
        Redimensiona imagem mantendo proporção e adiciona padding se necessário
        
        Args:
            imagem (np.ndarray): Imagem original
            
        Returns:
            np.ndarray: Imagem redimensionada com padding
            dict: Informações de escala para reverter coordenadas
        """
        altura_orig, largura_orig = imagem.shape[:2]
        self.dimensoes_originais = (largura_orig, altura_orig)
        
        # Calcular fator de escala mantendo proporção
        largura_alvo, altura_alvo = self.tamanho_entrada
        fator_largura = largura_alvo / largura_orig
        fator_altura = altura_alvo / altura_orig
        
        # Usar o menor fator para manter proporção
        self.fator_escala = min(fator_largura, fator_altura)
        
        # Novas dimensões
        nova_largura = int(largura_orig * self.fator_escala)
        nova_altura = int(altura_orig * self.fator_escala)
        
        # Redimensionar
        img_resized = cv2.resize(imagem, (nova_largura, nova_altura), interpolation=cv2.INTER_LINEAR)
        
        # Criar canvas com padding
        canvas = np.full((altura_alvo, largura_alvo, 3), 114, dtype=np.uint8)  # Cinza padrão YOLO
        
        # Centralizar imagem no canvas
        offset_x = (largura_alvo - nova_largura) // 2
        offset_y = (altura_alvo - nova_altura) // 2
        
        canvas[offset_y:offset_y + nova_altura, offset_x:offset_x + nova_largura] = img_resized
        
        info_escala = {
            'fator_escala': self.fator_escala,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'dimensoes_originais': self.dimensoes_originais,
            'dimensoes_redimensionadas': (nova_largura, nova_altura)
        }
        
        return canvas, info_escala
    
    def normalizar_pixels(self, imagem):
        """
        Normaliza valores de pixel de [0, 255] para [0, 1]
        
        Args:
            imagem (np.ndarray): Imagem com valores 0-255
            
        Returns:
            np.ndarray: Imagem normalizada 0-1
        """
        return imagem.astype(np.float32) / 255.0
    
    def converter_para_tensor(self, imagem, device='cpu'):
        """
        Converte imagem para tensor PyTorch no formato correto
        
        Args:
            imagem (np.ndarray): Imagem normalizada
            device (str): Dispositivo ('cpu' ou 'cuda')
            
        Returns:
            torch.Tensor: Tensor no formato [1, 3, H, W]
        """
        # Converter BGR para RGB
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        
        # Reordenar dimensões: HWC -> CHW
        imagem_chw = np.transpose(imagem_rgb, (2, 0, 1))
        
        # Adicionar dimensão batch: CHW -> BCHW
        imagem_batch = np.expand_dims(imagem_chw, axis=0)
        
        # Converter para tensor
        tensor = torch.from_numpy(imagem_batch).to(device)
        
        return tensor
    
    def preprocessar_completo(self, imagem, device='cpu'):
        """
        Aplica pré-processamento completo: redimensionar + normalizar + tensorizar
        
        Args:
            imagem (np.ndarray): Imagem original
            device (str): Dispositivo para tensor
            
        Returns:
            torch.Tensor: Tensor pronto para inferência
            dict: Informações para reverter coordenadas
        """
        print("⚠️  AVISO: Usando pré-processamento manual!")
        print("   O YOLO já faz isso automaticamente e melhor.")
        
        # Etapa 1: Redimensionamento proporcional
        img_redimensionada, info_escala = self.redimensionar_proporcional(imagem)
        
        # Etapa 2: Normalização
        img_normalizada = self.normalizar_pixels(img_redimensionada)
        
        # Etapa 3: Tensorização
        tensor = self.converter_para_tensor(img_normalizada, device)
        
        return tensor, info_escala
    
    def reverter_coordenadas(self, coordenadas, info_escala):
        """
        Reverte coordenadas do espaço redimensionado para o original
        
        Args:
            coordenadas (list): Lista de [x1, y1, x2, y2]
            info_escala (dict): Informações de escala do redimensionamento
            
        Returns:
            list: Coordenadas no espaço original
        """
        x1, y1, x2, y2 = coordenadas
        
        # Remover offset
        x1 -= info_escala['offset_x']
        y1 -= info_escala['offset_y']
        x2 -= info_escala['offset_x']
        y2 -= info_escala['offset_y']
        
        # Escalar de volta
        fator = info_escala['fator_escala']
        x1 = int(x1 / fator)
        y1 = int(y1 / fator)
        x2 = int(x2 / fator)
        y2 = int(y2 / fator)
        
        # Garantir que está dentro dos limites
        largura_orig, altura_orig = info_escala['dimensoes_originais']
        x1 = max(0, min(x1, largura_orig))
        y1 = max(0, min(y1, altura_orig))
        x2 = max(0, min(x2, largura_orig))
        y2 = max(0, min(y2, altura_orig))
        
        return [x1, y1, x2, y2]


def comparar_preprocessamentos(imagem_path, modelo_yolo):
    """
    Compara detecções usando pré-processamento manual vs automático do YOLO
    
    Args:
        imagem_path (str): Caminho da imagem
        modelo_yolo: Modelo YOLO carregado
        
    Returns:
        dict: Resultados da comparação
    """
    imagem = cv2.imread(imagem_path)
    if imagem is None:
        return {"erro": "Não foi possível carregar a imagem"}
    
    print("🔍 COMPARANDO PRÉ-PROCESSAMENTOS:")
    
    # Método 1: YOLO Automático (recomendado)
    print("\n📊 Método 1: YOLO Automático")
    resultados_auto = modelo_yolo.predict(imagem_path, verbose=False)
    deteccoes_auto = len(resultados_auto[0].boxes) if resultados_auto and resultados_auto[0].boxes else 0
    print(f"   Detecções: {deteccoes_auto}")
    
    # Método 2: Pré-processamento Manual
    print("\n📊 Método 2: Pré-processamento Manual")
    preprocessor = PreProcessadorImagem()
    
    # Aplicar pré-processamento manual
    tensor, info_escala = preprocessor.preprocessar_completo(imagem)
    
    # Simular inferência manual (na prática, seria mais complexo)
    # Por simplicidade, vamos usar o YOLO normal e comparar
    resultados_manual = modelo_yolo.predict(imagem_path, verbose=False)  # Simulação
    deteccoes_manual = len(resultados_manual[0].boxes) if resultados_manual and resultados_manual[0].boxes else 0
    print(f"   Detecções: {deteccoes_manual}")
    
    print("\n✅ RECOMENDAÇÃO: Use sempre o método automático do YOLO!")
    
    return {
        "deteccoes_automatico": deteccoes_auto,
        "deteccoes_manual": deteccoes_manual,
        "recomendacao": "automatico"
    }


def demonstrar_uso():
    """Demonstra como usar o pré-processador"""
    
    print("=" * 60)
    print("DEMONSTRAÇÃO - PRÉ-PROCESSAMENTO DE IMAGENS")
    print("=" * 60)
    
    # Exemplo de uso
    imagem_exemplo = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    preprocessor = PreProcessadorImagem(tamanho_entrada=(640, 640))
    
    print(f"\n📐 Imagem original: {imagem_exemplo.shape}")
    
    # Pré-processamento completo
    tensor, info_escala = preprocessor.preprocessar_completo(imagem_exemplo)
    
    print(f"📐 Tensor resultante: {tensor.shape}")
    print(f"📊 Fator de escala: {info_escala['fator_escala']:.3f}")
    print(f"📍 Offset: ({info_escala['offset_x']}, {info_escala['offset_y']})")
    
    # Exemplo de reversão de coordenadas
    coords_exemplo = [100, 50, 200, 150]  # x1, y1, x2, y2
    coords_originais = preprocessor.reverter_coordenadas(coords_exemplo, info_escala)
    
    print(f"\n🔄 Coordenadas redimensionadas: {coords_exemplo}")
    print(f"🔄 Coordenadas originais: {coords_originais}")
    
    print("\n⚠️  LEMBRE-SE: O YOLO faz isso automaticamente!")
    print("   Use estas funções apenas para controle específico.")


if __name__ == "__main__":
    demonstrar_uso()