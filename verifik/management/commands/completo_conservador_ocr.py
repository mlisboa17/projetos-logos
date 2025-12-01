from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from datetime import datetime
import json
import tempfile


class Command(BaseCommand):
    help = 'Pré-processamento Conservador + YOLO + OCR nos produtos detectados'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima YOLO (padrão: 0.25)')
        parser.add_argument('--reduzir-luz', type=float, default=0.85,
                          help='Fator de redução de luminosidade (0.85 = reduzir 15%)')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        confianca = options['confianca']
        reducao_luz = options['reduzir_luz']

        self.stdout.write('=' * 100)
        self.stdout.write('🔧 PROCESSAMENTO COMPLETO: CONSERVADOR + YOLO + OCR')
        self.stdout.write('=' * 100)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Confiança YOLO: {confianca}')
        self.stdout.write(f'   Redução luminosidade: {int((1-reducao_luz)*100)}%')

        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'processamento_completo_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')

            # ETAPA 1: PRÉ-PROCESSAMENTO CONSERVADOR
            img_processada = self.preprocessing_conservador_completo(imagem_path, reducao_luz, output_dir)
            
            # ETAPA 2: DETECÇÃO YOLO
            deteccoes = self.executar_deteccao_yolo(img_processada, confianca, output_dir)
            
            if not deteccoes:
                self.stdout.write(self.style.WARNING('⚠️  Nenhuma detecção - finalizando sem OCR'))
                return
            
            # ETAPA 3: OCR NAS REGIÕES DETECTADAS
            resultados_ocr = self.executar_ocr_nas_deteccoes(img_processada, deteccoes, output_dir)
            
            # ETAPA 4: RESULTADO FINAL COMBINADO
            self.gerar_resultado_final_combinado(img_processada, deteccoes, resultados_ocr, output_dir)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def preprocessing_conservador_completo(self, imagem_path, reducao_luz, output_dir):
        """ETAPA 1: Pré-processamento conservador completo"""
        self.stdout.write(f'\n🎨 ETAPA 1: PRÉ-PROCESSAMENTO CONSERVADOR')
        
        # Carregar imagem
        img_original = cv2.imread(imagem_path)
        altura, largura = img_original.shape[:2]
        self.stdout.write(f'   ✓ Imagem carregada: {largura}x{altura}')
        
        # Salvar original
        cv2.imwrite(str(output_dir / '01_original.jpg'), img_original)
        
        # SUB-ETAPA 1.1: REMOVER FUNDO CONSERVADOR
        img_sem_fundo = self.remover_fundo_conservador(img_original, output_dir)
        
        # SUB-ETAPA 1.2: AJUSTAR LUMINOSIDADE
        img_ajustada = self.ajustar_luminosidade(img_sem_fundo, reducao_luz, output_dir)
        
        # SUB-ETAPA 1.3: MELHORAR QUALIDADE
        img_final = self.melhorar_qualidade_final(img_ajustada, output_dir)
        
        # Salvar resultado do pré-processamento
        preprocessed_path = output_dir / '01_preprocessamento_final.jpg'
        cv2.imwrite(str(preprocessed_path), img_final)
        
        self.stdout.write(f'   ✅ Pré-processamento conservador concluído')
        
        return img_final

    def remover_fundo_conservador(self, img, output_dir):
        """Remoção de fundo muito conservadora"""
        altura, largura = img.shape[:2]
        
        # Detectar contornos
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 30, 100)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges_dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Criar máscara
        mask = np.zeros(gray.shape, dtype=np.uint8)
        area_minima = (altura * largura) * 0.001
        
        contornos_validos = [c for c in contours if cv2.contourArea(c) > area_minima]
        cv2.fillPoly(mask, contornos_validos, 255)
        
        # Expandir máscara MUITO (para preservar produtos)
        kernel_expand = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))  # Kernel bem grande
        mask_expanded = cv2.dilate(mask, kernel_expand, iterations=4)  # 4 iterações
        
        # Suavizar
        mask_smooth = cv2.GaussianBlur(mask_expanded, (25, 25), 0)
        mask_norm = mask_smooth.astype(np.float32) / 255.0
        
        # Aplicar com fundo cinza claro
        fundo = np.full_like(img, (245, 245, 245), dtype=np.uint8)
        
        img_result = img.astype(np.float32)
        fundo_float = fundo.astype(np.float32)
        
        for c in range(3):
            img_result[:, :, c] = (img_result[:, :, c] * mask_norm + 
                                 fundo_float[:, :, c] * (1 - mask_norm))
        
        resultado = img_result.astype(np.uint8)
        
        # Salvar
        cv2.imwrite(str(output_dir / '01a_fundo_removido.jpg'), resultado)
        
        return resultado

    def ajustar_luminosidade(self, img, fator, output_dir):
        """Ajustar luminosidade da imagem"""
        self.stdout.write(f'   💡 Ajustando luminosidade ({int((1-fator)*100)}% redução)...')
        
        # Converter para HSV para ajustar apenas o V (Value/Luminosidade)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Reduzir luminosidade
        v_adjusted = cv2.multiply(v, fator)
        
        # Recompor imagem
        hsv_adjusted = cv2.merge([h, s, v_adjusted])
        img_adjusted = cv2.cvtColor(hsv_adjusted, cv2.COLOR_HSV2BGR)
        
        # Salvar
        cv2.imwrite(str(output_dir / '01b_luminosidade_ajustada.jpg'), img_adjusted)
        
        return img_adjusted

    def melhorar_qualidade_final(self, img, output_dir):
        """Melhorias finais de qualidade"""
        self.stdout.write(f'   ✨ Aplicando melhorias finais...')
        
        # CLAHE adaptativo
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img_clahe = cv2.merge([l, a, b])
        img_clahe = cv2.cvtColor(img_clahe, cv2.COLOR_LAB2BGR)
        
        # Sharpening suave
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        img_sharp = cv2.filter2D(img_clahe, -1, kernel)
        
        # Misturar (80% processada + 20% original)
        img_final = cv2.addWeighted(img_sharp, 0.8, img_clahe, 0.2, 0)
        
        # Salvar
        cv2.imwrite(str(output_dir / '01c_qualidade_final.jpg'), img_final)
        
        return img_final

    def executar_deteccao_yolo(self, img, confianca, output_dir):
        """ETAPA 2: Detecção YOLO na imagem processada"""
        self.stdout.write(f'\n🎯 ETAPA 2: DETECÇÃO YOLO PÓS-PROCESSAMENTO')
        
        try:
            from ultralytics import YOLO
            
            # Carregar modelo
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ ProductScan_v1 não encontrado'))
                return []
                
            model = YOLO(model_path)
            self.stdout.write(f'   ✓ ProductScan_v1 carregado')

            # Salvar imagem temporária para detecção
            temp_path = output_dir / 'temp_deteccao.jpg'
            cv2.imwrite(str(temp_path), img)
            
            # Executar detecção
            resultados = model.predict(str(temp_path), conf=confianca, verbose=False)
            
            if not resultados or len(resultados) == 0:
                self.stdout.write(f'   ❌ Nenhum resultado')
                return []
                
            resultado = resultados[0]
            boxes = resultado.boxes
            
            if boxes is None or len(boxes) == 0:
                self.stdout.write(f'   ❌ Nenhum produto detectado')
                return []
            
            # Processar detecções
            deteccoes = []
            img_deteccoes = img.copy()
            
            self.stdout.write(f'   🎯 {len(boxes)} produtos detectados:')
            
            for i, box in enumerate(boxes):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                deteccao = {
                    'id': i,
                    'classe': nome_classe,
                    'confianca': conf,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'centro': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                    'area': int((x2 - x1) * (y2 - y1))
                }
                deteccoes.append(deteccao)
                
                self.stdout.write(f'     [{i+1}] {nome_classe}: {conf*100:.1f}% - Área: {deteccao["area"]}px')
                
                # Desenhar detecção
                cor = (0, 255, 0) if conf > 0.5 else (0, 255, 255)
                cv2.rectangle(img_deteccoes, (int(x1), int(y1)), (int(x2), int(y2)), cor, 3)
                cv2.putText(img_deteccoes, f'{nome_classe} {conf:.2f}', (int(x1), int(y1)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            
            # Salvar resultado da detecção
            deteccao_path = output_dir / '02_deteccoes_yolo.jpg'
            cv2.imwrite(str(deteccao_path), img_deteccoes)
            
            # Salvar dados JSON
            deteccoes_json = output_dir / '02_deteccoes_dados.json'
            with open(deteccoes_json, 'w', encoding='utf-8') as f:
                json.dump(deteccoes, f, indent=2, ensure_ascii=False)
            
            # Remover arquivo temporário
            temp_path.unlink()
            
            self.stdout.write(f'   ✅ Detecções processadas e salvas')
            
            return deteccoes
            
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            return []

    def executar_ocr_nas_deteccoes(self, img, deteccoes, output_dir):
        """ETAPA 3: OCR nas regiões detectadas pelo YOLO"""
        self.stdout.write(f'\n📖 ETAPA 3: OCR NAS REGIÕES DETECTADAS')
        
        # Tentar EasyOCR primeiro
        ocr_reader = None
        ocr_engine = None
        
        try:
            import easyocr
            ocr_reader = easyocr.Reader(['pt', 'en'])
            ocr_engine = 'easyocr'
            self.stdout.write(f'   ✓ EasyOCR inicializado')
        except:
            # Fallback para Tesseract
            try:
                import pytesseract
                ocr_engine = 'tesseract'
                self.stdout.write(f'   ✓ Tesseract inicializado')
            except:
                self.stdout.write(self.style.ERROR('   ✗ Nenhum OCR disponível'))
                return {}
        
        resultados_ocr = {}
        img_com_ocr = img.copy()
        
        for det in deteccoes:
            det_id = det['id']
            x1, y1, x2, y2 = det['bbox']
            classe = det['classe']
            
            self.stdout.write(f'\n   📄 OCR na detecção {det_id+1} ({classe}):')
            
            # Expandir região para capturar rótulos ao redor
            margem = 30
            altura_img, largura_img = img.shape[:2]
            
            x1_exp = max(0, x1 - margem)
            y1_exp = max(0, y1 - margem)
            x2_exp = min(largura_img, x2 + margem)
            y2_exp = min(altura_img, y2 + margem)
            
            # Extrair região expandida
            regiao = img[y1_exp:y2_exp, x1_exp:x2_exp]
            
            if regiao.size == 0:
                continue
            
            # Pré-processar região para OCR
            regiao_ocr = self.preprocessar_para_ocr(regiao)
            
            # Salvar região para análise
            regiao_path = output_dir / f'03_regiao_{det_id+1}_{classe}.jpg'
            cv2.imwrite(str(regiao_path), regiao_ocr)
            
            # Executar OCR
            try:
                textos_encontrados = []
                
                if ocr_engine == 'easyocr':
                    resultados = ocr_reader.readtext(regiao_ocr)
                    for (bbox_ocr, text, confidence) in resultados:
                        if confidence > 0.3 and len(text.strip()) > 1:  # Threshold baixo
                            textos_encontrados.append({
                                'text': text.strip(),
                                'confidence': confidence,
                                'bbox': bbox_ocr
                            })
                
                elif ocr_engine == 'tesseract':
                    import pytesseract
                    # Configuração para produtos
                    config = '--oem 3 --psm 6'
                    texto = pytesseract.image_to_string(regiao_ocr, config=config, lang='por+eng')
                    linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
                    
                    for linha in linhas:
                        if len(linha) > 1:
                            textos_encontrados.append({
                                'text': linha,
                                'confidence': 0.8,  # Assumir confiança média
                                'bbox': []
                            })
                
                # Processar textos encontrados
                if textos_encontrados:
                    # Identificar marcas conhecidas
                    marcas = ['corona', 'heineken', 'skol', 'brahma', 'antarctica', 'stella', 'budweiser', 'devassa']
                    produtos_identificados = []
                    
                    for texto_item in textos_encontrados:
                        texto_lower = texto_item['text'].lower()
                        
                        for marca in marcas:
                            if marca in texto_lower:
                                produtos_identificados.append({
                                    'marca': marca.upper(),
                                    'texto_original': texto_item['text'],
                                    'confianca_ocr': texto_item['confidence']
                                })
                                break
                    
                    resultados_ocr[det_id] = {
                        'deteccao': det,
                        'regiao_expandida': [x1_exp, y1_exp, x2_exp, y2_exp],
                        'textos_brutos': textos_encontrados,
                        'produtos_identificados': produtos_identificados
                    }
                    
                    self.stdout.write(f'     ✓ {len(textos_encontrados)} textos encontrados')
                    for texto in textos_encontrados[:3]:  # Mostrar apenas primeiros 3
                        self.stdout.write(f'       - "{texto["text"]}" ({texto["confidence"]:.2f})')
                    
                    if produtos_identificados:
                        self.stdout.write(f'     🏷️  Produtos identificados:')
                        for produto in produtos_identificados:
                            self.stdout.write(f'       - {produto["marca"]}: "{produto["texto_original"]}"')
                    
                    # Desenhar textos na imagem
                    for texto in produtos_identificados:
                        label = f'📖 {texto["marca"]}'
                        cv2.putText(img_com_ocr, label, (x1, y1-30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                else:
                    self.stdout.write(f'     ⭕ Nenhum texto detectado')
                    
            except Exception as e:
                self.stdout.write(f'     ✗ Erro OCR: {str(e)}')
        
        # Salvar imagem com OCR
        ocr_result_path = output_dir / '03_resultado_ocr.jpg'
        cv2.imwrite(str(ocr_result_path), img_com_ocr)
        
        # Salvar dados OCR
        ocr_json_path = output_dir / '03_dados_ocr.json'
        with open(ocr_json_path, 'w', encoding='utf-8') as f:
            json.dump(resultados_ocr, f, indent=2, ensure_ascii=False)
        
        total_textos = sum(len(r.get('textos_brutos', [])) for r in resultados_ocr.values())
        total_produtos = sum(len(r.get('produtos_identificados', [])) for r in resultados_ocr.values())
        
        self.stdout.write(f'\n   ✅ OCR concluído: {total_textos} textos, {total_produtos} produtos identificados')
        
        return resultados_ocr

    def preprocessar_para_ocr(self, regiao):
        """Pré-processar região específica para OCR"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        
        # Redimensionar se muito pequena (melhora OCR)
        altura, largura = gray.shape
        if altura < 50 or largura < 50:
            fator = max(2, 100 // min(altura, largura))
            gray = cv2.resize(gray, (largura * fator, altura * fator), interpolation=cv2.INTER_CUBIC)
        
        # Equalização adaptativa
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Sharpening para texto
        kernel_sharp = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32)
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharp)
        
        # Converter de volta para BGR para compatibilidade
        resultado = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
        
        return resultado

    def gerar_resultado_final_combinado(self, img, deteccoes, resultados_ocr, output_dir):
        """ETAPA 4: Resultado final combinado"""
        self.stdout.write(f'\n🎨 ETAPA 4: RESULTADO FINAL COMBINADO')
        
        img_final = img.copy()
        
        # Desenhar detecções com OCR
        for det in deteccoes:
            det_id = det['id']
            x1, y1, x2, y2 = det['bbox']
            classe = det['classe']
            confianca = det['confianca']
            
            # Cor baseada na confiança
            cor = (0, 255, 0) if confianca > 0.7 else (0, 255, 255) if confianca > 0.4 else (0, 165, 255)
            
            # Bounding box
            cv2.rectangle(img_final, (x1, y1), (x2, y2), cor, 3)
            
            # Label principal
            label_principal = f'{classe} {confianca:.2f}'
            cv2.putText(img_final, label_principal, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            
            # Labels OCR (se disponíveis)
            if det_id in resultados_ocr:
                produtos_ocr = resultados_ocr[det_id].get('produtos_identificados', [])
                y_offset = y1 - 40
                
                for produto in produtos_ocr[:2]:  # Máximo 2 produtos OCR
                    label_ocr = f'📖 {produto["marca"]}'
                    cv2.putText(img_final, label_ocr, (x1, y_offset), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    y_offset -= 25
        
        # Salvar resultado final
        resultado_path = output_dir / '04_resultado_final_completo.jpg'
        cv2.imwrite(str(resultado_path), img_final)
        
        # Abrir resultado
        os.startfile(str(resultado_path))
        
        # Estatísticas finais
        total_deteccoes = len(deteccoes)
        total_com_ocr = len(resultados_ocr)
        total_produtos_ocr = sum(len(r.get('produtos_identificados', [])) for r in resultados_ocr.values())
        
        self.stdout.write(f'\n📊 ESTATÍSTICAS FINAIS:')
        self.stdout.write(f'   ✓ Total de detecções YOLO: {total_deteccoes}')
        self.stdout.write(f'   ✓ Detecções com OCR: {total_com_ocr}')
        self.stdout.write(f'   ✓ Produtos identificados via OCR: {total_produtos_ocr}')
        
        # Resumo por tipo
        tipos_detectados = {}
        for det in deteccoes:
            classe = det['classe']
            tipos_detectados[classe] = tipos_detectados.get(classe, 0) + 1
        
        self.stdout.write(f'\n🏷️  PRODUTOS YOLO:')
        for tipo, quantidade in tipos_detectados.items():
            self.stdout.write(f'   - {tipo}: {quantidade}x')
        
        # Marcas identificadas via OCR
        if total_produtos_ocr > 0:
            marcas_ocr = {}
            for resultado in resultados_ocr.values():
                for produto in resultado.get('produtos_identificados', []):
                    marca = produto['marca']
                    marcas_ocr[marca] = marcas_ocr.get(marca, 0) + 1
            
            self.stdout.write(f'\n📖 MARCAS OCR:')
            for marca, quantidade in marcas_ocr.items():
                self.stdout.write(f'   - {marca}: {quantidade}x')
        
        self.stdout.write(f'\n💾 Resultado final: {resultado_path.name}')
        self.stdout.write(f'📁 Pasta completa: {output_dir.absolute()}')
        self.stdout.write(f'\n🚀 PROCESSAMENTO COMPLETO FINALIZADO!')
        self.stdout.write(f'👁️  RESULTADO ABERTO!')