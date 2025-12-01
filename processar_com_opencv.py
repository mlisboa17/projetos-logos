#!/usr/bin/env python
"""
Processador de imagens usando OpenCV e técnicas alternativas
Sem dependência do rembg - usa segmentação com OpenCV
"""

import os
import sys
import django
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemAnotada
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json


def remover_fundo_opencv(caminho_entrada, caminho_saida):
    """Remove fundo usando OpenCV - Grabcut segmentation"""
    try:
        # Ler imagem
        img = cv2.imread(str(caminho_entrada))
        if img is None:
            return False, "Não conseguiu ler a imagem"
        
        # Converter para RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Criar máscara inicial
        mask = np.zeros(img.shape[:2], np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        # Definir retângulo (área aproximada do objeto)
        altura, largura = img.shape[:2]
        rect = (10, 10, largura-20, altura-20)
        
        # Aplicar GrabCut
        cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        
        # Criar máscara final
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        # Aplicar máscara à imagem
        img_resultado = img_rgb * mask2[:, :, np.newaxis]
        
        # Converter para PIL e salvar com fundo transparente
        pil_img = Image.fromarray(img_resultado.astype('uint8'))
        
        # Adicionar canal alpha (transparência)
        pil_img_rgba = Image.new("RGBA", pil_img.size)
        pil_img_rgba.paste(pil_img, (0, 0))
        
        pil_img_rgba.save(str(caminho_saida), 'PNG')
        return True, None
        
    except Exception as e:
        return False, str(e)


def processar_com_threshold(caminho_entrada, caminho_saida):
    """Método alternativo: remove cores similares usando threshold"""
    try:
        img = cv2.imread(str(caminho_entrada))
        if img is None:
            return False, "Não conseguiu ler a imagem"
        
        # Converter para HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Definir range para cores de fundo comum (branco/cinza)
        lower_bg = np.array([0, 0, 200])
        upper_bg = np.array([180, 30, 255])
        
        # Criar máscara
        mask = cv2.inRange(hsv, lower_bg, upper_bg)
        mask = cv2.bitwise_not(mask)
        
        # Aplicar operações morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Converter BGR para RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Aplicar máscara
        resultado = img_rgb.copy()
        resultado[mask == 0] = [255, 255, 255]  # Fundo branco
        
        # Salvar
        pil_img = Image.fromarray(resultado.astype('uint8'))
        pil_img.save(str(caminho_saida), 'PNG')
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def processar_imagem_opencv(caminho_original, prefixo):
    """Processa uma imagem com OpenCV"""
    try:
        path_obj = Path(caminho_original)
        pasta_saida = Path('media/processadas')
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        nome_saida = f"{prefixo}_{path_obj.stem}_processada.png"
        caminho_saida = pasta_saida / nome_saida
        
        # Tentar com GrabCut primeiro
        sucesso, erro = remover_fundo_opencv(caminho_original, str(caminho_saida))
        
        if not sucesso:
            # Se falhar, tentar com threshold
            sucesso, erro = processar_com_threshold(caminho_original, str(caminho_saida))
        
        if sucesso:
            return {
                'original': caminho_original,
                'processada': f'processadas/{nome_saida}',
                'tipo': 'remover_fundo'
            }
        else:
            return None, {'arquivo': caminho_original, 'erro': erro}
    
    except Exception as e:
        return None, {'arquivo': caminho_original, 'erro': str(e)}


def processar_todas_opencv():
    """Processa TODAS as imagens usando OpenCV"""
    
    print("\n" + "="*80)
    print("🔧 PROCESSADOR COM OpenCV - REMOVE FUNDO")
    print("="*80 + "\n")
    
    # Verificar se OpenCV está disponível
    print(f"📦 OpenCV versão: {cv2.__version__}")
    print()
    
    # Buscar imagens anotadas
    print("📊 Buscando imagens anotadas...")
    anotadas = set()
    for img in ImagemAnotada.objects.all():
        anotadas.add(img.imagem)
    
    print(f"✅ {len(anotadas)} imagens anotadas\n")
    
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
    
    print("⏳ Iniciando processamento...\n")
    
    for idx, caminho in enumerate(caminhos, 1):
        # Mostrar progresso
        if idx % 50 == 1 or idx == 1:
            porcentagem = (idx / len(caminhos)) * 100
            print(f"\n📦 Processando {idx}/{len(caminhos)} ({porcentagem:.1f}%)")
            print("-" * 80)
        
        try:
            resultado = processar_imagem_opencv(caminho, f'proc_{prefixo_counter:04d}')
            
            if resultado and isinstance(resultado, dict):
                # Registrar sucesso
                ProcessadorImagensLog.objects.create(
                    tipo='remover_fundo',
                    imagem_original=resultado['original'],
                    imagem_processada=resultado['processada'],
                    status='sucesso',
                    parametros=json.dumps({'metodo': 'opencv', 'prefixo': prefixo_counter})
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
                        parametros=json.dumps({'metodo': 'opencv'})
                    )
                total_erros += 1
                print(f"  ❌ {idx}: {Path(caminho).name}")
        
        except Exception as e:
            total_erros += 1
            print(f"  ❌ {idx}: {str(e)[:50]}")
        
        prefixo_counter += 1
    
    # Resumo final
    print("\n" + "="*80)
    print("✅ PROCESSAMENTO CONCLUÍDO COM OpenCV")
    print("="*80)
    print(f"✅ Processadas com sucesso: {total_processados}")
    print(f"❌ Imagens com erro: {total_erros}")
    if total_processados + total_erros > 0:
        taxa = (total_processados / (total_processados + total_erros)) * 100
        print(f"📊 Taxa de sucesso: {taxa:.1f}%")
    print("="*80 + "\n")
    
    return total_processados, total_erros


if __name__ == '__main__':
    try:
        processar_todas_opencv()
        print("🎉 Processamento finalizado!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Processamento interrompido!")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
