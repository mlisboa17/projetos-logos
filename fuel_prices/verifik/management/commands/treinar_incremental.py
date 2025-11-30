from django.core.management.base import BaseCommand
from verifik.models import ProdutoMae, ImagemProduto
from ultralytics import YOLO
import albumentations as A
import cv2
import numpy as np
from pathlib import Path
import yaml
import shutil
from datetime import datetime


class Command(BaseCommand):
    help = 'Treina modelo YOLO incrementalmente com data augmentation usando Albumentations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--augmentations',
            type=int,
            default=7,
            help='Número de variações aumentadas por imagem original (padrão: 7)'
        )
        parser.add_argument(
            '--epochs',
            type=int,
            default=50,
            help='Número de épocas para treinar (padrão: 50)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=8,
            help='Tamanho do batch (padrão: 8)'
        )
        parser.add_argument(
            '--only-new',
            action='store_true',
            help='Treinar apenas imagens que ainda não foram treinadas'
        )
        parser.add_argument(
            '--produto-id',
            type=int,
            help='ID do produto específico para treinar (opcional)'
        )

    def handle(self, *args, **options):
        augmentations_count = options['augmentations']
        epochs = options['epochs']
        batch_size = options['batch_size']
        only_new = options.get('only_new', False)
        produto_id = options.get('produto_id', None)

        self.stdout.write(self.style.SUCCESS('=' * 70))
        if only_new and produto_id:
            self.stdout.write(self.style.SUCCESS('🚀 TREINAMENTO INCREMENTAL - PRODUTO ESPECÍFICO'))
        elif only_new:
            self.stdout.write(self.style.SUCCESS('🚀 TREINAMENTO INCREMENTAL - APENAS IMAGENS NOVAS'))
        else:
            self.stdout.write(self.style.SUCCESS('🚀 TREINAMENTO INCREMENTAL COM DATA AUGMENTATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 1. BUSCAR IMAGENS
        if only_new:
            if produto_id:
                self.stdout.write(f'\n📊 Passo 1: Buscando imagens NÃO treinadas do produto ID {produto_id}...')
            else:
                self.stdout.write('\n📊 Passo 1: Buscando imagens NÃO treinadas...')
        else:
            self.stdout.write('\n📊 Passo 1: Buscando todas as imagens de treinamento...')
        
        # Buscar imagens de treino agrupadas por produto
        produtos_com_imagens = {}
        total_imagens_originais = 0
        
        # Filtrar produtos se produto_id fornecido
        if produto_id:
            produtos_query = ProdutoMae.objects.filter(id=produto_id)
        else:
            produtos_query = ProdutoMae.objects.all()
        
        for produto in produtos_query:
            if only_new:
                # Apenas imagens não treinadas
                imagens = list(produto.imagens_treino.filter(treinada=False))
            else:
                # Todas as imagens
                imagens = list(produto.imagens_treino.all())
            
            if imagens:
                produtos_com_imagens[produto] = imagens
                total_imagens_originais += len(imagens)
                status = '🆕 NOVAS' if only_new else ''
                self.stdout.write(f'  ✓ {produto.marca} {produto.descricao_produto}: {len(imagens)} imagens {status}')
        
        if not produtos_com_imagens:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma imagem encontrada para treinamento!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total: {len(produtos_com_imagens)} produtos, {total_imagens_originais} imagens originais'))

        # 2. CONFIGURAR DATA AUGMENTATION COM ALBUMENTATIONS
        self.stdout.write('\n🎨 Passo 2: Configurando pipeline de Data Augmentation...')
        
        transform = A.Compose([
            # Transformações geométricas
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=15, border_mode=cv2.BORDER_CONSTANT, value=0, p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.1, 
                scale_limit=0.15, 
                rotate_limit=10, 
                border_mode=cv2.BORDER_CONSTANT,
                p=0.5
            ),
            
            # Transformações de cor e iluminação
            A.RandomBrightnessContrast(
                brightness_limit=0.3, 
                contrast_limit=0.3, 
                p=0.6
            ),
            A.HueSaturationValue(
                hue_shift_limit=15, 
                sat_shift_limit=25, 
                val_shift_limit=20, 
                p=0.5
            ),
            
            # Ruído e desfoque
            A.OneOf([
                A.GaussNoise(var_limit=(10.0, 50.0), p=1.0),
                A.GaussianBlur(blur_limit=3, p=1.0),
                A.MotionBlur(blur_limit=3, p=1.0),
            ], p=0.4),
            
            # Ajustes de qualidade
            A.OneOf([
                A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=1.0),
                A.Emboss(alpha=(0.2, 0.5), strength=(0.2, 0.7), p=1.0),
            ], p=0.3),
            
            # Condições de iluminação
            A.RandomShadow(
                shadow_roi=(0, 0.5, 1, 1),
                num_shadows_lower=1,
                num_shadows_upper=2,
                shadow_dimension=5,
                p=0.3
            ),
            
        ], bbox_params=A.BboxParams(
            format='yolo',
            label_fields=['class_labels'],
            min_visibility=0.3  # Bbox deve ter pelo menos 30% visível após augmentation
        ))
        
        self.stdout.write('  ✓ Pipeline configurado: 10 transformações de augmentation')

        # 3. CRIAR ESTRUTURA DE DATASET YOLO
        self.stdout.write('\n📁 Passo 3: Preparando estrutura de dataset YOLO...')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dataset_path = Path('verifik/dataset_treino_incremental') / timestamp
        images_path = dataset_path / 'images' / 'train'
        labels_path = dataset_path / 'labels' / 'train'
        
        images_path.mkdir(parents=True, exist_ok=True)
        labels_path.mkdir(parents=True, exist_ok=True)
        
        self.stdout.write(f'  ✓ Dataset criado em: {dataset_path}')

        # 4. PROCESSAR E AUMENTAR IMAGENS
        self.stdout.write(f'\n🔄 Passo 4: Aplicando Data Augmentation ({augmentations_count}x por imagem)...')
        
        # Mapear classes para índices YOLO
        class_mapping = {}
        for idx, produto in enumerate(sorted(produtos_com_imagens.keys(), key=lambda p: f"{p.marca}_{p.descricao_produto}")):
            class_name = f"{produto.marca}_{produto.descricao_produto}".replace(' ', '_')
            class_mapping[produto.id] = {
                'index': idx,
                'name': class_name
            }
        
        total_images_generated = 0
        
        for produto, imagens in produtos_com_imagens.items():
            class_idx = class_mapping[produto.id]['index']
            class_name = class_mapping[produto.id]['name']
            
            self.stdout.write(f'\n  📦 Processando: {class_name}')
            
            for img_idx, imagem_obj in enumerate(imagens):
                # Ler imagem original
                img_path = Path(imagem_obj.imagem.path)
                if not img_path.exists():
                    self.stdout.write(self.style.WARNING(f'    ⚠️  Arquivo não encontrado: {img_path}'))
                    continue
                
                image = cv2.imread(str(img_path))
                if image is None:
                    self.stdout.write(self.style.WARNING(f'    ⚠️  Erro ao ler imagem: {img_path}'))
                    continue
                
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                h, w = image.shape[:2]
                
                # Bbox em formato YOLO (x_center, y_center, width, height) normalizado
                # Como cada imagem tem apenas 1 produto, bbox cobre maior parte da imagem
                bbox = [0.5, 0.5, 0.9, 0.9]  # Produto centralizado ocupando 90% da imagem
                
                # Salvar imagem original
                original_name = f"{class_name}_{img_idx}_original.jpg"
                original_img_path = images_path / original_name
                original_label_path = labels_path / f"{class_name}_{img_idx}_original.txt"
                
                cv2.imwrite(str(original_img_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
                with open(original_label_path, 'w') as f:
                    f.write(f"{class_idx} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")
                
                total_images_generated += 1
                
                # Gerar variações aumentadas
                for aug_idx in range(augmentations_count):
                    try:
                        # Aplicar augmentation
                        augmented = transform(
                            image=image,
                            bboxes=[bbox],
                            class_labels=[class_idx]
                        )
                        
                        aug_image = augmented['image']
                        aug_bboxes = augmented['bboxes']
                        
                        # Verificar se bbox ainda existe após transformação
                        if not aug_bboxes:
                            continue
                        
                        # Salvar imagem aumentada
                        aug_name = f"{class_name}_{img_idx}_aug{aug_idx + 1}.jpg"
                        aug_img_path = images_path / aug_name
                        aug_label_path = labels_path / f"{class_name}_{img_idx}_aug{aug_idx + 1}.txt"
                        
                        cv2.imwrite(str(aug_img_path), cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR))
                        
                        # Salvar label com bbox ajustado automaticamente pelo Albumentations
                        with open(aug_label_path, 'w') as f:
                            aug_bbox = aug_bboxes[0]
                            f.write(f"{class_idx} {aug_bbox[0]} {aug_bbox[1]} {aug_bbox[2]} {aug_bbox[3]}\n")
                        
                        total_images_generated += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    ⚠️  Erro ao aumentar imagem {img_idx}, aug {aug_idx}: {e}'))
                        continue
                
                self.stdout.write(f'    ✓ Imagem {img_idx + 1}/{len(imagens)}: 1 original + {augmentations_count} aumentadas')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total de imagens geradas: {total_images_generated}'))

        # 5. CRIAR ARQUIVO data.yaml
        self.stdout.write('\n📝 Passo 5: Criando arquivo de configuração YOLO...')
        
        data_yaml = {
            'path': str(dataset_path.absolute()),
            'train': 'images/train',
            'val': 'images/train',  # Usar mesmo conjunto para validação (pequeno dataset)
            'nc': len(class_mapping),
            'names': [class_mapping[pid]['name'] for pid in sorted(class_mapping.keys(), key=lambda k: class_mapping[k]['index'])]
        }
        
        yaml_path = dataset_path / 'data.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)
        
        self.stdout.write(f'  ✓ Configuração salva: {yaml_path}')
        self.stdout.write(f'  ✓ Classes: {data_yaml["names"]}')

        # 6. CARREGAR MODELO DO CHECKPOINT
        self.stdout.write('\n🤖 Passo 6: Carregando modelo do checkpoint...')
        
        # Tentar diferentes locais de checkpoint
        checkpoint_paths = [
            Path('verifik/runs/treino_verifik/weights/last.pt'),
            Path('verifik/runs/treino_incremental/weights/last.pt'),
        ]
        
        checkpoint_path = None
        for path in checkpoint_paths:
            if path.exists():
                checkpoint_path = path
                break
        
        if checkpoint_path:
            self.stdout.write(f'  ✓ Checkpoint encontrado: {checkpoint_path}')
            self.stdout.write('  📍 CONTINUANDO treinamento do último estado salvo...')
            self.stdout.write('  ⚡ Modo: Treinamento incremental (não reinicia do zero)')
            model = YOLO(str(checkpoint_path))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Checkpoint não encontrado, iniciando do zero com YOLOv8n'))
            model = YOLO('yolov8n.pt')

        # 7. TREINAR MODELO
        self.stdout.write(f'\n🎯 Passo 7: Iniciando treinamento ({epochs} épocas)...')
        self.stdout.write('=' * 70)
        
        try:
            results = model.train(
                data=str(yaml_path),
                epochs=epochs,
                batch=batch_size,
                imgsz=640,
                patience=15,  # Early stopping após 15 épocas sem melhoria
                save=True,
                project='verifik/runs',
                name='treino_incremental',
                exist_ok=True,
                pretrained=True,
                optimizer='AdamW',
                verbose=True,
                seed=42,
                deterministic=False,
                single_cls=False,
                rect=False,
                cos_lr=True,  # Cosine learning rate scheduler
                close_mosaic=10,  # Desativar mosaic nos últimos 10 epochs
                amp=True,  # Automatic Mixed Precision para treino mais rápido
                fraction=1.0,
                profile=False,
                overlap_mask=True,
                mask_ratio=4,
                dropout=0.0,
                val=True,
                plots=True,
            )
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('✅ TREINAMENTO CONCLUÍDO COM SUCESSO!'))
            self.stdout.write('=' * 70)
            
            # Estatísticas finais
            self.stdout.write(f'\n📊 Estatísticas:')
            self.stdout.write(f'  • Imagens originais: {total_imagens_originais}')
            self.stdout.write(f'  • Imagens após augmentation: {total_images_generated}')
            self.stdout.write(f'  • Multiplicador: {total_images_generated / total_imagens_originais:.1f}x')
            self.stdout.write(f'  • Classes treinadas: {len(class_mapping)}')
            self.stdout.write(f'  • Épocas: {epochs}')
            self.stdout.write(f'  • Modelo salvo em: verifik/runs/treino_incremental/')
            
            # Mostrar métricas finais se disponíveis
            if hasattr(results, 'results_dict'):
                metrics = results.results_dict
                self.stdout.write(f'\n🎯 Métricas finais:')
                if 'metrics/mAP50(B)' in metrics:
                    self.stdout.write(f'  • mAP@50: {metrics["metrics/mAP50(B)"]:.3f}')
                if 'metrics/mAP50-95(B)' in metrics:
                    self.stdout.write(f'  • mAP@50-95: {metrics["metrics/mAP50-95(B)"]:.3f}')
            
            self.stdout.write('\n✨ Modelo pronto para uso!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante treinamento: {e}'))
            raise
