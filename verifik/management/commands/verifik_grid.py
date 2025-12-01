from django.core.management.base import BaseCommand
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image, ImageDraw
import cv2
import os


class Command(BaseCommand):
    help = 'Sistema VerifiK - Detecção em Grid 4x4 com visualização'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--modelo', type=str, default='ProductScan_v1',
                          help='Modelo a usar (padrão: ProductScan_v1)')
        parser.add_argument('--confianca', type=float, default=0.25,
                          help='Confiança mínima (padrão: 0.25)')
        parser.add_argument('--abrir-imagem', action='store_true',
                          help='Abrir imagem no visualizador padrão')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        modelo_name = options['modelo']
        confianca = options['confianca']
        abrir_imagem = options['abrir_imagem']

        self.stdout.write('=' * 80)
        self.stdout.write(f'🎯 SISTEMA VERIFIK - DETECCAO GRID 4x4')
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Modelo: {modelo_name}')
        self.stdout.write(f'   Confiança: {confianca}')
        self.stdout.write(f'   Grid: 4x4 (16 seções)')

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

            # Processar com sistema de grid
            self.processar_grid_4x4(model, imagem_path, confianca, abrir_imagem)

        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            self.stdout.write('   Execute: pip install ultralytics opencv-python pillow')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def processar_grid_4x4(self, model, imagem_path, confianca, abrir_imagem):
        """Processa imagem dividindo em grid 4x4 e detectando sequencialmente"""
        
        # Criar pasta de resultados
        output_dir = Path('verifik_grid_deteccao')
        output_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')
        
        # Carregar imagem
        self.stdout.write(f'\n📥 ETAPA 1: CARREGAMENTO DA IMAGEM')
        img_original = cv2.imread(imagem_path)
        if img_original is None:
            self.stdout.write(self.style.ERROR('✗ Erro ao carregar imagem'))
            return
            
        altura, largura = img_original.shape[:2]
        self.stdout.write(f'   ✓ Imagem carregada: {largura}x{altura}')
        
        # Salvar imagem original
        img_original_path = output_dir / '0_imagem_original.jpg'
        cv2.imwrite(str(img_original_path), img_original)
        self.stdout.write(f'   💾 Original salva: {img_original_path.name}')
        
        # Abrir imagem se solicitado
        if abrir_imagem:
            os.startfile(str(img_original_path))
            self.stdout.write(f'   👁️  Imagem aberta no visualizador')
        
        # ETAPA 2: DIVISÃO EM GRID 4x4
        self.stdout.write(f'\n🔲 ETAPA 2: DIVISÃO EM GRID 4x4')
        
        # Calcular tamanhos das seções
        secao_largura = largura // 4
        secao_altura = altura // 4
        
        self.stdout.write(f'   📐 Cada seção: {secao_largura}x{secao_altura}')
        
        # Criar imagem com grid visual
        img_com_grid = img_original.copy()
        
        # Desenhar linhas do grid
        # Linhas verticais
        for i in range(1, 4):
            x = i * secao_largura
            cv2.line(img_com_grid, (x, 0), (x, altura), (0, 255, 255), 2)
        
        # Linhas horizontais  
        for i in range(1, 4):
            y = i * secao_altura
            cv2.line(img_com_grid, (0, y), (largura, y), (0, 255, 255), 2)
        
        # Numerar seções
        for linha in range(4):
            for coluna in range(4):
                numero = linha * 4 + coluna + 1
                x_centro = coluna * secao_largura + secao_largura // 2
                y_centro = linha * secao_altura + secao_altura // 2
                
                cv2.putText(img_com_grid, str(numero), (x_centro-10, y_centro+10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        grid_path = output_dir / '1_grid_4x4.jpg'
        cv2.imwrite(str(grid_path), img_com_grid)
        self.stdout.write(f'   💾 Grid salvo: {grid_path.name}')
        
        # ETAPA 3: DETECÇÃO SEQUENCIAL POR SEÇÃO
        self.stdout.write(f'\n🔍 ETAPA 3: DETECÇÃO SEQUENCIAL POR SEÇÃO')
        
        img_resultado = img_original.copy()
        objetos_detectados = []  # Lista de objetos já detectados (para evitar repetição)
        total_deteccoes = 0
        
        cores = [
            (0, 255, 0),    # Verde
            (255, 0, 0),    # Azul
            (0, 0, 255),    # Vermelho
            (255, 255, 0),  # Ciano
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Amarelo
            (128, 255, 0),  # Verde-lima
            (255, 128, 0),  # Laranja
        ]
        
        for linha in range(4):
            for coluna in range(4):
                secao_num = linha * 4 + coluna + 1
                
                # Calcular coordenadas da seção
                x1_secao = coluna * secao_largura
                y1_secao = linha * secao_altura
                x2_secao = min(x1_secao + secao_largura, largura)
                y2_secao = min(y1_secao + secao_altura, altura)
                
                self.stdout.write(f'\n   🔲 SEÇÃO {secao_num} ({linha+1},{coluna+1}):')
                self.stdout.write(f'      Região: ({x1_secao},{y1_secao}) → ({x2_secao},{y2_secao})')
                
                # Extrair seção da imagem
                secao_img = img_original[y1_secao:y2_secao, x1_secao:x2_secao]
                
                if secao_img.size == 0:
                    self.stdout.write(f'      ⚠️  Seção vazia - pulando')
                    continue
                
                # Salvar seção temporariamente
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    cv2.imwrite(tmp.name, secao_img)
                    tmp_path = tmp.name
                
                try:
                    # Executar detecção na seção
                    resultados = model.predict(tmp_path, conf=confianca, verbose=False)
                    
                    deteccoes_secao = 0
                    
                    if resultados and len(resultados) > 0:
                        resultado = resultados[0]
                        boxes = resultado.boxes
                        
                        if boxes is not None and len(boxes) > 0:
                            for box in boxes:
                                cls = int(box.cls)
                                conf = float(box.conf)
                                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                                
                                # Coordenadas na seção (relativas)
                                x1_rel, y1_rel, x2_rel, y2_rel = box.xyxy[0].cpu().numpy()
                                
                                # Converter para coordenadas absolutas na imagem original
                                x1_abs = int(x1_secao + x1_rel)
                                y1_abs = int(y1_secao + y1_rel)
                                x2_abs = int(x1_secao + x2_rel)
                                y2_abs = int(y1_secao + y2_rel)
                                
                                # Verificar se já foi detectado em seção anterior
                                objeto_atual = (x1_abs, y1_abs, x2_abs, y2_abs)
                                
                                # Verificar overlap com objetos já detectados
                                overlap_significativo = False
                                for obj_anterior in objetos_detectados:
                                    xa1, ya1, xa2, ya2, _, _, _ = obj_anterior
                                    
                                    # Calcular intersecção
                                    x_inter1 = max(x1_abs, xa1)
                                    y_inter1 = max(y1_abs, ya1)
                                    x_inter2 = min(x2_abs, xa2)
                                    y_inter2 = min(y2_abs, ya2)
                                    
                                    if x_inter1 < x_inter2 and y_inter1 < y_inter2:
                                        area_intersecao = (x_inter2 - x_inter1) * (y_inter2 - y_inter1)
                                        area_atual = (x2_abs - x1_abs) * (y2_abs - y1_abs)
                                        
                                        if area_atual > 0:
                                            overlap_percent = area_intersecao / area_atual
                                            if overlap_percent > 0.3:  # 30% de overlap
                                                overlap_significativo = True
                                                break
                                
                                if overlap_significativo:
                                    self.stdout.write(f'      ❌ {nome_classe} {conf:.2f} - JÁ DETECTADO')
                                    continue
                                
                                # Novo objeto detectado
                                deteccoes_secao += 1
                                total_deteccoes += 1
                                
                                # Adicionar à lista de detectados
                                objetos_detectados.append((x1_abs, y1_abs, x2_abs, y2_abs, nome_classe, conf, secao_num))
                                
                                # Desenhar bounding box
                                cor = cores[total_deteccoes % len(cores)]
                                cv2.rectangle(img_resultado, (x1_abs, y1_abs), (x2_abs, y2_abs), cor, 3)
                                
                                # Label com seção
                                label = f'S{secao_num}-{nome_classe} {conf:.2f}'
                                cv2.putText(img_resultado, label, (x1_abs, y1_abs-10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
                                
                                self.stdout.write(f'      ✅ {nome_classe}: {conf*100:.1f}% - NOVO!')
                    
                    if deteccoes_secao == 0:
                        self.stdout.write(f'      ⭕ Nenhum objeto detectado')
                    else:
                        self.stdout.write(f'      🎯 {deteccoes_secao} novo(s) objeto(s)')
                
                finally:
                    # Limpar arquivo temporário
                    Path(tmp_path).unlink()
        
        # ETAPA 4: RESULTADOS FINAIS
        self.stdout.write(f'\n🎯 ETAPA 4: RESULTADOS FINAIS')
        
        # Salvar imagem final
        resultado_path = output_dir / '2_resultado_final_grid.jpg'
        cv2.imwrite(str(resultado_path), img_resultado)
        
        # Abrir resultado se solicitado
        if abrir_imagem:
            os.startfile(str(resultado_path))
            self.stdout.write(f'   👁️  Resultado aberto no visualizador')
        
        # Resumo detalhado
        self.stdout.write(f'\n📊 RESUMO DETALHADO:')
        self.stdout.write(f'   Total de objetos únicos: {total_deteccoes}')
        self.stdout.write(f'   Seções processadas: 16')
        
        if objetos_detectados:
            self.stdout.write(f'\n🏷️  OBJETOS DETECTADOS:')
            for i, (x1, y1, x2, y2, classe, conf, secao) in enumerate(objetos_detectados, 1):
                w, h = x2 - x1, y2 - y1
                self.stdout.write(f'      [{i}] {classe}: {conf*100:.1f}% - Seção {secao} - {w}x{h}px')
        
        self.stdout.write(f'\n💾 Arquivos salvos:')
        self.stdout.write(f'   - {img_original_path.name} (original)')
        self.stdout.write(f'   - {grid_path.name} (grid 4x4)')
        self.stdout.write(f'   - {resultado_path.name} (resultado final)')
        
        self.stdout.write(f'\n📁 Pasta: {output_dir.absolute()}')