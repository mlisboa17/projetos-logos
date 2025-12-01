from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import os


class Command(BaseCommand):
    help = 'Teste uma imagem específica com ProductScan_v1'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho completo da imagem')
        parser.add_argument('--confianca', type=float, default=0.3,
                          help='Confiança mínima')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        confianca = options['confianca']

        self.stdout.write('=' * 80)
        self.stdout.write(f'🎯 TESTE IMAGEM ÚNICA - ProductScan_v1')
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Confiança: {confianca}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            from ultralytics import YOLO
            
            # Carregar ProductScan_v1
            model_path = r'C:\dataset_yolo_verifik\yolo_embalagens_best.pt'
            if not Path(model_path).exists():
                self.stdout.write(self.style.ERROR(f'✗ ProductScan_v1 não encontrado: {model_path}'))
                return
                
            model = YOLO(model_path)
            self.stdout.write(self.style.SUCCESS(f'✓ ProductScan_v1 carregado'))

            # Fazer detecção
            self.stdout.write(f'\n🔍 Executando detecção...')
            resultados = model.predict(imagem_path, conf=confianca, verbose=False)
            
            if not resultados or len(resultados) == 0:
                self.stdout.write(f'❌ Nenhum resultado')
                return
                
            resultado = resultados[0]
            boxes = resultado.boxes
            
            if boxes is None or len(boxes) == 0:
                self.stdout.write(f'❌ Nenhum objeto detectado')
                return
            
            # Mostrar detecções
            self.stdout.write(f'\n🎯 DETECÇÕES ENCONTRADAS: {len(boxes)}')
            
            for i, box in enumerate(boxes, 1):
                cls = int(box.cls)
                conf = float(box.conf)
                nome_classe = resultado.names.get(cls, f'Classe {cls}')
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                w, h = x2 - x1, y2 - y1
                
                self.stdout.write(f'\n   [{i}] {nome_classe}')
                self.stdout.write(f'       Confiança: {conf*100:.1f}%')
                self.stdout.write(f'       Posição: x={x1:.0f}, y={y1:.0f}')
                self.stdout.write(f'       Tamanho: {w:.0f}x{h:.0f}')
            
            # Salvar resultado
            output_dir = Path('teste_imagem_unica')
            output_dir.mkdir(exist_ok=True)
            
            # Imagem original
            img_original = cv2.imread(imagem_path)
            original_path = output_dir / 'original.jpg'
            cv2.imwrite(str(original_path), img_original)
            
            # Imagem com detecções
            resultado_plotado = resultado.plot()
            resultado_path = output_dir / 'deteccao_resultado.jpg'
            cv2.imwrite(str(resultado_path), resultado_plotado)
            
            self.stdout.write(f'\n💾 Arquivos salvos:')
            self.stdout.write(f'   - original.jpg')
            self.stdout.write(f'   - deteccao_resultado.jpg')
            self.stdout.write(f'   📁 Pasta: {output_dir.absolute()}')
            
            # Abrir resultado automaticamente
            os.startfile(str(resultado_path))
            self.stdout.write(f'\n👁️  RESULTADO ABERTO!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()