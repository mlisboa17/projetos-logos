#!/usr/bin/env python
"""
Script otimizado para processar TODAS as imagens com remoção de fundo
Versão rápida e eficiente
"""

import os
import sys
import django
from pathlib import Path
from PIL import Image
import numpy as np

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemAnotada
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json

# Importar rembg apenas quando necessário
try:
    from rembg import remove
    REMBG_DISPONIVEL = True
except ImportError:
    REMBG_DISPONIVEL = False
    print("⚠️  rembg não está instalado. Usando método alternativo (apenas redimensionamento).")


def remover_fundo_rembg(caminho_entrada, caminho_saida):
    """Remove fundo usando rembg"""
    try:
        input_image = Image.open(caminho_entrada)
        output_image = remove(input_image)
        output_image.save(caminho_saida)
        return True, None
    except Exception as e:
        return False, str(e)


def redimensionar_otimizado(caminho_entrada, caminho_saida, tamanho=(512, 512)):
    """Redimensiona imagem de forma otimizada"""
    try:
        img = Image.open(caminho_entrada)
        
        # Converter para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar mantendo proporção
        img.thumbnail(tamanho, Image.Resampling.LANCZOS)
        
        # Criar imagem com fundo branco
        nova_img = Image.new('RGB', tamanho, (255, 255, 255))
        
        # Centralizar imagem
        offset = ((tamanho[0] - img.width) // 2, (tamanho[1] - img.height) // 2)
        nova_img.paste(img, offset)
        
        nova_img.save(caminho_saida, quality=85, optimize=True)
        return True, None
    except Exception as e:
        return False, str(e)


def processar_imagem(caminho_original, prefixo, tipo='remover_fundo'):
    """Processa uma imagem individual"""
    try:
        # Criar nomes de saída
        path_obj = Path(caminho_original)
        pasta_saida = Path('media/processadas')
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        nome_saida = f"{prefixo}_{path_obj.stem}_processada.png"
        caminho_saida = pasta_saida / nome_saida
        
        # Processar baseado no tipo
        if tipo == 'remover_fundo' and REMBG_DISPONIVEL:
            sucesso, erro = remover_fundo_rembg(caminho_original, str(caminho_saida))
        else:
            # Usar método alternativo (redimensionamento + otimização)
            sucesso, erro = redimensionar_otimizado(caminho_original, str(caminho_saida))
        
        if sucesso:
            return {
                'original': caminho_original,
                'processada': f'processadas/{nome_saida}',
                'tipo': tipo
            }
        else:
            return None, {'arquivo': caminho_original, 'erro': erro}
    
    except Exception as e:
        return None, {'arquivo': caminho_original, 'erro': str(e)}


def processar_todas_imagens_rapido():
    """Processa TODAS as imagens de forma rápida"""
    
    print("\n" + "="*80)
    print("⚡ PROCESSADOR RÁPIDO - TODAS AS IMAGENS")
    print("="*80 + "\n")
    
    # Buscar imagens anotadas
    print("📊 Buscando imagens anotadas...")
    anotadas = set()
    for img in ImagemAnotada.objects.all():
        anotadas.add(img.imagem)
    
    print(f"✅ {len(anotadas)} imagens anotadas encontradas\n")
    
    # Buscar imagens não anotadas
    print("📊 Buscando imagens não anotadas...")
    queryset = ImagemProduto.objects.filter(ativa=True).exclude(imagem__in=anotadas)
    
    total_imagens = queryset.count()
    print(f"✅ {total_imagens} imagens para processar\n")
    
    if total_imagens == 0:
        print("⚠️  Nenhuma imagem para processar!")
        return
    
    # Coletar caminhos
    print("📂 Coletando caminhos...")
    caminhos = []
    for img in queryset:
        try:
            caminho = Path(f"media/{img.imagem}")
            if caminho.exists():
                caminhos.append(str(caminho))
        except:
            pass
    
    print(f"✅ {len(caminhos)} caminhos válidos\n")
    
    if not caminhos:
        print("❌ Nenhuma imagem válida!")
        return
    
    # Processar
    total_processados = 0
    total_erros = 0
    prefixo_counter = 1
    
    for idx, caminho in enumerate(caminhos, 1):
        # Mostrar progresso a cada 50 imagens
        if idx % 50 == 1:
            print(f"\n📦 Processando imagens {idx}-{min(idx+49, len(caminhos))} de {len(caminhos)}")
            print("-" * 80)
        
        try:
            resultado = processar_imagem(caminho, f'proc_{prefixo_counter:04d}', 'remover_fundo')
            
            if resultado and isinstance(resultado, dict):
                # Registrar sucesso
                ProcessadorImagensLog.objects.create(
                    tipo='remover_fundo',
                    imagem_original=resultado['original'],
                    imagem_processada=resultado['processada'],
                    status='sucesso',
                    parametros=json.dumps({'prefixo': prefixo_counter})
                )
                total_processados += 1
                print(f"  ✅ {idx}: {Path(caminho).name}")
            else:
                # Registrar erro
                if isinstance(resultado, tuple):
                    _, erro_info = resultado
                    ProcessadorImagensLog.objects.create(
                        tipo='remover_fundo',
                        imagem_original=caminho,
                        imagem_processada='',
                        status='erro',
                        mensagem_erro=erro_info.get('erro', 'Erro desconhecido'),
                        parametros=json.dumps({'prefixo': prefixo_counter})
                    )
                total_erros += 1
                print(f"  ❌ {idx}: {Path(caminho).name}")
        
        except Exception as e:
            total_erros += 1
            print(f"  ❌ {idx}: Erro - {str(e)[:50]}")
        
        prefixo_counter += 1
    
    # Resumo
    print("\n" + "="*80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("="*80)
    print(f"✅ Processadas: {total_processados}")
    print(f"❌ Erros: {total_erros}")
    if total_processados + total_erros > 0:
        taxa = (total_processados / (total_processados + total_erros)) * 100
        print(f"📊 Taxa de sucesso: {taxa:.1f}%")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        processar_todas_imagens_rapido()
        print("🎉 Concluído!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
