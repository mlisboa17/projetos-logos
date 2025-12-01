#!/usr/bin/env python
"""
Remove fundo das imagens - 10 imagens por produto
Usando detecção automática de cor de fundo
"""

import os
import sys
import django
from pathlib import Path
from PIL import Image
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProduto, ProdutoMae
from verifik.models_anotacao import ImagemAnotada
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json


def detectar_e_remover_fundo(caminho_entrada, caminho_saida):
    """Remove fundo detectando automaticamente a cor predominante nos cantos"""
    try:
        # Abrir imagem
        img = Image.open(caminho_entrada)
        
        # Converter para RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Converter para numpy array
        img_array = np.array(img)
        
        # Pegar cores dos cantos (assume que cantos têm o fundo)
        altura, largura = img_array.shape[:2]
        tamanho_canto = min(50, altura // 4, largura // 4)
        
        # Coletar pixels dos cantos
        cantos = []
        cantos.extend(img_array[:tamanho_canto, :tamanho_canto].reshape(-1, 3))  # Canto superior esquerdo
        cantos.extend(img_array[:tamanho_canto, -tamanho_canto:].reshape(-1, 3))  # Canto superior direito
        cantos.extend(img_array[-tamanho_canto:, :tamanho_canto].reshape(-1, 3))  # Canto inferior esquerdo
        cantos.extend(img_array[-tamanho_canto:, -tamanho_canto:].reshape(-1, 3))  # Canto inferior direito
        
        cantos = np.array(cantos)
        
        # Encontrar cor dominante dos cantos (moda)
        cor_fundo = np.median(cantos, axis=0).astype(int)
        
        # Criar máscara: pixels similares ao fundo viram transparentes
        # Tolerar variação de até 30 em cada canal
        tolerancia = 30
        
        diferenca = np.abs(img_array.astype(float) - cor_fundo.astype(float))
        mascara = np.all(diferenca <= tolerancia, axis=2)
        
        # Converter para RGBA
        img_rgba = img.convert('RGBA')
        dados = np.array(img_rgba)
        
        # Aplicar máscara (fazer fundo transparente)
        dados[mascara, 3] = 0  # Canal alpha = 0 (transparente)
        
        # Criar imagem final
        resultado = Image.fromarray(dados, 'RGBA')
        resultado.save(str(caminho_saida), 'PNG')
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def processar_com_remocao_fundo():
    """Processa 10 imagens de cada produto REMOVENDO O FUNDO"""
    
    print("\n" + "="*80)
    print("✂️  REMOVE FUNDO - 10 IMAGENS POR PRODUTO")
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
    
    pasta_saida = Path('media/processadas_sem_fundo')
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    print(f"⏳ Removendo fundo de 10 imagens de cada um dos {total_produtos} produtos...\n")
    
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
                nome_saida = f"prod_{produto.id:04d}_{prefixo_counter:04d}_sem_fundo.png"
                caminho_saida = pasta_saida / nome_saida
                
                # Remover fundo
                sucesso, erro = detectar_e_remover_fundo(str(caminho_original), str(caminho_saida))
                
                if sucesso:
                    # Registrar no banco
                    ProcessadorImagensLog.objects.create(
                        tipo='remover_fundo',
                        imagem_original=str(caminho_original),
                        imagem_processada=f'processadas_sem_fundo/{nome_saida}',
                        status='sucesso',
                        parametros=json.dumps({
                            'produto_id': produto.id,
                            'produto_nome': produto.descricao_produto,
                            'metodo': 'deteccao_automatica_cantos'
                        })
                    )
                    total_processados += 1
                    print(f"  ✂️  {img.imagem.name}")
                else:
                    total_erros += 1
                    print(f"  ❌ {img.imagem.name}: {erro[:30]}")
                
                prefixo_counter += 1
                
            except Exception as e:
                total_erros += 1
                print(f"  ❌ Erro: {str(e)[:50]}")
    
    # Resumo final
    print("\n" + "="*80)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("="*80)
    print(f"✂️  Fundos removidos: {total_processados}")
    print(f"❌ Erros: {total_erros}")
    print(f"⏭️  Produtos sem imagens: {total_pulados}/{total_produtos}")
    print(f"📁 Salvas em: media/processadas_sem_fundo/")
    if total_processados + total_erros > 0:
        taxa = (total_processados / (total_processados + total_erros)) * 100
        print(f"📊 Taxa de sucesso: {taxa:.1f}%")
    print("="*80 + "\n")
    
    return total_processados, total_erros


if __name__ == '__main__':
    try:
        processar_com_remocao_fundo()
        print("🎉 Concluído!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido!")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
