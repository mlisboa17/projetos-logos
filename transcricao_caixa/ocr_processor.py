"""
Processador OCR usando Tesseract
Extrai texto de imagens de documentos fiscais
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TesseractOCRProcessor:
    """Processador de OCR usando Tesseract"""
    
    def __init__(self, tesseract_cmd=None):
        """
        Inicializa o processador
        
        Args:
            tesseract_cmd: Caminho para o executável do Tesseract
                          Se None, usa o padrão do sistema
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Configurações padrão para português
        self.config_padrao = '--oem 3 --psm 6'
        self.lang = 'por'  # Português
    
    def preprocessar_imagem(self, imagem_path):
        """
        Pré-processa imagem para melhorar OCR
        
        Args:
            imagem_path: Caminho da imagem
            
        Returns:
            PIL.Image: Imagem processada
        """
        try:
            # Abrir imagem
            img = Image.open(imagem_path)
            
            # Converter para escala de cinza
            img = img.convert('L')
            
            # Aumentar contraste
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)
            
            # Aumentar nitidez
            img = img.filter(ImageFilter.SHARPEN)
            
            # Binarização (preto e branco)
            threshold = 150
            img = img.point(lambda p: p > threshold and 255)
            
            return img
            
        except Exception as e:
            logger.error(f"Erro ao preprocessar imagem: {e}")
            # Retornar imagem original se falhar
            return Image.open(imagem_path)
    
    def extrair_texto(self, imagem_path, preprocessar=True):
        """
        Extrai texto completo da imagem
        
        Args:
            imagem_path: Caminho da imagem
            preprocessar: Se deve preprocessar a imagem
            
        Returns:
            dict: {
                'texto': str,
                'confianca': float,
                'sucesso': bool,
                'erro': str
            }
        """
        try:
            # Preprocessar se solicitado
            if preprocessar:
                img = self.preprocessar_imagem(imagem_path)
            else:
                img = Image.open(imagem_path)
            
            # Extrair texto
            texto = pytesseract.image_to_string(
                img,
                lang=self.lang,
                config=self.config_padrao
            )
            
            # Calcular confiança média
            dados = pytesseract.image_to_data(
                img,
                lang=self.lang,
                config=self.config_padrao,
                output_type=pytesseract.Output.DICT
            )
            
            confiances = [int(conf) for conf in dados['conf'] if conf != '-1']
            confianca_media = sum(confiances) / len(confiances) if confiances else 0
            
            return {
                'texto': texto.strip(),
                'confianca': round(confianca_media, 2),
                'sucesso': True,
                'erro': None
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            return {
                'texto': '',
                'confianca': 0,
                'sucesso': False,
                'erro': str(e)
            }
    
    def extrair_valores_monetarios(self, texto):
        """
        Extrai valores monetários do texto
        
        Args:
            texto: Texto extraído
            
        Returns:
            list: Lista de valores encontrados (Decimal)
        """
        # Padrões de valores monetários brasileiros
        padroes = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # R$ 1.234,56
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',         # 1.234,56
            r'(\d+,\d{2})',                          # 123,45
        ]
        
        valores = []
        for padrao in padroes:
            matches = re.findall(padrao, texto)
            for match in matches:
                try:
                    # Converter formato BR para Decimal
                    valor_str = match.replace('.', '').replace(',', '.')
                    valores.append(Decimal(valor_str))
                except:
                    continue
        
        return valores
    
    def extrair_datas(self, texto):
        """
        Extrai datas do texto
        
        Args:
            texto: Texto extraído
            
        Returns:
            list: Lista de datas encontradas (datetime.date)
        """
        datas = []
        
        # Padrões de data brasileiros
        padroes = [
            r'(\d{2})[/-](\d{2})[/-](\d{4})',  # DD/MM/YYYY ou DD-MM-YYYY
            r'(\d{2})[/-](\d{2})[/-](\d{2})',  # DD/MM/YY
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, texto)
            for match in matches:
                try:
                    if len(match[2]) == 2:  # Ano com 2 dígitos
                        ano = int('20' + match[2])
                    else:
                        ano = int(match[2])
                    
                    data = datetime(ano, int(match[1]), int(match[0])).date()
                    datas.append(data)
                except:
                    continue
        
        return datas
    
    def extrair_numeros_documento(self, texto):
        """
        Extrai possíveis números de documento
        
        Args:
            texto: Texto extraído
            
        Returns:
            list: Lista de números encontrados
        """
        numeros = []
        
        # Padrões comuns em documentos fiscais
        padroes = [
            r'N[FºF°]\s*:?\s*(\d+)',              # NF: 123456
            r'NOTA\s*(?:FISCAL)?\s*:?\s*(\d+)',   # NOTA FISCAL: 123456
            r'CUPOM\s*:?\s*(\d+)',                 # CUPOM: 123456
            r'DOC\s*:?\s*(\d+)',                   # DOC: 123456
            r'N[UÚ]MERO\s*:?\s*(\d+)',            # NÚMERO: 123456
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            numeros.extend(matches)
        
        return list(set(numeros))  # Remover duplicatas
    
    def processar_documento_completo(self, imagem_path):
        """
        Processa documento e extrai todas as informações
        
        Args:
            imagem_path: Caminho da imagem
            
        Returns:
            dict: Dados extraídos estruturados
        """
        # Extrair texto
        resultado = self.extrair_texto(imagem_path)
        
        if not resultado['sucesso']:
            return resultado
        
        texto = resultado['texto']
        
        # Extrair informações específicas
        valores = self.extrair_valores_monetarios(texto)
        datas = self.extrair_datas(texto)
        numeros = self.extrair_numeros_documento(texto)
        
        # Determinar valor total (maior valor encontrado)
        valor_total = max(valores) if valores else Decimal('0')
        
        # Determinar data do documento (primeira data encontrada)
        data_documento = datas[0] if datas else None
        
        # Determinar número do documento (primeiro número encontrado)
        numero_documento = numeros[0] if numeros else ''
        
        return {
            'texto': texto,
            'confianca': resultado['confianca'],
            'sucesso': True,
            'erro': None,
            'dados_extraidos': {
                'valor_total': float(valor_total),
                'valores_encontrados': [float(v) for v in valores],
                'data_documento': data_documento.isoformat() if data_documento else None,
                'datas_encontradas': [d.isoformat() for d in datas],
                'numero_documento': numero_documento,
                'numeros_encontrados': numeros,
            }
        }
    
    def detectar_tipo_documento(self, texto):
        """
        Detecta o tipo de documento baseado no texto
        
        Args:
            texto: Texto extraído
            
        Returns:
            str: Tipo detectado ('nota_fiscal', 'cupom', 'recibo', 'desconhecido')
        """
        texto_upper = texto.upper()
        
        if 'NOTA FISCAL' in texto_upper or 'NF-E' in texto_upper:
            return 'nota_fiscal'
        elif 'CUPOM FISCAL' in texto_upper or 'CF-E' in texto_upper:
            return 'cupom'
        elif 'RECIBO' in texto_upper:
            return 'recibo'
        else:
            return 'desconhecido'


def testar_tesseract():
    """Testa se Tesseract está instalado e funcionando"""
    try:
        versao = pytesseract.get_tesseract_version()
        return True, f"Tesseract instalado: {versao}"
    except Exception as e:
        return False, f"Tesseract não encontrado: {e}"
