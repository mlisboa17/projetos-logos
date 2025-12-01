#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE DETECÇÃO ORGANIZADO - VerifiK
Pipeline completo: Detecção → OCR → Identificação → Validação
"""

import os
import sys
import cv2
import numpy as np
import pytesseract
import json
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO
import django

# Importar configurações
from config_deteccao import *

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
try:
    django.setup()
    DJANGO_DISPONIVEL = True
except:
    DJANGO_DISPONIVEL = False
    print("⚠️  Django não disponível, usando modo standalone")

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = OCR_CONFIG['tesseract_path']

class DetectorOrganizado:
    """Sistema de detecção organizado com pipeline estruturado"""
    
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.resultados = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar diretório de resultados
        self.pasta_resultados = Path(f"deteccao_organizada_{self.timestamp}")
        self.pasta_resultados.mkdir(exist_ok=True)
        
        # Carregar modelo YOLO
        self.model = self._carregar_modelo()
        
        # Usar base de conhecimento do arquivo de configuração
        self.marcas_conhecidas = MARCAS_CONHECIDAS
    
    def _carregar_modelo(self):
        """Carrega modelo YOLO disponível"""        
        for modelo_path in MODELOS_YOLO:
            if os.path.exists(modelo_path):
                print(f"🤖 Carregando modelo: {modelo_path}")
                return YOLO(modelo_path)
        
        print("❌ Nenhum modelo YOLO encontrado")
        return None
    
    def detectar_produtos(self, imagem_path):
        """Etapa 1: Detectar produtos na imagem"""
        print(f"\n{'='*60}")
        print(f"🔍 ETAPA 1: DETECÇÃO DE PRODUTOS")
        print(f"{'='*60}")
        
        # Carregar imagem
        img = cv2.imread(imagem_path)
        if img is None:
            print(f"❌ Erro ao carregar imagem: {imagem_path}")
            return []
        
        altura, largura = img.shape[:2]
        print(f"📷 Imagem: {largura}x{altura} pixels")
        
        # Detecção com YOLO
        results = self.model.predict(
            source=imagem_path,
            conf=0.25,
            iou=0.45,
            max_det=20,
            save=False,
            verbose=False
        )
        
        deteccoes = []
        boxes = results[0].boxes
        
        print(f"📦 Objetos detectados: {len(boxes)}")
        
        for i, box in enumerate(boxes):
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            # Filtrar detecções muito pequenas ou com baixa confiança
            bbox_area = (x2 - x1) * (y2 - y1)
            img_area = largura * altura
            percentual_area = (bbox_area / img_area) * 100
            
            if percentual_area < 1.0 or conf < 0.25:
                continue
            
            deteccao = {
                'id': i + 1,
                'bbox': (x1, y1, x2, y2),
                'confianca': conf,
                'classe_generica': self.model.names.get(cls_id, f"classe_{cls_id}"),
                'area_percentual': percentual_area
            }
            
            deteccoes.append(deteccao)
            print(f"  {i+1}. {deteccao['classe_generica']} ({conf*100:.1f}%) - Área: {percentual_area:.1f}%")
        
        # Salvar imagem com detecções
        img_debug = img.copy()
        for det in deteccoes:
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(img_debug, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_debug, f"#{det['id']}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        debug_path = self.pasta_resultados / "1_deteccoes.jpg"
        cv2.imwrite(str(debug_path), img_debug)
        
        return img, deteccoes
    
    def analisar_rotulos(self, img, deteccoes):
        """Etapa 2: Analisar rótulos de cada produto detectado"""
        print(f"\n{'='*60}")
        print(f"🏷️  ETAPA 2: ANÁLISE DE RÓTULOS")
        print(f"{'='*60}")
        
        for det in deteccoes:
            print(f"\n🔍 Analisando produto #{det['id']}:")
            
            # Extrair região do produto
            x1, y1, x2, y2 = det['bbox']
            produto = img[y1:y2, x1:x2]
            
            if produto.size == 0:
                det['marca'] = 'PRODUTO_INVALIDO'
                continue
            
            # Salvar produto individual
            produto_path = self.pasta_resultados / f"produto_{det['id']}.jpg"
            cv2.imwrite(str(produto_path), produto)
            
            # Focar na região do rótulo
            altura_p, largura_p = produto.shape[:2]
            
            # Diferentes regiões para buscar o rótulo
            regioes_rotulo = [
                # (nome, x1%, y1%, x2%, y2%)
                ("centro_superior", 0.2, 0.1, 0.8, 0.5),
                ("centro_meio", 0.15, 0.3, 0.85, 0.7),
                ("superior_completo", 0.1, 0.05, 0.9, 0.4),
                ("meio_completo", 0.1, 0.25, 0.9, 0.75)
            ]
            
            melhor_resultado = None
            melhor_confianca = 0
            
            for nome_regiao, x1_p, y1_p, x2_p, y2_p in regioes_rotulo:
                # Coordenadas da região
                rx1 = int(largura_p * x1_p)
                ry1 = int(altura_p * y1_p)
                rx2 = int(largura_p * x2_p)
                ry2 = int(altura_p * y2_p)
                
                rotulo = produto[ry1:ry2, rx1:rx2]
                
                if rotulo.size == 0:
                    continue
                
                # Salvar região para debug
                regiao_path = self.pasta_resultados / f"rotulo_{det['id']}_{nome_regiao}.jpg"
                cv2.imwrite(str(regiao_path), rotulo)
                
                # Analisar esta região
                resultado = self._ocr_rotulo(rotulo, nome_regiao)
                
                if resultado['confianca'] > melhor_confianca:
                    melhor_confianca = resultado['confianca']
                    melhor_resultado = resultado
                    melhor_resultado['regiao'] = nome_regiao
            
            # Atribuir melhor resultado
            if melhor_resultado:
                det['marca'] = melhor_resultado['marca']
                det['ocr_confianca'] = melhor_resultado['confianca']
                det['ocr_textos'] = melhor_resultado['textos']
                det['regiao_usada'] = melhor_resultado['regiao']
                print(f"  ✅ Melhor resultado: {det['marca']} (confiança: {det['ocr_confianca']:.1f})")
            else:
                det['marca'] = 'MARCA_NAO_IDENTIFICADA'
                det['ocr_confianca'] = 0
                print(f"  ❌ Não foi possível identificar a marca")
    
    def _ocr_rotulo(self, rotulo, nome_regiao):
        """Executa OCR em uma região do rótulo"""
        # Preprocessar imagem
        gray = cv2.cvtColor(rotulo, cv2.COLOR_BGR2GRAY)
        
        # Múltiplos processamentos
        processamentos = [
            ("original", gray),
            ("contraste", cv2.convertScaleAbs(gray, alpha=2.0, beta=30)),
            ("threshold_otsu", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ("adaptivo", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
        ]
        
        # Configurações OCR
        configs = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ]
        
        todos_textos = []
        
        for proc_nome, img_proc in processamentos:
            for config in configs:
                try:
                    texto = pytesseract.image_to_string(img_proc, lang='eng+por', config=config)
                    texto_limpo = ''.join(c for c in texto.upper() if c.isalnum() or c.isspace()).strip()
                    
                    if texto_limpo and len(texto_limpo) >= 3:
                        todos_textos.append(texto_limpo)
                except:
                    continue
        
        # Analisar textos encontrados
        marca_identificada = None
        confianca = 0
        
        for marca, info in self.marcas_conhecidas.items():
            for padrao in info['padroes']:
                for texto in todos_textos:
                    if padrao in texto:
                        # Calcular confiança baseada no comprimento do padrão
                        conf = len(padrao) / len(marca) * 100
                        if conf > confianca:
                            confianca = conf
                            marca_identificada = marca
        
        return {
            'marca': marca_identificada or 'DESCONHECIDA',
            'confianca': confianca,
            'textos': todos_textos[:5]  # Primeiros 5 textos
        }
    
    def gerar_resultado_final(self, img, deteccoes):
        """Etapa 3: Gerar resultado visual e relatório"""
        print(f"\n{'='*60}")
        print(f"📊 ETAPA 3: RESULTADO FINAL")
        print(f"{'='*60}")
        
        # Imagem resultado
        img_resultado = img.copy()
        
        # Resumo
        marcas_encontradas = {}
        
        for det in deteccoes:
            x1, y1, x2, y2 = det['bbox']
            marca = det.get('marca', 'DESCONHECIDA')
            
            # Contar marcas
            if marca in marcas_encontradas:
                marcas_encontradas[marca] += 1
            else:
                marcas_encontradas[marca] = 1
            
            # Cor baseada na marca
            if marca in self.marcas_conhecidas:
                cor = self.marcas_conhecidas[marca]['cores_tipicas'][0]
            else:
                cor = (128, 128, 128)  # Cinza para desconhecidas
            
            # Desenhar bbox
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 3)
            
            # Texto da marca
            cv2.putText(img_resultado, marca, (x1, y1-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            
            # ID e confiança
            cv2.putText(img_resultado, f"#{det['id']} {det['confianca']*100:.0f}%", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
        
        # Salvar resultado
        resultado_path = self.pasta_resultados / "resultado_final.jpg"
        cv2.imwrite(str(resultado_path), img_resultado)
        
        # Gerar relatório
        relatorio = {
            'timestamp': self.timestamp,
            'total_produtos': len(deteccoes),
            'marcas_encontradas': marcas_encontradas,
            'deteccoes': deteccoes,
            'arquivos_gerados': list(self.pasta_resultados.glob("*.jpg"))
        }
        
        relatorio_path = self.pasta_resultados / "relatorio.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        # Mostrar resumo
        print(f"📦 Total de produtos detectados: {len(deteccoes)}")
        print(f"🏷️  Marcas identificadas:")
        for marca, qtd in marcas_encontradas.items():
            print(f"   {marca}: {qtd} unidade(s)")
        
        print(f"\n💾 Arquivos salvos em: {self.pasta_resultados}")
        print(f"   - resultado_final.jpg (imagem com detecções)")
        print(f"   - relatorio.json (dados completos)")
        print(f"   - produto_*.jpg (produtos individuais)")
        print(f"   - rotulo_*.jpg (regiões dos rótulos)")
        
        return img_resultado, relatorio

def main():
    """Função principal"""
    print("🚀 SISTEMA DE DETECÇÃO ORGANIZADO - VerifiK")
    print("="*60)
    
    # Caminho da imagem
    caminho_imagem = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if not os.path.exists(caminho_imagem):
        print(f"❌ Imagem não encontrada: {caminho_imagem}")
        return
    
    # Inicializar detector
    detector = DetectorOrganizado(debug_mode=True)
    
    # Pipeline completo
    try:
        # Etapa 1: Detectar produtos
        img, deteccoes = detector.detectar_produtos(caminho_imagem)
        
        if not deteccoes:
            print("❌ Nenhum produto detectado")
            return
        
        # Etapa 2: Analisar rótulos
        detector.analisar_rotulos(img, deteccoes)
        
        # Etapa 3: Resultado final
        img_resultado, relatorio = detector.gerar_resultado_final(img, deteccoes)
        
        print("\n✅ DETECÇÃO CONCLUÍDA COM SUCESSO!")
        
    except Exception as e:
        print(f"❌ Erro durante detecção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()