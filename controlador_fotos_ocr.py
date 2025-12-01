#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONTROLADOR DO APP FOTOS + OCR
Manipula o aplicativo Fotos do Windows + detecta produtos
"""

import os
import cv2
import numpy as np
import pytesseract
import time
import pyautogui
import subprocess
from ultralytics import YOLO
from pathlib import Path

class ControladorFotos:
    """Controla o app Fotos do Windows + executa OCR"""
    
    def __init__(self):
        print("📷 CONTROLADOR DO APP FOTOS + OCR")
        
        # Configurar pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Carregar YOLO
        self.model = YOLO('yolov8n.pt')
        
        # Marcas conhecidas
        self.marcas = {
            'HEINEKEN': ['HEINEKEN', 'HEINE', 'NEKEN'],
            'DEVASSA': ['DEVASSA', 'DEVAS', 'EVASSA'],
            'BUDWEISER': ['BUDWEISER', 'BUDWEI', 'BUD'],
            'AMSTEL': ['AMSTEL', 'AMSTE', 'MATEL'],
            'STELLA': ['STELLA', 'ARTOIS', 'STELA'],
            'BRAHMA': ['BRAHMA', 'BRAMA', 'RAHMA'],
            'SKOL': ['SKOL', 'SK0L', 'KOLL'],
            'PEPSI': ['PEPSI', 'P3PSI', 'PEPS'],
            'COCA': ['COCA', 'COLA', 'COCACOLA']
        }
    
    def abrir_foto_no_app(self, caminho_imagem):
        """Abre foto no app Fotos do Windows"""
        print(f"📱 Abrindo no app Fotos: {Path(caminho_imagem).name}")
        
        try:
            # Método 1: Comando direto
            subprocess.run(['start', 'ms-photos:', caminho_imagem], shell=True, check=True)
            time.sleep(3)  # Aguardar app abrir
            
            print("✅ App Fotos aberto")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao abrir Fotos: {e}")
            
            # Método alternativo
            try:
                os.startfile(caminho_imagem)
                time.sleep(3)
                print("✅ Imagem aberta (método alternativo)")
                return True
            except Exception as e2:
                print(f"❌ Erro alternativo: {e2}")
                return False
    
    def controlar_app_fotos(self):
        """Controla o app Fotos usando automação"""
        print("\n🎮 CONTROLANDO APP FOTOS:")
        
        # Aguardar app estar pronto
        time.sleep(2)
        
        print("  🔍 Aplicando zoom para melhor visualização...")
        
        # Zoom in (Ctrl + Plus)
        pyautogui.hotkey('ctrl', 'plus')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'plus')
        time.sleep(0.5)
        
        print("  📸 Capturando screenshot da tela...")
        
        # Capturar screenshot da imagem no app
        screenshot = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Salvar screenshot
        cv2.imwrite("screenshot_app_fotos.jpg", screenshot_cv)
        print("  💾 Screenshot salvo: screenshot_app_fotos.jpg")
        
        return screenshot_cv
    
    def detectar_e_ler_na_tela(self, screenshot):
        """Detecta produtos na tela e lê nomes com OCR"""
        print("\n🔍 DETECTANDO PRODUTOS NA TELA:")
        
        altura, largura = screenshot.shape[:2]
        print(f"  📐 Tela capturada: {largura}x{altura}")
        
        # Detectar produtos no screenshot
        results = self.model.predict(
            source=screenshot,
            conf=0.3,
            save=False,
            verbose=False
        )
        
        boxes = results[0].boxes
        print(f"  📦 Produtos detectados: {len(boxes)}")
        
        if len(boxes) == 0:
            print("  ⚠️  Nenhum produto detectado na tela")
            return []
        
        resultados = []
        
        for i, box in enumerate(boxes):
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            conf = float(box.conf[0])
            
            print(f"\n  🎯 PRODUTO {i+1}:")
            print(f"     Posição: [{x1},{y1},{x2},{y2}]")
            print(f"     Confiança: {conf*100:.1f}%")
            
            # Extrair região do produto
            produto_img = screenshot[y1:y2, x1:x2]
            
            if produto_img.size == 0:
                continue
            
            # Salvar produto
            cv2.imwrite(f"produto_tela_{i+1}.jpg", produto_img)
            
            # Aplicar OCR com preprocessamento
            nome_detectado = self.ocr_com_preprocessamento(produto_img, i+1)
            
            resultado = {
                'id': i+1,
                'bbox': (x1, y1, x2, y2),
                'confianca': conf,
                'nome': nome_detectado
            }
            
            resultados.append(resultado)
            print(f"     🏷️  Nome detectado: {nome_detectado}")
        
        return resultados
    
    def ocr_com_preprocessamento(self, produto_img, produto_id):
        """Aplica OCR com preprocessamento intensivo"""
        print(f"    🔤 Aplicando OCR no produto {produto_id}...")
        
        altura_p, largura_p = produto_img.shape[:2]
        
        # Focar na região do rótulo (parte superior central)
        x1_rot = int(largura_p * 0.15)
        y1_rot = int(altura_p * 0.1)
        x2_rot = int(largura_p * 0.85)
        y2_rot = int(altura_p * 0.6)
        
        rotulo = produto_img[y1_rot:y2_rot, x1_rot:x2_rot]
        
        if rotulo.size == 0:
            rotulo = produto_img  # Usar imagem completa se região for inválida
        
        # Salvar região do rótulo
        cv2.imwrite(f"rotulo_{produto_id}.jpg", rotulo)
        
        # PREPROCESSAMENTOS PARA OCR
        preprocessamentos = self._aplicar_preprocessamentos(rotulo, produto_id)
        
        # Tentar OCR em cada preprocessamento
        todos_textos = []
        
        for nome_prep, img_prep in preprocessamentos:
            print(f"      📝 Testando {nome_prep}...")
            
            # Configurações OCR
            configs = [
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ]
            
            for config in configs:
                try:
                    texto = pytesseract.image_to_string(img_prep, lang='eng+por', config=config)
                    texto_limpo = self._limpar_texto_ocr(texto)
                    
                    if texto_limpo and len(texto_limpo) >= 3:
                        todos_textos.append(texto_limpo)
                        print(f"        📄 Texto: '{texto_limpo}'")
                
                except Exception as e:
                    continue
        
        # Analisar textos para identificar marca
        return self._identificar_marca(todos_textos)
    
    def _aplicar_preprocessamentos(self, rotulo, produto_id):
        """Aplica múltiplos preprocessamentos"""
        preprocessamentos = []
        
        # 1. Original
        preprocessamentos.append(("original", rotulo))
        
        # 2. Escala de cinza
        gray = cv2.cvtColor(rotulo, cv2.COLOR_BGR2GRAY)
        preprocessamentos.append(("cinza", gray))
        
        # 3. Contraste alto
        contraste = cv2.convertScaleAbs(gray, alpha=3.5, beta=40)
        preprocessamentos.append(("contraste_alto", contraste))
        cv2.imwrite(f"debug_contraste_{produto_id}.jpg", contraste)
        
        # 4. Threshold OTSU
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessamentos.append(("threshold_otsu", thresh_otsu))
        cv2.imwrite(f"debug_threshold_{produto_id}.jpg", thresh_otsu)
        
        # 5. Threshold adaptativo
        thresh_adapt = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        preprocessamentos.append(("adaptativo", thresh_adapt))
        
        # 6. Morfologia para limpar texto
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel)
        preprocessamentos.append(("morfologia", morph))
        
        # 7. Denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        preprocessamentos.append(("denoised", denoised))
        
        # 8. Erosão + Dilatação
        kernel_ero = np.ones((1, 1), np.uint8)
        erosao = cv2.erode(thresh_otsu, kernel_ero, iterations=1)
        dilatacao = cv2.dilate(erosao, kernel_ero, iterations=1)
        preprocessamentos.append(("erosao_dilatacao", dilatacao))
        
        print(f"      🔧 {len(preprocessamentos)} preprocessamentos aplicados")
        return preprocessamentos
    
    def _limpar_texto_ocr(self, texto):
        """Limpa texto do OCR"""
        if not texto:
            return ""
        
        import re
        
        # Manter só letras, números e espaços
        texto_limpo = re.sub(r'[^A-Za-z0-9\s]', '', texto)
        texto_limpo = texto_limpo.strip().upper()
        
        # Correções comuns de OCR
        correções = {
            '0': 'O', '1': 'I', '3': 'E', '5': 'S', 
            '6': 'G', '8': 'B', '9': 'G'
        }
        
        for errado, correto in correções.items():
            texto_limpo = texto_limpo.replace(errado, correto)
        
        return texto_limpo
    
    def _identificar_marca(self, textos):
        """Identifica marca nos textos encontrados"""
        if not textos:
            return "NÃO_IDENTIFICADO"
        
        # Combinar todos os textos
        texto_completo = " ".join(textos).upper()
        
        # Procurar marcas conhecidas
        for marca, padroes in self.marcas.items():
            for padrao in padroes:
                if padrao in texto_completo:
                    return marca
        
        # Se não encontrou, retornar o melhor texto
        melhor_texto = max(textos, key=len) if textos else ""
        
        if melhor_texto and len(melhor_texto) >= 4:
            return f"PRODUTO_{melhor_texto[:15]}"
        
        return "NÃO_IDENTIFICADO"
    
    def marcar_produtos_na_tela(self, resultados):
        """Marca produtos detectados na tela usando pyautogui"""
        print(f"\n🎯 MARCANDO {len(resultados)} PRODUTO(S) NA TELA:")
        
        for resultado in resultados:
            x1, y1, x2, y2 = resultado['bbox']
            nome = resultado['nome']
            
            # Calcular centro do produto
            centro_x = (x1 + x2) // 2
            centro_y = (y1 + y2) // 2
            
            print(f"  🖱️  Clicando no produto: {nome}")
            
            # Mover mouse para o produto e clicar
            pyautogui.moveTo(centro_x, centro_y)
            time.sleep(0.5)
            pyautogui.click()
            time.sleep(0.5)
            
            # Usar ferramenta de desenho (se disponível)
            try:
                # Tentar ativar ferramenta de edição
                pyautogui.hotkey('ctrl', 'e')  # Editar no Fotos
                time.sleep(1)
            except:
                pass
    
    def criar_resultado_visual(self, screenshot, resultados):
        """Cria imagem resultado com marcações"""
        img_resultado = screenshot.copy()
        
        for resultado in resultados:
            x1, y1, x2, y2 = resultado['bbox']
            nome = resultado['nome']
            conf = resultado['confianca']
            
            # Cor baseada no sucesso
            cor = (0, 255, 0) if nome != 'NÃO_IDENTIFICADO' else (0, 165, 255)
            
            # Desenhar bbox
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 4)
            
            # Texto do nome
            cv2.putText(img_resultado, nome, (x1, y1-50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, cor, 3)
            
            # Confiança
            cv2.putText(img_resultado, f"{conf*100:.0f}%", (x1, y1-15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
        
        # Salvar resultado
        cv2.imwrite("resultado_app_fotos_ocr.jpg", img_resultado)
        return img_resultado

def main():
    """Função principal"""
    print("📷 CONTROLADOR APP FOTOS + OCR COM PREPROCESSAMENTO")
    print("="*60)
    
    caminho_imagem = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
    
    if not os.path.exists(caminho_imagem):
        print(f"❌ Imagem não encontrada: {caminho_imagem}")
        return
    
    # Inicializar controlador
    controlador = ControladorFotos()
    
    try:
        # 1. Abrir foto no app Fotos
        if not controlador.abrir_foto_no_app(caminho_imagem):
            print("❌ Não foi possível abrir o app Fotos")
            return
        
        # 2. Controlar app e capturar tela
        screenshot = controlador.controlar_app_fotos()
        
        # 3. Detectar produtos na tela com OCR
        resultados = controlador.detectar_e_ler_na_tela(screenshot)
        
        if resultados:
            # 4. Marcar produtos na tela
            controlador.marcar_produtos_na_tela(resultados)
            
            # 5. Criar resultado visual
            controlador.criar_resultado_visual(screenshot, resultados)
            
            # 6. Mostrar resumo
            print(f"\n🎯 RESUMO FINAL:")
            for res in resultados:
                nome = res['nome']
                conf = res['confianca']
                emoji = "✅" if nome != 'NÃO_IDENTIFICADO' else "❓"
                print(f"   {emoji} {nome} ({conf*100:.0f}%)")
            
            print(f"\n💾 Arquivos gerados:")
            print(f"   - resultado_app_fotos_ocr.jpg (resultado final)")
            print(f"   - screenshot_app_fotos.jpg (captura da tela)")
            print(f"   - produto_tela_*.jpg (produtos detectados)")
            print(f"   - rotulo_*.jpg (regiões dos rótulos)")
            print(f"   - debug_*.jpg (preprocessamentos)")
        
        else:
            print("❌ Nenhum produto detectado")
        
        print("\n✅ CONTROLE DO APP FOTOS CONCLUÍDO!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()