from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'OCR Simples para reconhecer produtos'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')

    def handle(self, *args, **options):
        imagem_path = options['imagem']

        self.stdout.write('=' * 60)
        self.stdout.write('📖 OCR SIMPLES - RECONHECIMENTO DE PRODUTOS')
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'\n📊 Imagem: {Path(imagem_path).name}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'ocr_simples_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'📁 Pasta: {output_dir.absolute()}')

            # Carregar imagem
            img = cv2.imread(imagem_path)
            altura, largura = img.shape[:2]
            self.stdout.write(f'✓ Imagem carregada: {largura}x{altura}')

            # Aplicar OCR
            self.ocr_rapido(img, output_dir)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def ocr_rapido(self, img, output_dir):
        """OCR rápido com Tesseract"""
        self.stdout.write(f'\n🔍 EXECUTANDO OCR...')
        
        try:
            import pytesseract
            self.stdout.write(f'✓ Tesseract disponível')
        except ImportError:
            self.stdout.write(f'✗ Tesseract não instalado')
            self.stdout.write(f'  Execute: pip install pytesseract')
            return

        # Preparar imagem para OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Aplicar threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Salvar imagem processada
        processed_path = output_dir / 'processada_ocr.jpg'
        cv2.imwrite(str(processed_path), thresh)
        
        try:
            # Configuração Tesseract otimizada para produtos
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%°.'
            
            # Executar OCR
            texto_completo = pytesseract.image_to_string(thresh, config=config, lang='por+eng')
            
            # Processar resultado
            linhas = [linha.strip() for linha in texto_completo.split('\n') if linha.strip()]
            
            self.stdout.write(f'\n📝 TEXTOS ENCONTRADOS ({len(linhas)} linhas):')
            
            textos_encontrados = []
            produtos_identificados = []
            
            # Marcas conhecidas
            marcas = {
                'CORONA': ['corona', 'coronita'],
                'HEINEKEN': ['heineken'],
                'SKOL': ['skol'],
                'BRAHMA': ['brahma'], 
                'ANTARCTICA': ['antarctica'],
                'STELLA': ['stella', 'artois'],
                'BUDWEISER': ['budweiser', 'bud'],
                'DEVASSA': ['devassa'],
                'ORIGINAL': ['original'],
                'ITAIPAVA': ['itaipava'],
                'EISENBAHN': ['eisenbahn']
            }
            
            for i, linha in enumerate(linhas, 1):
                if len(linha) > 2:  # Filtrar linhas muito pequenas
                    textos_encontrados.append(linha)
                    self.stdout.write(f'[{i:2d}] "{linha}"')
                    
                    # Verificar se é produto conhecido
                    linha_lower = linha.lower()
                    for marca, variantes in marcas.items():
                        for variante in variantes:
                            if variante in linha_lower:
                                produtos_identificados.append({
                                    'marca': marca,
                                    'texto_original': linha,
                                    'variante_encontrada': variante
                                })
                                self.stdout.write(f'     🎯 {marca} detectado!')
                                break
            
            # Resumo
            self.stdout.write(f'\n📊 RESUMO:')
            self.stdout.write(f'   Total de textos: {len(textos_encontrados)}')
            self.stdout.write(f'   Produtos identificados: {len(produtos_identificados)}')
            
            if produtos_identificados:
                self.stdout.write(f'\n🏷️  PRODUTOS ENCONTRADOS:')
                produtos_contagem = {}
                for produto in produtos_identificados:
                    marca = produto['marca']
                    produtos_contagem[marca] = produtos_contagem.get(marca, 0) + 1
                
                for marca, count in produtos_contagem.items():
                    self.stdout.write(f'   - {marca}: {count}x')
            
            # Salvar resultados
            resultado = {
                'textos_encontrados': textos_encontrados,
                'produtos_identificados': produtos_identificados,
                'total_textos': len(textos_encontrados),
                'total_produtos': len(produtos_identificados),
                'contagem_produtos': produtos_contagem if produtos_identificados else {}
            }
            
            resultado_path = output_dir / 'resultado_ocr.json'
            with open(resultado_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f'\n💾 Resultado salvo: {resultado_path.name}')
            
            # Abrir imagem processada
            os.startfile(str(processed_path))
            self.stdout.write(f'👁️  Imagem processada aberta!')
            
        except Exception as e:
            self.stdout.write(f'✗ Erro no OCR: {str(e)}')
            # Pode ser que Tesseract não esteja configurado
            self.stdout.write(f'  Verifique se o Tesseract está instalado no sistema')
            self.stdout.write(f'  Download: https://github.com/UB-Mannheim/tesseract/wiki')