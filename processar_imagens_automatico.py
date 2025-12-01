"""
Script para processar automaticamente todas as imagens pendentes
com reconhecimento de código de barras + IA multi-modal
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente
from verifik.models import ProdutoMae, CodigoBarrasProdutoMae
from verifik.views_coleta import (
    get_yolo_model,
    detectar_codigo_barras,
    extrair_texto_ocr,
    classificar_forma_produto,
    sugerir_produto_ia
)
import cv2
import numpy as np
from pathlib import Path
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

def processar_imagem_com_ia(imagem_obj):
    """
    Processa uma imagem e tenta reconhecer o produto automaticamente
    Retorna: (produto_sugerido, confianca, razao, detalhes)
    """
    print(f"\n{'='*80}")
    print(f"📷 Processando: {imagem_obj.imagem.name}")
    print(f"   Produto atual: {imagem_obj.produto.descricao_produto}")
    print(f"{'='*80}")
    
    try:
        # Carregar imagem
        img_path = imagem_obj.imagem.path
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"   ❌ Erro ao carregar imagem")
            return (None, 0, "Erro ao carregar imagem", {})
        
        print(f"   ✓ Imagem carregada: {img.shape}")
        
        # 1. YOLO - Detectar produtos
        print(f"\n   🔍 Etapa 1/4: Detecção YOLO...")
        model = get_yolo_model()
        results = model(img, conf=0.25, iou=0.45)
        
        bboxes_detectados = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                conf = float(box.conf[0].cpu().numpy())
                bboxes_detectados.append((x1, y1, x2, y2, conf))
        
        if not bboxes_detectados:
            print(f"   ⚠️ Nenhum produto detectado pelo YOLO")
            return (None, 0, "YOLO não detectou produtos", {})
        
        print(f"   ✓ {len(bboxes_detectados)} produto(s) detectado(s)")
        
        # Processar cada bbox (usar o de maior confiança)
        melhor_bbox = max(bboxes_detectados, key=lambda x: x[4])
        x1, y1, x2, y2, yolo_conf = melhor_bbox
        bbox_img = img[y1:y2, x1:x2]
        
        print(f"   ✓ Usando bbox com confiança YOLO: {yolo_conf:.2%}")
        
        # 2. CÓDIGO DE BARRAS - Prioridade máxima
        print(f"\n   🔥 Etapa 2/4: Detecção de Código de Barras...")
        codigo_barras, tipo_barcode = detectar_codigo_barras(bbox_img)
        
        if codigo_barras:
            print(f"   ✅ CÓDIGO DETECTADO: {codigo_barras} (Tipo: {tipo_barcode})")
            try:
                codigo_obj = CodigoBarrasProdutoMae.objects.get(codigo=codigo_barras)
                produto_sugerido = codigo_obj.produto_mae
                print(f"   ✅ MATCH PERFEITO: {produto_sugerido.descricao_produto}")
                return (
                    produto_sugerido,
                    99.99,
                    f"🔥 CÓDIGO DE BARRAS: {codigo_barras} (Match Exato)",
                    {
                        'codigo_barras': codigo_barras,
                        'tipo_barcode': tipo_barcode,
                        'yolo_conf': yolo_conf,
                        'bbox': (x1, y1, x2, y2)
                    }
                )
            except CodigoBarrasProdutoMae.DoesNotExist:
                print(f"   ⚠️ Código {codigo_barras} não encontrado no banco")
        else:
            print(f"   ℹ️ Nenhum código de barras detectado")
        
        # 3. OCR - Extrair texto
        print(f"\n   📝 Etapa 3/4: OCR (Tesseract)...")
        texto_ocr = extrair_texto_ocr(bbox_img)
        print(f"   ✓ Texto extraído: {texto_ocr[:10]}")
        
        # 4. FORMA - Análise geométrica
        print(f"\n   🔷 Etapa 4/4: Análise de Forma...")
        forma = classificar_forma_produto(bbox_img)
        print(f"   ✓ Forma classificada: {forma}")
        
        # 5. SUGESTÃO - Pontuação multi-critério
        print(f"\n   🎯 Calculando sugestão...")
        produtos_db = list(ProdutoMae.objects.all())
        produto_id, confianca, razao = sugerir_produto_ia(
            texto_ocr, forma, produtos_db, codigo_barras=codigo_barras
        )
        
        if produto_id:
            produto_sugerido = ProdutoMae.objects.get(id=produto_id)
            print(f"   ✓ Sugestão: {produto_sugerido.descricao_produto}")
            print(f"   ✓ Confiança: {confianca:.2f}%")
            print(f"   ✓ Razão: {razao}")
            
            return (
                produto_sugerido,
                confianca,
                razao,
                {
                    'ocr_texto': texto_ocr,
                    'forma': forma,
                    'yolo_conf': yolo_conf,
                    'bbox': (x1, y1, x2, y2)
                }
            )
        else:
            print(f"   ❌ Nenhuma sugestão encontrada")
            return (None, 0, "Nenhuma correspondência encontrada", {})
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return (None, 0, f"Erro: {str(e)}", {})


def main():
    print("\n" + "="*80)
    print("🤖 PROCESSAMENTO AUTOMÁTICO DE IMAGENS COM IA")
    print("="*80)
    
    # Buscar imagens pendentes para processar
    imagens = ImagemProdutoPendente.objects.filter(
        status='pendente'
    ).filter(
        produto__descricao_produto__icontains='DESCONHECIDO'
    ) | ImagemProdutoPendente.objects.filter(
        status='pendente',
        produto__descricao_produto__icontains='FAMILIA_HEINEKEN_MANUAL'
    )
    
    total = imagens.count()
    print(f"\n📊 Total de imagens para processar: {total}")
    
    if total == 0:
        print("   ℹ️ Nenhuma imagem pendente encontrada")
        return
    
    # Perguntar quantas processar
    try:
        limite = input(f"\nQuantas imagens processar? (1-{total}, Enter=10): ").strip()
        limite = int(limite) if limite else 10
        limite = min(limite, total)
    except:
        limite = 10
    
    print(f"\n🚀 Processando {limite} imagens...\n")
    
    # Estatísticas
    stats = {
        'codigo_barras': 0,
        'alta_confianca': 0,
        'media_confianca': 0,
        'baixa_confianca': 0,
        'erro': 0
    }
    
    resultados = []
    
    # Processar cada imagem
    for idx, imagem in enumerate(imagens[:limite], 1):
        print(f"\n[{idx}/{limite}]")
        
        produto_sugerido, confianca, razao, detalhes = processar_imagem_com_ia(imagem)
        
        resultado = {
            'imagem': imagem,
            'produto_atual': imagem.produto.descricao_produto,
            'produto_sugerido': produto_sugerido.descricao_produto if produto_sugerido else None,
            'produto_sugerido_obj': produto_sugerido,
            'confianca': confianca,
            'razao': razao,
            'detalhes': detalhes
        }
        resultados.append(resultado)
        
        # Atualizar estatísticas
        if confianca >= 99.9:
            stats['codigo_barras'] += 1
        elif confianca >= 70:
            stats['alta_confianca'] += 1
        elif confianca >= 40:
            stats['media_confianca'] += 1
        elif confianca > 0:
            stats['baixa_confianca'] += 1
        else:
            stats['erro'] += 1
    
    # Exibir resultados
    print("\n" + "="*80)
    print("📊 RESULTADOS DO PROCESSAMENTO")
    print("="*80)
    
    print(f"\n⭐ Código de Barras (99.99%): {stats['codigo_barras']}")
    print(f"🟢 Alta Confiança (≥70%): {stats['alta_confianca']}")
    print(f"🟡 Média Confiança (40-69%): {stats['media_confianca']}")
    print(f"🔴 Baixa Confiança (<40%): {stats['baixa_confianca']}")
    print(f"❌ Erros: {stats['erro']}")
    
    # Mostrar detalhes
    print("\n" + "="*80)
    print("📋 DETALHAMENTO")
    print("="*80)
    
    for idx, r in enumerate(resultados, 1):
        emoji = "⭐" if r['confianca'] >= 99.9 else \
                "🟢" if r['confianca'] >= 70 else \
                "🟡" if r['confianca'] >= 40 else \
                "🔴" if r['confianca'] > 0 else "❌"
        
        print(f"\n{idx}. {emoji} {r['imagem'].imagem.name}")
        print(f"   Atual: {r['produto_atual']}")
        print(f"   Sugestão: {r['produto_sugerido'] or 'NENHUMA'}")
        print(f"   Confiança: {r['confianca']:.2f}%")
        print(f"   Razão: {r['razao']}")
    
    # Perguntar se quer aplicar automaticamente
    print("\n" + "="*80)
    print("💾 APLICAR MUDANÇAS?")
    print("="*80)
    
    print("\nOpções de aplicação:")
    print("1. Apenas código de barras (99.99%)")
    print("2. Alta confiança (≥70%)")
    print("3. Média e alta (≥40%)")
    print("4. Manual - revisar cada um")
    print("5. Cancelar")
    
    try:
        opcao = input("\nEscolha uma opção (1-5): ").strip()
    except:
        opcao = "5"
    
    if opcao == "5":
        print("\n❌ Cancelado. Nenhuma mudança aplicada.")
        return
    
    # Aplicar mudanças
    usuario_sistema = User.objects.filter(is_superuser=True).first()
    if not usuario_sistema:
        print("❌ Erro: Nenhum superusuário encontrado")
        return
    
    aplicados = 0
    
    for r in resultados:
        aplicar = False
        
        if opcao == "1" and r['confianca'] >= 99.9:
            aplicar = True
        elif opcao == "2" and r['confianca'] >= 70:
            aplicar = True
        elif opcao == "3" and r['confianca'] >= 40:
            aplicar = True
        elif opcao == "4":
            # Revisar manual
            print(f"\n📷 {r['imagem'].imagem.name}")
            print(f"   Atual: {r['produto_atual']}")
            print(f"   Sugestão: {r['produto_sugerido']} ({r['confianca']:.2f}%)")
            resposta = input("   Aplicar? (S/n): ").strip().lower()
            aplicar = resposta != 'n'
        
        if aplicar and r['produto_sugerido_obj']:
            r['imagem'].produto = r['produto_sugerido_obj']
            r['imagem'].status = 'aprovada'
            r['imagem'].aprovado_por = usuario_sistema
            r['imagem'].data_aprovacao = timezone.now()
            r['imagem'].save()
            
            print(f"   ✅ Aplicado: {r['produto_sugerido']}")
            aplicados += 1
    
    print(f"\n{'='*80}")
    print(f"✅ CONCLUÍDO! {aplicados} imagens atualizadas")
    print(f"{'='*80}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
        sys.exit(0)
