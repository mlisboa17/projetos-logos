"""
Django Command - Treinar YOLO8 com Fine-tune para detectar embalagens
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from verifik.models_anotacao import ImagemUnificada, HistoricoTreino, ImagemTreino
from verifik.models import ProdutoMae
from pathlib import Path
import json
import shutil
import os
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Treina YOLOv8 com fine-tune para detectar tipos de embalagem'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=50,
            help='Número de epochs para treinamento (default: 50)'
        )
        parser.add_argument(
            '--batch',
            type=int,
            default=8,
            help='Batch size (default: 8)'
        )
        parser.add_argument(
            '--device',
            type=int,
            default=0,
            help='Dispositivo: 0=GPU, -1=CPU (default: 0)'
        )
        parser.add_argument(
            '--split-test',
            type=float,
            default=0.1,
            help='Percentual para teste (default: 0.1 = 10%)'
        )
        parser.add_argument(
            '--split-val',
            type=float,
            default=0.1,
            help='Percentual para validação (default: 0.1 = 10%)'
        )
        parser.add_argument(
            '--nome-modelo',
            type=str,
            default='ProductScan_v1',
            help='Nome da IA (default: ProductScan_v1)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('🚀 TREINAMENTO YOLO8 - FINE-TUNE PARA EMBALAGENS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Importar YOLO
        try:
            from ultralytics import YOLO
            self.stdout.write(self.style.SUCCESS('✅ ultralytics importado com sucesso'))
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ ultralytics não está instalado'))
            self.stdout.write('Instale com: pip install ultralytics')
            return
        
        # Configurações
        epochs = options['epochs']
        batch = options['batch']
        device = options['device']
        split_test = options['split_test']
        split_val = options['split_val']
        nome_modelo = options['nome_modelo']
        
        # Criar diretório de dataset em local simples (sem caracteres especiais)
        dataset_dir = Path('C:\\dataset_yolo_verifik')
        dataset_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\n📁 Dataset directory: {dataset_dir}')
        
        # ════════════════════════════════════════════════════════════
        # PASSO 1: Organizar imagens por tipo de embalagem
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('📊 PASSO 1: Organizando imagens por tipo de embalagem...')
        self.stdout.write('─' * 80)
        
        # Buscar imagens com tipo de embalagem (de recipiente_fk)
        imagens_por_tipo = self._organizar_imagens_por_tipo()
        
        if not imagens_por_tipo:
            self.stdout.write(self.style.ERROR('❌ Nenhuma imagem encontrada!'))
            return
        
        self.stdout.write(f'\n✅ Imagens por tipo:')
        for tipo, imgs in imagens_por_tipo.items():
            self.stdout.write(f'   {tipo}: {len(imgs)} imagens')
        
        # ════════════════════════════════════════════════════════════
        # PASSO 2: Criar estrutura train/val/test
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('📂 PASSO 2: Criando estrutura train/val/test...')
        self.stdout.write('─' * 80)
        
        # Limpar dataset anterior
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)
        dataset_dir.mkdir(exist_ok=True)
        
        # Criar diretórios
        for split in ['train', 'val', 'test']:
            for tipo in imagens_por_tipo.keys():
                (dataset_dir / split / 'images' / tipo).mkdir(parents=True, exist_ok=True)
                (dataset_dir / split / 'labels' / tipo).mkdir(parents=True, exist_ok=True)
        
        # Distribuir imagens
        split_train = 1 - split_val - split_test
        
        for tipo, imagens in imagens_por_tipo.items():
            random.shuffle(imagens)
            
            n_train = int(len(imagens) * split_train)
            n_val = int(len(imagens) * split_val)
            
            train_imgs = imagens[:n_train]
            val_imgs = imagens[n_train:n_train + n_val]
            test_imgs = imagens[n_train + n_val:]
            
            # Copiar imagens para train
            for img in train_imgs:
                self._copiar_imagem(img, dataset_dir / 'train', tipo)
            
            # Copiar imagens para val
            for img in val_imgs:
                self._copiar_imagem(img, dataset_dir / 'val', tipo)
            
            # Copiar imagens para test
            for img in test_imgs:
                self._copiar_imagem(img, dataset_dir / 'test', tipo)
            
            self.stdout.write(f'✅ {tipo}: train={len(train_imgs)}, val={len(val_imgs)}, test={len(test_imgs)}')
        
        # ════════════════════════════════════════════════════════════
        # PASSO 3: Criar dataset.yaml
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('⚙️  PASSO 3: Criando dataset.yaml...')
        self.stdout.write('─' * 80)
        
        classes = list(imagens_por_tipo.keys())
        nc = len(classes)
        
        yaml_content = f"""# Dataset YOLO - Detecção de Embalagens VerifiK
