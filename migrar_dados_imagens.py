"""
SCRIPT DE MIGRACAO DE DADOS
Migra dados das tabelas antigas para ImagemUnificada

Fluxo:
1. ImagemProduto → ImagemUnificada (tipo_imagem='original')
2. ImagemProcessada → ImagemUnificada (tipo_imagem='processada')
3. ImagemAnotada + AnotacaoProduto → ImagemUnificada (tipo_imagem='anotada')
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).resolve().parent))
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import (
    ImagemProcessada, 
    ImagemAnotada, 
    AnotacaoProduto,
    ImagemUnificada,
    HistoricoTreino
)
from django.core.files.base import ContentFile
import shutil
from datetime import datetime

print("=" * 80)
print("MIGRACAO DE DADOS - IMAGENS")
print("=" * 80)

# ============================================================================
# 1. MIGRAR ImagemProduto → ImagemUnificada (original)
# ============================================================================

print("\n[1/3] Migrando ImagemProduto → ImagemUnificada (tipo='original')...")

contagem_original = 0
erros_original = []

try:
    imagens_produto = ImagemProduto.objects.all()
    print(f"    Total de ImagemProduto: {imagens_produto.count()}")
    
    for img_produto in imagens_produto:
        try:
            if ImagemUnificada.objects.filter(
                produto=img_produto.produto,
                tipo_imagem='original',
                ordem=img_produto.ordem if hasattr(img_produto, 'ordem') else 0
            ).exists():
                print(f"    ⊘ Pulando duplicada: {img_produto.id} (produto: {img_produto.produto.descricao_produto})")
                continue
            
            # Copiar arquivo
            novo_arquivo = None
            if img_produto.imagem:
                try:
                    # Ler arquivo original
                    img_produto.imagem.open('rb')
                    conteudo = img_produto.imagem.read()
                    img_produto.imagem.close()
                    
                    # Nome do arquivo
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
                    
                    contagem_original += 1
                    if contagem_original % 50 == 0:
                        print(f"    ✓ Processadas {contagem_original} imagens...")
                    
                except Exception as e:
                    erro_msg = f"Erro ao copiar arquivo de ImagemProduto {img_produto.id}: {str(e)}"
                    erros_original.append(erro_msg)
                    print(f"    ✗ {erro_msg}")
                    continue
        
        except Exception as e:
            erro_msg = f"Erro ao migrar ImagemProduto {img_produto.id}: {str(e)}"
            erros_original.append(erro_msg)
            print(f"    ✗ {erro_msg}")
            continue
    
    print(f"\n✓ ImagemProduto migradas: {contagem_original}")
    if erros_original:
        print(f"⚠ Erros encontrados: {len(erros_original)}")
        for erro in erros_original[:5]:  # Mostrar primeiros 5
            print(f"  - {erro}")

except Exception as e:
    print(f"✗ ERRO CRÍTICO na migração de ImagemProduto: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 2. MIGRAR ImagemProcessada → ImagemUnificada (processada)
# ============================================================================

print("\n[2/3] Migrando ImagemProcessada → ImagemUnificada (tipo='processada')...")

contagem_processada = 0
erros_processada = []

try:
    imagens_processadas = ImagemProcessada.objects.all()
    print(f"    Total de ImagemProcessada: {imagens_processadas.count()}")
    
    for img_proc in imagens_processadas:
        try:
            # Verificar duplicada
            if ImagemUnificada.objects.filter(
                produto=img_proc.imagem_original.produto,
                tipo_imagem='processada',
                imagem_original__isnull=False  # Referencia a original
            ).exists():
                print(f"    ⊘ Pulando duplicada: {img_proc.id}")
                continue
            
            if img_proc.imagem_processada:
                try:
                    # Ler arquivo
                    img_proc.imagem_processada.open('rb')
                    conteudo = img_proc.imagem_processada.read()
                    img_proc.imagem_processada.close()
                    
                    nome_arquivo = Path(img_proc.imagem_processada.name).name
                    
                    # Encontrar a imagem original migrada em ImagemUnificada
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
                        descricao=img_proc.descricao or f"Processada (fundo removido)",
                        ativa=True,
                        status='ativa',
                        data_criacao=img_proc.data_criacao,
                        created_at=img_proc.data_criacao,
                    )
                    
                    # Salvar arquivo
                    imagem_unificada.arquivo.save(nome_arquivo, ContentFile(conteudo), save=True)
                    
                    contagem_processada += 1
                    if contagem_processada % 50 == 0:
                        print(f"    ✓ Processadas {contagem_processada} imagens...")
                
                except Exception as e:
                    erro_msg = f"Erro ao copiar arquivo de ImagemProcessada {img_proc.id}: {str(e)}"
                    erros_processada.append(erro_msg)
                    print(f"    ✗ {erro_msg}")
                    continue
        
        except Exception as e:
            erro_msg = f"Erro ao migrar ImagemProcessada {img_proc.id}: {str(e)}"
            erros_processada.append(erro_msg)
            print(f"    ✗ {erro_msg}")
            continue
    
    print(f"\n✓ ImagemProcessada migradas: {contagem_processada}")
    if erros_processada:
        print(f"⚠ Erros encontrados: {len(erros_processada)}")
        for erro in erros_processada[:5]:
            print(f"  - {erro}")

except Exception as e:
    print(f"✗ ERRO CRÍTICO na migração de ImagemProcessada: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 3. MIGRAR ImagemAnotada + AnotacaoProduto → ImagemUnificada (anotada)
# ============================================================================

print("\n[3/3] Migrando ImagemAnotada + AnotacaoProduto → ImagemUnificada (tipo='anotada')...")

contagem_anotada = 0
erros_anotada = []

try:
    imagens_anotadas = ImagemAnotada.objects.all()
    print(f"    Total de ImagemAnotada: {imagens_anotadas.count()}")
    
    for img_anotada in imagens_anotadas:
        try:
            # Para cada ImagemAnotada com multiplas anotacoes,
            # criar uma ImagemUnificada POR ANOTACAO (produto)
            anotacoes = AnotacaoProduto.objects.filter(imagem_anotada=img_anotada)
            
            for anotacao in anotacoes:
                try:
                    # Verificar duplicada
                    if ImagemUnificada.objects.filter(
                        produto=anotacao.produto,
                        tipo_imagem='anotada',
                        bbox_x=anotacao.bbox_x,
                        bbox_y=anotacao.bbox_y
                    ).exists():
                        continue
                    
                    if img_anotada.imagem:
                        try:
                            # Ler arquivo
                            img_anotada.imagem.open('rb')
                            conteudo = img_anotada.imagem.read()
                            img_anotada.imagem.close()
                            
                            nome_arquivo = Path(img_anotada.imagem.name).name
                            # Adicionar nome do produto ao arquivo
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
                            
                            contagem_anotada += 1
                            if contagem_anotada % 50 == 0:
                                print(f"    ✓ Processadas {contagem_anotada} anotacoes...")
                        
                        except Exception as e:
                            erro_msg = f"Erro ao copiar arquivo de ImagemAnotada {img_anotada.id}: {str(e)}"
                            erros_anotada.append(erro_msg)
                            print(f"    ✗ {erro_msg}")
                            continue
                
                except Exception as e:
                    erro_msg = f"Erro ao migrar anotacao {anotacao.id}: {str(e)}"
                    erros_anotada.append(erro_msg)
                    print(f"    ✗ {erro_msg}")
                    continue
        
        except Exception as e:
            erro_msg = f"Erro ao processar ImagemAnotada {img_anotada.id}: {str(e)}"
            erros_anotada.append(erro_msg)
            print(f"    ✗ {erro_msg}")
            continue
    
    print(f"\n✓ ImagemAnotada migradas: {contagem_anotada}")
    if erros_anotada:
        print(f"⚠ Erros encontrados: {len(erros_anotada)}")
        for erro in erros_anotada[:5]:
            print(f"  - {erro}")

except Exception as e:
    print(f"✗ ERRO CRÍTICO na migração de ImagemAnotada: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO DA MIGRACAO")
print("=" * 80)

total_migrado = contagem_original + contagem_processada + contagem_anotada
total_erros = len(erros_original) + len(erros_processada) + len(erros_anotada)

print(f"\n✓ Total migrado para ImagemUnificada: {total_migrado} imagens")
print(f"  - Original (ImagemProduto): {contagem_original}")
print(f"  - Processada (ImagemProcessada): {contagem_processada}")
print(f"  - Anotada (ImagemAnotada + AnotacaoProduto): {contagem_anotada}")

if total_erros > 0:
    print(f"\n⚠ Total de erros: {total_erros}")
    print(f"  - Erros em original: {len(erros_original)}")
    print(f"  - Erros em processada: {len(erros_processada)}")
    print(f"  - Erros em anotada: {len(erros_anotada)}")

# Contar resultado final
final_count = ImagemUnificada.objects.count()
print(f"\n📊 Total de registros em ImagemUnificada: {final_count}")

print("\n✓ MIGRACAO CONCLUIDA")
print("=" * 80)
