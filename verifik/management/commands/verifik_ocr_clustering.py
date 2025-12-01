from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
import tempfile


class Command(BaseCommand):
    help = 'Sistema VerifiK - OCR + Clustering + DBSCAN para detecção avançada'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima YOLO (padrão: 0.25)')
        parser.add_argument('--eps', type=float, default=50.0,
                          help='Epsilon para DBSCAN (padrão: 50.0)')
        parser.add_argument('--min-samples', type=int, default=2,
                          help='Mínimo de samples para DBSCAN (padrão: 2)')
        parser.add_argument('--ocr-engine', type=str, default='easyocr',
                          choices=['easyocr', 'tesseract', 'paddleocr'],
                          help='Engine OCR (padrão: easyocr)')
        parser.add_argument('--save-steps', action='store_true',
                          help='Salvar passos intermediários')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        confianca = options['confianca']
        eps = options['eps']
        min_samples = options['min_samples']
        ocr_engine = options['ocr_engine']
        save_steps = options['save_steps']

        self.stdout.write('=' * 100)
        self.stdout.write('🔬 SISTEMA VERIFIK - OCR + CLUSTERING + DBSCAN AVANÇADO')
        self.stdout.write('=' * 100)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Confiança YOLO: {confianca}')
        self.stdout.write(f'   DBSCAN eps: {eps}')
        self.stdout.write(f'   DBSCAN min_samples: {min_samples}')
        self.stdout.write(f'   OCR Engine: {ocr_engine.upper()}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'verifik_ocr_clustering_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')

            # ETAPA 1: DETECÇÃO YOLO
            deteccoes = self.executar_deteccao_yolo(imagem_path, confianca, output_dir, save_steps)
            
            if not deteccoes:
                self.stdout.write(self.style.WARNING('⚠️  Nenhuma detecção YOLO encontrada'))
                return
            
            # ETAPA 2: EXTRAÇÃO DE CENTROS E BORDAS
            centros, bordas = self.extrair_centros_bordas(deteccoes, output_dir, save_steps)
            
            # ETAPA 3: CLUSTERING COM DBSCAN
            clusters = self.aplicar_dbscan_clustering(centros, eps, min_samples, output_dir, save_steps)
            
            # ETAPA 4: ASSOCIAÇÃO BOUNDING BOX → CLUSTER
            associacoes = self.associar_bbox_clusters(deteccoes, centros, clusters, output_dir, save_steps)
            
            # ETAPA 5: OCR NAS REGIÕES DOS CLUSTERS
            resultados_ocr = self.executar_ocr_clusters(imagem_path, associacoes, ocr_engine, output_dir, save_steps)
            
            # ETAPA 6: RESULTADO FINAL
            self.gerar_resultado_final(imagem_path, deteccoes, associacoes, resultados_ocr, output_dir)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def executar_deteccao_yolo(self, imagem_path, confianca, output_dir, save_steps):
        """ETAPA 1: Detecção YOLO ProductScan_v1"""
        self.stdout.write(f'\n🎯 ETAPA 1: DETECÇÃO YOLO ProductScan_v1')
        
        try:
            from ultralytics import YOLO
            
            # Carregar modelo
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ ProductScan_v1 não encontrado: {model_path}'))
                return []
                
            model = YOLO(model_path)
            self.stdout.write(f'✓ ProductScan_v1 carregado')

            # Executar detecção
            resultados = model.predict(imagem_path, conf=confianca, verbose=False)
            
            if not resultados or len(resultados) == 0:
                return []
                
            resultado = resultados[0]
            boxes = resultado.boxes
            
            if boxes is None or len(boxes) == 0:
                return []
            
            # Processar detecções
            deteccoes = []
            img_original = cv2.imread(imagem_path)
            img_deteccoes = img_original.copy()
            
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
                    'largura': float(x2 - x1),
                    'altura': float(y2 - y1),
                    'area': float((x2 - x1) * (y2 - y1))
                }
                deteccoes.append(deteccao)
                
                # Desenhar bbox
                cv2.rectangle(img_deteccoes, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(img_deteccoes, f'{nome_classe} {conf:.2f}', (int(x1), int(y1)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            self.stdout.write(f'✓ {len(deteccoes)} objetos detectados')
            
            # Salvar imagem com detecções
            if save_steps:
                deteccoes_path = output_dir / '1_deteccoes_yolo.jpg'
                cv2.imwrite(str(deteccoes_path), img_deteccoes)
                self.stdout.write(f'   💾 Detecções salvas: {deteccoes_path.name}')
            
            # Salvar JSON das detecções
            deteccoes_json_path = output_dir / '1_deteccoes_yolo.json'
            with open(deteccoes_json_path, 'w', encoding='utf-8') as f:
                json.dump(deteccoes, f, indent=2, ensure_ascii=False)
            
            return deteccoes
            
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            return []

    def extrair_centros_bordas(self, deteccoes, output_dir, save_steps):
        """ETAPA 2: Extração de centros e bordas das detecções"""
        self.stdout.write(f'\n📐 ETAPA 2: EXTRAÇÃO DE CENTROS E BORDAS')
        
        centros = []
        bordas = []
        
        for det in deteccoes:
            # Centro da detecção
            centro = det['centro']
            centros.append(centro)
            
            # Bordas (x1, y1, x2, y2)
            x1, y1, x2, y2 = det['bbox']
            borda = {
                'id': det['id'],
                'top_left': [x1, y1],
                'top_right': [x2, y1],
                'bottom_left': [x1, y2],
                'bottom_right': [x2, y2],
                'centro': centro,
                'largura': det['largura'],
                'altura': det['altura']
            }
            bordas.append(borda)
        
        centros = np.array(centros)
        
        self.stdout.write(f'✓ {len(centros)} centros extraídos')
        self.stdout.write(f'✓ {len(bordas)} bordas extraídas')
        
        # Salvar dados
        centros_bordas_data = {
            'centros': centros.tolist(),
            'bordas': bordas
        }
        
        centros_json_path = output_dir / '2_centros_bordas.json'
        with open(centros_json_path, 'w', encoding='utf-8') as f:
            json.dump(centros_bordas_data, f, indent=2, ensure_ascii=False)
        
        return centros, bordas

    def aplicar_dbscan_clustering(self, centros, eps, min_samples, output_dir, save_steps):
        """ETAPA 3: Aplicar clustering DBSCAN nos centros"""
        self.stdout.write(f'\n🧮 ETAPA 3: CLUSTERING DBSCAN')
        
        if len(centros) < min_samples:
            self.stdout.write(f'⚠️  Poucos pontos para clustering ({len(centros)} < {min_samples})')
            # Criar cluster único para todos os pontos
            clusters = [0] * len(centros)
        else:
            # Aplicar DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            clusters = dbscan.fit_predict(centros)
        
        # Analisar clusters
        unique_clusters = set(clusters)
        n_clusters = len(unique_clusters) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        self.stdout.write(f'✓ Clusters encontrados: {n_clusters}')
        self.stdout.write(f'✓ Pontos de ruído: {n_noise}')
        
        # Estatísticas por cluster
        cluster_stats = {}
        for cluster_id in unique_clusters:
            if cluster_id == -1:
                continue
            cluster_points = centros[clusters == cluster_id]
            cluster_stats[int(cluster_id)] = {
                'pontos': len(cluster_points),
                'centro_medio': np.mean(cluster_points, axis=0).tolist(),
                'std': np.std(cluster_points, axis=0).tolist()
            }
            self.stdout.write(f'   Cluster {cluster_id}: {len(cluster_points)} pontos')
        
        # Salvar visualização dos clusters
        if save_steps and len(centros) > 0:
            self.visualizar_clusters(centros, clusters, output_dir)
        
        # Salvar dados dos clusters
        clusters_data = {
            'clusters': clusters.tolist(),
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'eps': eps,
            'min_samples': min_samples,
            'cluster_stats': cluster_stats
        }
        
        clusters_json_path = output_dir / '3_clusters_dbscan.json'
        with open(clusters_json_path, 'w', encoding='utf-8') as f:
            json.dump(clusters_data, f, indent=2, ensure_ascii=False)
        
        return clusters

    def visualizar_clusters(self, centros, clusters, output_dir):
        """Criar visualização dos clusters"""
        plt.figure(figsize=(12, 8))
        
        # Cores para os clusters
        unique_clusters = set(clusters)
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
        
        for cluster_id, color in zip(unique_clusters, colors):
            if cluster_id == -1:
                # Pontos de ruído em preto
                cluster_points = centros[clusters == cluster_id]
                plt.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                           c='black', marker='x', s=100, alpha=0.7, label=f'Ruído')
            else:
                cluster_points = centros[clusters == cluster_id]
                plt.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                           c=[color], s=100, alpha=0.7, label=f'Cluster {cluster_id}')
        
        plt.title('DBSCAN Clustering - Centros das Detecções')
        plt.xlabel('X (pixels)')
        plt.ylabel('Y (pixels)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Inverter eixo Y para corresponder à imagem
        plt.gca().invert_yaxis()
        
        clusters_img_path = output_dir / '3_clusters_visualization.png'
        plt.savefig(clusters_img_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.stdout.write(f'   💾 Visualização salva: {clusters_img_path.name}')

    def associar_bbox_clusters(self, deteccoes, centros, clusters, output_dir, save_steps):
        """ETAPA 4: Associar cada bounding box ao seu cluster"""
        self.stdout.write(f'\n🔗 ETAPA 4: ASSOCIAÇÃO BOUNDING BOX → CLUSTER')
        
        associacoes = []
        
        for i, det in enumerate(deteccoes):
            cluster_id = int(clusters[i])
            
            associacao = {
                'deteccao_id': det['id'],
                'classe': det['classe'],
                'confianca': det['confianca'],
                'bbox': det['bbox'],
                'centro': det['centro'],
                'cluster_id': cluster_id,
                'area': det['area']
            }
            associacoes.append(associacao)
        
        # Agrupar por cluster
        clusters_grupos = {}
        for assoc in associacoes:
            cluster_id = assoc['cluster_id']
            if cluster_id not in clusters_grupos:
                clusters_grupos[cluster_id] = []
            clusters_grupos[cluster_id].append(assoc)
        
        self.stdout.write(f'✓ {len(associacoes)} associações criadas')
        
        for cluster_id, grupo in clusters_grupos.items():
            if cluster_id == -1:
                self.stdout.write(f'   Ruído: {len(grupo)} objetos isolados')
            else:
                self.stdout.write(f'   Cluster {cluster_id}: {len(grupo)} objetos')
                for obj in grupo:
                    self.stdout.write(f'     - {obj["classe"]}: {obj["confianca"]:.2f}')
        
        # Salvar associações
        associacoes_data = {
            'associacoes': associacoes,
            'clusters_grupos': {str(k): v for k, v in clusters_grupos.items()}
        }
        
        associacoes_json_path = output_dir / '4_associacoes_clusters.json'
        with open(associacoes_json_path, 'w', encoding='utf-8') as f:
            json.dump(associacoes_data, f, indent=2, ensure_ascii=False)
        
        return associacoes

    def executar_ocr_clusters(self, imagem_path, associacoes, ocr_engine, output_dir, save_steps):
        """ETAPA 5: Executar OCR nas regiões dos clusters"""
        self.stdout.write(f'\n📖 ETAPA 5: OCR NAS REGIÕES DOS CLUSTERS')
        
        # Carregar imagem
        img = cv2.imread(imagem_path)
        
        # Inicializar OCR
        ocr_reader = self.init_ocr_engine(ocr_engine)
        if ocr_reader is None:
            return {}
        
        resultados_ocr = {}
        
        # Agrupar associações por cluster
        clusters_grupos = {}
        for assoc in associacoes:
            cluster_id = assoc['cluster_id']
            if cluster_id not in clusters_grupos:
                clusters_grupos[cluster_id] = []
            clusters_grupos[cluster_id].append(assoc)
        
        for cluster_id, objetos in clusters_grupos.items():
            if cluster_id == -1:
                continue  # Pular ruído
                
            self.stdout.write(f'\n   🔍 Processando Cluster {cluster_id}:')
            
            # Determinar região do cluster (bounding box que engloba todos os objetos)
            x_mins = [obj['bbox'][0] for obj in objetos]
            y_mins = [obj['bbox'][1] for obj in objetos]
            x_maxs = [obj['bbox'][2] for obj in objetos]
            y_maxs = [obj['bbox'][3] for obj in objetos]
            
            # Expandir região para capturar rótulos próximos
            margem = 20
            x1 = max(0, int(min(x_mins)) - margem)
            y1 = max(0, int(min(y_mins)) - margem)
            x2 = min(img.shape[1], int(max(x_maxs)) + margem)
            y2 = min(img.shape[0], int(max(y_maxs)) + margem)
            
            self.stdout.write(f'     Região: ({x1},{y1}) → ({x2},{y2})')
            
            # Extrair região
            regiao = img[y1:y2, x1:x2]
            
            if regiao.size == 0:
                continue
            
            # Pré-processar região para OCR
            regiao_preprocessada = self.preprocessar_para_ocr(regiao)
            
            # Salvar região se solicitado
            if save_steps:
                regiao_path = output_dir / f'5_cluster_{cluster_id}_regiao.jpg'
                cv2.imwrite(str(regiao_path), regiao_preprocessada)
            
            # Executar OCR
            try:
                texto_detectado = self.executar_ocr_engine(regiao_preprocessada, ocr_reader, ocr_engine)
                
                resultados_ocr[cluster_id] = {
                    'regiao': [x1, y1, x2, y2],
                    'objetos': objetos,
                    'texto': texto_detectado,
                    'produtos_identificados': self.identificar_produtos_texto(texto_detectado)
                }
                
                self.stdout.write(f'     ✓ Texto encontrado: {len(texto_detectado)} elementos')
                for texto_item in texto_detectado:
                    confidence = texto_item.get('confidence', 0)
                    text = texto_item.get('text', '').strip()
                    if text and confidence > 0.5:
                        self.stdout.write(f'       - "{text}" ({confidence:.2f})')
                        
            except Exception as e:
                self.stdout.write(f'     ✗ Erro OCR: {str(e)}')
                resultados_ocr[cluster_id] = {
                    'regiao': [x1, y1, x2, y2],
                    'objetos': objetos,
                    'texto': [],
                    'erro': str(e)
                }
        
        # Salvar resultados OCR
        ocr_json_path = output_dir / '5_resultados_ocr.json'
        with open(ocr_json_path, 'w', encoding='utf-8') as f:
            json.dump(resultados_ocr, f, indent=2, ensure_ascii=False)
        
        return resultados_ocr

    def init_ocr_engine(self, ocr_engine):
        """Inicializar engine OCR escolhida"""
        try:
            if ocr_engine == 'easyocr':
                import easyocr
                reader = easyocr.Reader(['pt', 'en'])
                self.stdout.write(f'✓ EasyOCR inicializado (PT/EN)')
                return reader
            elif ocr_engine == 'tesseract':
                import pytesseract
                # Tesseract precisa estar instalado no sistema
                return 'tesseract'
            elif ocr_engine == 'paddleocr':
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='pt')
                self.stdout.write(f'✓ PaddleOCR inicializado (PT)')
                return ocr
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao importar {ocr_engine}: {str(e)}'))
            self.stdout.write(f'   Execute: pip install {self.get_install_command(ocr_engine)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao inicializar {ocr_engine}: {str(e)}'))
        return None

    def get_install_command(self, ocr_engine):
        """Comando de instalação para cada engine OCR"""
        commands = {
            'easyocr': 'easyocr',
            'tesseract': 'pytesseract',
            'paddleocr': 'paddlepaddle paddleocr'
        }
        return commands.get(ocr_engine, ocr_engine)

    def preprocessar_para_ocr(self, imagem):
        """Pré-processar imagem para melhorar OCR"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro gaussiano para reduzir ruído
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Equalização de histograma adaptativa
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blur)
        
        # Thresholding adaptativo
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Operações morfológicas para limpar
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Converter de volta para BGR para compatibilidade
        result = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
        
        return result

    def executar_ocr_engine(self, imagem, reader, engine):
        """Executar OCR conforme engine escolhida"""
        if engine == 'easyocr':
            resultados = reader.readtext(imagem)
            texto_detectado = []
            for (bbox, text, confidence) in resultados:
                texto_detectado.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': bbox
                })
            return texto_detectado
            
        elif engine == 'tesseract':
            import pytesseract
            # Configuração otimizada para produtos
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            texto = pytesseract.image_to_string(imagem, config=config)
            return [{'text': texto.strip(), 'confidence': 1.0, 'bbox': []}]
            
        elif engine == 'paddleocr':
            result = reader.ocr(imagem, cls=True)
            texto_detectado = []
            if result and result[0]:
                for line in result[0]:
                    texto_detectado.append({
                        'text': line[1][0],
                        'confidence': line[1][1],
                        'bbox': line[0]
                    })
            return texto_detectado
        
        return []

    def identificar_produtos_texto(self, texto_detectado):
        """Identificar produtos baseado no texto detectado"""
        produtos_conhecidos = {
            'corona': ['corona', 'coronita'],
            'heineken': ['heineken'],
            'skol': ['skol'],
            'brahma': ['brahma'],
            'antarctica': ['antarctica'],
            'stella': ['stella', 'artois'],
            'budweiser': ['budweiser', 'bud'],
            'devassa': ['devassa'],
            'original': ['original']
        }
        
        produtos_identificados = []
        
        for item in texto_detectado:
            texto = item.get('text', '').lower().strip()
            confianca = item.get('confidence', 0)
            
            if confianca < 0.5 or len(texto) < 3:
                continue
                
            for produto, palavras in produtos_conhecidos.items():
                for palavra in palavras:
                    if palavra in texto:
                        produtos_identificados.append({
                            'produto': produto,
                            'texto_original': item['text'],
                            'confianca_ocr': confianca,
                            'palavra_encontrada': palavra
                        })
                        break
        
        return produtos_identificados

    def gerar_resultado_final(self, imagem_path, deteccoes, associacoes, resultados_ocr, output_dir):
        """ETAPA 6: Gerar resultado final com visualização"""
        self.stdout.write(f'\n🎨 ETAPA 6: RESULTADO FINAL')
        
        # Carregar imagem original
        img = cv2.imread(imagem_path)
        img_resultado = img.copy()
        
        # Cores para clusters
        cores_clusters = [
            (0, 255, 0),    # Verde
            (255, 0, 0),    # Azul  
            (0, 0, 255),    # Vermelho
            (255, 255, 0),  # Ciano
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Amarelo
            (128, 255, 0),  # Verde-lima
            (255, 128, 0),  # Laranja
        ]
        
        # Desenhar detecções coloridas por cluster
        for assoc in associacoes:
            cluster_id = assoc['cluster_id']
            x1, y1, x2, y2 = [int(v) for v in assoc['bbox']]
            
            if cluster_id == -1:
                cor = (128, 128, 128)  # Cinza para ruído
            else:
                cor = cores_clusters[cluster_id % len(cores_clusters)]
            
            # Bounding box
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 3)
            
            # Label
            label = f'C{cluster_id}-{assoc["classe"]} {assoc["confianca"]:.2f}'
            cv2.putText(img_resultado, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
        
        # Desenhar regiões OCR
        for cluster_id, resultado_ocr in resultados_ocr.items():
            if cluster_id == -1:
                continue
                
            x1, y1, x2, y2 = resultado_ocr['regiao']
            cor = cores_clusters[int(cluster_id) % len(cores_clusters)]
            
            # Região OCR com linha tracejada
            cv2.rectangle(img_resultado, (x1, y1), (x2, y2), cor, 2, cv2.LINE_AA)
            
            # Texto encontrado
            produtos = resultado_ocr.get('produtos_identificados', [])
            if produtos:
                y_offset = y1 - 30
                for produto in produtos[:3]:  # Máximo 3 produtos
                    texto_produto = f"📖 {produto['produto'].upper()}"
                    cv2.putText(img_resultado, texto_produto, (x1, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)
                    y_offset -= 20
        
        # Salvar resultado final
        resultado_path = output_dir / '6_resultado_final_ocr_clustering.jpg'
        cv2.imwrite(str(resultado_path), img_resultado)
        
        # Abrir resultado
        os.startfile(str(resultado_path))
        
        # Resumo final
        n_clusters = len(set(assoc['cluster_id'] for assoc in associacoes if assoc['cluster_id'] != -1))
        n_deteccoes = len(deteccoes)
        n_ocr_resultados = len(resultados_ocr)
        
        self.stdout.write(f'\n📊 RESUMO FINAL:')
        self.stdout.write(f'   ✓ Detecções YOLO: {n_deteccoes}')
        self.stdout.write(f'   ✓ Clusters formados: {n_clusters}')
        self.stdout.write(f'   ✓ Regiões com OCR: {n_ocr_resultados}')
        
        # Produtos identificados via OCR
        produtos_totais = []
        for resultado in resultados_ocr.values():
            produtos_totais.extend(resultado.get('produtos_identificados', []))
        
        if produtos_totais:
            self.stdout.write(f'   ✓ Produtos identificados via OCR: {len(produtos_totais)}')
            produtos_unicos = set(p['produto'] for p in produtos_totais)
            for produto in produtos_unicos:
                count = sum(1 for p in produtos_totais if p['produto'] == produto)
                self.stdout.write(f'     - {produto.upper()}: {count}x')
        
        self.stdout.write(f'\n💾 Arquivo final: {resultado_path.name}')
        self.stdout.write(f'📁 Todos os arquivos em: {output_dir.absolute()}')
        self.stdout.write(f'\n👁️  RESULTADO FINAL ABERTO!')