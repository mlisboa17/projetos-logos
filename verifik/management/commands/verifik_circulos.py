from django.core.management.base import BaseCommand
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image, ImageDraw
import cv2
import os
import math


class Command(BaseCommand):
    help = 'Sistema VerifiK - Detecção com círculos e recortes'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str,
                          help='Caminho para imagem a processar')
        parser.add_argument('--banco', action='store_true',
                          help='Usar imagem do banco de dados')
        parser.add_argument('--modelo', type=str, default='ProductScan_v1',
                          help='Modelo a usar (padrão: ProductScan_v1)')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima (padrão: 0.25)')
        parser.add_argument('--abrir-imagem', action='store_true',
                          help='Abrir imagem no visualizador padrão')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        usar_banco = options['banco']
        modelo_name = options['modelo']
        confianca = options['confianca']
        abrir_imagem = options['abrir_imagem']

        self.stdout.write('=' * 80)
        self.stdout.write(f'⭕ SISTEMA VERIFIK - DETECCAO COM CIRCULOS')
        self.stdout.write('=' * 80)
        
        # Se não especificou imagem nem banco, usar banco por padrão
        if not imagem_path and not usar_banco:
            usar_banco = True
            
        if usar_banco:
            self.stdout.write(f'\n📊 Configuração: MODO BANCO DE DADOS')
            self.stdout.write(f'   Modelo: {modelo_name}')
            self.stdout.write(f'   Confiança: {confianca}')
            self.stdout.write(f'   Visualização: Círculos + Recortes')
        else:
            self.stdout.write(f'\n📊 Configuração:')
            self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
            self.stdout.write(f'   Modelo: {modelo_name}')
            self.stdout.write(f'   Confiança: {confianca}')
            self.stdout.write(f'   Visualização: Círculos + Recortes')

            # Verificar se imagem existe
            if not Path(imagem_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
                return

        try:
            from ultralytics import YOLO
            
            # Carregar modelo
            self.stdout.write(f'\n🚀 Carregando modelo {modelo_name}...')
            
            if modelo_name == 'ProductScan_v1':
                model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
                if not Path(model_path).exists():
                    self.stdout.write(self.style.ERROR(f'✗ Modelo não encontrado: {model_path}'))
                    return
                model = YOLO(model_path)
                self.stdout.write(self.style.SUCCESS(f'✓ ProductScan_v1 carregado'))
            else:
                model = YOLO(modelo_name)
                self.stdout.write(self.style.SUCCESS(f'✓ {modelo_name} carregado'))

            # Processar imagem
            if usar_banco:
                self.processar_banco_com_circulos(model, confianca, abrir_imagem)
            else:
                self.processar_com_circulos(model, imagem_path, confianca, abrir_imagem)

        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            self.stdout.write('   Execute: pip install ultralytics opencv-python pillow')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def processar_com_circulos(self, model, imagem_path, confianca, abrir_imagem):
        """Processa imagem inteira com círculos e recortes"""
        
        # Criar pasta de resultados
        output_dir = Path('verifik_circulos')
        output_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')
        
        # ETAPA 1: CARREGAMENTO
        self.stdout.write(f'\n📥 ETAPA 1: CARREGAMENTO DA IMAGEM')
        img_original = cv2.imread(imagem_path)
        if img_original is None:
            self.stdout.write(self.style.ERROR('✗ Erro ao carregar imagem'))
            return
            
        altura, largura = img_original.shape[:2]
        self.stdout.write(f'   ✓ Imagem carregada: {largura}x{altura}')
        
        # Salvar original
        img_original_path = output_dir / '1_original.jpg'
        cv2.imwrite(str(img_original_path), img_original)
        self.stdout.write(f'   💾 Original salva: 1_original.jpg')

        # ETAPA 2: DETECÇÃO NA IMAGEM COMPLETA
        self.stdout.write(f'\n🔍 ETAPA 2: DETECÇÃO NA IMAGEM COMPLETA')
        
        # Executar detecção
        resultados = model.predict(imagem_path, conf=confianca, verbose=False)
        
        if not resultados or len(resultados) == 0:
            self.stdout.write(f'   ❌ Nenhum resultado da detecção')
            return
        
        resultado = resultados[0]
        boxes = resultado.boxes
        
        if boxes is None or len(boxes) == 0:
            self.stdout.write(f'   ❌ Nenhum objeto detectado')
            return
        
        self.stdout.write(f'   ✅ {len(boxes)} objeto(s) detectado(s)')
        
        # ETAPA 3: APLICAR NMS CUSTOMIZADO (EVITAR OVERLAP)
        self.stdout.write(f'\n🚫 ETAPA 3: ELIMINAÇÃO DE OVERLAPS')
        
        # Converter boxes para lista
        deteccoes = []
        for box in boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            nome_classe = resultado.names.get(cls, f'Classe {cls}')
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            
            deteccoes.append({
                'classe': nome_classe,
                'confianca': conf,
                'x1': int(x1), 'y1': int(y1),
                'x2': int(x2), 'y2': int(y2),
                'centro_x': int((x1 + x2) / 2),
                'centro_y': int((y1 + y2) / 2),
                'largura': int(x2 - x1),
                'altura': int(y2 - y1)
            })
        
        # Ordenar por confiança (maior primeiro)
        deteccoes_ordenadas = sorted(deteccoes, key=lambda x: x['confianca'], reverse=True)
        
        # Eliminar overlaps
        deteccoes_unicas = []
        for det in deteccoes_ordenadas:
            overlap = False
            
            for det_aceita in deteccoes_unicas:
                # Calcular distância entre centros
                dx = det['centro_x'] - det_aceita['centro_x']
                dy = det['centro_y'] - det_aceita['centro_y']
                distancia = math.sqrt(dx*dx + dy*dy)
                
                # Calcular raio médio
                raio_atual = (det['largura'] + det['altura']) / 4
                raio_aceita = (det_aceita['largura'] + det_aceita['altura']) / 4
                raio_minimo = max(raio_atual, raio_aceita)
                
                # Se muito próximo, é overlap
                if distancia < raio_minimo * 0.8:  # 80% do raio = overlap
                    overlap = True
                    break
            
            if not overlap:
                deteccoes_unicas.append(det)
                self.stdout.write(f'   ✅ {det["classe"]}: {det["confianca"]*100:.1f}% - ACEITO')
            else:
                self.stdout.write(f'   ❌ {det["classe"]}: {det["confianca"]*100:.1f}% - OVERLAP')
        
        self.stdout.write(f'   🎯 {len(deteccoes_unicas)} objetos únicos após NMS')
        
        # ETAPA 4: DESENHAR CÍRCULOS E CRIAR VISUALIZAÇÕES
        self.stdout.write(f'\n⭕ ETAPA 4: DESENHO DE CÍRCULOS E LABELS')
        
        img_com_circulos = img_original.copy()
        
        # Cores vibrantes para cada produto
        cores = [
            (0, 255, 0),      # Verde brilhante
            (255, 0, 0),      # Azul brilhante  
            (0, 0, 255),      # Vermelho brilhante
            (255, 255, 0),    # Ciano
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Amarelo
            (128, 255, 0),    # Verde-lima
            (255, 128, 0),    # Laranja
            (0, 128, 255),    # Azul-laranja
            (255, 0, 128),    # Rosa
        ]
        
        produtos_recortados = []
        
        for i, det in enumerate(deteccoes_unicas):
            cor = cores[i % len(cores)]
            
            # Calcular círculo
            centro_x = det['centro_x']
            centro_y = det['centro_y']
            raio = max(det['largura'], det['altura']) // 2 + 10  # Raio baseado no maior lado + margem
            
            # Desenhar círculo
            cv2.circle(img_com_circulos, (centro_x, centro_y), raio, cor, 4)
            
            # Desenhar ponto central
            cv2.circle(img_com_circulos, (centro_x, centro_y), 8, cor, -1)
            
            # Label com número e classe
            label = f'{i+1}. {det["classe"]} {det["confianca"]*100:.0f}%'
            
            # Fundo para o texto
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(img_com_circulos, 
                         (centro_x - text_w//2 - 5, centro_y - raio - text_h - 10),
                         (centro_x + text_w//2 + 5, centro_y - raio + 5), cor, -1)
            
            # Texto
            cv2.putText(img_com_circulos, label, 
                       (centro_x - text_w//2, centro_y - raio - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            self.stdout.write(f'   ⭕ Produto {i+1}: {det["classe"]} - Círculo raio {raio}px')
            
            # ETAPA 5: RECORTAR PRODUTOS
            x1, y1, x2, y2 = det['x1'], det['y1'], det['x2'], det['y2']
            
            # Adicionar margem ao recorte
            margem = 20
            x1_crop = max(0, x1 - margem)
            y1_crop = max(0, y1 - margem)
            x2_crop = min(largura, x2 + margem)
            y2_crop = min(altura, y2 + margem)
            
            # Recortar
            produto_crop = img_original[y1_crop:y2_crop, x1_crop:x2_crop]
            
            if produto_crop.size > 0:
                # Salvar recorte
                nome_arquivo = f'produto_{i+1}_{det["classe"]}_{det["confianca"]*100:.0f}pct.jpg'
                crop_path = output_dir / nome_arquivo
                cv2.imwrite(str(crop_path), produto_crop)
                produtos_recortados.append(str(crop_path))
                
                self.stdout.write(f'      📄 Recortado: {nome_arquivo}')
        
        # Salvar imagem com círculos
        resultado_path = output_dir / '2_deteccao_circulos.jpg'
        cv2.imwrite(str(resultado_path), img_com_circulos)
        self.stdout.write(f'   💾 Resultado salvo: 2_deteccao_circulos.jpg')
        
        # ETAPA 6: CRIAR MOSAICO DOS RECORTES
        if produtos_recortados:
            self.stdout.write(f'\n🖼️  ETAPA 6: CRIANDO MOSAICO DOS PRODUTOS')
            self.criar_mosaico(produtos_recortados, output_dir, abrir_imagem)
        
        # RESUMO FINAL
        self.stdout.write(f'\n📊 RESUMO FINAL:')
        self.stdout.write(f'   Total detectado: {len(deteccoes_unicas)} produtos únicos')
        self.stdout.write(f'   Produtos recortados: {len(produtos_recortados)}')
        self.stdout.write(f'   Visualização: Círculos coloridos + números')
        
        self.stdout.write(f'\n💾 Arquivos gerados:')
        self.stdout.write(f'   - 1_original.jpg (original)')
        self.stdout.write(f'   - 2_deteccao_circulos.jpg (com círculos)')
        self.stdout.write(f'   - produto_*.jpg ({len(produtos_recortados)} recortes)')
        if produtos_recortados:
            self.stdout.write(f'   - 3_mosaico_produtos.jpg (galeria)')
        
        self.stdout.write(f'\n📁 Pasta: {output_dir.absolute()}')
        
        # ABRIR RESULTADOS FINAIS
        if abrir_imagem:
            self.stdout.write(f'\n👁️  ABRINDO RESULTADOS:')
            # Abrir resultado principal com círculos
            os.startfile(str(resultado_path))
            self.stdout.write(f'   🔵 Detecções com círculos')
            
            # Abrir mosaico se existir
            mosaico_path = output_dir / '3_mosaico_produtos.jpg'
            if mosaico_path.exists():
                os.startfile(str(mosaico_path))
                self.stdout.write(f'   🖼️  Mosaico de produtos')

    def criar_mosaico(self, produtos_recortados, output_dir, abrir_imagem):
        """Cria um mosaico com todos os produtos recortados"""
        
        if not produtos_recortados:
            return
        
        # Carregar todas as imagens recortadas
        imagens = []
        for path in produtos_recortados:
            img = cv2.imread(path)
            if img is not None:
                # Redimensionar para tamanho padrão
                img_resized = cv2.resize(img, (200, 200))
                imagens.append(img_resized)
        
        if not imagens:
            return
        
        # Calcular layout do mosaico
        num_imagens = len(imagens)
        colunas = min(4, num_imagens)  # Máximo 4 colunas
        linhas = (num_imagens + colunas - 1) // colunas
        
        # Criar canvas do mosaico
        largura_mosaico = colunas * 200 + (colunas - 1) * 10  # 10px de espaço
        altura_mosaico = linhas * 200 + (linhas - 1) * 10
        
        mosaico = np.ones((altura_mosaico, largura_mosaico, 3), dtype=np.uint8) * 240  # Fundo cinza claro
        
        # Colocar imagens no mosaico
        for i, img in enumerate(imagens):
            linha = i // colunas
            coluna = i % colunas
            
            y = linha * 210  # 200 + 10 espaço
            x = coluna * 210
            
            mosaico[y:y+200, x:x+200] = img
            
            # Número da imagem
            cv2.putText(mosaico, str(i+1), (x+10, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Salvar mosaico
        mosaico_path = output_dir / '3_mosaico_produtos.jpg'
        cv2.imwrite(str(mosaico_path), mosaico)
        
        self.stdout.write(f'   🎨 Mosaico criado: {num_imagens} produtos em {linhas}x{colunas}')
        self.stdout.write(f'   💾 Salvo: 3_mosaico_produtos.jpg')
    
    def processar_banco_com_circulos(self, model, confianca, abrir_imagem):
        """Processa uma imagem do banco que sabemos que funciona"""
        
        from verifik.models_anotacao import ImagemUnificada
        import tempfile
        
        # Buscar uma imagem que sabemos que tem detecções
        imagem = ImagemUnificada.objects.filter(
            ativa=True,
            tipo_imagem='original',
            produto__descricao_produto__icontains='CERVEJA'
        ).first()
        
        if not imagem or not imagem.arquivo:
            self.stdout.write(self.style.ERROR('✗ Nenhuma imagem encontrada no banco'))
            return
            
        self.stdout.write(f'\n🗄️  Imagem selecionada: {imagem.produto.descricao_produto[:50]}')
        
        try:
            # Salvar temporariamente
            imagem.arquivo.open('rb')
            conteudo = imagem.arquivo.read()
            imagem.arquivo.close()
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(conteudo)
                tmp_path = tmp.name
            
            # Processar com método normal
            self.processar_com_circulos(model, tmp_path, confianca, abrir_imagem)
            
            # Limpar
            Path(tmp_path).unlink()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao processar imagem do banco: {str(e)}'))