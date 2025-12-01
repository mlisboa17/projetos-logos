"""
TREINO DE YOLO8 ESPECIALIZADO EM FORMATOS DE BEBIDA
Categorias: Garrafa, Lata, PET 2L
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime
import json

from verifik.models_anotacao import ImagemUnificada, HistoricoTreino, ImagemTreino
from verifik.models import ProdutoMae


class Command(BaseCommand):
    help = 'Treina YOLOv8n especializado em formatos de bebida (Garrafa, Lata, PET 2L)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=50,
            help='Número de épocas (default: 50)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=8,
            help='Tamanho do batch (default: 8)'
        )
        parser.add_argument(
            '--imgsz',
            type=int,
            default=640,
            help='Tamanho das imagens (default: 640)'
        )
        parser.add_argument(
            '--device',
            type=str,
            default='cpu',
            help='Dispositivo: cpu, 0 (GPU), etc (default: cpu)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula sem treinar'
        )

    def handle(self, *args, **options):
        try:
            from ultralytics import YOLO
        except ImportError:
            raise CommandError('ultralytics não instalado. Execute: pip install ultralytics')

        epochs = options['epochs']
        batch_size = options['batch_size']
        imgsz = options['imgsz']
        device = options['device']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('TREINO YOLO8N - DETECCAO DE FORMATOS DE BEBIDA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ MODO DRY-RUN (sem treinar)'))

        # Categorias de formato
        categorias = {
            'garrafa': ['vidro', 'garraf', 'bottle'],  # Keywords
            'lata': ['lata', 'can', 'aluminio'],
            'pet_2l': ['2l', '2 l', 'pet', 'plástico', '2000'],
        }

        self.stdout.write(f'\n📊 Categorias reconhecidas:')
        for cat, keywords in categorias.items():
            self.stdout.write(f'   - {cat.upper()}: {", ".join(keywords)}')

        # Classificar imagens por categoria
        self.stdout.write(f'\n🔍 Classificando imagens por formato...')
        
        imagens_por_categoria = self._classificar_imagens(categorias)
        
        for cat, count in imagens_por_categoria.items():
            self.stdout.write(f'   {cat:15} {count:6} imagens')

        total_imagens = sum(imagens_por_categoria.values())
        self.stdout.write(f'\n   TOTAL: {total_imagens} imagens para treino')

        if total_imagens == 0:
            raise CommandError('Nenhuma imagem encontrada para treino!')

        # Distribuição: 70% treino, 15% validação, 15% teste
        train_split = 0.7
        val_split = 0.15

        self.stdout.write(f'\n📁 Criando dataset YOLO...')
        
        if dry_run:
            self.stdout.write(f'   ⊘ (Pulando criação de arquivos em dry-run)')
            dataset_path = None
        else:
            dataset_path = self._criar_dataset_yolo(
                imagens_por_categoria,
                categorias,
                train_split,
                val_split
            )

        # Iniciar histórico de treino
        self.stdout.write(f'\n🔬 Iniciando histórico de treino...')
        
        versao_modelo = f'yolov8n_formato_v{self._get_next_version()}'
        
        historico = None
        if not dry_run:
            historico = HistoricoTreino.objects.create(
                versao_modelo=versao_modelo,
                status='processando',
                total_imagens=total_imagens,
                total_produtos=len(imagens_por_categoria),
                epocas=epochs,
                parametros={
                    'batch_size': batch_size,
                    'imgsz': imgsz,
                    'device': device,
                    'categorias': list(imagens_por_categoria.keys()),
                    'train_split': train_split,
                    'val_split': val_split,
                }
            )
            self.stdout.write(f'   Versão: {versao_modelo}')
            self.stdout.write(f'   ID Histórico: {historico.id}')

        # Treinar modelo
        self.stdout.write(f'\n🚀 Treinando YOLOv8n...')
        self.stdout.write(f'   Epochs: {epochs}')
        self.stdout.write(f'   Batch Size: {batch_size}')
        self.stdout.write(f'   Image Size: {imgsz}')
        self.stdout.write(f'   Device: {device}')

        if dry_run:
            self.stdout.write(f'   ⊘ (Treinamento pulado em dry-run)')
            resultados_treino = {
                'accuracy': 0.85,
                'loss': 0.15,
                'mAP50': 0.78,
                'mAP50-95': 0.65,
            }
        else:
            try:
                # Carregar modelo pré-treinado YOLOv8n
                self.stdout.write(f'\n   Carregando YOLOv8n pré-treinado...')
                model = YOLO('yolov8n.pt')

                # Treinar
                self.stdout.write(f'\n   Iniciando treino (pode levar varios minutos)...')
                results = model.train(
                    data=str(dataset_path / 'data.yaml'),
                    epochs=epochs,
                    imgsz=imgsz,
                    batch=batch_size,
                    device=device,
                    patience=10,  # Early stopping
                    save=True,
                    verbose=True,
                )

                # Extrair resultados
                resultados_treino = {
                    'accuracy': float(results.results_dict.get('metrics/accuracy', 0)),
                    'loss': float(results.results_dict.get('train/loss', 0)),
                    'mAP50': float(results.results_dict.get('metrics/mAP50', 0)),
                    'mAP50-95': float(results.results_dict.get('metrics/mAP50-95', 0)),
                }

                # Salvar modelo final
                model_path = Path(settings.BASE_DIR) / 'modelos' / f'{versao_modelo}.pt'
                model_path.parent.mkdir(parents=True, exist_ok=True)
                model.save(str(model_path))
                self.stdout.write(self.style.SUCCESS(f'   ✓ Modelo salvo em: {model_path}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erro no treino: {str(e)}'))
                if historico:
                    historico.status = 'erro'
                    historico.observacoes = str(e)
                    historico.save()
                raise

        # Atualizar histórico e imagens
        if not dry_run:
            self.stdout.write(f'\n💾 Atualizando banco de dados...')
            
            historico.status = 'concluido'
            historico.acuracia = resultados_treino['accuracy']
            historico.perda = resultados_treino['loss']
            historico.data_conclusao = timezone.now()
            historico.save()

            # Atualizar todas as imagens usadas
            imagens_treino = ImagemUnificada.objects.filter(
                tipo_imagem__in=['original', 'processada', 'augmentada'],
                ativa=True
            )

            for img in imagens_treino:
                # Criar relação em ImagemTreino
                ImagemTreino.objects.get_or_create(
                    imagem=img,
                    historico_treino=historico,
                    defaults={'foi_usada': True}
                )

                # Atualizar campos de treino em ImagemUnificada
                img.num_treinos = (img.num_treinos or 0) + 1
                img.ultimo_treino = timezone.now()
                img.versao_modelo = versao_modelo
                img.save(update_fields=['num_treinos', 'ultimo_treino', 'versao_modelo'])

            self.stdout.write(self.style.SUCCESS(f'   ✓ {imagens_treino.count()} imagens atualizadas'))

        # Resumo final
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('RESUMO DO TREINO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        self.stdout.write(f'\n✓ Modelo: {versao_modelo}')
        self.stdout.write(f'✓ Imagens: {total_imagens}')
        self.stdout.write(f'✓ Epochs: {epochs}')
        self.stdout.write(f'✓ Batch Size: {batch_size}')

        self.stdout.write(f'\n📊 Resultados:')
        self.stdout.write(f'   Acurácia: {resultados_treino["accuracy"]:.4f}')
        self.stdout.write(f'   Perda: {resultados_treino["loss"]:.4f}')
        self.stdout.write(f'   mAP50: {resultados_treino["mAP50"]:.4f}')
        self.stdout.write(f'   mAP50-95: {resultados_treino["mAP50-95"]:.4f}')

        self.stdout.write(self.style.SUCCESS('\n✓ TREINO CONCLUIDO'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Limpar dataset temporário
        if not dry_run and dataset_path and dataset_path.parent.exists():
            shutil.rmtree(dataset_path.parent)

    def _classificar_imagens(self, categorias):
        """Classifica imagens por categoria de formato"""
        imagens_por_categoria = {cat: 0 for cat in categorias.keys()}
        
        imagens = ImagemUnificada.objects.filter(
            tipo_imagem__in=['original', 'processada', 'augmentada'],
            ativa=True
        ).select_related('produto')

        for img in imagens:
            desc = img.produto.descricao_produto.lower()
            
            # Tentar classificar por keywords
            encontrou = False
            for categoria, keywords in categorias.items():
                if any(kw in desc for kw in keywords):
                    imagens_por_categoria[categoria] += 1
                    encontrou = True
                    break
            
            # Se não encontrou, tentar por padrões de nome comum
            if not encontrou:
                if 'lata' in desc or 'can' in desc:
                    imagens_por_categoria['lata'] += 1
                elif '2l' in desc or '2 l' in desc:
                    imagens_por_categoria['pet_2l'] += 1
                else:
                    imagens_por_categoria['garrafa'] += 1
        
        return imagens_por_categoria

    def _criar_dataset_yolo(self, imagens_por_categoria, categorias, train_split, val_split):
        """Cria estrutura de dataset para YOLO"""
        import random
        
        temp_dir = Path(tempfile.mkdtemp(prefix='yolo_dataset_'))
        dataset_path = temp_dir / 'dataset'
        dataset_path.mkdir()

        # Criar pastas
        for split in ['train', 'val', 'test']:
            (dataset_path / 'images' / split).mkdir(parents=True, exist_ok=True)
            (dataset_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

        # Mapear categorias para IDs
        cat_ids = {cat: idx for idx, cat in enumerate(imagens_por_categoria.keys())}

        # Processar imagens
        imagens = ImagemUnificada.objects.filter(
            tipo_imagem__in=['original', 'processada', 'augmentada'],
            ativa=True
        ).select_related('produto')

        images_list = list(imagens)
        random.shuffle(images_list)

        train_count = int(len(images_list) * train_split)
        val_count = int(len(images_list) * val_split)

        for idx, img in enumerate(images_list):
            if idx < train_count:
                split = 'train'
            elif idx < train_count + val_count:
                split = 'val'
            else:
                split = 'test'

            # Copiar imagem
            if img.arquivo:
                ext = Path(img.arquivo.name).suffix
                dest_img = dataset_path / 'images' / split / f'{img.id}{ext}'
                
                img.arquivo.open('rb')
                with open(dest_img, 'wb') as f:
                    f.write(img.arquivo.read())
                img.arquivo.close()

                # Criar label (categoria)
                desc = img.produto.descricao_produto.lower()
                categoria = None
                
                for cat, keywords in categorias.items():
                    if any(kw in desc for kw in keywords):
                        categoria = cat
                        break
                
                if not categoria:
                    categoria = 'garrafa'  # Default

                cat_id = cat_ids[categoria]
                
                # Criar arquivo de label YOLO (classe sem bboxes neste caso)
                label_file = dataset_path / 'labels' / split / f'{img.id}.txt'
                with open(label_file, 'w') as f:
                    f.write(f'{cat_id}\n')  # Apenas a classe

        # Criar data.yaml
        yaml_content = f"""path: {dataset_path}
train: images/train
val: images/val
test: images/test

nc: {len(imagens_por_categoria)}
names: {list(imagens_por_categoria.keys())}
"""
        
        with open(dataset_path / 'data.yaml', 'w') as f:
            f.write(yaml_content)

        return dataset_path

    def _get_next_version(self):
        """Retorna o próximo número de versão"""
        latest = HistoricoTreino.objects.filter(
            versao_modelo__startswith='yolov8n_formato_v'
        ).order_by('-id').first()
        
        if not latest:
            return 1
        
        try:
            version = int(latest.versao_modelo.split('_v')[-1])
            return version + 1
        except:
            return 1
