"""
Detector Ultra Rápido para Marcas - Versão Otimizada
Focado em velocidade máxima e detecção de marcas
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from ultralytics import YOLO
import json
from datetime import datetime
import re

class DetectorUltraRapido:
    def __init__(self):
        """Inicializa o detector ultra otimizado"""
        
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Não carregar YOLO inicialmente para ser mais rápido
        self.modelo = None
        
        # Marcas conhecidas com regex otimizado
        self.patterns_marcas = [
            (r'heineken|heinken', 'Heineken'),
            (r'budweiser|bud\b', 'Budweiser'),
            (r'devassa|devasa', 'Devassa'),
            (r'corona\b|coroa', 'Corona'),
            (r'stella|artois', 'Stella Artois'),
            (r'brahma|brama', 'Brahma'),
            (r'skol|scol', 'Skol'),
            (r'antarctica|antartica', 'Antarctica'),
            (r'original\b', 'Original'),
            (r'eisenbahn|eisen', 'Eisenbahn'),
            (r'bohemia|boemia', 'Bohemia'),
            (r'beck.?s|becks', 'Becks'),
            (r'amstel', 'Amstel'),
            (r'kaiser', 'Kaiser')
        ]
        
    def preprocessar_ultra_rapido(self, imagem):
        """Preprocessamento ultra rápido focado em texto"""
        
        # Converter para PIL para manipulações rápidas
        if isinstance(imagem, np.ndarray):
            if len(imagem.shape) == 3:
                pil_img = Image.fromarray(cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(imagem)
        else:
            pil_img = imagem
            
        versoes = []
        
        # 1. Original em escala de cinza
        cinza = pil_img.convert('L')
        versoes.append(cinza)
        
        # 2. Contrast aumentado
        enhancer = ImageEnhance.Contrast(cinza)
        alta_contraste = enhancer.enhance(2.0)
        versoes.append(alta_contraste)
        
        # 3. Brilho ajustado
        enhancer = ImageEnhance.Brightness(alta_contraste)
        brilho_ajustado = enhancer.enhance(1.2)
        versoes.append(brilho_ajustado)
        
        # 4. Sharpening para texto
        sharp = brilho_ajustado.filter(ImageFilter.SHARPEN)
        versoes.append(sharp)
        
        return versoes
    
    def ocr_ultra_rapido(self, imagem):
        """OCR ultra rápido com múltiplas configurações"""
        
        versoes = self.preprocessar_ultra_rapido(imagem)
        todos_textos = []
        
        # Configurações OCR otimizadas
        configs = [
            r'--oem 3 --psm 6',  # Bloco uniforme de texto
            r'--oem 3 --psm 8',  # Palavra única
            r'--oem 3 --psm 7',  # Linha de texto única
            r'--oem 3 --psm 13'  # Linha crua - melhor para marcas
        ]
        
        for i, versao in enumerate(versoes):
            for j, config in enumerate(configs):
                try:
                    texto = pytesseract.image_to_string(
                        versao, 
                        lang='eng',  # Só inglês para ser mais rápido
                        config=config
                    ).strip()
                    
                    if texto and len(texto) > 1:
                        todos_textos.append({
                            'texto': texto,
                            'versao_img': i,
                            'config_ocr': j,
                            'confianca': len(texto) * (5 - j)  # Priorizar configs anteriores
                        })
                        
                except Exception:
                    continue
                    
        return todos_textos
    
    def detectar_marcas_rapido(self, textos):
        """Detecção ultra rápida de marcas usando regex"""
        
        marcas_encontradas = set()
        detalhes_marcas = []
        
        # Juntar todos os textos
        texto_completo = ' '.join([t['texto'] for t in textos]).lower()
        
        # Buscar cada padrão
        for pattern, nome_marca in self.patterns_marcas:
            matches = re.findall(pattern, texto_completo, re.IGNORECASE)
            if matches:
                if nome_marca not in marcas_encontradas:
                    marcas_encontradas.add(nome_marca)
                    detalhes_marcas.append({
                        'marca': nome_marca,
                        'matches': matches,
                        'confianca': len(matches) * 10
                    })
                    
        return detalhes_marcas
    
    def processar_imagem_ultra_rapido(self, caminho_imagem):
        """Processamento ultra rápido de uma imagem"""
        
        inicio = datetime.now()
        
        try:
            # Carregar imagem diretamente como PIL
            imagem = Image.open(caminho_imagem)
            
            # Redimensionar se muito grande
            largura, altura = imagem.size
            if largura > 1000:
                fator = 1000 / largura
                nova_largura = int(largura * fator)
                nova_altura = int(altura * fator)
                imagem = imagem.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
                
            print(f"📸 {os.path.basename(caminho_imagem)} ({largura}x{altura})")
            
        except Exception as e:
            return {'erro': f'Erro ao carregar: {e}'}
        
        # 1. OCR ultra rápido
        print("📝 OCR...")
        textos = self.ocr_ultra_rapido(imagem)
        
        # 2. Detecção de marcas
        print("🏷️ Marcas...")
        marcas = self.detectar_marcas_rapido(textos)
        
        fim = datetime.now()
        tempo = (fim - inicio).total_seconds()
        
        return {
            'arquivo': os.path.basename(caminho_imagem),
            'caminho': caminho_imagem,
            'timestamp': inicio.isoformat(),
            'tempo_processamento': tempo,
            'textos_extraidos': len(textos),
            'textos_completos': textos,
            'marcas_detectadas': marcas,
            'total_marcas': len(marcas)
        }
    
    def mostrar_resultado(self, resultado):
        """Mostra resultado de forma clara"""
        
        print("\n" + "="*60)
        print("📊 RESULTADO ULTRA RÁPIDO")
        print("="*60)
        
        if 'erro' in resultado:
            print(f"❌ {resultado['erro']}")
            return
            
        print(f"📁 Arquivo: {resultado['arquivo']}")
        print(f"⚡ Tempo: {resultado['tempo_processamento']:.2f}s")
        print(f"📝 Textos: {resultado['textos_extraidos']}")
        print(f"🏷️ Marcas: {resultado['total_marcas']}")
        
        if resultado['marcas_detectadas']:
            print("\n✅ MARCAS ENCONTRADAS:")
            for marca in resultado['marcas_detectadas']:
                matches_str = ', '.join(marca['matches'])
                print(f"  🍺 {marca['marca']} - {matches_str} (conf: {marca['confianca']})")
        else:
            print("\n❌ Nenhuma marca identificada")
            
        if resultado['textos_completos']:
            print(f"\n📝 TEXTOS EXTRAÍDOS ({len(resultado['textos_completos'])}):")
            for i, texto in enumerate(resultado['textos_completos'][:5]):  # Max 5
                texto_limpo = texto['texto'].replace('\n', ' ').strip()
                if texto_limpo:
                    print(f"  {i+1}. '{texto_limpo}' (v{texto['versao_img']}.{texto['config_ocr']})")

def main():
    """Execução principal ultra rápida"""
    
    detector = DetectorUltraRapido()
    
    # Testar com imagem do WhatsApp
    caminho_teste = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if os.path.exists(caminho_teste):
        print("⚡ DETECTOR ULTRA RÁPIDO INICIANDO...")
        
        resultado = detector.processar_imagem_ultra_rapido(caminho_teste)
        detector.mostrar_resultado(resultado)
        
        # Salvar resultado
        with open('deteccao_ultra_rapida.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Salvo em: deteccao_ultra_rapida.json")
        
    else:
        print(f"❌ Arquivo não encontrado: {caminho_teste}")

if __name__ == "__main__":
    main()