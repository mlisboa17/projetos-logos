"""
Django Command - Testar YOLOv8 Pré-treinado (COCO) nas imagens
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from verifik.models_anotacao import ImagemUnificada
from verifik.models import ProdutoMae
from pathlib import Path
from PIL import Image
import numpy as np
import os

class Command(BaseCommand):
    help = 'Testa YOLOv8 pré-treinado (COCO) para detectar garrafas e latas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limite',
            type=int,
            default=10,
            help='Número máximo de imagens para testar (default: 10)'
        )
        parser.add_argument(
            '--produto-id',
            type=int,
            default=None,
            help='Testar apenas imagens de um produto específico'
        )
        parser.add_argument(
            '--tipo-imagem',
            type=str,
            default='original',
            help='Tipo de imagem: original, processada, anotada, augmentada'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('🤖 TESTANDO YOLO8 PRÉ-TREINADO (COCO)'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Importar YOLO
        try:
            from ultralytics import YOLO
            self.stdout.write(self.style.SUCCESS('✅ ultralytics importado com sucesso'))
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ ultralytics não está instalado'))
            self.stdout.write('Instale com: pip install ultralytics')
            return
        
        # Carregar modelo pré-treinado
        self.stdout.write('\n📥 Baixando modelo YOLOv8n COCO...')
        model = YOLO('yolov8n.pt')
        self.stdout.write(self.style.SUCCESS('✅ Modelo YOLOv8n COCO carregado!'))
        
        # Classes do COCO que interessam
        classes_interesse = {
            39: 'bottle',      # Garrafa
            41: 'cup',         # Copo
            47: 'wine glass'   # Taça de vinho
        }
        
        self.stdout.write(f'\n🎯 Classes COCO que vou procurar: {list(classes_interesse.values())}')
        
        # Buscar imagens
        limite = options['limite']
        produto_id = options['produto_id']
        tipo_imagem = options['tipo_imagem']
        
        query = ImagemUnificada.objects.filter(
            tipo_imagem=tipo_imagem,
            ativa=True
        )
        
        if produto_id:
            query = query.filter(produto_id=produto_id)
        
        imagens = query[:limite]
        
        self.stdout.write(f'\n📊 Testando {imagens.count()} imagens...')
        self.stdout.write('=' * 80)
        
        deteccoes_por_classe = {}
        total_detectado = 0
        
        for idx, img_record in enumerate(imagens, 1):
            # Construir caminho da imagem
            arquivo_path = img_record.arquivo.path if hasattr(img_record.arquivo, 'path') else str(img_record.arquivo)
            
            if not os.path.exists(arquivo_path):
                self.stdout.write(f'⚠️  [{idx}] Arquivo não encontrado: {arquivo_path}')
                continue
            
            try:
                # Fazer predição
                results = model.predict(arquivo_path, conf=0.5, verbose=False)
                
                # Analisar resultados
                deteccoes = []
                if len(results) > 0:
                    boxes = results[0].boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            
                            if class_id in classes_interesse:
                                classe_nome = classes_interesse[class_id]
                                deteccoes.append({
                                    'classe': classe_nome,
                                    'confianca': confidence
                                })
                                
                                if classe_nome not in deteccoes_por_classe:
                                    deteccoes_por_classe[classe_nome] = 0
                                deteccoes_por_classe[classe_nome] += 1
                                total_detectado += 1
                
                # Exibir resultado
                produto_nome = img_record.produto.descricao_produto if img_record.produto else 'N/A'
                
                if deteccoes:
                    msg = f'✅ [{idx}] {produto_nome[:40]:40} → '
                    for d in deteccoes:
                        msg += f"{d['classe']} ({d['confianca']:.1%}) "
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    self.stdout.write(f'⚠️  [{idx}] {produto_nome[:40]:40} → Sem detecções')
                
            except Exception as e:
                self.stdout.write(f'❌ [{idx}] Erro: {str(e)[:60]}')
        
        # Resumo
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DAS DETECÇÕES'))
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n🎯 Total de detecções: {total_detectado}')
        self.stdout.write(f'📸 Imagens testadas: {imagens.count()}')
        
        if deteccoes_por_classe:
            self.stdout.write('\n📋 Detecções por classe:')
            for classe, count in sorted(deteccoes_por_classe.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f'   - {classe}: {count}')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Nenhuma detecção realizada'))
        
        # Próximos passos
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('📚 PRÓXIMOS PASSOS (FINE-TUNE)'))
        self.stdout.write('=' * 80)
        self.stdout.write('''
💡 O modelo genérico COCO detecta garrafas/copos/taças mas não sabe diferenciar:
   - LATA 350ML vs LATA 473ML
   - GARRAFA LONG NECK vs GARRAFA 600ML
   - Marcas e tipos específicos de embalagem

🔧 PARA FAZER FINE-TUNE (especializar para seus produtos):

1. Criar dataset YOLO com suas 1.336 imagens
2. Rotular as imagens com bounding boxes
3. Criar arquivo dataset.yaml com as classes
4. Executar: python manage.py treinar_yolo --epochs=50

Próximo comando:
   python manage.py criar_dataset_yolo
''')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))
