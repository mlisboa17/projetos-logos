"""
Detector Inteligente de Marcas - Foca nas regiões certas
Combina detecção de objetos + OCR direcionado
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from ultralytics import YOLO
import json
from datetime import datetime
import re

class DetectorInteligenteMarcas:
    def __init__(self):
        """Inicializa detector inteligente"""
        
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Carregar YOLO apenas se necessário
        self.modelo = None
        
        # Padrões de marcas mais abrangentes
        self.patterns_marcas = [
            (r'heineken|heinken|heinek', 'Heineken'),
            (r'budweiser|bud(?!get)|budw', 'Budweiser'), 
            (r'devassa|devasa|devas', 'Devassa'),
            (r'corona(?!virus)|coroa', 'Corona'),
            (r'stella|artois|stelle', 'Stella Artois'),
            (r'brahma|brama|braha', 'Brahma'),
            (r'skol|scol|skool', 'Skol'),
            (r'antarctica|antartica|antarc', 'Antarctica'),
            (r'original(?!ity)', 'Original'),
            (r'eisenbahn|eisen|eisenb', 'Eisenbahn'),
            (r'bohemia|boemia|bohem', 'Bohemia'),
            (r'beck.?s|becks|beck', 'Becks'),
            (r'amstel|amste', 'Amstel'),
            (r'kaiser|kaise', 'Kaiser'),
            (r'coca.?cola|coke|coca', 'Coca-Cola'),
            (r'pepsi|peps', 'Pepsi'),
            (r'fanta|fant', 'Fanta'),
            (r'sprite|sprit', 'Sprite')
        ]
        
    def carregar_yolo_se_necessario(self):
        """Carrega YOLO apenas quando necessário"""
        if self.modelo is None:
            try:
                self.modelo = YOLO('yolov8n.pt')
                print("✓ YOLO carregado")
            except:
                print("⚠️ YOLO não disponível - usando só OCR")
                
    def detectar_regioes_interesse(self, imagem_cv):
        """Detecta regiões de interesse com YOLO"""
        
        self.carregar_yolo_se_necessario()
        
        if self.modelo is None:
            # Se não tiver YOLO, usar imagem inteira
            altura, largura = imagem_cv.shape[:2]
            return [{'bbox': [0, 0, largura, altura], 'confianca': 1.0, 'tipo': 'imagem_completa'}]
        
        try:
            resultados = self.modelo(imagem_cv, conf=0.25, verbose=False)
            regioes = []
            
            for r in resultados:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf)
                    classe = int(box.cls)
                    
                    # Expandir região para pegar mais texto
                    margin = 20
                    x1 = max(0, x1 - margin)
                    y1 = max(0, y1 - margin)  
                    x2 = min(imagem_cv.shape[1], x2 + margin)
                    y2 = min(imagem_cv.shape[0], y2 + margin)
                    
                    regioes.append({
                        'bbox': [x1, y1, x2, y2],
                        'confianca': conf,
                        'classe': classe,
                        'tipo': 'objeto_detectado'
                    })
                    
            # Se não detectou nada, usar imagem inteira
            if not regioes:
                altura, largura = imagem_cv.shape[:2]
                regioes.append({
                    'bbox': [0, 0, largura, altura],
                    'confianca': 1.0,
                    'tipo': 'imagem_completa'
                })
                
            return regioes
            
        except Exception as e:
            print(f"Erro YOLO: {e}")
            altura, largura = imagem_cv.shape[:2]
            return [{'bbox': [0, 0, largura, altura], 'confianca': 1.0, 'tipo': 'fallback'}]
    
    def preprocessar_para_texto(self, imagem_pil):
        """Preprocessing especializado para leitura de texto em embalagens"""
        
        versoes = []
        
        # 1. Original em escala de cinza
        cinza = imagem_pil.convert('L')
        versoes.append(('original', cinza))
        
        # 2. Auto contraste
        auto_contrast = ImageOps.autocontrast(cinza)
        versoes.append(('auto_contrast', auto_contrast))
        
        # 3. Equalização
        eq_array = np.array(auto_contrast)
        eq_array = cv2.equalizeHist(eq_array)
        equalizada = Image.fromarray(eq_array)
        versoes.append(('equalizada', equalizada))
        
        # 4. Threshold adaptativo
        thresh_array = cv2.adaptiveThreshold(
            np.array(equalizada), 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        threshold = Image.fromarray(thresh_array)
        versoes.append(('threshold', threshold))
        
        # 5. Morphologia para limpar
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph_array = cv2.morphologyEx(thresh_array, cv2.MORPH_CLOSE, kernel)
        morfologia = Image.fromarray(morph_array)
        versoes.append(('morfologia', morfologia))
        
        return versoes
    
    def ocr_direcionado(self, imagem_pil):
        """OCR direcionado para marcas"""
        
        versoes = self.preprocessar_para_texto(imagem_pil)
        textos_extraidos = []
        
        # Configurações OCR otimizadas para marcas
        configs = [
            (r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'palavras_apenas'),
            (r'--oem 3 --psm 7', 'linha_texto'),
            (r'--oem 3 --psm 6', 'bloco_uniforme'), 
            (r'--oem 3 --psm 13', 'linha_crua')
        ]
        
        for nome_versao, versao_img in versoes:
            for config, nome_config in configs:
                try:
                    texto = pytesseract.image_to_string(
                        versao_img,
                        lang='eng+por',
                        config=config
                    ).strip()
                    
                    if texto and len(texto.replace(' ', '')) > 2:
                        textos_extraidos.append({
                            'texto': texto,
                            'versao': nome_versao,
                            'config': nome_config,
                            'confianca': len(texto.replace(' ', ''))
                        })
                        
                except Exception:
                    continue
                    
        return textos_extraidos
    
    def detectar_marcas_inteligente(self, textos):
        """Detecção inteligente de marcas"""
        
        marcas_encontradas = {}
        
        # Processar cada texto
        for item_texto in textos:
            texto_limpo = re.sub(r'[^a-zA-Z\s]', '', item_texto['texto']).lower()
            
            for pattern, nome_marca in self.patterns_marcas:
                matches = re.findall(pattern, texto_limpo, re.IGNORECASE)
                
                if matches:
                    if nome_marca not in marcas_encontradas:
                        marcas_encontradas[nome_marca] = {
                            'marca': nome_marca,
                            'matches': [],
                            'confianca': 0,
                            'fontes': []
                        }
                    
                    marcas_encontradas[nome_marca]['matches'].extend(matches)
                    marcas_encontradas[nome_marca]['confianca'] += item_texto['confianca']
                    marcas_encontradas[nome_marca]['fontes'].append({
                        'texto_original': item_texto['texto'],
                        'versao': item_texto['versao'],
                        'config': item_texto['config']
                    })
        
        return list(marcas_encontradas.values())
    
    def processar_imagem_inteligente(self, caminho_imagem):
        """Processamento inteligente completo"""
        
        inicio = datetime.now()
        
        try:
            # Carregar imagem
            imagem_cv = cv2.imread(caminho_imagem)
            if imagem_cv is None:
                raise Exception("Não foi possível carregar a imagem")
                
            imagem_pil = Image.fromarray(cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2RGB))
            
            altura, largura = imagem_cv.shape[:2]
            print(f"📸 {os.path.basename(caminho_imagem)} ({largura}x{altura})")
            
        except Exception as e:
            return {'erro': str(e)}
        
        # 1. Detectar regiões de interesse
        print("🎯 Detectando regiões...")
        regioes = self.detectar_regioes_interesse(imagem_cv)
        
        todos_textos = []
        todas_marcas = []
        
        # 2. Processar cada região
        for i, regiao in enumerate(regioes):
            print(f"📝 OCR região {i+1}/{len(regioes)} ({regiao['tipo']})...")
            
            # Extrair região
            x1, y1, x2, y2 = regiao['bbox']
            regiao_pil = imagem_pil.crop((x1, y1, x2, y2))
            
            # OCR na região
            textos_regiao = self.ocr_direcionado(regiao_pil)
            todos_textos.extend(textos_regiao)
            
            # Detectar marcas na região
            marcas_regiao = self.detectar_marcas_inteligente(textos_regiao)
            todas_marcas.extend(marcas_regiao)
        
        # Se não processou regiões específicas, processar imagem inteira
        if len(regioes) == 1 and regioes[0]['tipo'] in ['imagem_completa', 'fallback']:
            print("📝 OCR imagem completa...")
            textos_completos = self.ocr_direcionado(imagem_pil)
            todos_textos.extend(textos_completos)
            
            marcas_completas = self.detectar_marcas_inteligente(textos_completos)
            todas_marcas.extend(marcas_completas)
        
        # Consolidar marcas duplicadas
        marcas_consolidadas = {}
        for marca in todas_marcas:
            nome = marca['marca']
            if nome not in marcas_consolidadas:
                marcas_consolidadas[nome] = marca
            else:
                # Somar confiança e juntar matches
                marcas_consolidadas[nome]['confianca'] += marca['confianca']
                marcas_consolidadas[nome]['matches'].extend(marca['matches'])
                marcas_consolidadas[nome]['fontes'].extend(marca['fontes'])
        
        fim = datetime.now()
        
        return {
            'arquivo': os.path.basename(caminho_imagem),
            'caminho': caminho_imagem,
            'timestamp': inicio.isoformat(),
            'tempo_processamento': (fim - inicio).total_seconds(),
            'regioes_processadas': len(regioes),
            'textos_extraidos': len(todos_textos),
            'textos_detalhes': todos_textos,
            'marcas_detectadas': list(marcas_consolidadas.values()),
            'total_marcas_unicas': len(marcas_consolidadas)
        }
    
    def mostrar_resultado_inteligente(self, resultado):
        """Mostra resultado detalhado"""
        
        print("\n" + "="*70)
        print("🧠 DETECÇÃO INTELIGENTE DE MARCAS")
        print("="*70)
        
        if 'erro' in resultado:
            print(f"❌ {resultado['erro']}")
            return
            
        print(f"📁 Arquivo: {resultado['arquivo']}")
        print(f"⚡ Tempo: {resultado['tempo_processamento']:.2f}s")
        print(f"🎯 Regiões: {resultado['regioes_processadas']}")
        print(f"📝 Textos: {resultado['textos_extraidos']}")
        print(f"🏷️ Marcas únicas: {resultado['total_marcas_unicas']}")
        
        if resultado['marcas_detectadas']:
            print("\n✅ MARCAS IDENTIFICADAS:")
            for marca in sorted(resultado['marcas_detectadas'], key=lambda x: x['confianca'], reverse=True):
                matches_str = ', '.join(set(marca['matches']))
                print(f"  🍺 {marca['marca']} - '{matches_str}' (conf: {marca['confianca']})")
                
                # Mostrar fontes principais
                for fonte in marca['fontes'][:2]:  # Max 2 fontes
                    texto_curto = fonte['texto_original'][:50]
                    print(f"      └─ '{texto_curto}' ({fonte['versao']}.{fonte['config']})")
        else:
            print("\n❌ Nenhuma marca identificada")
            
        # Mostrar alguns textos extraídos
        if resultado['textos_detalhes']:
            print(f"\n📝 TEXTOS MAIS RELEVANTES:")
            textos_ordenados = sorted(resultado['textos_detalhes'], key=lambda x: x['confianca'], reverse=True)
            for i, texto in enumerate(textos_ordenados[:6]):
                texto_limpo = texto['texto'].replace('\n', ' ').strip()
                if texto_limpo and len(texto_limpo) > 2:
                    print(f"  {i+1}. '{texto_limpo}' ({texto['versao']}.{texto['config']})")

def main():
    """Execução principal inteligente"""
    
    detector = DetectorInteligenteMarcas()
    
    caminho_teste = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if os.path.exists(caminho_teste):
        print("🧠 DETECTOR INTELIGENTE INICIANDO...")
        
        resultado = detector.processar_imagem_inteligente(caminho_teste)
        detector.mostrar_resultado_inteligente(resultado)
        
        # Salvar resultado
        with open('deteccao_inteligente.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultado salvo: deteccao_inteligente.json")
        
    else:
        print(f"❌ Arquivo não encontrado: {caminho_teste}")

if __name__ == "__main__":
    main()