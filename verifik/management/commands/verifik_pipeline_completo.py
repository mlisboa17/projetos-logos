from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Sistema VerifiK - Pipeline Completo: Pré-processamento + YOLO + OCR + Clustering'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima YOLO (padrão: 0.25)')
        parser.add_argument('--preprocessing', action='store_true',
                          help='Aplicar pré-processamento com remoção de fundo')
        parser.add_argument('--metodo-bg', type=str, default='grabcut',
                          choices=['grabcut', 'watershed', 'cor', 'contorno'],
                          help='Método de remoção de fundo (padrão: grabcut)')
        parser.add_argument('--grid', action='store_true',
                          help='Usar sistema de grid 4x4')
        parser.add_argument('--ocr', action='store_true',
                          help='Aplicar OCR nos resultados')
        parser.add_argument('--clustering', action='store_true',
                          help='Aplicar clustering DBSCAN')
        parser.add_argument('--eps', type=float, default=50.0,
                          help='Epsilon para DBSCAN (padrão: 50.0)')
        parser.add_argument('--save-steps', action='store_true',
                          help='Salvar todos os passos intermediários')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        confianca = options['confianca']
        use_preprocessing = options['preprocessing']
        metodo_bg = options['metodo_bg']
        use_grid = options['grid']
        use_ocr = options['ocr']
        use_clustering = options['clustering']
        eps = options['eps']
        save_steps = options['save_steps']

        self.stdout.write('=' * 120)
        self.stdout.write('🚀 SISTEMA VERIFIK - PIPELINE COMPLETO DE DETECÇÃO')
        self.stdout.write('=' * 120)
        
        self.stdout.write(f'\n📊 Configuração do Pipeline:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Confiança YOLO: {confianca}')
        self.stdout.write(f'   ✓ Pré-processamento: {"SIM" if use_preprocessing else "NÃO"}')
        if use_preprocessing:
            self.stdout.write(f'   ✓ Método remoção fundo: {metodo_bg.upper()}')
        self.stdout.write(f'   ✓ Sistema Grid: {"SIM" if use_grid else "NÃO"}')
        self.stdout.write(f'   ✓ OCR: {"SIM" if use_ocr else "NÃO"}')
        self.stdout.write(f'   ✓ Clustering: {"SIM" if use_clustering else "NÃO"}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'verifik_pipeline_completo_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')

            # PIPELINE PRINCIPAL
            imagem_processada = self.executar_pipeline(
                imagem_path, output_dir, confianca, 
                use_preprocessing, metodo_bg, use_grid, 
                use_ocr, use_clustering, eps, save_steps
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro no pipeline: {str(e)}'))
            import traceback
            traceback.print_exc()

    def executar_pipeline(self, imagem_path, output_dir, confianca, use_preprocessing, 
                         metodo_bg, use_grid, use_ocr, use_clustering, eps, save_steps):
        """Executar pipeline completo de processamento"""
        
        # Carregar imagem original
        img_original = cv2.imread(imagem_path)
        if img_original is None:
            self.stdout.write(self.style.ERROR('✗ Erro ao carregar imagem'))
            return
            
        altura, largura = img_original.shape[:2]
        self.stdout.write(f'✓ Imagem carregada: {largura}x{altura}')
        
        # Salvar original
        original_path = output_dir / '0_imagem_original.jpg'
        cv2.imwrite(str(original_path), img_original)

        # ETAPA 1: PRÉ-PROCESSAMENTO (opcional)
        if use_preprocessing:
            img_processada = self.aplicar_preprocessing(img_original, metodo_bg, output_dir, save_steps)
            imagem_para_deteccao = str(output_dir / '1_preprocessada.jpg')
            cv2.imwrite(imagem_para_deteccao, img_processada)
        else:
            img_processada = img_original
            imagem_para_deteccao = imagem_path

        # ETAPA 2: DETECÇÃO YOLO
        deteccoes = self.executar_deteccao_yolo(imagem_para_deteccao, confianca, use_grid, output_dir, save_steps)
        
        if not deteccoes:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma detecção encontrada - Pipeline finalizado'))
            return

        # ETAPA 3: CLUSTERING (opcional)
        if use_clustering:
            clusters_info = self.aplicar_clustering_dbscan(deteccoes, eps, output_dir, save_steps)
        else:
            clusters_info = None

        # ETAPA 4: OCR (opcional)
        if use_ocr:
            resultados_ocr = self.aplicar_ocr_deteccoes(imagem_para_deteccao, deteccoes, clusters_info, output_dir, save_steps)
        else:
            resultados_ocr = None

        # ETAPA 5: RESULTADO FINAL
        self.gerar_resultado_final_pipeline(imagem_para_deteccao, deteccoes, clusters_info, resultados_ocr, output_dir)

        return img_processada

    def aplicar_preprocessing(self, img, metodo_bg, output_dir, save_steps):
        """ETAPA 1: Aplicar pré-processamento com remoção de fundo"""
        self.stdout.write(f'\n🎨 ETAPA 1: PRÉ-PROCESSAMENTO COM REMOÇÃO DE FUNDO')
        
        # Pré-processamento básico
        img_enhanced = self.preprocessamento_rapido(img)
        self.stdout.write('   ✓ Enhancement básico aplicado')
        
        # Remoção de fundo
        if metodo_bg == 'grabcut':
            img_sem_fundo = self.remover_fundo_grabcut_rapido(img_enhanced)
        elif metodo_bg == 'watershed':
            img_sem_fundo = self.remover_fundo_watershed_rapido(img_enhanced)
        elif metodo_bg == 'cor':
            img_sem_fundo = self.remover_fundo_por_cor_rapido(img_enhanced)
        elif metodo_bg == 'contorno':
            img_sem_fundo = self.remover_fundo_contorno_rapido(img_enhanced)
        else:
            img_sem_fundo = img_enhanced
            
        self.stdout.write(f'   ✓ Fundo removido usando {metodo_bg.upper()}')
        
        # Otimização final
        img_resultado = self.otimizar_para_deteccao(img_sem_fundo)
        self.stdout.write('   ✓ Otimização para detecção aplicada')
        
        if save_steps:
            preprocessed_path = output_dir / '1_preprocessada.jpg'
            cv2.imwrite(str(preprocessed_path), img_resultado)
            self.stdout.write(f'   💾 Salvo: {preprocessed_path.name}')
        
        return img_resultado

    def preprocessamento_rapido(self, img):
        """Pré-processamento básico otimizado para velocidade"""
        # Enhancement rápido
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img_enhanced = cv2.merge([l, a, b])
        img_enhanced = cv2.cvtColor(img_enhanced, cv2.COLOR_LAB2BGR)
        
        # Ajuste de saturação
        hsv = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2HSV)
        hsv[:,:,1] = cv2.multiply(hsv[:,:,1], 1.2)
        img_resultado = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return img_resultado

    def remover_fundo_grabcut_rapido(self, img):
        """GrabCut otimizado"""
        altura, largura = img.shape[:2]
        mask = np.zeros((altura, largura), np.uint8)
        
        # Retângulo central (85% da imagem)
        margem_x = int(largura * 0.075)
        margem_y = int(altura * 0.075)
        rect = (margem_x, margem_y, largura - 2*margem_x, altura - 2*margem_y)
        
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # GrabCut com menos iterações para velocidade
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
        
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        resultado = img * mask2[:, :, np.newaxis]
        
        return resultado

    def remover_fundo_watershed_rapido(self, img):
        """Watershed otimizado"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        kernel = np.ones((2, 2), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        sure_bg = cv2.dilate(opening, kernel, iterations=2)
        
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.6 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        markers = cv2.watershed(img, markers)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[markers > 1] = 255
        
        resultado = cv2.bitwise_and(img, img, mask=mask)
        return resultado

    def remover_fundo_por_cor_rapido(self, img):
        """Segmentação por cor otimizada"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Máscara para fundo claro
        lower_light = np.array([0, 0, 180])
        upper_light = np.array([180, 50, 255])
        mask_light = cv2.inRange(hsv, lower_light, upper_light)
        
        # Inverter para pegar objetos
        mask_objects = cv2.bitwise_not(mask_light)
        
        # Limpeza rápida
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_objects = cv2.morphologyEx(mask_objects, cv2.MORPH_CLOSE, kernel)
        
        resultado = cv2.bitwise_and(img, img, mask=mask_objects)
        return resultado

    def remover_fundo_contorno_rapido(self, img):
        """Contorno otimizado"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        altura, largura = img.shape[:2]
        area_minima = (altura * largura) * 0.005  # 0.5% da imagem
        
        mask = np.zeros(gray.shape, dtype=np.uint8)
        for contour in contours:
            if cv2.contourArea(contour) > area_minima:
                cv2.fillPoly(mask, [contour], 255)
        
        resultado = cv2.bitwise_and(img, img, mask=mask)
        return resultado

    def otimizar_para_deteccao(self, img):
        """Otimizações finais para melhorar detecção YOLO"""
        # Sharpening leve
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        img_sharp = cv2.filter2D(img, -1, kernel)
        
        # Filtro bilateral para suavizar preservando bordas
        img_smooth = cv2.bilateralFilter(img_sharp, 5, 50, 50)
        
        return img_smooth

    def executar_deteccao_yolo(self, imagem_path, confianca, use_grid, output_dir, save_steps):
        """ETAPA 2: Detecção YOLO (com ou sem grid)"""
        self.stdout.write(f'\n🎯 ETAPA 2: DETECÇÃO YOLO {"COM GRID 4x4" if use_grid else "PADRÃO"}')
        
        try:
            from ultralytics import YOLO
            
            # Carregar modelo
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ ProductScan_v1 não encontrado: {model_path}'))
                return []
                
            model = YOLO(model_path)
            self.stdout.write(f'✓ ProductScan_v1 carregado')

            if use_grid:
                deteccoes = self.deteccao_com_grid(model, imagem_path, confianca, output_dir, save_steps)
            else:
                deteccoes = self.deteccao_simples(model, imagem_path, confianca, output_dir, save_steps)
                
            self.stdout.write(f'✓ {len(deteccoes)} objetos detectados')
            return deteccoes
            
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            return []

    def deteccao_simples(self, model, imagem_path, confianca, output_dir, save_steps):
        """Detecção YOLO simples"""
        resultados = model.predict(imagem_path, conf=confianca, verbose=False)
        
        if not resultados or len(resultados) == 0:
            return []
            
        resultado = resultados[0]
        boxes = resultado.boxes
        
        if boxes is None or len(boxes) == 0:
            return []
        
        deteccoes = []
        img = cv2.imread(imagem_path)
        img_resultado = img.copy()
        
        for i, box in enumerate(boxes):
            cls = int(box.cls)
            conf = float(box.conf)
            nome_classe = resultado.names.get(cls, f'Classe {cls}')
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            
            deteccao = {
                'id': i,
                'classe': nome_classe,
                'confianca': conf,
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'centro': [float((x1 + x2) / 2), float((y1 + y2) / 2)],
                'area': float((x2 - x1) * (y2 - y1))
            }
            deteccoes.append(deteccao)
            
            # Desenhar
            cv2.rectangle(img_resultado, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(img_resultado, f'{nome_classe} {conf:.2f}', (int(x1), int(y1)-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        if save_steps:
            deteccao_path = output_dir / '2_deteccoes_yolo.jpg'
            cv2.imwrite(str(deteccao_path), img_resultado)
        
        return deteccoes

    def deteccao_com_grid(self, model, imagem_path, confianca, output_dir, save_steps):
        """Detecção YOLO com grid 4x4 (versão simplificada)"""
        img = cv2.imread(imagem_path)
        altura, largura = img.shape[:2]
        
        # Dividir em grid 4x4
        secao_largura = largura // 4
        secao_altura = altura // 4
        
        deteccoes = []
        deteccoes_globais = []
        
        self.stdout.write('   📐 Processando grid 4x4...')
        
        for linha in range(4):
            for coluna in range(4):
                x1_secao = coluna * secao_largura
                y1_secao = linha * secao_altura
                x2_secao = min(x1_secao + secao_largura, largura)
                y2_secao = min(y1_secao + secao_altura, altura)
                
                secao_img = img[y1_secao:y2_secao, x1_secao:x2_secao]
                
                if secao_img.size > 0:
                    # Salvar seção temporariamente
                    temp_path = output_dir / f'temp_secao_{linha}_{coluna}.jpg'
                    cv2.imwrite(str(temp_path), secao_img)
                    
                    # Executar detecção
                    resultados = model.predict(str(temp_path), conf=confianca, verbose=False)
                    
                    if resultados and len(resultados) > 0:
                        resultado = resultados[0]
                        boxes = resultado.boxes
                        
                        if boxes is not None and len(boxes) > 0:
                            for i, box in enumerate(boxes):
                                cls = int(box.cls)
                                conf = float(box.conf)
                                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                                
                                # Coordenadas relativas à seção
                                x1_rel, y1_rel, x2_rel, y2_rel = box.xyxy[0].cpu().numpy()
                                
                                # Converter para coordenadas globais
                                x1_global = x1_secao + x1_rel
                                y1_global = y1_secao + y1_rel
                                x2_global = x1_secao + x2_rel
                                y2_global = y1_secao + y2_rel
                                
                                deteccao = {
                                    'id': len(deteccoes_globais),
                                    'classe': nome_classe,
                                    'confianca': conf,
                                    'bbox': [float(x1_global), float(y1_global), float(x2_global), float(y2_global)],
                                    'centro': [float((x1_global + x2_global) / 2), float((y1_global + y2_global) / 2)],
                                    'area': float((x2_global - x1_global) * (y2_global - y1_global)),
                                    'secao': f'{linha}_{coluna}'
                                }
                                
                                deteccoes_globais.append(deteccao)
                    
                    # Remover arquivo temporário
                    temp_path.unlink()
        
        # Remover overlaps
        deteccoes_filtradas = self.remover_overlaps_simples(deteccoes_globais)
        
        self.stdout.write(f'   ✓ {len(deteccoes_globais)} detecções → {len(deteccoes_filtradas)} após filtrar overlaps')
        
        # Salvar resultado visual
        if save_steps:
            img_resultado = img.copy()
            for det in deteccoes_filtradas:
                x1, y1, x2, y2 = [int(v) for v in det['bbox']]
                cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_resultado, f'{det["classe"]} {det["confianca"]:.2f}', 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            grid_result_path = output_dir / '2_deteccoes_grid.jpg'
            cv2.imwrite(str(grid_result_path), img_resultado)
        
        return deteccoes_filtradas

    def remover_overlaps_simples(self, deteccoes):
        """Remover overlaps usando IoU simples"""
        if len(deteccoes) <= 1:
            return deteccoes
        
        deteccoes_filtradas = []
        
        for i, det1 in enumerate(deteccoes):
            manter = True
            
            for j, det2 in enumerate(deteccoes):
                if i != j and det1['confianca'] < det2['confianca']:
                    # Calcular IoU
                    x1_1, y1_1, x2_1, y2_1 = det1['bbox']
                    x1_2, y1_2, x2_2, y2_2 = det2['bbox']
                    
                    # Intersecção
                    x1_inter = max(x1_1, x1_2)
                    y1_inter = max(y1_1, y1_2)
                    x2_inter = min(x2_1, x2_2)
                    y2_inter = min(y2_1, y2_2)
                    
                    if x1_inter < x2_inter and y1_inter < y2_inter:
                        area_inter = (x2_inter - x1_inter) * (y2_inter - y1_inter)
                        area_1 = (x2_1 - x1_1) * (y2_1 - y1_1)
                        area_2 = (x2_2 - x1_2) * (y2_2 - y1_2)
                        area_uniao = area_1 + area_2 - area_inter
                        
                        iou = area_inter / area_uniao if area_uniao > 0 else 0
                        
                        if iou > 0.3:  # 30% overlap
                            manter = False
                            break
            
            if manter:
                deteccoes_filtradas.append(det1)
        
        return deteccoes_filtradas

    def aplicar_clustering_dbscan(self, deteccoes, eps, output_dir, save_steps):
        """ETAPA 3: Aplicar clustering DBSCAN"""
        self.stdout.write(f'\n🧮 ETAPA 3: CLUSTERING DBSCAN')
        
        try:
            from sklearn.cluster import DBSCAN
            
            if len(deteccoes) < 2:
                self.stdout.write('   ⚠️  Poucos objetos para clustering')
                return None
            
            # Extrair centros
            centros = np.array([det['centro'] for det in deteccoes])
            
            # Aplicar DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=2)
            clusters = dbscan.fit_predict(centros)
            
            # Analisar resultados
            unique_clusters = set(clusters)
            n_clusters = len(unique_clusters) - (1 if -1 in clusters else 0)
            n_noise = list(clusters).count(-1)
            
            self.stdout.write(f'   ✓ Clusters: {n_clusters}, Ruído: {n_noise}')
            
            # Adicionar cluster_id às detecções
            for i, det in enumerate(deteccoes):
                det['cluster_id'] = int(clusters[i])
            
            clusters_info = {
                'clusters': clusters.tolist(),
                'n_clusters': n_clusters,
                'n_noise': n_noise,
                'eps': eps
            }
            
            if save_steps:
                clusters_json_path = output_dir / '3_clusters_info.json'
                with open(clusters_json_path, 'w', encoding='utf-8') as f:
                    json.dump(clusters_info, f, indent=2, ensure_ascii=False)
            
            return clusters_info
            
        except ImportError:
            self.stdout.write(self.style.ERROR('   ✗ scikit-learn não disponível'))
            return None

    def aplicar_ocr_deteccoes(self, imagem_path, deteccoes, clusters_info, output_dir, save_steps):
        """ETAPA 4: Aplicar OCR nas regiões detectadas"""
        self.stdout.write(f'\n📖 ETAPA 4: OCR NAS DETECÇÕES')
        
        try:
            import easyocr
            reader = easyocr.Reader(['pt', 'en'])
            self.stdout.write('   ✓ EasyOCR carregado')
            
        except ImportError:
            self.stdout.write(self.style.ERROR('   ✗ EasyOCR não disponível'))
            return None
        
        img = cv2.imread(imagem_path)
        resultados_ocr = {}
        
        for i, det in enumerate(deteccoes):
            # Expandir região para capturar rótulos
            x1, y1, x2, y2 = det['bbox']
            margem = 20
            x1_exp = max(0, int(x1) - margem)
            y1_exp = max(0, int(y1) - margem)
            x2_exp = min(img.shape[1], int(x2) + margem)
            y2_exp = min(img.shape[0], int(y2) + margem)
            
            # Extrair região
            regiao = img[y1_exp:y2_exp, x1_exp:x2_exp]
            
            if regiao.size > 0:
                try:
                    # Executar OCR
                    texto_detectado = reader.readtext(regiao)
                    
                    textos = []
                    for (bbox_ocr, text, confidence) in texto_detectado:
                        if confidence > 0.5 and len(text.strip()) > 2:
                            textos.append({
                                'text': text.strip(),
                                'confidence': confidence
                            })
                    
                    if textos:
                        resultados_ocr[i] = {
                            'deteccao': det,
                            'textos': textos,
                            'regiao': [x1_exp, y1_exp, x2_exp, y2_exp]
                        }
                        
                        self.stdout.write(f'   ✓ Det {i}: {len(textos)} textos encontrados')
                        for texto in textos[:2]:  # Mostrar apenas 2 primeiros
                            self.stdout.write(f'     - "{texto["text"]}" ({texto["confidence"]:.2f})')
                
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Erro OCR detecção {i}: {str(e)}')
        
        if save_steps and resultados_ocr:
            ocr_json_path = output_dir / '4_resultados_ocr.json'
            with open(ocr_json_path, 'w', encoding='utf-8') as f:
                json.dump(resultados_ocr, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'   ✓ OCR aplicado em {len(resultados_ocr)} detecções')
        return resultados_ocr

    def gerar_resultado_final_pipeline(self, imagem_path, deteccoes, clusters_info, resultados_ocr, output_dir):
        """ETAPA 5: Gerar resultado final do pipeline completo"""
        self.stdout.write(f'\n🎨 ETAPA 5: RESULTADO FINAL DO PIPELINE')
        
        img = cv2.imread(imagem_path)
        img_final = img.copy()
        
        # Cores para visualização
        cores = [(0,255,0), (255,0,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        
        # Desenhar detecções
        for i, det in enumerate(deteccoes):
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            
            # Cor baseada no cluster (se disponível)
            if clusters_info and 'cluster_id' in det:
                cluster_id = det['cluster_id']
                cor = cores[cluster_id % len(cores)] if cluster_id != -1 else (128, 128, 128)
            else:
                cor = (0, 255, 0)
            
            # Bounding box
            cv2.rectangle(img_final, (x1, y1), (x2, y2), cor, 3)
            
            # Label principal
            label = f'{det["classe"]} {det["confianca"]:.2f}'
            cv2.putText(img_final, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            
            # Texto OCR (se disponível)
            if resultados_ocr and i in resultados_ocr:
                textos = resultados_ocr[i]['textos']
                y_offset = y1 - 35
                for j, texto in enumerate(textos[:2]):  # Máximo 2 textos
                    texto_label = f'📖 {texto["text"][:15]}'
                    cv2.putText(img_final, texto_label, (x1, y_offset), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)
                    y_offset -= 20
        
        # Salvar resultado final
        resultado_path = output_dir / '5_resultado_final_pipeline.jpg'
        cv2.imwrite(str(resultado_path), img_final)
        
        # Abrir resultado
        os.startfile(str(resultado_path))
        
        # Estatísticas finais
        self.stdout.write(f'\n📊 ESTATÍSTICAS FINAIS:')
        self.stdout.write(f'   ✓ Total de detecções: {len(deteccoes)}')
        
        if clusters_info:
            self.stdout.write(f'   ✓ Clusters formados: {clusters_info["n_clusters"]}')
            
        if resultados_ocr:
            total_textos = sum(len(r['textos']) for r in resultados_ocr.values())
            self.stdout.write(f'   ✓ Textos OCR encontrados: {total_textos}')
        
        # Produtos identificados
        produtos = {}
        for det in deteccoes:
            classe = det['classe']
            produtos[classe] = produtos.get(classe, 0) + 1
            
        self.stdout.write(f'\n🏷️  PRODUTOS DETECTADOS:')
        for produto, quantidade in produtos.items():
            self.stdout.write(f'   - {produto}: {quantidade}x')
        
        self.stdout.write(f'\n💾 Resultado final: {resultado_path.name}')
        self.stdout.write(f'📁 Pasta completa: {output_dir.absolute()}')
        self.stdout.write(f'\n🚀 PIPELINE COMPLETO FINALIZADO!')
        self.stdout.write(f'👁️  RESULTADO ABERTO!')