from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import tempfile


class Command(BaseCommand):
    help = 'Sistema de pré-processamento avançado para melhoria de detecção'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--ocr', action='store_true',
                          help='Ativar reconhecimento de texto (OCR)')
        parser.add_argument('--grid-adaptativo', action='store_true',
                          help='Usar grid adaptativo baseado na densidade')
        parser.add_argument('--melhorar-qualidade', action='store_true',
                          help='Aplicar melhorias de qualidade de imagem')
        parser.add_argument('--detectar-produtos', action='store_true',
                          help='Executar detecção após pré-processamento')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima para detecção')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        usar_ocr = options['ocr']
        grid_adaptativo = options['grid_adaptativo']
        melhorar_qualidade = options['melhorar_qualidade']
        detectar_produtos = options['detectar_produtos']
        confianca = options['confianca']

        self.stdout.write('=' * 80)
        self.stdout.write('🔧 SISTEMA DE PRÉ-PROCESSAMENTO AVANÇADO')
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   OCR: {"✓" if usar_ocr else "✗"}')
        self.stdout.write(f'   Grid Adaptativo: {"✓" if grid_adaptativo else "✗"}')
        self.stdout.write(f'   Melhoria Qualidade: {"✓" if melhorar_qualidade else "✗"}')
        self.stdout.write(f'   Detecção: {"✓" if detectar_produtos else "✗"}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            output_dir = Path('preprocessamento_avancado')
            output_dir.mkdir(exist_ok=True)
            
            # Carregar imagem
            self.stdout.write(f'\n📥 CARREGANDO IMAGEM')
            img_original = cv2.imread(imagem_path)
            if img_original is None:
                self.stdout.write(self.style.ERROR('✗ Erro ao carregar imagem'))
                return
                
            altura, largura = img_original.shape[:2]
            self.stdout.write(f'   ✓ Dimensões: {largura}x{altura}')
            
            # Salvar original
            original_path = output_dir / '01_original.jpg'
            cv2.imwrite(str(original_path), img_original)
            
            img_processada = img_original.copy()
            
            # ETAPA 1: MELHORIA DE QUALIDADE
            if melhorar_qualidade:
                self.stdout.write(f'\n🎨 ETAPA 1: MELHORIA DE QUALIDADE')
                img_processada = self.melhorar_qualidade_imagem(img_processada, output_dir)
            
            # ETAPA 2: OCR - RECONHECIMENTO DE TEXTO
            textos_encontrados = []
            if usar_ocr:
                self.stdout.write(f'\n📝 ETAPA 2: RECONHECIMENTO DE TEXTO (OCR)')
                textos_encontrados = self.processar_ocr(img_processada, output_dir)
            
            # ETAPA 3: ANÁLISE DE DENSIDADE PARA GRID ADAPTATIVO
            grid_info = None
            if grid_adaptativo:
                self.stdout.write(f'\n🔲 ETAPA 3: GRID ADAPTATIVO')
                grid_info = self.calcular_grid_adaptativo(img_processada, output_dir)
            
            # ETAPA 4: DETECÇÃO DE PRODUTOS
            if detectar_produtos:
                self.stdout.write(f'\n🎯 ETAPA 4: DETECÇÃO DE PRODUTOS')
                self.executar_deteccao_otimizada(img_processada, grid_info, confianca, output_dir)
            
            # ETAPA 5: RELATÓRIO FINAL
            self.stdout.write(f'\n📊 RELATÓRIO FINAL')
            self.gerar_relatorio_completo(textos_encontrados, grid_info, output_dir)
            
            self.stdout.write(f'\n✅ PROCESSAMENTO CONCLUÍDO!')
            self.stdout.write(f'📁 Resultados em: {output_dir.absolute()}')
            
            # Abrir pasta de resultados
            os.startfile(str(output_dir))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def melhorar_qualidade_imagem(self, img, output_dir):
        """Aplicar várias técnicas de melhoria de qualidade"""
        
        # 1. Redução de ruído
        self.stdout.write(f'   🔧 Aplicando redução de ruído...')
        img_denoised = cv2.bilateralFilter(img, 9, 75, 75)
        
        # Salvar resultado
        denoised_path = output_dir / '02_ruido_reduzido.jpg'
        cv2.imwrite(str(denoised_path), img_denoised)
        
        # 2. Melhoria de contraste e brilho
        self.stdout.write(f'   💡 Ajustando contraste e brilho...')
        img_pil = Image.fromarray(cv2.cvtColor(img_denoised, cv2.COLOR_BGR2RGB))
        
        # Enhancer de contraste
        enhancer_contrast = ImageEnhance.Contrast(img_pil)
        img_contraste = enhancer_contrast.enhance(1.3)  # 30% mais contraste
        
        # Enhancer de brilho
        enhancer_brightness = ImageEnhance.Brightness(img_contraste)
        img_brilho = enhancer_brightness.enhance(1.1)  # 10% mais brilho
        
        # Enhancer de nitidez
        enhancer_sharpness = ImageEnhance.Sharpness(img_brilho)
        img_nitida = enhancer_sharpness.enhance(1.5)  # 50% mais nitidez
        
        # Converter de volta para OpenCV
        img_melhorada = cv2.cvtColor(np.array(img_nitida), cv2.COLOR_RGB2BGR)
        
        # Salvar resultado
        melhorada_path = output_dir / '03_qualidade_melhorada.jpg'
        cv2.imwrite(str(melhorada_path), img_melhorada)
        
        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        self.stdout.write(f'   📊 Aplicando equalização adaptativa...')
        lab = cv2.cvtColor(img_melhorada, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        lab[:,:,0] = clahe.apply(lab[:,:,0])
        img_clahe = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Salvar resultado final
        final_path = output_dir / '04_processamento_final.jpg'
        cv2.imwrite(str(final_path), img_clahe)
        
        self.stdout.write(f'   ✅ Qualidade melhorada - 4 etapas aplicadas')
        
        return img_clahe

    def processar_ocr(self, img, output_dir):
        """Executar OCR para reconhecimento de texto nos rótulos"""
        
        textos_encontrados = []
        
        # Converter para escala de cinza para OCR
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplicar threshold para melhorar OCR
        _, img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Salvar imagem preparada para OCR
        ocr_prep_path = output_dir / '05_preparada_ocr.jpg'
        cv2.imwrite(str(ocr_prep_path), img_thresh)
        
        try:
            # Configurar Tesseract
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%.'
            
            # Executar OCR
            self.stdout.write(f'   🔍 Executando OCR...')
            texto_detectado = pytesseract.image_to_string(img_thresh, config=config, lang='por+eng')
            
            # Processar texto encontrado
            linhas = [linha.strip() for linha in texto_detectado.split('\n') if linha.strip()]
            
            # Filtrar textos relevantes (marcas conhecidas, números, etc.)
            palavras_relevantes = []
            marcas_conhecidas = ['corona', 'heineken', 'skol', 'brahma', 'antarctica', 'stella', 'budweiser']
            
            for linha in linhas:
                linha_lower = linha.lower()
                # Verificar se contém marca conhecida
                for marca in marcas_conhecidas:
                    if marca in linha_lower:
                        palavras_relevantes.append(f"MARCA: {linha}")
                        break
                
                # Verificar se contém porcentagem (teor alcoólico)
                if '%' in linha or 'ml' in linha.lower():
                    palavras_relevantes.append(f"INFO: {linha}")
            
            textos_encontrados = palavras_relevantes
            
            if textos_encontrados:
                self.stdout.write(f'   ✅ Textos encontrados: {len(textos_encontrados)}')
                for texto in textos_encontrados:
                    self.stdout.write(f'      • {texto}')
            else:
                self.stdout.write(f'   ⚠️ Nenhum texto relevante detectado')
                
            # Salvar OCR com bounding boxes
            dados_ocr = pytesseract.image_to_data(img_thresh, output_type=pytesseract.Output.DICT, config=config)
            img_ocr = img.copy()
            
            for i in range(len(dados_ocr['text'])):
                if int(dados_ocr['conf'][i]) > 30:  # Confiança > 30%
                    texto = dados_ocr['text'][i].strip()
                    if len(texto) > 2:  # Palavras com mais de 2 caracteres
                        x, y, w, h = dados_ocr['left'][i], dados_ocr['top'][i], dados_ocr['width'][i], dados_ocr['height'][i]
                        cv2.rectangle(img_ocr, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(img_ocr, texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Salvar resultado com OCR
            ocr_result_path = output_dir / '06_resultado_ocr.jpg'
            cv2.imwrite(str(ocr_result_path), img_ocr)
            
        except Exception as e:
            self.stdout.write(f'   ❌ Erro no OCR: {str(e)}')
            self.stdout.write(f'      Instale: pip install pytesseract')
            self.stdout.write(f'      E baixe o Tesseract: https://github.com/UB-Mannheim/tesseract/wiki')
        
        return textos_encontrados

    def calcular_grid_adaptativo(self, img, output_dir):
        """Calcular grid adaptativo baseado na densidade de objetos"""
        
        # Converter para escala de cinza
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar bordas
        edges = cv2.Canny(img_gray, 50, 150)
        
        # Salvar bordas detectadas
        edges_path = output_dir / '07_bordas_detectadas.jpg'
        cv2.imwrite(str(edges_path), edges)
        
        altura, largura = img.shape[:2]
        
        # Analisar densidade por regiões
        self.stdout.write(f'   🔍 Analisando densidade de objetos...')
        
        # Dividir em grid inicial 8x8 para análise
        grid_analise = 8
        secao_w = largura // grid_analise
        secao_h = altura // grid_analise
        
        densidade_mapa = np.zeros((grid_analise, grid_analise))
        
        for i in range(grid_analise):
            for j in range(grid_analise):
                x1 = j * secao_w
                y1 = i * secao_h
                x2 = min(x1 + secao_w, largura)
                y2 = min(y1 + secao_h, altura)
                
                # Contar pixels de borda na seção
                secao_edges = edges[y1:y2, x1:x2]
                densidade = np.sum(secao_edges > 0) / (secao_edges.shape[0] * secao_edges.shape[1])
                densidade_mapa[i, j] = densidade
        
        # Determinar grid otimizado baseado na densidade
        densidade_media = np.mean(densidade_mapa)
        densidade_max = np.max(densidade_mapa)
        
        self.stdout.write(f'   📊 Densidade média: {densidade_media:.3f}')
        self.stdout.write(f'   📊 Densidade máxima: {densidade_max:.3f}')
        
        # Decidir tamanho do grid baseado na densidade
        if densidade_max > 0.15:  # Muitos objetos
            grid_size = 6  # Grid 6x6
            self.stdout.write(f'   🔲 Grid recomendado: 6x6 (alta densidade)')
        elif densidade_max > 0.08:  # Densidade média
            grid_size = 4  # Grid 4x4
            self.stdout.write(f'   🔲 Grid recomendado: 4x4 (densidade média)')
        else:  # Baixa densidade
            grid_size = 3  # Grid 3x3
            self.stdout.write(f'   🔲 Grid recomendado: 3x3 (baixa densidade)')
        
        # Criar visualização do mapa de densidade
        img_densidade = img.copy()
        
        for i in range(grid_analise):
            for j in range(grid_analise):
                x1 = j * secao_w
                y1 = i * secao_h
                x2 = min(x1 + secao_w, largura)
                y2 = min(y1 + secao_h, altura)
                
                densidade = densidade_mapa[i, j]
                cor_intensidade = int(densidade * 255)
                
                # Desenhar retângulo com intensidade baseada na densidade
                overlay = img_densidade.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, cor_intensidade, 255-cor_intensidade), -1)
                cv2.addWeighted(img_densidade, 0.7, overlay, 0.3, 0, img_densidade)
                
                # Adicionar texto com densidade
                cv2.putText(img_densidade, f'{densidade:.3f}', 
                          (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Salvar mapa de densidade
        densidade_path = output_dir / '08_mapa_densidade.jpg'
        cv2.imwrite(str(densidade_path), img_densidade)
        
        grid_info = {
            'size': grid_size,
            'densidade_media': densidade_media,
            'densidade_maxima': densidade_max,
            'mapa': densidade_mapa
        }
        
        return grid_info

    def executar_deteccao_otimizada(self, img, grid_info, confianca, output_dir):
        """Executar detecção usando grid otimizado"""
        
        try:
            from ultralytics import YOLO
            
            # Carregar ProductScan_v1
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ ProductScan_v1 não encontrado'))
                return
                
            model = YOLO(model_path)
            self.stdout.write(f'   ✅ ProductScan_v1 carregado')
            
            # Usar grid adaptativo se disponível
            if grid_info:
                grid_size = grid_info['size']
                self.stdout.write(f'   🔲 Usando grid adaptativo {grid_size}x{grid_size}')
            else:
                grid_size = 4  # Padrão
                self.stdout.write(f'   🔲 Usando grid padrão 4x4')
            
            # Executar detecção em grid
            altura, largura = img.shape[:2]
            secao_w = largura // grid_size
            secao_h = altura // grid_size
            
            img_resultado = img.copy()
            total_deteccoes = 0
            objetos_detectados = []
            
            cores = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), 
                    (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0)]
            
            for i in range(grid_size):
                for j in range(grid_size):
                    secao_num = i * grid_size + j + 1
                    
                    x1 = j * secao_w
                    y1 = i * secao_h
                    x2 = min(x1 + secao_w, largura)
                    y2 = min(y1 + secao_h, altura)
                    
                    # Extrair seção
                    secao_img = img[y1:y2, x1:x2]
                    
                    if secao_img.size == 0:
                        continue
                    
                    # Salvar seção temporariamente
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        cv2.imwrite(tmp.name, secao_img)
                        tmp_path = tmp.name
                    
                    try:
                        # Detectar na seção
                        resultados = model.predict(tmp_path, conf=confianca, verbose=False)
                        
                        if resultados and len(resultados) > 0:
                            resultado = resultados[0]
                            boxes = resultado.boxes
                            
                            if boxes is not None and len(boxes) > 0:
                                for box in boxes:
                                    cls = int(box.cls)
                                    conf = float(box.conf)
                                    nome_classe = resultado.names.get(cls, f'Classe {cls}')
                                    
                                    # Coordenadas absolutas
                                    x1_rel, y1_rel, x2_rel, y2_rel = box.xyxy[0].cpu().numpy()
                                    x1_abs = int(x1 + x1_rel)
                                    y1_abs = int(y1 + y1_rel)
                                    x2_abs = int(x1 + x2_rel)
                                    y2_abs = int(y1 + y2_rel)
                                    
                                    # Verificar overlap
                                    overlap = False
                                    for obj in objetos_detectados:
                                        if self.calcular_overlap(
                                            (x1_abs, y1_abs, x2_abs, y2_abs), 
                                            (obj['x1'], obj['y1'], obj['x2'], obj['y2'])
                                        ) > 0.3:
                                            overlap = True
                                            break
                                    
                                    if not overlap:
                                        total_deteccoes += 1
                                        
                                        objetos_detectados.append({
                                            'x1': x1_abs, 'y1': y1_abs, 'x2': x2_abs, 'y2': y2_abs,
                                            'classe': nome_classe, 'confianca': conf, 'secao': secao_num
                                        })
                                        
                                        # Desenhar detecção
                                        cor = cores[total_deteccoes % len(cores)]
                                        cv2.rectangle(img_resultado, (x1_abs, y1_abs), (x2_abs, y2_abs), cor, 3)
                                        
                                        label = f'{nome_classe} {conf:.2f}'
                                        cv2.putText(img_resultado, label, (x1_abs, y1_abs-10),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
                    
                    finally:
                        Path(tmp_path).unlink()
            
            # Salvar resultado da detecção
            deteccao_path = output_dir / '09_deteccao_otimizada.jpg'
            cv2.imwrite(str(deteccao_path), img_resultado)
            
            self.stdout.write(f'   🎯 Total detectado: {total_deteccoes} objetos')
            
            for i, obj in enumerate(objetos_detectados, 1):
                self.stdout.write(f'      [{i}] {obj["classe"]}: {obj["confianca"]*100:.1f}%')
            
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro na detecção: {str(e)}'))

    def calcular_overlap(self, box1, box2):
        """Calcular overlap entre duas caixas"""
        x1_inter = max(box1[0], box2[0])
        y1_inter = max(box1[1], box2[1])
        x2_inter = min(box1[2], box2[2])
        y2_inter = min(box1[3], box2[3])
        
        if x1_inter < x2_inter and y1_inter < y2_inter:
            area_inter = (x2_inter - x1_inter) * (y2_inter - y1_inter)
            area_box1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
            return area_inter / area_box1 if area_box1 > 0 else 0
        return 0

    def gerar_relatorio_completo(self, textos_encontrados, grid_info, output_dir):
        """Gerar relatório completo do processamento"""
        
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("📋 RELATÓRIO DE PRÉ-PROCESSAMENTO AVANÇADO")
        relatorio.append("=" * 80)
        relatorio.append("")
        
        # Seção OCR
        relatorio.append("📝 RECONHECIMENTO DE TEXTO (OCR):")
        if textos_encontrados:
            for texto in textos_encontrados:
                relatorio.append(f"   • {texto}")
        else:
            relatorio.append("   • Nenhum texto relevante detectado")
        relatorio.append("")
        
        # Seção Grid
        relatorio.append("🔲 ANÁLISE DE GRID:")
        if grid_info:
            relatorio.append(f"   • Grid recomendado: {grid_info['size']}x{grid_info['size']}")
            relatorio.append(f"   • Densidade média: {grid_info['densidade_media']:.3f}")
            relatorio.append(f"   • Densidade máxima: {grid_info['densidade_maxima']:.3f}")
        else:
            relatorio.append("   • Análise de grid não executada")
        relatorio.append("")
        
        # Seção Arquivos
        relatorio.append("📁 ARQUIVOS GERADOS:")
        arquivos = list(output_dir.glob("*.jpg"))
        for arquivo in sorted(arquivos):
            relatorio.append(f"   • {arquivo.name}")
        
        # Salvar relatório
        relatorio_path = output_dir / 'RELATORIO_COMPLETO.txt'
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(relatorio))
        
        self.stdout.write(f'   📋 Relatório salvo: RELATORIO_COMPLETO.txt')
        
        # Mostrar resumo
        for linha in relatorio[:20]:  # Mostrar primeiras 20 linhas
            self.stdout.write(f'   {linha}')