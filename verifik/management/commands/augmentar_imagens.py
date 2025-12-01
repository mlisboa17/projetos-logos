"""
AUGMENTACAO DE IMAGENS
Gera variações de imagens (rotacao, flip, zoom, brightness, contrast)
e salva diretamente em ImagemUnificada com tipo_imagem='augmentada'
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from pathlib import Path
from PIL import Image, ImageEnhance
import io
import random
from datetime import datetime

from verifik.models_anotacao import ImagemUnificada


class Command(BaseCommand):
    help = 'Gera augmentacoes de imagens e salva em ImagemUnificada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantidade',
            type=int,
            default=5,
            help='Quantas variações gerar por imagem original (default: 5)'
        )
        parser.add_argument(
            '--tipos',
            type=str,
            default='rotacao,flip,zoom,brightness,contrast',
            help='Tipos de augmentacao separados por virgula'
        )
        parser.add_argument(
            '--max-por-produto',
            type=int,
            default=50,
            help='Máximo de augmentacoes por produto (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula sem salvar'
        )

    def handle(self, *args, **options):
        quantidade = options['quantidade']
        tipos_str = options['tipos']
        max_por_produto = options['max_por_produto']
        dry_run = options['dry_run']
        
        tipos_augmentacao = [t.strip() for t in tipos_str.split(',')]
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('AUGMENTACAO DE IMAGENS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ MODO DRY-RUN (sem salvar)'))
        
        self.stdout.write(f'\n📊 Configuracao:')
        self.stdout.write(f'  - Variacoes por imagem: {quantidade}')
        self.stdout.write(f'  - Tipos: {", ".join(tipos_augmentacao)}')
        self.stdout.write(f'  - Maximo por produto: {max_por_produto}')
        
        # Buscar imagens originais e processadas
        imagens_base = ImagemUnificada.objects.filter(
            tipo_imagem__in=['original', 'processada'],
            ativa=True
        ).select_related('produto')
        
        total_base = imagens_base.count()
        self.stdout.write(f'\n🖼️  Imagens base encontradas: {total_base}')
        
        total_criadas = 0
        total_erros = 0
        produtos_processados = {}
        
        for img_base in imagens_base:
            produto_id = img_base.produto.id
            
            # Verificar limite por produto
            if produto_id not in produtos_processados:
                produtos_processados[produto_id] = 0
            
            if produtos_processados[produto_id] >= max_por_produto:
                continue
            
            # Contar augmentacoes ja existentes deste produto
            aug_existentes = ImagemUnificada.objects.filter(
                produto=img_base.produto,
                tipo_imagem='augmentada'
            ).count()
            
            if aug_existentes >= max_por_produto:
                continue
            
            # Gerar variações
            for i in range(quantidade):
                if produtos_processados[produto_id] >= max_por_produto:
                    break
                
                try:
                    tipo_escolhido = random.choice(tipos_augmentacao)
                    
                    if not img_base.arquivo:
                        self.stdout.write(self.style.ERROR(f'    ✗ Arquivo nao encontrado: {img_base.id}'))
                        total_erros += 1
                        continue
                    
                    # Abrir imagem original
                    img_base.arquivo.open('rb')
                    img = Image.open(img_base.arquivo)
                    img.load()  # Carregar dados
                    
                    # Aplicar transformacao
                    img_aumentada = self.aplicar_augmentacao(
                        img,
                        tipo_escolhido,
                        i
                    )
                    
                    if img_aumentada is None:
                        img_base.arquivo.close()
                        total_erros += 1
                        continue
                    
                    # Converter para bytes
                    output = io.BytesIO()
                    format_img = img.format or 'PNG'
                    img_aumentada.save(output, format=format_img)
                    output.seek(0)
                    conteudo = output.getvalue()
                    
                    img_base.arquivo.close()
                    
                    if not dry_run:
                        # Criar novo registro em ImagemUnificada
                        nome_arquivo = Path(img_base.arquivo.name).stem
                        ext = Path(img_base.arquivo.name).suffix
                        novo_nome = f"aug_{tipo_escolhido}_{i}_{nome_arquivo}{ext}"
                        
                        imagem_augmentada = ImagemUnificada(
                            produto=img_base.produto,
                            tipo_imagem='augmentada',
                            tipo_augmentacao=tipo_escolhido,
                            foi_augmentada=True,
                            imagem_original=img_base,
                            descricao=f"Augmentada: {tipo_escolhido} (variacao {i+1})",
                            ativa=True,
                            status='ativa',
                            created_at=timezone.now(),
                        )
                        
                        # Salvar arquivo
                        imagem_augmentada.arquivo.save(novo_nome, ContentFile(conteudo), save=True)
                    
                    total_criadas += 1
                    produtos_processados[produto_id] += 1
                    
                    if total_criadas % 25 == 0:
                        self.stdout.write(f'    ✓ Criadas {total_criadas} augmentacoes...')
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erro ao augmentar {img_base.id}: {str(e)}'))
                    total_erros += 1
                    continue
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('RESUMO DA AUGMENTACAO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total de augmentacoes criadas: {total_criadas}'))
        self.stdout.write(f'⚠ Total de erros: {total_erros}')
        self.stdout.write(f'📊 Produtos processados: {len(produtos_processados)}')
        
        if not dry_run:
            aug_count = ImagemUnificada.objects.filter(tipo_imagem='augmentada').count()
            self.stdout.write(self.style.SUCCESS(f'\n📊 Total de augmentacoes no banco: {aug_count}'))
        else:
            self.stdout.write(self.style.WARNING('\n✓ DRY-RUN CONCLUIDO (nada foi salvo)'))
        
        self.stdout.write(self.style.SUCCESS('=' * 80))

    def aplicar_augmentacao(self, img, tipo, variacao):
        """Aplica transformacao a imagem"""
        try:
            # Garantir RGB
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            if tipo == 'rotacao':
                # Rotacao: 15, 30, 45 graus
                angulos = [15, 30, 45]
                angulo = angulos[variacao % len(angulos)]
                return img.rotate(angulo, expand=False, fillcolor=(255, 255, 255))
            
            elif tipo == 'flip':
                # Flip: horizontal, vertical, ambos
                flips = ['horizontal', 'vertical', 'ambos']
                flip_tipo = flips[variacao % len(flips)]
                
                if flip_tipo == 'horizontal':
                    return img.transpose(Image.FLIP_LEFT_RIGHT)
                elif flip_tipo == 'vertical':
                    return img.transpose(Image.FLIP_TOP_BOTTOM)
                else:  # ambos
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    return img.transpose(Image.FLIP_TOP_BOTTOM)
            
            elif tipo == 'zoom':
                # Zoom: 1.1x, 1.2x, 1.3x
                fatores = [1.1, 1.2, 1.3]
                fator = fatores[variacao % len(fatores)]
                
                novo_tamanho = (
                    int(img.width * fator),
                    int(img.height * fator)
                )
                img_zoom = img.resize(novo_tamanho, Image.LANCZOS)
                
                # Crop para tamanho original
                esquerda = (img_zoom.width - img.width) // 2
                topo = (img_zoom.height - img.height) // 2
                direita = esquerda + img.width
                fundo = topo + img.height
                
                return img_zoom.crop((esquerda, topo, direita, fundo))
            
            elif tipo == 'brightness':
                # Brightness: 0.7x, 0.85x, 1.15x, 1.3x
                fatores = [0.7, 0.85, 1.15, 1.3]
                fator = fatores[variacao % len(fatores)]
                
                enhancer = ImageEnhance.Brightness(img)
                return enhancer.enhance(fator)
            
            elif tipo == 'contrast':
                # Contrast: 0.7x, 0.85x, 1.15x, 1.3x
                fatores = [0.7, 0.85, 1.15, 1.3]
                fator = fatores[variacao % len(fatores)]
                
                enhancer = ImageEnhance.Contrast(img)
                return enhancer.enhance(fator)
            
            elif tipo == 'saturacao':
                # Saturacao: 0.5x, 0.75x, 1.25x, 1.5x
                fatores = [0.5, 0.75, 1.25, 1.5]
                fator = fatores[variacao % len(fatores)]
                
                enhancer = ImageEnhance.Color(img)
                return enhancer.enhance(fator)
            
            elif tipo == 'nitidez':
                # Nitidez: 0.5x, 0.75x, 1.25x, 1.5x
                fatores = [0.5, 0.75, 1.25, 1.5]
                fator = fatores[variacao % len(fatores)]
                
                enhancer = ImageEnhance.Sharpness(img)
                return enhancer.enhance(fator)
            
            else:
                return img
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Erro ao aplicar {tipo}: {str(e)}'))
            return None
