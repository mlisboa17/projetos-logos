#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETECTOR FOCADO EM LER NOMES - Otimizado para identificar marcas em rótulos
Foco: Extrair e ler com precisão o nome da marca no produto
"""

import os
import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO
from pathlib import Path
import re
import json

class LeitorDeNomes:
    """Detector especializado em ler nomes de marcas em produtos"""
    
    def __init__(self):
        print("🔤 LEITOR DE NOMES - Inicializando...")
        
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Carregar modelo YOLO
        self.model = self._carregar_yolo()
        
        # Marcas conhecidas com padrões de reconhecimento
        self.marcas_conhecidas = {
            'HEINEKEN': {
                'padroes': ['HEINEKEN', 'HEINE', 'NEKEN', 'HEINEK', 'HEINKEN', 'HEIEKEN'],
                'cor_fundo': 'verde',
                'tamanho_fonte': 'grande'
            },
            'DEVASSA': {
                'padroes': ['DEVASSA', 'DEVAS', 'EVASSA', 'VASSA', 'DEVASA', 'D3VASSA'],
                'cor_fundo': 'vermelho',
                'tamanho_fonte': 'grande'
            },
            'BUDWEISER': {
                'padroes': ['BUDWEISER', 'BUDWEI', 'BUD', 'WEISER', 'BUDWISER', 'BUDWEIZER'],
                'cor_fundo': 'branco_vermelho',
                'tamanho_fonte': 'medio'
            },
            'AMSTEL': {
                'padroes': ['AMSTEL', 'AMSTE', 'MATEL', 'AMSTEI', 'AMST3L'],
                'cor_fundo': 'dourado',
                'tamanho_fonte': 'medio'
            },
            'STELLA': {
                'padroes': ['STELLA', 'ARTOIS', 'STELA', 'STELLA ARTOIS', 'ST3LLA'],
                'cor_fundo': 'dourado',
                'tamanho_fonte': 'medio'
            },
            'BRAHMA': {
                'padroes': ['BRAHMA', 'BRAMA', 'RAHMA', 'BRAHM', 'BR4HMA'],
                'cor_fundo': 'vermelho_branco',
                'tamanho_fonte': 'grande'
            },
            'SKOL': {
                'padroes': ['SKOL', 'SK0L', 'KOLL', '5KOL', 'SKOI'],
                'cor_fundo': 'azul_branco',
                'tamanho_fonte': 'grande'
            },
            'ANTARCTICA': {
                'padroes': ['ANTARCTICA', 'ANTARTIC', 'ANTART', 'ANTARTICA', 'ANT4RTICA'],
                'cor_fundo': 'azul',
                'tamanho_fonte': 'medio'
            },
            'PEPSI': {
                'padroes': ['PEPSI', 'P3PSI', 'PEPS', 'PEPSY', 'PEPS1'],
                'cor_fundo': 'azul_vermelho',
                'tamanho_fonte': 'grande'
            },
            'COCA': {
                'padroes': ['COCA', 'COLA', 'COCACOLA', 'COCA COLA', 'C0CA'],
                'cor_fundo': 'vermelho',
                'tamanho_fonte': 'grande'
            }
        }
    
    def _carregar_yolo(self):
        """Carrega modelo YOLO disponível"""
        modelos = ['yolov8n.pt', 'yolov8s.pt', 'verifik/verifik_yolov8.pt']
        
        for modelo in modelos:
            if os.path.exists(modelo):
                print(f"🤖 Modelo carregado: {modelo}")
                return YOLO(modelo)
        
        print("❌ Nenhum modelo encontrado")
        return None
    
    def processar_imagem(self, caminho_imagem):
        """Pipeline completo para ler nomes em uma imagem"""
        print(f"\n{'='*60}")
        print(f"📷 PROCESSANDO: {Path(caminho_imagem).name}")
        print(f"{'='*60}")
        
        # Verificar arquivo
        if not os.path.exists(caminho_imagem):
            print(f"❌ Arquivo não encontrado: {caminho_imagem}")
            return None
        
        # Carregar imagem
        img = cv2.imread(caminho_imagem)
        if img is None:
            print("❌ Erro ao carregar imagem")
            return None
        
        altura, largura = img.shape[:2]
        print(f"📐 Dimensões: {largura} x {altura}")
        
        # 1. DETECTAR PRODUTOS
        produtos_detectados = self._detectar_produtos(img, caminho_imagem)
        
        if not produtos_detectados:
            print("⚠️  Nenhum produto detectado")
            return None
        
        # 2. LER NOMES EM CADA PRODUTO
        resultados = []
        for i, produto in enumerate(produtos_detectados):
            print(f"\n🔍 LENDO PRODUTO #{i+1}:")
            resultado = self._ler_nome_produto(img, produto, i+1)
            resultados.append(resultado)
        
        # 3. GERAR RESULTADO VISUAL
        img_resultado = self._criar_imagem_resultado(img, resultados)
        
        return {
            'imagem_original': caminho_imagem,
            'produtos_encontrados': len(resultados),
            'resultados': resultados,
            'imagem_resultado': img_resultado
        }
    
    def _detectar_produtos(self, img, caminho_imagem):
        """Detecta produtos na imagem usando YOLO"""
        print("🔍 Detectando produtos...")
        
        results = self.model.predict(
            source=caminho_imagem,
            conf=0.2,  # Confiança mais baixa para capturar mais produtos
            iou=0.4,
            max_det=15,
            save=False,
            verbose=False
        )
        
        produtos = []
        boxes = results[0].boxes
        
        for i, box in enumerate(boxes):
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            conf = float(box.conf[0])
            
            # Filtrar produtos muito pequenos
            area = (x2 - x1) * (y2 - y1)
            area_img = img.shape[0] * img.shape[1]
            percentual = (area / area_img) * 100
            
            if percentual < 2.0:  # Menor que 2% da imagem
                continue
            
            produto = {
                'id': i + 1,
                'bbox': (x1, y1, x2, y2),
                'confianca': conf,
                'area_percentual': percentual
            }
            
            produtos.append(produto)
            print(f"  Produto {i+1}: {conf*100:.1f}% confiança, {percentual:.1f}% da imagem")
        
        print(f"✅ {len(produtos)} produto(s) detectado(s)")
        return produtos
    
    def _ler_nome_produto(self, img, produto, produto_id):
        """Foca em ler o nome da marca em um produto específico"""
        x1, y1, x2, y2 = produto['bbox']
        
        # Extrair imagem do produto
        img_produto = img[y1:y2, x1:x2]
        
        # Salvar produto para debug
        cv2.imwrite(f"debug_produto_{produto_id}.jpg", img_produto)
        
        altura_p, largura_p = img_produto.shape[:2]
        print(f"  📏 Produto: {largura_p}x{altura_p}")
        
        # ESTRATÉGIA: Múltiplas regiões do rótulo
        regioes_para_testar = [
            # (nome, x1%, y1%, x2%, y2%)
            ("topo_centro", 0.2, 0.05, 0.8, 0.4),       # Topo central
            ("centro_marca", 0.1, 0.2, 0.9, 0.6),       # Centro para marca
            ("superior_largo", 0.05, 0.1, 0.95, 0.5),   # Superior largo
            ("meio_foco", 0.25, 0.3, 0.75, 0.7),        # Meio focado
            ("produto_completo", 0.0, 0.0, 1.0, 1.0)    # Produto inteiro
        ]
        
        melhor_resultado = {
            'nome_encontrado': 'NÃO_IDENTIFICADO',
            'confianca': 0,
            'regiao_usada': 'nenhuma',
            'textos_ocr': []
        }
        
        for nome_regiao, x1_p, y1_p, x2_p, y2_p in regioes_para_testar:
            print(f"    🎯 Testando região: {nome_regiao}")
            
            # Calcular coordenadas da região
            rx1 = max(0, int(largura_p * x1_p))
            ry1 = max(0, int(altura_p * y1_p))
            rx2 = min(largura_p, int(largura_p * x2_p))
            ry2 = min(altura_p, int(altura_p * y2_p))
            
            if rx2 <= rx1 or ry2 <= ry1:
                continue
            
            # Extrair região
            regiao = img_produto[ry1:ry2, rx1:rx2]
            
            if regiao.size == 0:
                continue
            
            # Salvar região para debug
            cv2.imwrite(f"debug_regiao_{produto_id}_{nome_regiao}.jpg", regiao)
            
            # Aplicar OCR nesta região
            resultado_ocr = self._ocr_intensivo(regiao, nome_regiao)
            
            # Verificar se encontrou marca conhecida
            if resultado_ocr['confianca'] > melhor_resultado['confianca']:
                melhor_resultado = resultado_ocr
                melhor_resultado['regiao_usada'] = nome_regiao
        
        # Adicionar informações do produto
        melhor_resultado.update(produto)
        
        print(f"  🏆 Melhor resultado: {melhor_resultado['nome_encontrado']} (confiança: {melhor_resultado['confianca']:.1f})")
        return melhor_resultado
    
    def _ocr_intensivo(self, regiao, nome_regiao):
        """Aplica OCR intensivo em uma região"""
        # Múltiplos preprocessamentos
        processamentos = self._preprocessar_para_ocr(regiao)
        
        # Configurações de OCR específicas para texto de marca
        configs_ocr = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # Só maiúsculas
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # Linha única
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # Palavra única
            '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ', # Texto cru
            '--psm 6',  # Padrão
            '--psm 7',  # Linha
            '--psm 8'   # Palavra
        ]
        
        todos_textos = []
        
        # Testar cada processamento com cada configuração
        for proc_nome, img_processada in processamentos:
            for config in configs_ocr:
                try:
                    texto = pytesseract.image_to_string(img_processada, lang='eng+por', config=config)
                    texto_limpo = self._limpar_texto(texto)
                    
                    if texto_limpo and len(texto_limpo) >= 3:
                        todos_textos.append(texto_limpo)
                except:
                    continue
        
        # Analisar textos para encontrar marca
        return self._analisar_textos_para_marca(todos_textos)
    
    def _preprocessar_para_ocr(self, regiao):
        """Aplica múltiplos preprocessamentos para melhorar OCR"""
        processamentos = []
        
        # 1. Original
        processamentos.append(("original", regiao))
        
        # 2. Escala de cinza
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        processamentos.append(("cinza", gray))
        
        # 3. Contraste alto
        contraste = cv2.convertScaleAbs(gray, alpha=3.0, beta=50)
        processamentos.append(("contraste", contraste))
        
        # 4. Threshold OTSU
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processamentos.append(("threshold_otsu", thresh_otsu))
        
        # 5. Threshold adaptativo
        thresh_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processamentos.append(("adaptativo", thresh_adapt))
        
        # 6. Morfologia para limpar
        kernel = np.ones((2,2), np.uint8)
        morph = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel)
        processamentos.append(("morfologia", morph))
        
        # 7. Denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        processamentos.append(("denoised", denoised))
        
        # 8. Blur + threshold
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, blur_thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processamentos.append(("blur_thresh", blur_thresh))
        
        return processamentos
    
    def _limpar_texto(self, texto):
        """Limpa e normaliza texto do OCR"""
        if not texto:
            return ""
        
        # Remover caracteres especiais e manter só letras/números
        texto_limpo = re.sub(r'[^A-Za-z0-9\s]', '', texto)
        texto_limpo = texto_limpo.strip().upper()
        
        # Correções comuns de OCR
        correções = {
            '0': 'O', '1': 'I', '3': 'E', '5': 'S', '6': 'G', '8': 'B'
        }
        
        for errado, correto in correções.items():
            texto_limpo = texto_limpo.replace(errado, correto)
        
        return texto_limpo
    
    def _analisar_textos_para_marca(self, textos):
        """Analisa textos encontrados para identificar marca"""
        marca_encontrada = None
        confianca_maxima = 0
        
        print(f"      📝 Textos encontrados: {textos[:3]}...")  # Mostrar primeiros 3
        
        # Combinar todos os textos
        texto_combinado = " ".join(textos)
        
        # Procurar por cada marca conhecida
        for marca, info in self.marcas_conhecidas.items():
            for padrao in info['padroes']:
                # Busca exata
                if padrao in texto_combinado:
                    confianca = len(padrao) * 10  # Confiança baseada no tamanho
                    if confianca > confianca_maxima:
                        confianca_maxima = confianca
                        marca_encontrada = marca
                
                # Busca por similaridade (para erros de OCR)
                for texto in textos:
                    if len(texto) >= 4:
                        # Calcular similaridade simples
                        chars_comuns = len(set(padrao) & set(texto))
                        similaridade = chars_comuns / len(padrao)
                        
                        if similaridade >= 0.6:  # 60% de similaridade
                            confianca = similaridade * 100
                            if confianca > confianca_maxima:
                                confianca_maxima = confianca
                                marca_encontrada = marca
        
        return {
            'nome_encontrado': marca_encontrada or 'NÃO_IDENTIFICADO',
            'confianca': confianca_maxima,
            'textos_ocr': textos[:5]  # Primeiros 5 textos
        }
    
    def _criar_imagem_resultado(self, img, resultados):
        """Cria imagem com os nomes identificados"""
        img_resultado = img.copy()
        
        for resultado in resultados:
            x1, y1, x2, y2 = resultado['bbox']
            nome = resultado['nome_encontrado']
            confianca = resultado['confianca']
            
            # Cor baseada no sucesso
            if nome != 'NÃO_IDENTIFICADO':
                cor = (0, 255, 0)  # Verde para sucesso
            else:
                cor = (0, 165, 255)  # Laranja para não identificado
            
            # Desenhar bbox
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 3)
            
            # Texto do nome
            cv2.putText(img_resultado, nome, (x1, y1-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
            
            # Confiança
            cv2.putText(img_resultado, f"{confianca:.0f}%", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
        
        # Salvar resultado
        cv2.imwrite("resultado_leitura_nomes.jpg", img_resultado)
        return img_resultado


def main():
    """Função principal para testar o leitor de nomes"""
    print("🔤 LEITOR DE NOMES DE MARCAS")
    print("="*50)
    
    # Caminho da imagem
    caminho_imagem = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    # Inicializar leitor
    leitor = LeitorDeNomes()
    
    # Processar imagem
    resultado = leitor.processar_imagem(caminho_imagem)
    
    if resultado:
        print(f"\n🎯 RESUMO FINAL:")
        print(f"   📦 Produtos processados: {resultado['produtos_encontrados']}")
        
        for i, res in enumerate(resultado['resultados'], 1):
            nome = res['nome_encontrado']
            conf = res['confianca']
            emoji = "✅" if nome != 'NÃO_IDENTIFICADO' else "❓"
            print(f"   {emoji} Produto {i}: {nome} ({conf:.0f}%)")
        
        print(f"\n💾 Resultado visual salvo: resultado_leitura_nomes.jpg")
        print(f"🔍 Arquivos de debug: debug_produto_*.jpg, debug_regiao_*.jpg")
    
    print("\n🔤 LEITURA DE NOMES CONCLUÍDA!")

if __name__ == "__main__":
    main()