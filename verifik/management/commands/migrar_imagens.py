"""
Django Management Command - Migração de Dados de Imagens
Migra dados das tabelas antigas para ImagemUnificada
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from pathlib import Path
from datetime import datetime

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import (
    ImagemProcessada, 
    ImagemAnotada, 
    AnotacaoProduto,
    ImagemUnificada,
    HistoricoTreino
)


class Command(BaseCommand):
    help = 'Migra dados das tabelas antigas (ImagemProduto, ImagemProcessada, ImagemAnotada) para ImagemUnificada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar (apenas simula)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('MIGRACAO DE DADOS - IMAGENS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ MODO DRY-RUN (sem salvar)'))
        
        contagem_original = self.migrar_imagemProduto(dry_run)
        contagem_processada = self.migrar_imagemProcessada(dry_run)
        contagem_anotada = self.migrar_imagemAnotada(dry_run)
        
        # Resumo
        total_migrado = contagem_original + contagem_processada + contagem_anotada
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('RESUMO DA MIGRACAO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total migrado para ImagemUnificada: {total_migrado} imagens'))
        self.stdout.write(f'  - Original (ImagemProduto): {contagem_original}')
        self.stdout.write(f'  - Processada (ImagemProcessada): {contagem_processada}')
        self.stdout.write(f'  - Anotada (ImagemAnotada + AnotacaoProduto): {contagem_anotada}')
        
        if not dry_run:
            final_count = ImagemUnificada.objects.count()
            self.stdout.write(self.style.SUCCESS(f'\n📊 Total de registros em ImagemUnificada: {final_count}'))
            self.stdout.write(self.style.SUCCESS('\n✓ MIGRACAO CONCLUIDA'))
        else:
            self.stdout.write(self.style.WARNING('\n✓ DRY-RUN CONCLUIDO (nada foi salvo)'))
        
        self.stdout.write(self.style.SUCCESS('=' * 80))

    def migrar_imagemProduto(self, dry_run):
        """Migra ImagemProduto → ImagemUnificada (tipo='original')"""
        
        self.stdout.write(self.style.SUCCESS('\n[1/3] Migrando ImagemProduto → ImagemUnificada (tipo="original")...'))
        
        contagem = 0
        erros = []
        
        try:
            imagens_produto = ImagemProduto.objects.all()
            self.stdout.write(f'    Total de ImagemProduto: {imagens_produto.count()}')
            
            for img_produto in imagens_produto:
                try:
                    
                    if img_produto.imagem:
                        try:
                            if not dry_run:
                                # Ler arquivo original
                                img_produto.imagem.open('rb')
                                conteudo = img_produto.imagem.read()
                                img_produto.imagem.close()
                                
                                nome_arquivo = Path(img_produto.imagem.name).name
                                
                                # Criar nova imagem unificada
                                imagem_unificada = ImagemUnificada(
                                    produto=img_produto.produto,
                                    tipo_imagem='original',
                                    descricao=f"Imagem original do produto {img_produto.produto.descricao_produto}",
                                    ativa=True,
                                    status='ativa',
                                    enviado_por=getattr(img_produto, 'enviado_por', None),
                                    data_envio=getattr(img_produto, 'data_envio', None),
                                    created_at=getattr(img_produto, 'data_envio', datetime.now()),
                                )
                                
                                # Salvar arquivo
                                imagem_unificada.arquivo.save(nome_arquivo, ContentFile(conteudo), save=True)
                            
                            contagem += 1
                            if contagem % 50 == 0:
                                self.stdout.write(f'    ✓ Processadas {contagem} imagens...')
                        
                        except Exception as e:
                            erro_msg = f"Erro ao copiar arquivo de ImagemProduto {img_produto.id}: {str(e)}"
                            erros.append(erro_msg)
                            self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                            continue
                
                except Exception as e:
                    erro_msg = f"Erro ao migrar ImagemProduto {img_produto.id}: {str(e)}"
                    erros.append(erro_msg)
                    self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ ImagemProduto migradas: {contagem}'))
            if erros:
                self.stdout.write(self.style.WARNING(f'⚠ Erros encontrados: {len(erros)}'))
                for erro in erros[:5]:
                    self.stdout.write(f'  - {erro}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ ERRO CRÍTICO: {str(e)}'))
            import traceback
            traceback.print_exc()
        
        return contagem

    def migrar_imagemProcessada(self, dry_run):
        """Migra ImagemProcessada → ImagemUnificada (tipo='processada')"""
        
        self.stdout.write(self.style.SUCCESS('\n[2/3] Migrando ImagemProcessada → ImagemUnificada (tipo="processada")...'))
        
        contagem = 0
        erros = []
        
        try:
            imagens_processadas = ImagemProcessada.objects.all()
            self.stdout.write(f'    Total de ImagemProcessada: {imagens_processadas.count()}')
            
            for img_proc in imagens_processadas:
                try:
                    
                    if img_proc.imagem_processada:
                        try:
                            if not dry_run:
                                # Ler arquivo
                                img_proc.imagem_processada.open('rb')
                                conteudo = img_proc.imagem_processada.read()
                                img_proc.imagem_processada.close()
                                
                                nome_arquivo = Path(img_proc.imagem_processada.name).name
                                
                                # Encontrar a imagem original migrada
                                imagem_original = ImagemUnificada.objects.filter(
                                    produto=img_proc.imagem_original.produto,
                                    tipo_imagem='original'
                                ).first()
                                
                                # Criar nova imagem unificada
                                imagem_unificada = ImagemUnificada(
                                    produto=img_proc.imagem_original.produto,
                                    tipo_imagem='processada',
                                    tipo_processamento=img_proc.tipo_processamento,
                                    imagem_original=imagem_original,
                                    descricao=img_proc.descricao or 'Processada (fundo removido)',
                                    ativa=True,
                                    status='ativa',
                                    created_at=img_proc.data_criacao,
                                )
                                
                                # Salvar arquivo
                                imagem_unificada.arquivo.save(nome_arquivo, ContentFile(conteudo), save=True)
                            
                            contagem += 1
                            if contagem % 50 == 0:
                                self.stdout.write(f'    ✓ Processadas {contagem} imagens...')
                        
                        except Exception as e:
                            erro_msg = f"Erro ao copiar arquivo de ImagemProcessada {img_proc.id}: {str(e)}"
                            erros.append(erro_msg)
                            self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                            continue
                
                except Exception as e:
                    erro_msg = f"Erro ao migrar ImagemProcessada {img_proc.id}: {str(e)}"
                    erros.append(erro_msg)
                    self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ ImagemProcessada migradas: {contagem}'))
            if erros:
                self.stdout.write(self.style.WARNING(f'⚠ Erros encontrados: {len(erros)}'))
                for erro in erros[:5]:
                    self.stdout.write(f'  - {erro}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ ERRO CRÍTICO: {str(e)}'))
            import traceback
            traceback.print_exc()
        
        return contagem

    def migrar_imagemAnotada(self, dry_run):
        """Migra ImagemAnotada + AnotacaoProduto → ImagemUnificada (tipo='anotada')"""
        
        self.stdout.write(self.style.SUCCESS('\n[3/3] Migrando ImagemAnotada + AnotacaoProduto → ImagemUnificada (tipo="anotada")...'))
        
        contagem = 0
        erros = []
        
        try:
            imagens_anotadas = ImagemAnotada.objects.all()
            self.stdout.write(f'    Total de ImagemAnotada: {imagens_anotadas.count()}')
            
            for img_anotada in imagens_anotadas:
                try:
                    anotacoes = AnotacaoProduto.objects.filter(imagem_anotada=img_anotada)
                    
                    for anotacao in anotacoes:
                        try:
                            
                            if img_anotada.imagem:
                                try:
                                    if not dry_run:
                                        # Ler arquivo
                                        img_anotada.imagem.open('rb')
                                        conteudo = img_anotada.imagem.read()
                                        img_anotada.imagem.close()
                                        
                                        nome_arquivo = Path(img_anotada.imagem.name).name
                                        nome_arquivo = f"anotada_{anotacao.produto.id}_{nome_arquivo}"
                                        
                                        # Criar nova imagem unificada
                                        imagem_unificada = ImagemUnificada(
                                            produto=anotacao.produto,
                                            tipo_imagem='anotada',
                                            descricao=f"Anotada - {anotacao.produto.descricao_produto}",
                                            ativa=True,
                                            status=img_anotada.status,
                                            total_anotacoes=1,
                                            bbox_x=anotacao.bbox_x,
                                            bbox_y=anotacao.bbox_y,
                                            bbox_width=anotacao.bbox_width,
                                            bbox_height=anotacao.bbox_height,
                                            confianca=anotacao.confianca,
                                            observacoes=anotacao.observacoes or img_anotada.observacoes,
                                            enviado_por=img_anotada.enviado_por,
                                            aprovado_por=img_anotada.aprovado_por,
                                            data_envio=img_anotada.data_envio,
                                            data_aprovacao=img_anotada.data_aprovacao,
                                            created_at=img_anotada.data_envio or datetime.now(),
                                        )
                                        
                                        # Salvar arquivo
                                        imagem_unificada.arquivo.save(nome_arquivo, ContentFile(conteudo), save=True)
                                    
                                    contagem += 1
                                    if contagem % 50 == 0:
                                        self.stdout.write(f'    ✓ Processadas {contagem} anotacoes...')
                                
                                except Exception as e:
                                    erro_msg = f"Erro ao copiar arquivo de ImagemAnotada {img_anotada.id}: {str(e)}"
                                    erros.append(erro_msg)
                                    self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                                    continue
                        
                        except Exception as e:
                            erro_msg = f"Erro ao migrar anotacao {anotacao.id}: {str(e)}"
                            erros.append(erro_msg)
                            self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                            continue
                
                except Exception as e:
                    erro_msg = f"Erro ao processar ImagemAnotada {img_anotada.id}: {str(e)}"
                    erros.append(erro_msg)
                    self.stdout.write(self.style.ERROR(f'    ✗ {erro_msg}'))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ ImagemAnotada migradas: {contagem}'))
            if erros:
                self.stdout.write(self.style.WARNING(f'⚠ Erros encontrados: {len(erros)}'))
                for erro in erros[:5]:
                    self.stdout.write(f'  - {erro}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ ERRO CRÍTICO: {str(e)}'))
            import traceback
            traceback.print_exc()
        
        return contagem
