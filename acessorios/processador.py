"""
Processador de Imagens Genérico
Suporta múltiplos tipos de processamento e filtros
"""
import os
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np
from datetime import datetime

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


class ProcessadorImagensGenerico:
    """Classe para processar imagens com múltiplos filtros"""
    
    def __init__(self, diretorio_saida='media/produtos/processadas'):
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        
    def remover_fundo(self, caminho_imagem, nome_saida=None):
        """Remove o fundo da imagem usando rembg"""
        if not REMBG_AVAILABLE:
            raise ImportError("rembg não está instalado. Execute: pip install rembg")
        
        img_path = Path(caminho_imagem)
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")
        
        # Carregar e processar
        imagem = Image.open(img_path)
        imagem_sem_fundo = remove(imagem)
        
        # Salvar resultado
        if nome_saida is None:
            nome_saida = f"{img_path.stem}_no_bg.png"
        
        caminho_saida = self.diretorio_saida / nome_saida
        imagem_sem_fundo.save(caminho_saida)
        
        return str(caminho_saida)
    
    def remover_fundo_lote(self, caminhos_imagens, prefixo=''):
        """Processa múltiplas imagens em lote"""
        resultados = []
        erros = []
        
        for caminho in caminhos_imagens:
            try:
                nome_saida = f"{prefixo}_{Path(caminho).stem}_no_bg.png"
                resultado = self.remover_fundo(caminho, nome_saida)
                resultados.append({
                    'original': str(caminho),
                    'processada': resultado,
                    'status': 'sucesso'
                })
            except Exception as e:
                erros.append({
                    'arquivo': str(caminho),
                    'erro': str(e)
                })
        
        return resultados, erros
    
    def redimensionar(self, caminho_imagem, largura=640, altura=480, nome_saida=None):
        """Redimensiona a imagem mantendo proporção"""
        img_path = Path(caminho_imagem)
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")
        
        imagem = Image.open(img_path)
        imagem_redimensionada = imagem.resize((largura, altura), Image.Resampling.LANCZOS)
        
        if nome_saida is None:
            nome_saida = f"{img_path.stem}_resized.jpg"
        
        caminho_saida = self.diretorio_saida / nome_saida
        imagem_redimensionada.save(caminho_saida, quality=95)
        
        return str(caminho_saida)
    
    def normalizar_cores(self, caminho_imagem, nome_saida=None):
        """Normaliza as cores da imagem"""
        img_path = Path(caminho_imagem)
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")
        
        imagem = Image.open(img_path).convert('RGB')
        array = np.array(imagem, dtype=np.float32)
        
        # Normalizar cada canal
        for i in range(3):
            min_val = array[:, :, i].min()
            max_val = array[:, :, i].max()
            if max_val > min_val:
                array[:, :, i] = ((array[:, :, i] - min_val) / (max_val - min_val)) * 255
        
        imagem_normalizada = Image.fromarray(array.astype(np.uint8))
        
        if nome_saida is None:
            nome_saida = f"{img_path.stem}_normalized.jpg"
        
        caminho_saida = self.diretorio_saida / nome_saida
        imagem_normalizada.save(caminho_saida, quality=95)
        
        return str(caminho_saida)
    
    def aumentar_contraste(self, caminho_imagem, fator=1.5, nome_saida=None):
        """Aumenta o contraste da imagem"""
        img_path = Path(caminho_imagem)
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")
        
        imagem = Image.open(img_path)
        enhancer = ImageEnhance.Contrast(imagem)
        imagem_contrastada = enhancer.enhance(fator)
        
        if nome_saida is None:
            nome_saida = f"{img_path.stem}_contrast.jpg"
        
        caminho_saida = self.diretorio_saida / nome_saida
        imagem_contrastada.save(caminho_saida, quality=95)
        
        return str(caminho_saida)
    
    def processar_lote(self, tipo_processamento, caminhos_imagens, **kwargs):
        """Processa um lote de imagens com um tipo de processamento"""
        metodo = getattr(self, tipo_processamento, None)
        
        if metodo is None:
            raise ValueError(f"Tipo de processamento não suportado: {tipo_processamento}")
        
        resultados = []
        erros = []
        
        # Extrar prefixo se fornecido
        prefixo = kwargs.pop('prefixo', '')
        
        for i, caminho in enumerate(caminhos_imagens, 1):
            try:
                # Gerar nome de saída
                nome_saida = f"{prefixo}_{Path(caminho).stem}_{tipo_processamento}.png"
                
                # Remover problemas de nome de arquivo
                nome_saida = nome_saida.replace('__', '_').replace(' ', '_')
                
                # Chamar método com os kwargs apropriados
                if tipo_processamento == 'remover_fundo':
                    resultado = self.remover_fundo(caminho, nome_saida)
                elif tipo_processamento == 'redimensionar':
                    largura = kwargs.get('largura', 640)
                    altura = kwargs.get('altura', 480)
                    resultado = self.redimensionar(caminho, largura, altura, nome_saida)
                elif tipo_processamento == 'normalizar_cores':
                    resultado = self.normalizar_cores(caminho, nome_saida)
                elif tipo_processamento == 'aumentar_contraste':
                    fator = kwargs.get('fator', 1.5)
                    resultado = self.aumentar_contraste(caminho, fator, nome_saida)
                else:
                    raise ValueError(f"Tipo desconhecido: {tipo_processamento}")
                
                resultados.append({
                    'original': str(caminho),
                    'processada': resultado,
                    'status': 'sucesso'
                })
            except Exception as e:
                erros.append({
                    'arquivo': str(caminho),
                    'erro': str(e)[:100]
                })
        
        return resultados, erros