path: {dataset_dir}
train: train/images
val: val/images
test: test/images

nc: {nc}
names: {classes}
"""
        
        yaml_path = dataset_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        self.stdout.write(f'✅ dataset.yaml criado: {yaml_path}')
        self.stdout.write(f'   Classes: {classes}')
        self.stdout.write(f'   Total de classes: {nc}')
        
        # ════════════════════════════════════════════════════════════
        # PASSO 4: Carregar e configurar modelo
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('🤖 PASSO 4: Carregando modelo YOLOv8n...')
        self.stdout.write('─' * 80)
        
        model = YOLO('yolov8n.pt')
        self.stdout.write('✅ Modelo YOLOv8n carregado (pré-treinado em COCO)')
        
        # ════════════════════════════════════════════════════════════
        # PASSO 5: Fine-tune
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('🔥 PASSO 5: Iniciando fine-tune...')
        self.stdout.write('─' * 80)
        self.stdout.write(f'\n📊 Configurações:')
        self.stdout.write(f'   Epochs: {epochs}')
        self.stdout.write(f'   Batch size: {batch}')
        self.stdout.write(f'   Dispositivo: {"GPU 0" if device >= 0 else "CPU"}')
        self.stdout.write(f'   Imagem size: 640x640')
        self.stdout.write(f'\n🔄 Treinando...\n')
        
        try:
            results = model.train(
                data=str(yaml_path),
                epochs=epochs,
                imgsz=640,
                batch=batch,
                device='cpu' if device < 0 else device,
                patience=10,
                save=True,
                cache=True,
                workers=4,
                project=str(dataset_dir / 'runs'),
                name='yolo_embalagens',
                verbose=True
            )
            
            self.stdout.write(self.style.SUCCESS('\n✅ Treinamento concluído!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante treinamento: {str(e)}'))
            return
        
        # ════════════════════════════════════════════════════════════
        # PASSO 6: Salvar modelo e registrar no banco
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '─' * 80)
        self.stdout.write('💾 PASSO 6: Salvando modelo e registrando no banco...')
        self.stdout.write('─' * 80)
        
        # Salvar modelo
        modelo_path = dataset_dir / 'yolo_embalagens_best.pt'
        best_model_path = dataset_dir / 'runs' / 'yolo_embalagens' / 'weights' / 'best.pt'
        
        if best_model_path.exists():
            shutil.copy(str(best_model_path), str(modelo_path))
            self.stdout.write(f'✅ Modelo salvo: {modelo_path}')
        
        # Registrar no banco de dados
        try:
            versao = f'{nome_modelo}-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            
            historico = HistoricoTreino.objects.create(
                versao_modelo=versao,
                data_inicio=datetime.now(),
                data_conclusao=datetime.now(),
                status='concluido',
                total_imagens=sum(len(imgs) for imgs in imagens_por_tipo.values()),
                total_produtos=len(ProdutoMae.objects.all()),
                epocas=epochs,
                acuracia=float(results.results_dict.get('metrics/mAP50', 0)) if hasattr(results, 'results_dict') else 0,
                perda=float(results.results_dict.get('loss/train', 0)) if hasattr(results, 'results_dict') else 0,
                parametros=json.dumps({
                    'batch_size': batch,
                    'device': device,
                    'classes': classes,
                    'imgsz': 640
                })
            )
            
            self.stdout.write(f'✅ Registro criado em HistoricoTreino (ID: {historico.id})')
            self.stdout.write(f'   Versão: {versao}')
            self.stdout.write(f'   Imagens: {historico.total_imagens}')
            self.stdout.write(f'   Produtos: {historico.total_produtos}')
            
            # Atualizar imagens com o novo treinamento
            imagens = ImagemUnificada.objects.filter(ativa=True)
            for img in imagens:
                img.num_treinos = (img.num_treinos or 0) + 1
                img.ultimo_treino = datetime.now()
                img.versao_modelo = versao
                img.save()
                
                # Registrar na tabela ImagemTreino
                ImagemTreino.objects.get_or_create(
                    imagem=img,
                    historico_treino=historico
                )
            
            self.stdout.write(f'✅ {imagens.count()} imagens atualizadas')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Erro ao registrar no banco: {str(e)}'))
        
        # ════════════════════════════════════════════════════════════
        # RESUMO FINAL
        # ════════════════════════════════════════════════════════════
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ TREINAMENTO CONCLUÍDO COM SUCESSO!'))
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'''
📊 RESUMO DO TREINAMENTO:

🎯 Classes treinadas: {classes}
📸 Total de imagens: {sum(len(imgs) for imgs in imagens_por_tipo.values())}
   - Train: {int(sum(len(imgs) for imgs in imagens_por_tipo.values()) * split_train)}
   - Val: {int(sum(len(imgs) for imgs in imagens_por_tipo.values()) * split_val)}
   - Test: {int(sum(len(imgs) for imgs in imagens_por_tipo.values()) * split_test)}

🔥 Epochs: {epochs}
📦 Batch size: {batch}
🖥️  Dispositivo: {"GPU" if device >= 0 else "CPU"}

💾 Modelo salvo: {modelo_path}
📊 Dataset: {dataset_dir}

🚀 Próximos passos:
   1. Validar modelo em imagens de teste
   2. Usar modelo para detectar embalagens: python manage.py detectar_embalagens
   3. Treinar por produto específico

''')
        
        self.stdout.write('=' * 80 + '\n')
    
    def _organizar_imagens_por_tipo(self):
        """Organiza imagens por tipo de embalagem baseado em recipiente_fk"""
        imagens_por_tipo = {
            'LATA_350ML': [],
            'LATA_473ML': [],
            'GARRAFA_LONG_NECK': [],
            'GARRAFA_600ML': [],
            'OUTROS': []
        }
        
        # Buscar todas as imagens
        todas_imagens = ImagemUnificada.objects.filter(ativa=True).select_related('produto')
        
        for img in todas_imagens:
            if not img.produto or not img.produto.recipiente_fk:
                imagens_por_tipo['OUTROS'].append(img)
                continue
            
            recipiente = img.produto.recipiente_fk
            nome_recipiente = recipiente.nome.upper()
            
            # Diferenciar LATA 350ML de LATA 473ML
            if 'LATA' in nome_recipiente:
                if '350' in nome_recipiente:
                    imagens_por_tipo['LATA_350ML'].append(img)
                elif '473' in nome_recipiente or '550' in nome_recipiente:
                    imagens_por_tipo['LATA_473ML'].append(img)
                else:
                    # Outras latas (269ml, 220ml, etc)
                    imagens_por_tipo['LATA_473ML'].append(img)
            elif 'LONG NECK' in nome_recipiente or '330' in nome_recipiente:
                imagens_por_tipo['GARRAFA_LONG_NECK'].append(img)
            elif '600' in nome_recipiente:
                imagens_por_tipo['GARRAFA_600ML'].append(img)
            else:
                imagens_por_tipo['OUTROS'].append(img)
        
        # Remover tipos vazios
        return {k: v for k, v in imagens_por_tipo.items() if v}
    
    def _copiar_imagem(self, img_record, split_dir, tipo):
        """Copia imagem para o diretório de split"""
        try:
            arquivo_path = img_record.arquivo.path if hasattr(img_record.arquivo, 'path') else str(img_record.arquivo)
            
            if not os.path.exists(arquivo_path):
                return False
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{img_record.id}_{timestamp}.jpg"
            
            # Criar symlink ao invés de copiar (muito mais rápido!)
            dest_img = split_dir / 'images' / tipo / filename
            
            try:
                # Windows: criar link simbólico
                os.symlink(arquivo_path, dest_img, target_is_directory=False)
            except (OSError, NotImplementedError):
                # Se falhar, fazer cópia (modo fallback lento)
                shutil.copy2(arquivo_path, dest_img)
            
            # Criar arquivo labels vazio (YOLO format)
            dest_label = split_dir / 'labels' / tipo / (filename.replace('.jpg', '.txt'))
            
            label_content = ""
            if img_record.bbox_x is not None:
                label_content = f"0 {img_record.bbox_x} {img_record.bbox_y} {img_record.bbox_width} {img_record.bbox_height}\n"
            
            with open(dest_label, 'w') as f:
                f.write(label_content)
            
            return True
            
        except Exception as e:
            print(f"Erro ao copiar imagem {img_record.id}: {e}")
            return False
