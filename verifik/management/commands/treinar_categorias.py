"""
TREINAMENTO YOLO8n - CATEGORIAS DE FORMATO
Treina modelo para reconhecer: garrafas, latas, PET 2L, barras chocolate
Usa base pré-treinada YOLOv8n e fine-tune com dataset específico
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from pathlib import Path
import shutil
import yaml
import os
from datetime import datetime

from verifik.models_anotacao import ImagemUnificada, HistoricoTreino, ImagemTreino
from verifik.models import ProdutoMae


class Command(BaseCommand):
    help = 'Treina YOLOv8n com categorias de formato (garrafas, latas, PET, chocolate)'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=50, help='Numero de epocas (default: 50)')
        parser.add_argument('--batch', type=int, default=8, help='Batch size (default: 8)')
        parser.add_argument('--img-size', type=int, default=640, help='Tamanho da imagem (default: 640)')
        parser.add_argument('--device', type=str, default='0', help='GPU device (default: 0)')
        parser.add_argument('--resume', action='store_true', help='Retomar treino anterior')
        parser.add_argument('--test-split', type=float, default=0.2, help='Percentual de teste (default: 0.2)')
        parser.add_argument('--dry-run', action='store_true', help='Simula sem treinar')

    def handle(self, *args, **options):
        epochs = options['epochs']
        batch_size = options['batch_size']
        img_size = options['img_size']
        device = options['device']
        resume = options['resume']
        test_split = options['test_split']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('TREINAMENTO YOLO8n - CATEGORIAS DE FORMATO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ MODO DRY-RUN (sem treinar)'))
        
        # Definir categorias por formato
        categorias = {
            'garrafa': ['CERVEJA', 'VINHO', 'REFRIGERANTE'],
            'lata': ['LATA', 'ENERGETICO'],
            'pet_2l': ['PET', '2L', '2LITRO'],
            'chocolate': ['CHOCOLATE', 'BARRA', 'BOMBOM']
        }
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Épocas: {epochs}')
        self.stdout.write(f'   Batch size: {batch_size}')
        self.stdout.write(f'   Tamanho imagem: {img_size}x{img_size}')
        self.stdout.write(f'   Device: GPU {device}')
        self.stdout.write(f'   Split teste: {test_split*100:.1f}%')
        
        self.stdout.write(f'\n🏷️  Categorias a reconhecer:')
        for cat, palavras in categorias.items():
            self.stdout.write(f'   - {cat}: {", ".join(palavras)}')
        
        # Criar dataset
        dataset_dir = Path('/tmp/dataset_yolo_categorias')
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)
        
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        self.stdout.write(f'\n🗂️  Criando dataset em {dataset_dir}...')
        
        # Categorizar imagens
        imagens_por_categoria = self.categorizar_imagens(categorias)
        
        # Dividir em train/val/test
        train_dir = dataset_dir / 'images' / 'train'
        val_dir = dataset_dir / 'images' / 'val'
        test_dir = dataset_dir / 'images' / 'test'
        
        train_labels_dir = dataset_dir / 'labels' / 'train'
        val_labels_dir = dataset_dir / 'labels' / 'val'
        test_labels_dir = dataset_dir / 'labels' / 'test'
        
        for d in [train_dir, val_dir, test_dir, train_labels_dir, val_labels_dir, test_labels_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        total_imagens = 0
        total_erro = 0
        
        for idx_cat, (categoria, imagens) in enumerate(imagens_por_categoria.items()):
            self.stdout.write(f'\n   {categoria}: {len(imagens)} imagens')
            
            # Dividir dataset
            num_test = max(1, int(len(imagens) * test_split))
            num_val = max(1, int((len(imagens) - num_test) * 0.2))
            num_train = len(imagens) - num_val - num_test
            
            train_imgs = imagens[:num_train]
            val_imgs = imagens[num_train:num_train + num_val]
            test_imgs = imagens[num_train + num_val:]
            
            self.stdout.write(f'      - Train: {len(train_imgs)}, Val: {len(val_imgs)}, Test: {len(test_imgs)}')
            
            # Copiar imagens e criar labels YOLO
            for subset, imgs, dst_dir, lbl_dir in [
                ('train', train_imgs, train_dir, train_labels_dir),
                ('val', val_imgs, val_dir, val_labels_dir),
                ('test', test_imgs, test_dir, test_labels_dir),
            ]:
                for img_unif in imgs:
                    try:
                        if not img_unif.arquivo:
                            total_erro += 1
                            continue
                        
                        # Copiar arquivo
                        nome_arquivo = Path(img_unif.arquivo.name).name
                        dst_path = dst_dir / nome_arquivo
                        
                        if not dry_run:
                            img_unif.arquivo.open('rb')
                            with open(dst_path, 'wb') as f:
                                f.write(img_unif.arquivo.read())
                            img_unif.arquivo.close()
                            
                            # Criar label YOLO (format: class_id center_x center_y width height)
                            # Para imagens sem bbox anotado, criar bbox full image (classe = índice categoria)
                            lbl_path = lbl_dir / (Path(nome_arquivo).stem + '.txt')
                            with open(lbl_path, 'w') as f:
                                # Classe = índice da categoria
                                f.write(f"{idx_cat} 0.5 0.5 1.0 1.0\n")
                        
                        total_imagens += 1
                    
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'      Erro: {str(e)}'))
                        total_erro += 1
                        continue
        
        self.stdout.write(f'\n✓ Dataset preparado: {total_imagens} imagens')
        if total_erro > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Erros: {total_erro}'))
        
        # Criar arquivo YAML de dataset
        yaml_path = dataset_dir / 'data.yaml'
        data_yaml = {
            'path': str(dataset_dir),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': len(categorias),
            'names': list(categorias.keys())
        }
        
        if not dry_run:
            with open(yaml_path, 'w') as f:
                yaml.dump(data_yaml, f)
        
        self.stdout.write(f'\n✓ YAML config criado: {yaml_path}')
        
        # Treinar com YOLO
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n🚀 Iniciando treino com YOLOv8n...'))
            self.stdout.write('   Carregando modelo pré-treinado (yolov8n.pt)...')
            
            try:
                from ultralytics import YOLO
                
                # Carregar modelo pré-treinado
                model = YOLO('yolov8n.pt')
                
                self.stdout.write('   ✓ Modelo carregado')
                self.stdout.write('   Iniciando fine-tune...')
                
                # Treinar
                versao_modelo = f"yolov8n_categorias_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                resultados = model.train(
                    data=str(yaml_path),
                    epochs=epochs,
                    imgsz=img_size,
                    batch=batch_size,
                    device=int(device),
                    patience=10,
                    save=True,
                    project='runs/categorias',
                    name=versao_modelo,
                    exist_ok=False,
                    verbose=True
                )
                
                self.stdout.write(self.style.SUCCESS('\n✅ TREINO CONCLUIDO!'))
                
                # Registrar no banco
                self.registrar_treino(
                    versao_modelo,
                    total_imagens,
                    len(categorias),
                    epochs,
                    resultados
                )
                
                # Mostrar resultados
                self.stdout.write(f'\n📊 Resultados:')
                self.stdout.write(f'   Versão: {versao_modelo}')
                self.stdout.write(f'   Imagens treinadas: {total_imagens}')
                self.stdout.write(f'   Categorias: {len(categorias)}')
                self.stdout.write(f'   Model path: runs/categorias/{versao_modelo}')
                
            except ImportError:
                self.stdout.write(self.style.ERROR('✗ Ultralytics YOLO não instalado'))
                self.stdout.write('   Execute: pip install ultralytics')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erro durante treino: {str(e)}'))
                import traceback
                traceback.print_exc()
        
        else:
            self.stdout.write(self.style.WARNING('\n✓ DRY-RUN CONCLUIDO (sem treinar)'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))

    def categorizar_imagens(self, categorias):
        """Categoriza imagens por tipo de formato"""
        
        imagens_por_categoria = {cat: [] for cat in categorias.keys()}
        
        # Buscar todas as imagens ativas
        imagens = ImagemUnificada.objects.filter(
            ativa=True,
            tipo_imagem__in=['original', 'processada', 'augmentada']
        ).select_related('produto')
        
        total = imagens.count()
        self.stdout.write(f'\n   Analisando {total} imagens...')
        
        for img in imagens:
            produto_desc = img.produto.descricao_produto.upper()
            
            # Tentar categorizar
            categorizado = False
            for categoria, palavras_chave in categorias.items():
                if any(palavra in produto_desc for palavra in palavras_chave):
                    imagens_por_categoria[categoria].append(img)
                    categorizado = True
                    break
            
            # Se não categorizado, colocar na primeira categoria (garrafa é default)
            if not categorizado:
                imagens_por_categoria['garrafa'].append(img)
        
        return imagens_por_categoria

    def registrar_treino(self, versao_modelo, total_imagens, num_categorias, epochs, resultados):
        """Registra treino no banco de dados"""
        
        try:
            # Criar registro de treino
            historico = HistoricoTreino.objects.create(
                versao_modelo=versao_modelo,
                status='concluido',
                total_imagens=total_imagens,
                total_produtos=num_categorias,
                epocas=epochs,
                parametros={
                    'batch_size': 8,
                    'img_size': 640,
                    'modelo_base': 'yolov8n.pt',
                    'tipo': 'categorias_formato'
                }
            )
            
            # Atualizar imagens usadas no treino
            imagens_treino = ImagemUnificada.objects.filter(
                ativa=True,
                tipo_imagem__in=['original', 'processada', 'augmentada']
            )
            
            for img in imagens_treino:
                img.num_treinos += 1
                img.ultimo_treino = timezone.now()
                img.versao_modelo = versao_modelo
                img.save()
                
                # Registrar na tabela ImagemTreino
                ImagemTreino.objects.get_or_create(
                    imagem=img,
                    historico_treino=historico
                )
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Treino registrado no banco: {versao_modelo}'))
            self.stdout.write(f'  ID Histórico: {historico.id}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Erro ao registrar treino: {str(e)}'))
