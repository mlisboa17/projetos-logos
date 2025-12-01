from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Pré-processamento CONSERVADOR - preserva produtos inteiros'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima YOLO (padrão: 0.25)')
        parser.add_argument('--remover-fundo', action='store_true',
                          help='Aplicar remoção de fundo conservadora')
        parser.add_argument('--melhorar-qualidade', action='store_true',
                          help='Aplicar melhorias de qualidade')
        parser.add_argument('--teste-deteccao', action='store_true',
                          help='Testar detecção após processamento')
        parser.add_argument('--luminosidade', type=float, default=0.85,
                          help='Fator de luminosidade (0.8=mais escuro, 1.0=original)')
        parser.add_argument('--ocr', action='store_true',
                          help='Aplicar OCR para reconhecer texto nos produtos')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        confianca = options['confianca']
        remover_fundo = options['remover_fundo']
        melhorar_qualidade = options['melhorar_qualidade']
        teste_deteccao = options['teste_deteccao']
        luminosidade = options['luminosidade']
        usar_ocr = options['ocr']

        self.stdout.write('=' * 80)
        self.stdout.write('🔧 PRÉ-PROCESSAMENTO CONSERVADOR - PRESERVA PRODUTOS')
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Remover fundo: {"✓" if remover_fundo else "✗"}')
        self.stdout.write(f'   Melhorar qualidade: {"✓" if melhorar_qualidade else "✗"}')
        self.stdout.write(f'   Teste detecção: {"✓" if teste_deteccao else "✗"}')
        self.stdout.write(f'   Luminosidade: {luminosidade*100:.0f}%')
        self.stdout.write(f'   OCR: {"✓" if usar_ocr else "✗"}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'preprocessamento_conservador_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')

            # Carregar imagem original
            self.stdout.write(f'\n📥 ETAPA 1: CARREGAMENTO DA IMAGEM')
            img_original = cv2.imread(imagem_path)
            altura, largura = img_original.shape[:2]
            self.stdout.write(f'   ✓ Imagem carregada: {largura}x{altura}')
            
            # Salvar original
            original_path = output_dir / '01_original.jpg'
            cv2.imwrite(str(original_path), img_original)

            img_processada = img_original.copy()

            # ETAPA 2: REMOÇÃO DE FUNDO CONSERVADORA
            if remover_fundo:
                img_processada = self.remover_fundo_conservador(img_processada, output_dir)

            # ETAPA 3: MELHORIA DE QUALIDADE
            if melhorar_qualidade:
                img_processada = self.melhorar_qualidade_conservador(img_processada, luminosidade, output_dir)

            # ETAPA 4: OCR (opcional)
            if usar_ocr:
                self.aplicar_ocr_avancado(img_processada, output_dir)

            # ETAPA 5: TESTE DE DETECÇÃO
            if teste_deteccao:
                self.testar_deteccao_pos_processamento(img_processada, confianca, output_dir)

            # Salvar resultado final
            final_path = output_dir / '99_resultado_final.jpg'
            cv2.imwrite(str(final_path), img_processada)
            
            # Abrir resultado
            os.startfile(str(final_path))
            
            self.stdout.write(f'\n🎯 PROCESSAMENTO CONCLUÍDO!')
            self.stdout.write(f'   📁 Arquivos em: {output_dir.absolute()}')
            self.stdout.write(f'   👁️  Resultado aberto!')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def remover_fundo_conservador(self, img, output_dir):
        """Remoção de fundo MUITO CONSERVADORA para preservar produtos inteiros"""
        self.stdout.write(f'\n🎭 ETAPA 2: REMOÇÃO DE FUNDO CONSERVADORA')
        
        altura, largura = img.shape[:2]
        
        # 1. DETECÇÃO DE CONTORNOS para identificar produtos
        self.stdout.write(f'   🔍 Detectando contornos de produtos...')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Suavizar para reduzir ruído
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detectar bordas com parâmetros conservadores
        edges = cv2.Canny(blur, 30, 100)  # Thresholds baixos para capturar mais bordas
        
        # Dilatar bordas para conectar partes dos produtos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges_dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # 2. ENCONTRAR CONTORNOS DE PRODUTOS
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Criar máscara baseada em contornos
        mask_contours = np.zeros(gray.shape, dtype=np.uint8)
        
        # Filtrar contornos por área (remover ruídos pequenos)
        area_minima = (altura * largura) * 0.001  # 0.1% da imagem
        contornos_validos = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > area_minima:
                contornos_validos.append(contour)
        
        self.stdout.write(f'   ✓ {len(contornos_validos)} contornos de produtos encontrados')
        
        # Desenhar contornos preenchidos na máscara
        cv2.fillPoly(mask_contours, contornos_validos, 255)
        
        # 3. EXPANDIR MÁSCARA para garantir que produtos não sejam cortados
        kernel_expand = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))  # Kernel grande
        mask_expanded = cv2.dilate(mask_contours, kernel_expand, iterations=3)  # 3 iterações
        
        # 4. SUAVIZAR BORDAS da máscara
        mask_smooth = cv2.GaussianBlur(mask_expanded, (21, 21), 0)  # Blur grande para suavizar
        
        # 5. APLICAR MÁSCARA DE FORMA SUAVE
        self.stdout.write(f'   🎨 Aplicando máscara conservadora...')
        
        # Normalizar máscara para [0, 1]
        mask_norm = mask_smooth.astype(np.float32) / 255.0
        
        # Criar fundo neutro (cinza claro para não contrastar)
        fundo = np.full_like(img, (240, 240, 240), dtype=np.uint8)
        
        # Aplicar máscara com transição suave
        img_result = img.astype(np.float32)
        fundo_float = fundo.astype(np.float32)
        
        for c in range(3):  # Para cada canal BGR
            img_result[:, :, c] = (img_result[:, :, c] * mask_norm + 
                                 fundo_float[:, :, c] * (1 - mask_norm))
        
        img_final = img_result.astype(np.uint8)
        
        # 6. SALVAR ETAPAS para análise
        edges_path = output_dir / '02a_bordas_detectadas.jpg'
        cv2.imwrite(str(edges_path), edges)
        
        contours_path = output_dir / '02b_contornos_produtos.jpg'
        img_contours = img.copy()
        cv2.drawContours(img_contours, contornos_validos, -1, (0, 255, 0), 2)
        cv2.imwrite(str(contours_path), img_contours)
        
        mask_path = output_dir / '02c_mascara_expandida.jpg'
        cv2.imwrite(str(mask_path), mask_expanded)
        
        resultado_path = output_dir / '02d_fundo_removido.jpg'
        cv2.imwrite(str(resultado_path), img_final)
        
        self.stdout.write(f'   ✅ Fundo removido preservando produtos inteiros')
        
        return img_final

    def melhorar_qualidade_conservador(self, img, fator_luminosidade, output_dir):
        """Melhorar qualidade da imagem sem afetar produtos"""
        self.stdout.write(f'\n✨ ETAPA 3: MELHORIA DE QUALIDADE CONSERVADORA')
        
        # 1. AJUSTE DE CONTRASTE E LUMINOSIDADE
        self.stdout.write(f'   📈 Aplicando CLAHE adaptativo e reduzindo luminosidade...')
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # REDUZIR LUMINOSIDADE conforme parâmetro
        l_channel_reduced = cv2.multiply(l_channel, fator_luminosidade)
        
        # CLAHE com clipping limitado para melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # Clip um pouco maior
        l_channel_clahe = clahe.apply(l_channel_reduced.astype(np.uint8))
        
        img_clahe = cv2.merge([l_channel_clahe, a_channel, b_channel])
        img_clahe = cv2.cvtColor(img_clahe, cv2.COLOR_LAB2BGR)
        
        # 2. REDUÇÃO DE RUÍDO SUAVE E RÁPIDA
        self.stdout.write(f'   🧹 Reduzindo ruído suavemente...')
        # Usar blur gaussiano ao invés de fastNlMeans (muito mais rápido)
        img_denoised = cv2.GaussianBlur(img_clahe, (3, 3), 0)
        
        # 3. SHARPENING CONTROLADO
        self.stdout.write(f'   🔍 Aplicando nitidez controlada...')
        # Kernel de sharpening suave
        kernel_sharp = np.array([[-0.5, -0.5, -0.5],
                               [-0.5,  5.0, -0.5],
                               [-0.5, -0.5, -0.5]], dtype=np.float32)
        
        img_sharp = cv2.filter2D(img_denoised, -1, kernel_sharp)
        
        # Misturar com original (70% processada + 30% original)
        img_final = cv2.addWeighted(img_sharp, 0.7, img_denoised, 0.3, 0)
        
        # 4. SALVAR ETAPAS
        clahe_path = output_dir / '03a_contraste_adaptativo.jpg'
        cv2.imwrite(str(clahe_path), img_clahe)
        
        denoised_path = output_dir / '03b_ruido_reduzido.jpg'
        cv2.imwrite(str(denoised_path), img_denoised)
        
        sharp_path = output_dir / '03c_nitidez_aplicada.jpg'
        cv2.imwrite(str(sharp_path), img_final)
        
        self.stdout.write(f'   ✅ Qualidade melhorada sem comprometer produtos')
        
        return img_final

    def testar_deteccao_pos_processamento(self, img, confianca, output_dir):
        """Testar detecção YOLO após o processamento"""
        self.stdout.write(f'\n🎯 ETAPA 4: TESTE DE DETECÇÃO PÓS-PROCESSAMENTO')
        
        try:
            from ultralytics import YOLO
            
            # Carregar ProductScan_v1
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(f'   ⚠️  ProductScan_v1 não encontrado')
                return
                
            model = YOLO(model_path)
            self.stdout.write(f'   ✓ ProductScan_v1 carregado')

            # Salvar imagem temporária para detecção
            temp_path = output_dir / 'temp_for_detection.jpg'
            cv2.imwrite(str(temp_path), img)
            
            # Executar detecção
            resultados = model.predict(str(temp_path), conf=confianca, verbose=False)
            
            if not resultados or len(resultados) == 0:
                self.stdout.write(f'   ❌ Nenhum resultado da detecção')
                return
                
            resultado = resultados[0]
            boxes = resultado.boxes
            
            if boxes is None or len(boxes) == 0:
                self.stdout.write(f'   ❌ Nenhum produto detectado')
                return
            
            # Processar detecções
            self.stdout.write(f'   🎯 {len(boxes)} produtos detectados:')
            
            img_deteccoes = img.copy()
            deteccoes_info = []
            
            for i, box in enumerate(boxes):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                deteccoes_info.append({
                    'classe': nome_classe,
                    'confianca': conf,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)]
                })
                
                self.stdout.write(f'     [{i+1}] {nome_classe}: {conf*100:.1f}%')
                
                # Desenhar detecção
                cor = (0, 255, 0) if conf > 0.5 else (0, 255, 255)  # Verde se alta confiança
                cv2.rectangle(img_deteccoes, (int(x1), int(y1)), (int(x2), int(y2)), cor, 2)
                cv2.putText(img_deteccoes, f'{nome_classe} {conf:.2f}', (int(x1), int(y1)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
            
            # Salvar resultado da detecção
            deteccao_path = output_dir / '04_deteccoes_pos_processamento.jpg'
            cv2.imwrite(str(deteccao_path), img_deteccoes)
            
            # Salvar dados JSON
            deteccoes_json_path = output_dir / '04_deteccoes_dados.json'
            with open(deteccoes_json_path, 'w', encoding='utf-8') as f:
                json.dump(deteccoes_info, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f'   ✅ Detecções salvas e testadas')
            
            # Remover arquivo temporário
            temp_path.unlink()
            
        except ImportError:
            self.stdout.write(f'   ⚠️  YOLO não disponível para teste')
        except Exception as e:
            self.stdout.write(f'   ✗ Erro no teste: {str(e)}')

    def aplicar_ocr_avancado(self, img, output_dir):
        """Aplicar OCR avançado para reconhecer produtos e textos"""
        self.stdout.write(f'\n📖 ETAPA 4: OCR AVANÇADO PARA RECONHECIMENTO DE PRODUTOS')
        
        try:
            import easyocr
            reader = easyocr.Reader(['pt', 'en'], gpu=False)  # CPU para compatibilidade
            self.stdout.write(f'   ✓ EasyOCR carregado (PT/EN)')
        except ImportError:
            self.stdout.write(f'   ⚠️  EasyOCR não disponível - tentando pytesseract...')
            try:
                import pytesseract
                self.stdout.write(f'   ✓ Pytesseract carregado')
            except ImportError:
                self.stdout.write(f'   ✗ Nenhuma biblioteca OCR disponível')
                return

        # Preparar imagem para OCR
        img_ocr = self.preparar_imagem_ocr(img, output_dir)
        
        # Executar OCR
        textos_encontrados = []
        produtos_identificados = []
        
        try:
            if 'easyocr' in locals():
                # EasyOCR - melhor para produtos
                self.stdout.write(f'   🔍 Executando EasyOCR...')
                resultados = reader.readtext(img_ocr)
                
                for (bbox, text, confidence) in resultados:
                    if confidence > 0.3 and len(text.strip()) > 1:  # Filtrar textos com baixa confiança
                        textos_encontrados.append({
                            'texto': text.strip(),
                            'confianca': confidence,
                            'bbox': bbox,
                            'metodo': 'EasyOCR'
                        })
            else:
                # Pytesseract como backup
                self.stdout.write(f'   🔍 Executando Pytesseract...')
                config = '--oem 3 --psm 6'
                texto = pytesseract.image_to_string(img_ocr, config=config, lang='por+eng')
                linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
                
                for linha in linhas:
                    textos_encontrados.append({
                        'texto': linha,
                        'confianca': 1.0,
                        'bbox': [],
                        'metodo': 'Tesseract'
                    })
            
            # Identificar produtos conhecidos
            marcas_conhecidas = {
                'corona': ['corona', 'coronita'],
                'heineken': ['heineken'],
                'skol': ['skol'],
                'brahma': ['brahma'],
                'antarctica': ['antarctica'],
                'stella': ['stella', 'artois'],
                'budweiser': ['budweiser', 'bud'],
                'devassa': ['devassa'],
                'original': ['original'],
                'itaipava': ['itaipava'],
                'eisenbahn': ['eisenbahn']
            }
            
            # Analisar textos encontrados
            self.stdout.write(f'\n   📊 ANÁLISE DOS TEXTOS ENCONTRADOS:')
            self.stdout.write(f'   Total de textos: {len(textos_encontrados)}')
            
            for i, texto_data in enumerate(textos_encontrados, 1):
                texto = texto_data['texto'].lower()
                confianca = texto_data['confianca']
                
                self.stdout.write(f'   [{i}] "{texto_data["texto"]}" (conf: {confianca:.2f})')
                
                # Verificar se é uma marca conhecida
                for marca, variantes in marcas_conhecidas.items():
                    for variante in variantes:
                        if variante in texto:
                            produtos_identificados.append({
                                'marca': marca.upper(),
                                'texto_original': texto_data['texto'],
                                'confianca_ocr': confianca,
                                'variante_encontrada': variante
                            })
                            self.stdout.write(f'       🎯 PRODUTO IDENTIFICADO: {marca.upper()}')
                            break
            
            # Salvar resultados
            if textos_encontrados:
                ocr_data = {
                    'textos_encontrados': textos_encontrados,
                    'produtos_identificados': produtos_identificados,
                    'total_textos': len(textos_encontrados),
                    'total_produtos': len(produtos_identificados)
                }
                
                ocr_json_path = output_dir / '04_resultados_ocr.json'
                with open(ocr_json_path, 'w', encoding='utf-8') as f:
                    json.dump(ocr_data, f, indent=2, ensure_ascii=False)
                
                self.stdout.write(f'\n   🎯 PRODUTOS IDENTIFICADOS VIA OCR:')
                if produtos_identificados:
                    produtos_unicos = {}
                    for produto in produtos_identificados:
                        marca = produto['marca']
                        produtos_unicos[marca] = produtos_unicos.get(marca, 0) + 1
                    
                    for marca, quantidade in produtos_unicos.items():
                        self.stdout.write(f'   - {marca}: {quantidade}x')
                else:
                    self.stdout.write(f'   - Nenhum produto conhecido identificado')
                
                self.stdout.write(f'   💾 Dados OCR salvos: {ocr_json_path.name}')
            else:
                self.stdout.write(f'   ⚠️  Nenhum texto detectado pelo OCR')
            
        except Exception as e:
            self.stdout.write(f'   ✗ Erro no OCR: {str(e)}')

    def preparar_imagem_ocr(self, img, output_dir):
        """Preparar imagem especificamente para OCR"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aumentar contraste para texto
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Aplicar sharpening para texto
        kernel_sharp = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharp)
        
        # Salvar imagem preparada para OCR
        ocr_prep_path = output_dir / '04a_preparada_ocr.jpg'
        cv2.imwrite(str(ocr_prep_path), sharpened)
        
        return sharpened