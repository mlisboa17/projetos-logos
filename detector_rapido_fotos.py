"""
Detector Rápido para Fotos - Versão Otimizada
Processa imagens diretamente sem automação GUI
"""

import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from ultralytics import YOLO
import json
from datetime import datetime

class DetectorRapidoFotos:
    def __init__(self):
        """Inicializa o detector com configurações otimizadas"""
        
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Carregar modelo YOLO leve
        try:
            self.modelo = YOLO('yolov8n.pt')  # Modelo mais rápido
            print("✓ Modelo YOLO carregado")
        except:
            print("✗ Erro ao carregar YOLO")
            self.modelo = None
            
        # Marcas conhecidas (otimizado)
        self.marcas = {
            'heineken': ['heineken', 'heinken'],
            'budweiser': ['budweiser', 'bud'],
            'devassa': ['devassa', 'devasa'],
            'corona': ['corona', 'coroa'],
            'stella': ['stella', 'artois'],
            'brahma': ['brahma', 'brama'],
            'skol': ['skol', 'scol'],
            'antarctica': ['antarctica', 'antartica'],
            'original': ['original'],
            'eisenbahn': ['eisenbahn', 'eisen'],
            'bohemia': ['bohemia', 'boemia']
        }
        
        # Configuração OCR otimizada
        self.config_ocr = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        
    def preprocessar_rapido(self, imagem):
        """Preprocessamento rápido da imagem"""
        
        # Redimensionar se muito grande (acelera processamento)
        altura, largura = imagem.shape[:2]
        if largura > 1200:
            fator = 1200 / largura
            nova_largura = int(largura * fator)
            nova_altura = int(altura * fator)
            imagem = cv2.resize(imagem, (nova_largura, nova_altura))
            
        # Converter para escala de cinza
        if len(imagem.shape) == 3:
            cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        else:
            cinza = imagem
            
        # Apenas melhorias essenciais
        # Equalização de histograma
        equalizada = cv2.equalizeHist(cinza)
        
        # Denoising leve
        denoised = cv2.fastNlMeansDenoising(equalizada)
        
        return [
            cinza,           # Original em cinza
            equalizada,      # Equalizada
            denoised         # Sem ruído
        ]
    
    def extrair_texto_rapido(self, imagem):
        """Extrai texto da imagem de forma rápida"""
        
        versoes = self.preprocessar_rapido(imagem)
        textos = []
        
        for i, versao in enumerate(versoes):
            try:
                # OCR com configuração básica
                texto = pytesseract.image_to_string(
                    versao, 
                    lang='eng+por',
                    config=self.config_ocr
                ).strip()
                
                if texto and len(texto) > 2:
                    textos.append({
                        'versao': i,
                        'texto': texto,
                        'confianca': len(texto)  # Aproximação simples
                    })
                    
            except Exception as e:
                continue
                
        return textos
    
    def detectar_yolo_rapido(self, imagem):
        """Detecção YOLO rápida"""
        
        if not self.modelo:
            return []
            
        try:
            # Redimensionar para acelerar
            altura, largura = imagem.shape[:2]
            if largura > 800:
                fator = 800 / largura
                nova_largura = int(largura * fator)
                nova_altura = int(altura * fator)
                imagem_pequena = cv2.resize(imagem, (nova_largura, nova_altura))
            else:
                imagem_pequena = imagem
                fator = 1.0
                
            # Detectar com confiança baixa para ser mais rápido
            resultados = self.modelo(imagem_pequena, conf=0.3, verbose=False)
            
            deteccoes = []
            for r in resultados:
                for box in r.boxes:
                    conf = float(box.conf)
                    if conf > 0.3:
                        # Ajustar coordenadas de volta
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1/fator), int(y1/fator), int(x2/fator), int(y2/fator)
                        
                        deteccoes.append({
                            'bbox': [x1, y1, x2, y2],
                            'confianca': conf,
                            'classe': int(box.cls)
                        })
                        
            return deteccoes
            
        except Exception as e:
            print(f"Erro YOLO: {e}")
            return []
    
    def identificar_marcas(self, textos):
        """Identifica marcas no texto de forma rápida"""
        
        marcas_encontradas = []
        
        for item_texto in textos:
            texto = item_texto['texto'].lower()
            
            for marca, variacoes in self.marcas.items():
                for variacao in variacoes:
                    if variacao in texto:
                        marcas_encontradas.append({
                            'marca': marca,
                            'variacao': variacao,
                            'confianca': item_texto['confianca'],
                            'versao_ocr': item_texto['versao']
                        })
                        break
                        
        return marcas_encontradas
    
    def processar_imagem_completa(self, caminho_imagem):
        """Processa uma imagem completa rapidamente"""
        
        inicio = datetime.now()
        
        # Carregar imagem
        try:
            imagem = cv2.imread(caminho_imagem)
            if imagem is None:
                return {'erro': 'Não foi possível carregar a imagem'}
                
            print(f"📸 Processando: {os.path.basename(caminho_imagem)}")
            
        except Exception as e:
            return {'erro': f'Erro ao carregar: {e}'}
        
        resultado = {
            'arquivo': os.path.basename(caminho_imagem),
            'caminho': caminho_imagem,
            'timestamp': inicio.isoformat()
        }
        
        # 1. Detecção YOLO (paralelo com OCR mentalmente)
        print("🔍 Detectando objetos...")
        deteccoes_yolo = self.detectar_yolo_rapido(imagem)
        resultado['deteccoes_yolo'] = deteccoes_yolo
        
        # 2. OCR
        print("📝 Extraindo texto...")
        textos = self.extrair_texto_rapido(imagem)
        resultado['textos_ocr'] = textos
        
        # 3. Identificar marcas
        print("🏷️ Identificando marcas...")
        marcas = self.identificar_marcas(textos)
        resultado['marcas_identificadas'] = marcas
        
        # Tempo total
        fim = datetime.now()
        resultado['tempo_processamento'] = (fim - inicio).total_seconds()
        
        return resultado
    
    def processar_pasta_fotos(self, pasta):
        """Processa todas as fotos de uma pasta"""
        
        extensoes = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        arquivos = []
        
        for arquivo in os.listdir(pasta):
            if any(arquivo.lower().endswith(ext) for ext in extensoes):
                arquivos.append(os.path.join(pasta, arquivo))
        
        resultados = []
        total = len(arquivos)
        
        print(f"📁 Encontradas {total} imagens para processar")
        
        for i, arquivo in enumerate(arquivos, 1):
            print(f"\n[{i}/{total}] Processando...")
            resultado = self.processar_imagem_completa(arquivo)
            resultados.append(resultado)
            
            # Mostrar progresso
            if 'marcas_identificadas' in resultado and resultado['marcas_identificadas']:
                marcas = [m['marca'] for m in resultado['marcas_identificadas']]
                print(f"✓ Marcas encontradas: {', '.join(set(marcas))}")
            else:
                print("○ Nenhuma marca identificada")
                
        return resultados
    
    def salvar_resultados(self, resultados, arquivo_saida='deteccao_rapida.json'):
        """Salva os resultados em JSON"""
        
        try:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)
            print(f"💾 Resultados salvos em: {arquivo_saida}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

def main():
    """Função principal - execução rápida"""
    
    detector = DetectorRapidoFotos()
    
    # Testar com a imagem do WhatsApp
    caminho_teste = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if os.path.exists(caminho_teste):
        print("🚀 Iniciando detecção rápida...")
        
        resultado = detector.processar_imagem_completa(caminho_teste)
        
        # Mostrar resultado
        print("\n" + "="*50)
        print("📊 RESULTADO DA DETECÇÃO")
        print("="*50)
        
        if 'erro' in resultado:
            print(f"❌ {resultado['erro']}")
            return
            
        print(f"⏱️  Tempo: {resultado['tempo_processamento']:.2f}s")
        print(f"🎯 Objetos detectados: {len(resultado.get('deteccoes_yolo', []))}")
        print(f"📝 Textos extraídos: {len(resultado.get('textos_ocr', []))}")
        
        if resultado.get('marcas_identificadas'):
            print("\n🏷️ MARCAS IDENTIFICADAS:")
            for marca in resultado['marcas_identificadas']:
                print(f"  • {marca['marca'].upper()} (confiança: {marca['confianca']})")
        else:
            print("\n🔍 Nenhuma marca identificada")
            
        if resultado.get('textos_ocr'):
            print("\n📝 TEXTOS EXTRAÍDOS:")
            for texto in resultado['textos_ocr'][:3]:  # Mostrar apenas os 3 primeiros
                print(f"  • {texto['texto'][:100]}...")
                
        # Salvar resultado
        detector.salvar_resultados([resultado])
        
    else:
        print(f"❌ Arquivo não encontrado: {caminho_teste}")
        
        # Alternativa: processar pasta Downloads
        pasta_downloads = r"C:\Users\gabri\Downloads"
        if os.path.exists(pasta_downloads):
            print(f"📁 Processando pasta Downloads...")
            resultados = detector.processar_pasta_fotos(pasta_downloads)
            detector.salvar_resultados(resultados)

if __name__ == "__main__":
    main()