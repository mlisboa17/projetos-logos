"""
DETECCAO DE EMBALAGENS - MODELO PRE-TREINADO
Usa modelo YOLO pré-treinado e adapta para reconhecer:
- Garrafas (vidro/plástico rígido)
- Latas (alumínio 473ml)
- PET 2L (plástico maleável)
"""

from django.core.management.base import BaseCommand
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Carrega modelo pré-treinado e usa para detectar embalagens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--modelo',
            type=str,
            default='ProductScan_v1',
            help='Modelo: ProductScan_v1 (treinado), yolov8n.pt (genérico)'
        )
        parser.add_argument(
            '--imagem',
            type=str,
            help='Caminho da imagem para testar deteccao'
        )
        parser.add_argument(
            '--pasta',
            type=str,
            help='Pasta com imagens para testar em lote'
        )
        parser.add_argument(
            '--confianca',
            type=float,
            default=0.5,
            help='Confianca minima para deteccao (default: 0.5)'
        )

    def handle(self, *args, **options):
        modelo_name = options['modelo']
        imagem_path = options['imagem']
        pasta_path = options['pasta']
        confianca = options['confianca']
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('🤖 DETECCAO DE EMBALAGENS - ProductScan_v1'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        self.stdout.write(f'\n📊 Configuracao:')
        self.stdout.write(f'   Modelo: {modelo_name}')
        self.stdout.write(f'   Confianca: {confianca}')
        
        # Categorias de embalagens
        categorias = {
            39: 'bottle',      # Garrafa (COCO dataset)
            41: 'cup',         # Copo/lata
            47: 'sports ball', # Para detectar objetos redondos (latas)
        }
        
        self.stdout.write(f'\n🏷️  Tipos de embalagem:')
        self.stdout.write(f'   - Garrafas (bottle)')
        self.stdout.write(f'   - Latas/Copos (cup)')
        self.stdout.write(f'   - Objetos redondos (sports ball)')
        
        try:
            from ultralytics import YOLO
            import cv2
            import numpy as np
            from PIL import Image
            
            self.stdout.write(f'\n🚀 Carregando modelo {modelo_name}...')
            
            # Carregar modelo
            if modelo_name == 'ProductScan_v1':
                # Usar modelo treinado
                model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
                if not Path(model_path).exists():
                    self.stdout.write(self.style.ERROR(f'\n✗ Modelo não encontrado: {model_path}'))
                    self.stdout.write('   Execute primeiro: python manage.py treinar_yolo_embalagens')
                    return
                model = YOLO(model_path)
                self.stdout.write(self.style.SUCCESS(f'✓ Modelo ProductScan_v1 carregado (TREINADO)'))
            else:
                # Usar modelo genérico pré-treinado
                model = YOLO(modelo_name)
                self.stdout.write(self.style.SUCCESS(f'✓ Modelo {modelo_name} carregado (PRÉ-TREINADO)'))
            
            # Testar com imagem
            if imagem_path:
                self.testar_imagem(model, imagem_path, confianca)
            
            # Testar com pasta
            elif pasta_path:
                self.testar_pasta(model, pasta_path, confianca)
            
            # Teste rapido com database
            else:
                self.testar_database(model, confianca)
        
        except ImportError:
            self.stdout.write(self.style.ERROR('\n✗ Ultralytics YOLO não instalado'))
            self.stdout.write('   Execute: pip install ultralytics opencv-python pillow')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))

    def testar_imagem(self, model, imagem_path, confianca):
        """Testa modelo em uma única imagem"""
        
        from pathlib import Path
        import cv2
        
        path = Path(imagem_path)
        
        if not path.exists():
            self.stdout.write(self.style.ERROR(f'\n✗ Arquivo não encontrado: {imagem_path}'))
            return
        
        self.stdout.write(f'\n🖼️  Analisando imagem: {path.name}')
        
        # Detectar
        resultados = model.predict(str(path), conf=confianca, verbose=False)
        
        if resultados:
            resultado = resultados[0]
            deteccoes = resultado.boxes
            
            self.stdout.write(f'\n✓ Objetos detectados: {len(deteccoes)}')
            
            for i, box in enumerate(deteccoes):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                
                self.stdout.write(f'   {i+1}. {nome_classe}: {conf*100:.1f}%')
        
        else:
            self.stdout.write('   Nenhum objeto detectado')

    def testar_pasta(self, model, pasta_path, confianca):
        """Testa modelo em pasta com imagens"""
        
        from pathlib import Path
        
        pasta = Path(pasta_path)
        
        if not pasta.exists():
            self.stdout.write(self.style.ERROR(f'\n✗ Pasta não encontrada: {pasta_path}'))
            return
        
        # Buscar imagens
        imagens = list(pasta.glob('*.jpg')) + list(pasta.glob('*.png')) + list(pasta.glob('*.jpeg'))
        
        self.stdout.write(f'\n📁 Analisando pasta: {pasta.name}')
        self.stdout.write(f'   Imagens encontradas: {len(imagens)}')
        
        total_detectadas = 0
        
        for i, img_path in enumerate(imagens[:10], 1):  # Limitar a 10
            self.stdout.write(f'\n   [{i}] {img_path.name}')
            
            resultados = model.predict(str(img_path), conf=confianca, verbose=False)
            
            if resultados:
                resultado = resultados[0]
                deteccoes = resultado.boxes
                total_detectadas += len(deteccoes)
                
                for box in deteccoes:
                    cls = int(box.cls)
                    conf = float(box.conf)
                    nome_classe = resultado.names.get(cls, f'Classe {cls}')
                    self.stdout.write(f'      ✓ {nome_classe}: {conf*100:.1f}%')

    def testar_database(self, model, confianca):
        """Testa modelo com imagens do database (suporta múltiplos produtos por imagem)"""
        
        from verifik.models_anotacao import ImagemUnificada
        from pathlib import Path
        import tempfile
        import os
        
        # Buscar imagens de produtos DIFERENTES (não só BARRIL!)
        produtos_diferentes = ImagemUnificada.objects.filter(
            ativa=True,
            tipo_imagem__in=['original', 'processada']
        ).values('produto_id').distinct()[:8]
        
        imagens = []
        for produto in produtos_diferentes:
            img = ImagemUnificada.objects.filter(
                ativa=True,
                tipo_imagem__in=['original', 'processada'],
                produto_id=produto['produto_id']
            ).first()
            if img:
                imagens.append(img)
        
        # Criar pasta para salvar resultados
        output_dir = Path('deteccoes_multiprodutos')
        output_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\n🗄️  Testando com imagens do database (MULTI-PRODUTO)')
        self.stdout.write(f'   Imagens a testar: {len(imagens)}')
        self.stdout.write(f'   Resultados salvos em: {output_dir.absolute()}')
        self.stdout.write(f'   Tamanho de entrada do modelo: 640x640 (redimensionamento automático)')
        
        total_detectadas = 0
        total_imagens_com_multiplos = 0
        
        for i, img in enumerate(imagens, 1):
            self.stdout.write(f'\n   [{i}] {img.produto.descricao_produto[:40]}')
            
            if not img.arquivo:
                self.stdout.write(f'      ✗ Sem arquivo')
                continue
            
            try:
                # Salvar temporariamente
                img.arquivo.open('rb')
                conteudo = img.arquivo.read()
                img.arquivo.close()
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp.write(conteudo)
                    tmp_path = tmp.name
                
                # PASSO 1: Pré-processamento automático pelo YOLO
                # - Redimensionamento para 640x640
                # - Normalização dos pixels (0-1)  
                # - Conversão para tensor PyTorch
                self.stdout.write(f'      🔄 Pré-processando: resize → 640x640, normalização, tensorização')
                
                # Detectar (inclui todos os passos de pré-processamento)
                resultados = model.predict(tmp_path, conf=confianca, verbose=False)
                
                if resultados:
                    resultado = resultados[0]
                    deteccoes = resultado.boxes
                    total_detectadas += len(deteccoes)
                    
                    # Contar imagens com múltiplos produtos
                    if len(deteccoes) > 1:
                        total_imagens_com_multiplos += 1
                        self.stdout.write(f'      ✓ {len(deteccoes)} PRODUTOS DETECTADOS (MULTI-PRODUTO!)')
                    else:
                        self.stdout.write(f'      ✓ {len(deteccoes)} produto detectado')
                    
                    # Mostrar cada detecção com coordenadas
                    for j, box in enumerate(deteccoes, 1):
                        cls = int(box.cls)
                        conf = float(box.conf)
                        nome_classe = resultado.names.get(cls, f'Classe {cls}')
                        
                        # Coordenadas da bounding box (já redimensionadas para imagem original)
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        w = x2 - x1
                        h = y2 - y1
                        
                        self.stdout.write(f'        [{j}] {nome_classe}: {conf*100:.1f}% - bbox({x1:.0f},{y1:.0f},{w:.0f}x{h:.0f})')
                    
                    # Salvar imagem com detecções
                    output_path = output_dir / f'deteccao_{i}_{len(deteccoes)}produtos_{img.produto.descricao_produto[:15].replace(" ", "_")}.jpg'
                    try:
                        resultado_plotado = resultado.plot()
                        import cv2
                        cv2.imwrite(str(output_path), resultado_plotado)
                        self.stdout.write(f'      💾 Salvo: {output_path.name}')
                        
                        # ABRIR TODAS AS DETECÇÕES AUTOMATICAMENTE
                        if len(deteccoes) > 0:  # Só abre se detectou algo
                            import os
                            os.startfile(str(output_path))
                            self.stdout.write(f'      👁️  ABERTO: {output_path.name}')
                            
                    except Exception as e:
                        self.stdout.write(f'      ⚠️  Erro ao salvar imagem: {str(e)}')
                
                else:
                    self.stdout.write(f'      ✗ Nenhum objeto detectado')
                
                # Limpar
                Path(tmp_path).unlink()
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'      ✗ Erro: {str(e)}'))
                import traceback
                self.stdout.write(self.style.ERROR(f'      Traceback: {traceback.format_exc()[:200]}...'))
        
        self.stdout.write(f'\n📊 RESUMO DA ANÁLISE MULTI-PRODUTO:')
        self.stdout.write(f'   Total de objetos detectados: {total_detectadas}')
        self.stdout.write(f'   Imagens com múltiplos produtos: {total_imagens_com_multiplos}/{len(imagens)} ({total_imagens_com_multiplos/len(imagens)*100:.1f}%)')
        self.stdout.write(f'   Média de produtos por imagem: {total_detectadas/len(imagens):.1f}')
