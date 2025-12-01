#!/usr/bin/env python
"""
Script para processar TODAS as imagens de forma rápida e direta
Remove fundo de todas as imagens não anotadas
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto
from verifik.models_anotacao import ImagemAnotada
from acessorios.processador import ProcessadorImagensGenerico
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json


def processar_todas_imagens():
    """Processa TODAS as imagens não anotadas"""
    
    print("\n" + "="*80)
    print("PROCESSADOR DE TODAS AS IMAGENS - REMOVE FUNDO")
    print("="*80 + "\n")
    
    # Buscar imagens anotadas
    print("📊 Buscando imagens anotadas...")
    anotadas = set()
    for img in ImagemAnotada.objects.all():
        anotadas.add(img.imagem)
    
    print(f"✅ Encontradas {len(anotadas)} imagens anotadas\n")
    
    # Buscar imagens não anotadas
    print("📊 Buscando imagens NÃO anotadas...")
    queryset = ImagemProduto.objects.filter(ativa=True).exclude(imagem__in=anotadas)
    
    total_imagens = queryset.count()
    print(f"✅ Encontradas {total_imagens} imagens para processar\n")
    
    if total_imagens == 0:
        print("⚠️  Nenhuma imagem para processar!")
        return
    
    # Coletar caminhos das imagens
    print("📂 Coletando caminhos das imagens...")
    caminhos = []
    for img in queryset:
        try:
            caminho = Path(f"media/{img.imagem}")
            if caminho.exists():
                caminhos.append(str(caminho))
            else:
                print(f"  ⚠️  Arquivo não encontrado: {caminho}")
        except Exception as e:
            print(f"  ❌ Erro ao processar {img.imagem}: {e}")
    
    print(f"✅ {len(caminhos)} caminhos coletados\n")
    
    if not caminhos:
        print("❌ Nenhuma imagem válida encontrada!")
        return
    
    # Processar em lotes
    lote_size = 100
    total_processados = 0
    total_erros = 0
    
    processador = ProcessadorImagensGenerico()
    
    for lote_num in range(0, len(caminhos), lote_size):
        lote = caminhos[lote_num:lote_num + lote_size]
        lote_atual = (lote_num // lote_size) + 1
        total_lotes = (len(caminhos) + lote_size - 1) // lote_size
        
        print(f"\n📦 Lote {lote_atual}/{total_lotes} ({len(lote)} imagens)")
        print("-" * 80)
        
        try:
            # Processar lote
            resultados, erros = processador.processar_lote(
                'remover_fundo',
                lote,
                prefixo=f'lote_{lote_atual}'
            )
            
            # Registrar no banco
            for resultado in resultados:
                ProcessadorImagensLog.objects.create(
                    tipo='remover_fundo',
                    imagem_original=resultado['original'],
                    imagem_processada=resultado['processada'],
                    status='sucesso',
                    parametros=json.dumps({'lote': lote_atual})
                )
                total_processados += 1
            
            for erro in erros:
                ProcessadorImagensLog.objects.create(
                    tipo='remover_fundo',
                    imagem_original=erro['arquivo'],
                    imagem_processada='',
                    status='erro',
                    mensagem_erro=erro['erro'],
                    parametros=json.dumps({'lote': lote_atual})
                )
                total_erros += 1
            
            print(f"  ✅ Processadas: {len(resultados)}")
            print(f"  ❌ Erros: {len(erros)}")
            print(f"  📊 Total até agora: {total_processados} processadas, {total_erros} erros")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar lote: {e}")
            total_erros += len(lote)
    
    # Resumo final
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    print(f"✅ Total processadas: {total_processados}")
    print(f"❌ Total com erro: {total_erros}")
    print(f"📊 Taxa de sucesso: {(total_processados / (total_processados + total_erros) * 100):.1f}%")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        processar_todas_imagens()
        print("🎉 Processamento concluído com sucesso!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Processamento interrompido pelo usuário!")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
