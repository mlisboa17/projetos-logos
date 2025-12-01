from django.core.management.base import BaseCommand
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image
import cv2


class Command(BaseCommand):
    help = 'Detecção detalhada com todas as etapas do pipeline de inferência'

    def add_arguments(self, parser):
        parser.add_argument('--modelo', type=str, default='ProductScan_v1',
                          help='Modelo a usar (padrão: ProductScan_v1)')
        parser.add_argument('--imagem', type=str, help='Caminho para imagem específica')
        parser.add_argument('--confianca', type=float, default=0.25, 
                          help='Confiança mínima (padrão: 0.25)')
        parser.add_argument('--nms-threshold', type=float, default=0.45,
                          help='Limiar NMS para eliminar duplicatas (padrão: 0.45)')
        parser.add_argument('--salvar-crops', action='store_true',
                          help='Salvar produtos recortados individualmente')

    def handle(self, *args, **options):
        modelo_name = options['modelo']
        imagem_path = options['imagem']
        confianca = options['confianca']
        nms_threshold = options['nms_threshold']
        salvar_crops = options['salvar_crops']

        self.stdout.write('=' * 80)
        self.stdout.write(f'🔬 DETECCAO DETALHADA - PIPELINE COMPLETO')
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Modelo: {modelo_name}')
        self.stdout.write(f'   Confiança mínima: {confianca}')
        self.stdout.write(f'   NMS Threshold: {nms_threshold}')
        self.stdout.write(f'   Salvar produtos individuais: {"Sim" if salvar_crops else "Não"}')

        try:
            from ultralytics import YOLO
            import torch
            
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

            # Testar com imagem específica ou database
            if imagem_path:
                self.processar_imagem_detalhada(model, imagem_path, confianca, nms_threshold, salvar_crops)
            else:
                self.processar_database_detalhada(model, confianca, nms_threshold, salvar_crops)

        except ImportError:
            self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
            self.stdout.write('   Execute: pip install ultralytics opencv-python pillow')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def processar_imagem_detalhada(self, model, imagem_path, confianca, nms_threshold, salvar_crops):
        """Processa uma imagem mostrando cada etapa do pipeline com exclusão de regiões"""
        
        self.stdout.write(f'\n🖼️  PROCESSANDO: {Path(imagem_path).name}')
        
        # Criar pasta de output
        output_dir = Path('deteccao_otimizada')
        output_dir.mkdir(exist_ok=True)
        
        try:
            # ETAPA 1: PRÉ-PROCESSAMENTO
            self.stdout.write(f'\n📥 ETAPA 1: PRÉ-PROCESSAMENTO')
            
            # Carregar imagem original
            img_original = cv2.imread(imagem_path)
            if img_original is None:
                self.stdout.write(self.style.ERROR('✗ Não foi possível carregar a imagem'))
                return
                
            altura_original, largura_original = img_original.shape[:2]
            self.stdout.write(f'   ✓ Imagem carregada: {largura_original}x{altura_original}')
            
            # Redimensionar para 640x640 (entrada do modelo)
            img_resized = cv2.resize(img_original, (640, 640))
            self.stdout.write(f'   ✓ Redimensionada para: 640x640')
            
            # Salvar imagem redimensionada
            cv2.imwrite(str(output_dir / '1_preprocessed_640x640.jpg'), img_resized)
            self.stdout.write(f'   💾 Salva: 1_preprocessed_640x640.jpg')

            # ETAPA 2: INFERÊNCIA
            self.stdout.write(f'\n🧠 ETAPA 2: INFERÊNCIA E OBTENÇÃO DE RESULTADOS')
            
            # Executar modelo (com configurações detalhadas)
            resultados = model.predict(
                imagem_path, 
                conf=confianca,
                iou=nms_threshold,  # NMS threshold
                verbose=False,
                save=False
            )
            
            if not resultados or len(resultados) == 0:
                self.stdout.write('   ✗ Nenhum resultado da inferência')
                return
                
            resultado = resultados[0]
            boxes = resultado.boxes
            
            if boxes is None or len(boxes) == 0:
                self.stdout.write('   ✗ Nenhuma caixa detectada')
                return
            
            self.stdout.write(f'   ✓ Inferência executada')
            self.stdout.write(f'   ✓ {len(boxes)} detecções brutas encontradas')
            
            # Mostrar todas as detecções (antes do filtro de confiança)
            self.stdout.write(f'\n   📊 DETECÇÕES BRUTAS (todas):')
            for i, box in enumerate(boxes):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                status = "✓ ACEITA" if conf >= confianca else "✗ REJEITADA"
                self.stdout.write(f'      [{i+1}] {nome_classe}: {conf*100:.1f}% - {status}')
                self.stdout.write(f'           bbox: ({x1:.0f},{y1:.0f}) → ({x2:.0f},{y2:.0f})')

            # ETAPA 3: PÓS-PROCESSAMENTO
            self.stdout.write(f'\n🔧 ETAPA 3: PÓS-PROCESSAMENTO E ISOLAMENTO')
            
            # Filtrar por confiança (já feito pelo YOLO, mas vamos mostrar)
            boxes_filtradas = []
            for box in boxes:
                if float(box.conf) >= confianca:
                    boxes_filtradas.append(box)
                    
            self.stdout.write(f'   ✓ Filtragem por confiança (≥{confianca}): {len(boxes_filtradas)} restantes')
            
            # NMS já foi aplicado pelo YOLO, mas vamos explicar
            self.stdout.write(f'   ✓ NMS (Non-Maximum Suppression) aplicado com threshold {nms_threshold}')
            self.stdout.write(f'   ✓ Duplicatas eliminadas automaticamente')
            
            # Escalar coordenadas de volta para imagem original
            self.stdout.write(f'   ✓ Escalar coordenadas: 640x640 → {largura_original}x{altura_original}')
            
            # ETAPA 4: DETECÇÃO SEQUENCIAL COM EXCLUSÃO DE REGIÕES
            self.stdout.write(f'\n🎯 ETAPA 4: DETECÇÃO SEQUENCIAL (SEM OVERLAP)')
            
            # Estratégia: Processar uma detecção por vez, mascarando regiões já detectadas
            img_com_boxes = img_original.copy()
            img_trabalho = img_original.copy()  # Imagem que vai sendo mascarada
            produtos_isolados = []
            regioes_excluidas = []  # Lista de regiões já detectadas
            
            # Ordenar detecções por confiança (maior primeiro)
            boxes_ordenadas = sorted(boxes_filtradas, key=lambda x: float(x.conf), reverse=True)
            
            self.stdout.write(f'   📋 Processando {len(boxes_ordenadas)} detecções em ordem de confiança')
            
            for i, box in enumerate(boxes_ordenadas):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                
                # Coordenadas já escaladas para imagem original
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                w, h = x2 - x1, y2 - y1
                
                # Verificar se esta região já foi coberta por uma detecção anterior
                area_atual = (x1, y1, x2, y2)
                overlap_significativo = False
                
                for regiao_anterior in regioes_excluidas:
                    xa1, ya1, xa2, ya2 = regiao_anterior
                    # Calcular intersecção
                    x_inter1 = max(x1, xa1)
                    y_inter1 = max(y1, ya1)
                    x_inter2 = min(x2, xa2)
                    y_inter2 = min(y2, ya2)
                    
                    if x_inter1 < x_inter2 and y_inter1 < y_inter2:
                        area_intersecao = (x_inter2 - x_inter1) * (y_inter2 - y_inter1)
                        area_box_atual = w * h
                        overlap_percent = area_intersecao / area_box_atual
                        
                        if overlap_percent > 0.3:  # 30% de overlap = muito overlap
                            overlap_significativo = True
                            break
                
                if overlap_significativo:
                    self.stdout.write(f'   ❌ PRODUTO {i+1} IGNORADO (overlap com detecção anterior):')
                    self.stdout.write(f'      {nome_classe}: {conf*100:.1f}% - REGIÃO JÁ DETECTADA')
                    continue
                
                self.stdout.write(f'   ✅ PRODUTO {len(produtos_isolados)+1} ACEITO:')
                self.stdout.write(f'      Classe: {nome_classe}')
                self.stdout.write(f'      Confiança: {conf*100:.1f}%')
                self.stdout.write(f'      Coordenadas: x={x1}, y={y1}, w={w}, h={h}')
                
                # Adicionar esta região à lista de excluídas (com margem)
                margem = 10  # pixels de margem
                x1_expandido = max(0, x1 - margem)
                y1_expandido = max(0, y1 - margem)
                x2_expandido = min(img_original.shape[1], x2 + margem)
                y2_expandido = min(img_original.shape[0], y2 + margem)
                regioes_excluidas.append((x1_expandido, y1_expandido, x2_expandido, y2_expandido))
                
                # Desenhar bounding box (cor diferente para cada produto)
                cores = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
                color = cores[len(produtos_isolados) % len(cores)]
                cv2.rectangle(img_com_boxes, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img_com_boxes, f'{nome_classe} {conf:.2f}', 
                          (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Mascarar região na imagem de trabalho (pintar de preto)
                cv2.rectangle(img_trabalho, (x1_expandido, y1_expandido), 
                            (x2_expandido, y2_expandido), (0, 0, 0), -1)
                
                self.stdout.write(f'      🚫 Região mascarada para próximas detecções')
                
                # Recortar produto (cropping) apenas dos aceitos
                if salvar_crops:
                    produto_crop = img_original[y1:y2, x1:x2]
                    if produto_crop.size > 0:
                        crop_path = output_dir / f'produto_{len(produtos_isolados)+1}_{nome_classe}_{conf:.2f}.jpg'
                        cv2.imwrite(str(crop_path), produto_crop)
                        produtos_isolados.append(str(crop_path))
                        self.stdout.write(f'      💾 Produto isolado: {crop_path.name}')
            
            # Salvar visualizações
            resultado_final = output_dir / 'resultado_final_sem_overlap.jpg'
            cv2.imwrite(str(resultado_final), img_com_boxes)
            self.stdout.write(f'\n💾 Resultado final: {resultado_final.name}')
            
            # Salvar imagem com regiões mascaradas (para debug)
            img_mascarada = output_dir / 'imagem_com_regioes_mascaradas.jpg'
            cv2.imwrite(str(img_mascarada), img_trabalho)
            self.stdout.write(f'💾 Regiões mascaradas: {img_mascarada.name}')
            
            # Resumo com otimização
            self.stdout.write(f'\n📈 RESUMO OTIMIZADO:')
            self.stdout.write(f'   Detecções brutas encontradas: {len(boxes_filtradas)}')
            self.stdout.write(f'   Produtos únicos (sem overlap): {len(produtos_isolados)}')
            self.stdout.write(f'   Regiões mascaradas: {len(regioes_excluidas)}')
            self.stdout.write(f'   Taxa de eficiência: {len(produtos_isolados)/len(boxes_filtradas)*100:.1f}%')
            if salvar_crops:
                self.stdout.write(f'   Produtos isolados salvos: {len(produtos_isolados)}')
            self.stdout.write(f'   Pasta de resultados: {output_dir.absolute()}')
            
            # Opcional: aplicar rembg aos produtos isolados
            if salvar_crops and len(produtos_isolados) > 0:
                self.stdout.write(f'\n🎨 OPCIONAL: Remover fundo dos produtos isolados?')
                self.stdout.write(f'   Execute: pip install rembg')
                self.stdout.write(f'   Depois aplique rembg em cada arquivo da pasta {output_dir}/')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro no processamento: {str(e)}'))
            import traceback
            traceback.print_exc()

    def processar_database_detalhada(self, model, confianca, nms_threshold, salvar_crops):
        """Processa algumas imagens do database"""
        
        from verifik.models_anotacao import ImagemUnificada
        
        # Buscar 3 imagens para análise detalhada
        imagens = ImagemUnificada.objects.filter(
            ativa=True,
            tipo_imagem__in=['original', 'processada']
        )[:3]
        
        self.stdout.write(f'\n🗄️  PROCESSANDO {len(imagens)} IMAGENS DO DATABASE')
        
        for i, img in enumerate(imagens, 1):
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'IMAGEM {i}: {img.produto.descricao_produto[:30]}')
            self.stdout.write(f'{"="*60}')
            
            if not img.arquivo:
                self.stdout.write('✗ Sem arquivo')
                continue
                
            try:
                # Salvar temporariamente
                img.arquivo.open('rb')
                conteudo = img.arquivo.read()
                img.arquivo.close()
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp.write(conteudo)
                    tmp_path = tmp.name
                
                # Processar com pipeline detalhado
                self.processar_imagem_detalhada(model, tmp_path, confianca, nms_threshold, salvar_crops)
                
                # Limpar
                Path(tmp_path).unlink()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))