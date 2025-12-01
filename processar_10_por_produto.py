#!/usr/bin/env python
"""
Processador otimizado - 10 imagens por produto
Rápido e eficiente usando Pillow
"""

import os
import sys
import django
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import warnings
warnings.filterwarnings('ignore')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import ImagemAnotada
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json


def otimizar_imagem(caminho_entrada, caminho_saida):
    """Otimiza imagem: redimensiona, melhora contraste e qualidade"""
    try:
        # Abrir imagem
        img = Image.open(caminho_entrada)
        
        # Converter para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar para tamanho padrão (mantendo proporção)
        tamanho_max = 512
        img.thumbnail((tamanho_max, tamanho_max), Image.Resampling.LANCZOS)
        
        # Melhorar contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Melhorar brilho
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Melhorar nitidez
        img = img.filter(ImageFilter.SHARPEN)
        
        # Salvar com compressão
        img.save(str(caminho_saida), 'JPEG', quality=85, optimize=True)
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def processar_10_por_produto():
    """Processa 10 imagens de cada produto"""
    
    print("\n" + "="*80)
    print("⚡ PROCESSADOR RÁPIDO - 10 IMAGENS POR PRODUTO")
    print("="*80 + "\n")
    
    # Buscar imagens anotadas
    print("📊 Buscando imagens anotadas...")
    anotadas = set()
    for img in ImagemAnotada.objects.all():
        anotadas.add(img.imagem)
    
    print(f"✅ {len(anotadas)} imagens anotadas\n")
    
    # Buscar todos os produtos
    print("📦 Buscando produtos...")
    produtos = ProdutoMae.objects.all()
    total_produtos = produtos.count()
    print(f"✅ {total_produtos} produtos encontrados\n")
    
    if total_produtos == 0:
        print("❌ Nenhum produto!")
        return
    
    # Processar
    total_processados = 0
    total_erros = 0
    total_pulados = 0
    prefixo_counter = 1
    
    pasta_saida = Path('media/processadas')
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    print(f"⏳ Processando 10 imagens de cada um dos {total_produtos} produtos...\n")
    
    for prod_idx, produto in enumerate(produtos, 1):
        # Buscar imagens do produto (máximo 10)
        imagens = ImagemProduto.objects.filter(
            produto=produto,
            ativa=True
        ).exclude(imagem__in=anotadas)[:10]  # Apenas 10 primeiras
        
        if imagens.count() == 0:
            total_pulados += 1
            continue
        
        # Mostrar progresso
        porcentagem = (prod_idx / total_produtos) * 100
        print(f"[{prod_idx}/{total_produtos}] {produto.descricao_produto:30} ({imagens.count()} imagens) - {porcentagem:.1f}%")
        
        # Processar imagens do produto
        for img in imagens:
            try:
                caminho_original = Path(f"media/{img.imagem}")
                
                if not caminho_original.exists():
                    total_erros += 1
                    continue
                
                # Gerar caminho de saída
                nome_saida = f"prod_{produto.id:04d}_{prefixo_counter:04d}_processada.jpg"
                caminho_saida = pasta_saida / nome_saida
                
                # Processar
                sucesso, erro = otimizar_imagem(str(caminho_original), str(caminho_saida))
                
                if sucesso:
                    # Registrar no banco
                    ProcessadorImagensLog.objects.create(
                        tipo='remover_fundo',
                        imagem_original=str(caminho_original),
                        imagem_processada=f'processadas/{nome_saida}',
                        status='sucesso',
                        parametros=json.dumps({
                            'produto_id': produto.id,
                            'produto_nome': produto.descricao_produto,
                            'metodo': 'otimizacao_pillow'
                        })
                    )
                    total_processados += 1
                    print(f"  ✅ {img.imagem.name}")
                else:
                    total_erros += 1
                    print(f"  ❌ {img.imagem.name}")
                
                prefixo_counter += 1
                
            except Exception as e:
                total_erros += 1
                print(f"  ❌ Erro: {str(e)[:50]}")
    
    # Resumo final
    print("\n" + "="*80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("="*80)
    print(f"✅ Processadas: {total_processados}")
    print(f"❌ Erros: {total_erros}")
    print(f"⏭️  Produtos sem imagens: {total_pulados}/{total_produtos}")
    if total_processados + total_erros > 0:
        taxa = (total_processados / (total_processados + total_erros)) * 100
        print(f"📊 Taxa de sucesso: {taxa:.1f}%")
    print("="*80 + "\n")
    
    return total_processados, total_erros


if __name__ == '__main__':
    try:
        processar_10_por_produto()
        print("🎉 Concluído!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
