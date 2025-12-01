#!/usr/bin/env python3
"""
DETECÇÃO HÍBRIDA: NOSSA METODOLOGIA + YOLOv8 BACKUP
Combina nosso método HSV+Forma (testado 4/4 Corona) com YOLOv8 como fallback
Baseado em: ThanhSan97/Retail-Product-Detection-using-YOLOv8
"""

import cv2
import numpy as np
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Verificar se YOLOv8 está disponível
YOLO_DISPONIVEL = False
try:
    from ultralytics import YOLO
    import torch
    YOLO_DISPONIVEL = True
    print("✅ YOLOv8 (ultralytics) disponível")
except ImportError:
    print("⚠️ YOLOv8 não instalado - usando apenas método HSV+Forma")

class DetectorHibrido:
    """
    Detector híbrido que combina:
    1. Método HSV + Análise de Forma (nossa metodologia testada)
    2. YOLOv8 para detecção de produtos em varejo (backup)
    """
    
    def __init__(self, usar_yolo=True, debug=True):
        self.usar_yolo = usar_yolo and YOLO_DISPONIVEL
        self.debug = debug
        self.pasta_debug = None
        
        # Configurar YOLOv8 se disponível
        self.modelo_yolo = None
        if self.usar_yolo:
            self.carregar_yolo()
    
    def carregar_yolo(self):
        """Carrega modelo YOLOv8 para detecção de objetos"""
        try:
            print("🤖 Carregando YOLOv8...")
            
            # Tentar modelos em ordem de preferência
            modelos_disponiveis = [
                'yolov8n.pt',  # Nano (mais rápido)
                'yolov8s.pt',  # Small
                'yolov8m.pt'   # Medium
            ]
            
            for modelo in modelos_disponiveis:
                try:
                    self.modelo_yolo = YOLO(modelo)
                    print(f"✅ YOLOv8 carregado: {modelo}")
                    break
                except Exception as e:
                    print(f"⚠️ Falha ao carregar {modelo}: {e}")
                    continue
            
            if self.modelo_yolo is None:
                print("❌ Nenhum modelo YOLOv8 pôde ser carregado")
                self.usar_yolo = False
                
        except Exception as e:
            print(f"❌ Erro geral ao carregar YOLOv8: {e}")
            self.usar_yolo = False
    
    def detectar_metodo_hsv_forma(self, img) -> List[Dict]:
        """
        MÉTODO PRINCIPAL: HSV + Análise de Forma
        Testado e aprovado: 4/4 produtos Corona
        """
        print("🎨 MÉTODO HSV + FORMA (testado 4/4 Corona)")
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # CORES CORONA ESPECÍFICAS
        lower_branco = np.array([0, 0, 200])
        upper_branco = np.array([180, 30, 255])
        mask_branco = cv2.inRange(hsv, lower_branco, upper_branco)
        
        lower_dourado = np.array([10, 50, 50])
        upper_dourado = np.array([35, 255, 255])
        mask_dourado = cv2.inRange(hsv, lower_dourado, upper_dourado)
        
        # Combinar máscaras
        mask_produtos = cv2.bitwise_or(mask_branco, mask_dourado)
        
        # Limpeza morfológica
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_OPEN, kernel)
        mask_produtos = cv2.morphologyEx(mask_produtos, cv2.MORPH_CLOSE, kernel)
        
        if self.debug and self.pasta_debug:
            cv2.imwrite(os.path.join(self.pasta_debug, "hsv_mask_produtos.jpg"), mask_produtos)
        
        # Encontrar contornos
        contornos, _ = cv2.findContours(mask_produtos, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        produtos_hsv = []
        
        for i, contorno in enumerate(contornos):
            area = cv2.contourArea(contorno)
            
            if area > 8000:  # Área mínima
                x, y, w, h = cv2.boundingRect(contorno)
                aspect_ratio = w / float(h)
                
                # Analisar cor dominante
                roi_branco = mask_branco[y:y+h, x:x+w]
                roi_dourado = mask_dourado[y:y+h, x:x+w]
                
                pixels_branco = np.sum(roi_branco > 0)
                pixels_dourado = np.sum(roi_dourado > 0)
                
                # Classificar
                if pixels_branco > pixels_dourado and 0.5 < aspect_ratio < 2.0:
                    tipo = "LATA_BRANCA"
                    confianca = pixels_branco / (pixels_branco + pixels_dourado + 1)
                elif pixels_dourado > pixels_branco and 0.2 < aspect_ratio < 1.0:
                    tipo = "GARRAFA_DOURADA"
                    confianca = pixels_dourado / (pixels_branco + pixels_dourado + 1)
                else:
                    continue
                
                produtos_hsv.append({
                    'metodo': 'HSV_FORMA',
                    'tipo': tipo,
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'confianca': confianca,
                    'centro': (x + w//2, y + h//2)
                })
        
        # Remover sobreposições
        produtos_hsv = self.remover_sobreposicoes(produtos_hsv)
        
        garrafas = len([p for p in produtos_hsv if p['tipo'] == 'GARRAFA_DOURADA'])
        latas = len([p for p in produtos_hsv if p['tipo'] == 'LATA_BRANCA'])
        
        print(f"   ✅ HSV: {len(produtos_hsv)} produtos ({garrafas} garrafas, {latas} latas)")
        
        return produtos_hsv
    
    def detectar_yolo(self, img) -> List[Dict]:
        """
        MÉTODO BACKUP: YOLOv8
        Detecção geral de objetos usando YOLOv8
        """
        if not self.usar_yolo or self.modelo_yolo is None:
            return []
        
        print("🤖 MÉTODO YOLO (backup/validação)")
        
        try:
            # Executar detecção YOLOv8
            resultados = self.modelo_yolo(img, conf=0.25, verbose=False)
            
            produtos_yolo = []
            
            for resultado in resultados:
                boxes = resultado.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extrair informações da detecção
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confianca = box.conf[0].cpu().numpy()
                        classe_id = int(box.cls[0].cpu().numpy())
                        
                        # Converter para nosso formato
                        x, y, w, h = int(x1), int(y1), int(x2-x1), int(y2-y1)
                        
                        # Filtrar apenas objetos relevantes (garrafas, latas, etc.)
                        # Classes COCO: 39=bottle, 44=bottle (wine), etc.
                        classes_relevantes = [39, 44, 47]  # bottle, wine glass, cup
                        
                        if classe_id in classes_relevantes:
                            aspect_ratio = w / float(h)
                            
                            # Classificar por forma
                            if aspect_ratio < 0.7:
                                tipo = "GARRAFA_YOLO"
                            elif 0.7 <= aspect_ratio <= 1.5:
                                tipo = "LATA_YOLO"
                            else:
                                tipo = "OBJETO_YOLO"
                            
                            produtos_yolo.append({
                                'metodo': 'YOLO',
                                'tipo': tipo,
                                'bbox': (x, y, w, h),
                                'area': w * h,
                                'aspect_ratio': aspect_ratio,
                                'confianca': float(confianca),
                                'classe_yolo': classe_id,
                                'centro': (x + w//2, y + h//2)
                            })
            
            print(f"   ✅ YOLO: {len(produtos_yolo)} objetos detectados")
            return produtos_yolo
            
        except Exception as e:
            print(f"   ❌ Erro YOLO: {e}")
            return []
    
    def remover_sobreposicoes(self, produtos: List[Dict]) -> List[Dict]:
        """Remove produtos que se sobrepõem (duplicatas)"""
        produtos_ordenados = sorted(produtos, key=lambda x: x['area'], reverse=True)
        produtos_finais = []
        
        for candidato in produtos_ordenados:
            muito_proximo = False
            
            for aceito in produtos_finais:
                distancia = np.sqrt((candidato['centro'][0] - aceito['centro'][0])**2 + 
                                  (candidato['centro'][1] - aceito['centro'][1])**2)
                
                if distancia < 100:
                    muito_proximo = True
                    break
            
            if not muito_proximo:
                produtos_finais.append(candidato)
        
        return produtos_finais
    
    def combinar_resultados(self, produtos_hsv: List[Dict], produtos_yolo: List[Dict]) -> Dict:
        """
        Combina resultados dos dois métodos
        Prioriza HSV (testado) mas usa YOLO para validação
        """
        print("🔄 COMBINANDO RESULTADOS...")
        
        # Método HSV tem prioridade (testado e aprovado)
        produtos_finais = produtos_hsv.copy()
        
        # YOLO como validação/backup
        if produtos_yolo:
            print(f"   📊 HSV detectou {len(produtos_hsv)}, YOLO detectou {len(produtos_yolo)}")
            
            # Se HSV não detectou nada, usar YOLO
            if not produtos_hsv:
                print("   🔄 HSV não detectou produtos, usando resultados YOLO")
                produtos_finais = produtos_yolo
            
            # Se diferença muito grande, investigar
            elif abs(len(produtos_hsv) - len(produtos_yolo)) > 2:
                print(f"   ⚠️ Grande diferença: HSV={len(produtos_hsv)}, YOLO={len(produtos_yolo)}")
        
        # Estatísticas
        estatisticas = {
            'total_hsv': len(produtos_hsv),
            'total_yolo': len(produtos_yolo),
            'total_final': len(produtos_finais),
            'metodo_principal': 'HSV_FORMA' if produtos_hsv else 'YOLO' if produtos_yolo else 'NENHUM'
        }
        
        if produtos_hsv:
            garrafas_hsv = len([p for p in produtos_hsv if 'GARRAFA' in p['tipo']])
            latas_hsv = len([p for p in produtos_hsv if 'LATA' in p['tipo']])
            estatisticas.update({
                'garrafas_hsv': garrafas_hsv,
                'latas_hsv': latas_hsv,
                'corona_perfeito': (len(produtos_hsv) == 4 and garrafas_hsv == 3 and latas_hsv == 1)
            })
        
        return {
            'produtos': produtos_finais,
            'estatisticas': estatisticas,
            'detalhes': {
                'hsv': produtos_hsv,
                'yolo': produtos_yolo
            }
        }
    
    def detectar_produtos_hibrido(self, img, pasta_debug=None) -> Dict:
        """
        MÉTODO PRINCIPAL: Detecção híbrida
        Combina HSV+Forma (principal) com YOLOv8 (backup)
        """
        print("🔍 DETECÇÃO HÍBRIDA: HSV+Forma + YOLOv8")
        
        if pasta_debug:
            self.pasta_debug = pasta_debug
            cv2.imwrite(os.path.join(pasta_debug, "original.jpg"), img)
        
        # MÉTODO 1: HSV + Forma (nossa metodologia testada)
        produtos_hsv = self.detectar_metodo_hsv_forma(img)
        
        # MÉTODO 2: YOLOv8 (backup/validação)
        produtos_yolo = []
        if self.usar_yolo:
            produtos_yolo = self.detectar_yolo(img)
        
        # COMBINAR RESULTADOS
        resultado_final = self.combinar_resultados(produtos_hsv, produtos_yolo)
        
        # DEBUG: Desenhar detecções
        if self.debug and self.pasta_debug:
            self.desenhar_deteccoes_comparativas(img, resultado_final)
        
        return resultado_final
    
    def desenhar_deteccoes_comparativas(self, img, resultado_final):
        """Desenha detecções dos dois métodos para comparação"""
        
        # Imagem com HSV
        img_hsv = img.copy()
        for produto in resultado_final['detalhes']['hsv']:
            x, y, w, h = produto['bbox']
            cor = (0, 255, 0) if 'GARRAFA' in produto['tipo'] else (255, 255, 255)
            cv2.rectangle(img_hsv, (x, y), (x+w, y+h), cor, 3)
            cv2.putText(img_hsv, produto['tipo'][:6], (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
        
        cv2.imwrite(os.path.join(self.pasta_debug, "deteccoes_hsv.jpg"), img_hsv)
        
        # Imagem com YOLO
        if resultado_final['detalhes']['yolo']:
            img_yolo = img.copy()
            for produto in resultado_final['detalhes']['yolo']:
                x, y, w, h = produto['bbox']
                cv2.rectangle(img_yolo, (x, y), (x+w, y+h), (0, 0, 255), 3)
                texto = f"{produto['tipo'][:6]} {produto['confianca']:.2f}"
                cv2.putText(img_yolo, texto, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            cv2.imwrite(os.path.join(self.pasta_debug, "deteccoes_yolo.jpg"), img_yolo)

def exemplo_uso_hibrido():
    """Exemplo de uso do detector híbrido"""
    print("=" * 80)
    print("🔍 DETECTOR HÍBRIDO: HSV+Forma + YOLOv8")
    print("🎯 Método principal: HSV testado (4/4 Corona)")
    print("🤖 Método backup: YOLOv8 para validação")
    print("=" * 80)
    
    # Criar detector
    detector = DetectorHibrido(usar_yolo=True, debug=True)
    
    # Caminho da imagem Corona
    imagem_path = "imagens_teste/corona_produtos.jpeg"
    
    if not os.path.exists(imagem_path):
        print(f"❌ Imagem não encontrada: {imagem_path}")
        return
    
    # Carregar imagem
    img = cv2.imread(imagem_path)
    if img is None:
        print(f"❌ Erro ao carregar imagem")
        return
    
    # Criar pasta de debug
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_debug = f"deteccao_hibrida_{timestamp}"
    os.makedirs(pasta_debug, exist_ok=True)
    
    print(f"📁 Pasta debug: {os.path.abspath(pasta_debug)}")
    
    # DETECÇÃO HÍBRIDA
    resultado = detector.detectar_produtos_hibrido(img, pasta_debug)
    
    # MOSTRAR RESULTADOS
    produtos = resultado['produtos']
    stats = resultado['estatisticas']
    
    print(f"\n🎉 RESULTADO HÍBRIDO:")
    print(f"   📊 HSV detectou: {stats['total_hsv']} produtos")
    if YOLO_DISPONIVEL:
        print(f"   📊 YOLO detectou: {stats['total_yolo']} produtos")
    print(f"   ✅ FINAL: {stats['total_final']} produtos")
    print(f"   🔧 Método usado: {stats['metodo_principal']}")
    
    if stats.get('corona_perfeito'):
        print(f"   🏆 PERFEITO! Detectou exatamente 3 garrafas + 1 lata = 4 produtos Corona")
    
    # Relatório
    with open(os.path.join(pasta_debug, "relatorio_hibrido.txt"), 'w', encoding='utf-8') as f:
        f.write("DETECÇÃO HÍBRIDA: HSV + YOLOv8\n")
        f.write("=" * 35 + "\n\n")
        
        f.write("MÉTODOS TESTADOS:\n")
        f.write("1. HSV + Análise de Forma (principal)\n")
        f.write("2. YOLOv8 (backup/validação)\n\n")
        
        f.write("RESULTADOS:\n")
        f.write(f"- HSV: {stats['total_hsv']} produtos\n")
        f.write(f"- YOLO: {stats['total_yolo']} produtos\n")
        f.write(f"- FINAL: {stats['total_final']} produtos\n")
        f.write(f"- MÉTODO PRINCIPAL: {stats['metodo_principal']}\n\n")
        
        if stats.get('corona_perfeito'):
            f.write("✅ STATUS: PERFEITO!\n")
            f.write("Detectou exatamente 3 garrafas + 1 lata = 4 produtos Corona\n")
        
        f.write("\nPRODUTOS DETECTADOS:\n")
        for i, produto in enumerate(produtos, 1):
            f.write(f"{i}. {produto['tipo']} ({produto['metodo']})\n")
            f.write(f"   Confiança: {produto['confianca']:.2f}\n")
            f.write(f"   Posição: {produto['bbox']}\n\n")
        
        f.write("BACKUP: ThanhSan97/Retail-Product-Detection-using-YOLOv8\n")
        f.write("Referência GitHub para YOLOv8 em produtos de varejo\n")
    
    try:
        os.startfile(os.path.abspath(pasta_debug))
        print("📂 Pasta de resultados aberta!")
    except:
        pass
    
    return resultado

def instalar_dependencias():
    """Script para instalar dependências necessárias"""
    print("📦 INSTALAÇÃO DE DEPENDÊNCIAS")
    print("Para usar YOLOv8, execute:")
    print("pip install ultralytics")
    print("pip install torch torchvision")
    print("\nRepositório de referência:")
    print("https://github.com/ThanhSan97/Retail-Product-Detection-using-YOLOv8")

if __name__ == "__main__":
    if not YOLO_DISPONIVEL:
        print("⚠️ YOLOv8 não disponível")
        instalar_dependencias()
        print("\n🔄 Executando apenas com método HSV...")
    
    # Executar exemplo
    exemplo_uso_hibrido()