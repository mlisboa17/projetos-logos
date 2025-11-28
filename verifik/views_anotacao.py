# Views para o sistema de anotação de imagens

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from verifik.models import ProdutoMae
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
import json
from pathlib import Path
from PIL import Image
import shutil
from django.conf import settings
from datetime import datetime


@login_required
def anotar_imagem(request):
    """Interface para enviar e anotar imagens com múltiplos produtos"""
    
    if request.method == 'POST':
        # Upload da imagem
        imagem_file = request.FILES.get('imagem')
        observacoes = request.POST.get('observacoes', '')
        
        if not imagem_file:
            messages.error(request, 'Selecione uma imagem para enviar.')
            return redirect('anotar_imagem')
        
        # Criar registro de imagem anotada
        imagem_anotada = ImagemAnotada.objects.create(
            imagem=imagem_file,
            enviado_por=request.user,
            observacoes=observacoes,
            status='anotando'
        )
        
        messages.success(request, f'Imagem enviada! Agora você pode adicionar as anotações dos produtos.')
        return redirect('editar_anotacoes', imagem_id=imagem_anotada.id)
    
    # GET - mostrar formulário
    imagens_usuario = ImagemAnotada.objects.filter(enviado_por=request.user).order_by('-data_envio')[:10]
    
    context = {
        'imagens_recentes': imagens_usuario,
    }
    
    return render(request, 'verifik/anotar_imagem.html', context)


@login_required
def editar_anotacoes(request, imagem_id):
    """Editor de anotações com bounding boxes"""
    
    imagem = get_object_or_404(ImagemAnotada, id=imagem_id)
    
    # Verificar permissão (owner ou staff)
    if imagem.enviado_por != request.user and not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para editar esta imagem.')
        return redirect('anotar_imagem')
    
    produtos = ProdutoMae.objects.all().order_by('nome')
    anotacoes = imagem.anotacoes.all()
    
    context = {
        'imagem': imagem,
        'produtos': produtos,
        'anotacoes': anotacoes,
        'anotacoes_json': json.dumps([
            {
                'id': a.id,
                'produto_id': a.produto.id,
                'produto_nome': a.produto.descricao_produto,
                'x': a.bbox_x,
                'y': a.bbox_y,
                'width': a.bbox_width,
                'height': a.bbox_height,
            }
            for a in anotacoes
        ])
    }
    
    return render(request, 'verifik/editar_anotacoes.html', context)


