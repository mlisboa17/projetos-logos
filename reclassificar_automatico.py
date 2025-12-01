"""
Script para reclassificar imagens DESCONHECIDAS usando IA
Analisa imagens sem produto correto e sugere automaticamente
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente
from verifik.models import ProdutoMae
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

# Importar funções da view
from verifik.views_coleta import classificar_forma_produto, extrair_texto_ocr, sugerir_produto_ia

def analisar_imagem_desconhecida(imagem_obj):
    """
    Analisa uma imagem e retorna sugestão de produto
    """
    try:
        # Carregar imagem
        img_path = imagem_obj.imagem.path
        img = cv2.imread(img_path)
        
        if img is None:
            return None, 0, "Erro ao carregar imagem"
        
        # Análise completa
        forma = classificar_forma_produto(img)
        texto_ocr = extrair_texto_ocr(img)
        
        # Buscar produtos
        produtos_db = list(ProdutoMae.objects.all())
        
        # Sugestão
        produto_id, confianca, razao = sugerir_produto_ia(texto_ocr, forma, produtos_db)
        
        return produto_id, confianca, razao, forma, texto_ocr
        
    except Exception as e:
        print(f"Erro ao analisar: {e}")
        return None, 0, str(e), "desconhecido", []


def main():
    print("=" * 60)
    print("🤖 RECLASSIFICAÇÃO INTELIGENTE DE PRODUTOS")
    print("=" * 60)
    print()
    
    # Buscar imagens sem produto ou com produto genérico
    imagens_problematicas = ImagemProdutoPendente.objects.filter(
        produto__descricao_produto__icontains='DESCONHECIDO'
    ) | ImagemProdutoPendente.objects.filter(
        produto__descricao_produto__icontains='FAMILIA_HEINEKEN_MANUAL'
    )
    
    total = imagens_problematicas.count()
    print(f"📊 Encontradas {total} imagens para reclassificar")
    print()
    
    if total == 0:
        print("✅ Nenhuma imagem precisa de reclassificação!")
        return
    
    reclassificadas = 0
    puladas = 0
    
    for idx, imagem in enumerate(imagens_problematicas, 1):
        print(f"\n{'─' * 60}")
        print(f"[{idx}/{total}] Analisando: {imagem.imagem.name}")
        print(f"Produto atual: {imagem.produto.descricao_produto}")
        
        # Analisar com IA
        resultado = analisar_imagem_desconhecida(imagem)
        
        if resultado[0] is None:
            print(f"❌ Erro: {resultado[2]}")
            puladas += 1
            continue
        
        produto_id, confianca, razao, forma, texto_ocr = resultado
        
        print(f"\n🔍 Análise:")
        print(f"  Forma detectada: {forma}")
        print(f"  Texto OCR: {', '.join(texto_ocr) if texto_ocr else 'Nenhum'}")
        
        if produto_id:
            produto_sugerido = ProdutoMae.objects.get(id=produto_id)
            print(f"\n🎯 SUGESTÃO:")
            print(f"  Produto: {produto_sugerido.descricao_produto}")
            print(f"  Confiança: {confianca:.1f}%")
            print(f"  Razão: {razao}")
            
            # Pedir confirmação
            if confianca >= 70:
                print(f"\n✨ Alta confiança! Recomendado aceitar.")
            elif confianca >= 40:
                print(f"\n⚠️ Confiança média. Revisar sugestão.")
            else:
                print(f"\n❌ Baixa confiança. Pode estar incorreto.")
            
            resposta = input("\n👉 Aceitar sugestão? [S/n/pular/sair]: ").strip().lower()
            
            if resposta == 'sair':
                print("\n🛑 Processo interrompido pelo usuário")
                break
            elif resposta == 'pular' or resposta == 'p':
                print("⏭️ Pulado")
                puladas += 1
                continue
            elif resposta == 'n' or resposta == 'nao':
                print("❌ Sugestão rejeitada")
                puladas += 1
                continue
            else:  # 's', 'sim' ou Enter
                # Aplicar reclassificação
                imagem.produto = produto_sugerido
                imagem.save()
                print(f"✅ Produto reclassificado com sucesso!")
                reclassificadas += 1
        else:
            print(f"\n⚠️ Nenhuma sugestão (confiança muito baixa)")
            print(f"  Razão: {razao}")
            puladas += 1
    
    print("\n" + "=" * 60)
    print("📊 RESUMO:")
    print(f"  Total analisadas: {total}")
    print(f"  ✅ Reclassificadas: {reclassificadas}")
    print(f"  ⏭️ Puladas: {puladas}")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Processo cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