@login_required
@require_http_methods(["POST"])
def salvar_anotacao(request):
    """API para salvar uma anotação (bbox)"""
    
    try:
        data = json.loads(request.body)
        
        imagem_id = data.get('imagem_id')
        produto_id = data.get('produto_id')
        bbox_x = float(data.get('bbox_x'))
        bbox_y = float(data.get('bbox_y'))
        bbox_width = float(data.get('bbox_width'))
        bbox_height = float(data.get('bbox_height'))
        
        imagem = get_object_or_404(ImagemAnotada, id=imagem_id)
        produto = get_object_or_404(ProdutoMae, id=produto_id)
        
        # Verificar permissão
        if imagem.enviado_por != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
        
        # Criar anotação
        anotacao = AnotacaoProduto.objects.create(
            imagem_anotada=imagem,
            produto=produto,
            bbox_x=bbox_x,
            bbox_y=bbox_y,
            bbox_width=bbox_width,
            bbox_height=bbox_height
        )
        
        # Atualizar contador
        imagem.total_anotacoes = imagem.anotacoes.count()
        imagem.save()
        
        return JsonResponse({
            'success': True,
            'anotacao_id': anotacao.id,
            'total': imagem.total_anotacoes
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def remover_anotacao(request, anotacao_id):
    """Remove uma anotação"""
    
    anotacao = get_object_or_404(AnotacaoProduto, id=anotacao_id)
    imagem = anotacao.imagem_anotada
    
    # Verificar permissão
    if imagem.enviado_por != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    anotacao.delete()
    
    # Atualizar contador
    imagem.total_anotacoes = imagem.anotacoes.count()
    imagem.save()
    
    return JsonResponse({'success': True, 'total': imagem.total_anotacoes})


@login_required
@require_http_methods(["POST"])
def finalizar_anotacao(request, imagem_id):
    """Marca a imagem como concluída"""
    
    imagem = get_object_or_404(ImagemAnotada, id=imagem_id)
    
    if imagem.enviado_por != request.user and not request.user.is_staff:
        messages.error(request, 'Sem permissão.')
        return redirect('anotar_imagem')
    
    if imagem.total_anotacoes == 0:
        messages.error(request, 'Adicione pelo menos uma anotação antes de finalizar.')
        return redirect('editar_anotacoes', imagem_id=imagem.id)
    
    imagem.status = 'concluida'
    imagem.save()
    
    messages.success(request, f'Imagem finalizada com {imagem.total_anotacoes} anotações!')
    return redirect('anotar_imagem')


@login_required
def importar_dataset(request):
    """Interface para importar imagens aprovadas para o dataset de treino"""
    
    if not request.user.is_staff:
        messages.error(request, 'Apenas gestores podem acessar esta área.')
        return redirect('verifik_home')
    
    # Estatísticas de imagens simples (1 produto por foto)
    imagens_simples = ImagemProdutoPendente.objects.filter(status='aprovada').select_related('produto')[:20]  # Limitar para performance
    stats_simples = {
        'total': ImagemProdutoPendente.objects.filter(status='aprovada').count(),
        'por_produto': {},
        'imagens_preview': imagens_simples
    }
    
    # Calcular distribuição por produto para todas as imagens simples
    todas_imagens_simples = ImagemProdutoPendente.objects.filter(status='aprovada').select_related('produto')
    for img in todas_imagens_simples:
        produto_nome = img.produto.descricao_produto
        if produto_nome not in stats_simples['por_produto']:
            stats_simples['por_produto'][produto_nome] = 0
        stats_simples['por_produto'][produto_nome] += 1
    
    # Estatísticas de imagens anotadas (múltiplos produtos)
    imagens_anotadas = ImagemAnotada.objects.filter(status='aprovada').select_related('enviado_por')[:20]  # Limitar para performance
    stats_anotadas = {
        'total_imagens': ImagemAnotada.objects.filter(status='aprovada').count(),
        'total_anotacoes': AnotacaoProduto.objects.filter(
            imagem_anotada__status='aprovada'
        ).count(),
        'por_produto': {},
        'imagens_preview': imagens_anotadas
    }
    
    anotacoes = AnotacaoProduto.objects.filter(
        imagem_anotada__status='aprovada'
    ).select_related('produto')
    
    for anotacao in anotacoes:
        produto_nome = anotacao.produto.descricao_produto
        if produto_nome not in stats_anotadas['por_produto']:
            stats_anotadas['por_produto'][produto_nome] = 0
        stats_anotadas['por_produto'][produto_nome] += 1
    
    context = {
        'stats_simples': stats_simples,
        'stats_anotadas': stats_anotadas,
    }
    
    return render(request, 'verifik/importar_dataset.html', context)


@login_required
@require_http_methods(["POST"])
def executar_importacao(request):
    """Executa a importação das imagens para o dataset"""
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    try:
        tipo = request.POST.get('tipo')  # 'simples' ou 'anotadas'
        
        base_dir = Path(settings.BASE_DIR) / 'assets' / 'dataset' / 'train'
        base_dir.mkdir(parents=True, exist_ok=True)
        
        importadas = 0
        erros = []
        
        if tipo == 'simples':
            # Importar imagens simples (1 produto = 1 imagem)
            imagens = ImagemProdutoPendente.objects.filter(status='aprovada')
            
            for img in imagens:
                try:
                    produto_dir = base_dir / img.produto.descricao_produto
                    produto_dir.mkdir(exist_ok=True)
                    
                    # Copiar imagem
                    src = Path(img.imagem.path)
                    if src.exists():
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        dst = produto_dir / f"{img.produto.descricao_produto}_{timestamp}_{src.name}"
                        shutil.copy2(src, dst)
                        importadas += 1
                        
                except Exception as e:
                    erros.append(f"Erro na imagem {img.id}: {str(e)}")
        
        elif tipo == 'anotadas':
            # Importar imagens com anotações (formato YOLO)
            imagens = ImagemAnotada.objects.filter(status='aprovada')
            
            for imagem in imagens:
                try:
                    # Copiar imagem principal
                    src_img = Path(imagem.imagem.path)
                    if not src_img.exists():
                        continue
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    img_name = f"anotada_{imagem.id}_{timestamp}.jpg"
                    
                    # Salvar em cada pasta de produto que aparece na imagem
                    produtos_na_imagem = set()
                    anotacoes = imagem.anotacoes.all()
                    
                    for anotacao in anotacoes:
                        produtos_na_imagem.add(anotacao.produto)
                    
                    # Para cada produto, salvar imagem + arquivo .txt com anotações
                    for produto in produtos_na_imagem:
                        produto_dir = base_dir / produto.descricao_produto
                        produto_dir.mkdir(exist_ok=True)
                        
                        # Copiar imagem
                        dst_img = produto_dir / img_name
                        shutil.copy2(src_img, dst_img)
                        
                        # Criar arquivo de anotações YOLO
                        txt_name = dst_img.stem + '.txt'
                        txt_path = produto_dir / txt_name
                        
                        with open(txt_path, 'w') as f:
                            for anotacao in anotacoes:
                                if anotacao.produto == produto:
                                    # Formato YOLO: class_id x_center y_center width height
                                    f.write(f"0 {anotacao.bbox_x} {anotacao.bbox_y} "
                                           f"{anotacao.bbox_width} {anotacao.bbox_height}\n")
                        
                        importadas += 1
                    
                except Exception as e:
                    erros.append(f"Erro na imagem {imagem.id}: {str(e)}")
        
        mensagem = f"{importadas} imagens importadas com sucesso!"
        if erros:
            mensagem += f" {len(erros)} erros encontrados."
        
        return JsonResponse({
            'success': True,
            'importadas': importadas,
            'erros': erros,
            'mensagem': mensagem
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
