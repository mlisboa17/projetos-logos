from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models_coleta import ImagemProdutoPendente, LoteFotos
from verifik.models import ProdutoMae
import os
import shutil
from pathlib import Path


@login_required
def enviar_fotos(request):
    """Interface para funcionários enviarem fotos"""
    
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        observacoes = request.POST.get('observacoes', '')
        arquivos = request.FILES.getlist('fotos')
        
        if not produto_id or not arquivos:
            messages.error(request, 'Selecione um produto e pelo menos uma foto')
            return redirect('enviar_fotos')
        
        produto = get_object_or_404(ProdutoMae, id=produto_id)
        
        # Criar lote
        lote = LoteFotos.objects.create(
            nome=f"{produto.descricao_produto} - {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            enviado_por=request.user,
            total_imagens=len(arquivos)
        )
        
        # Salvar imagens
        for arquivo in arquivos:
            ImagemProdutoPendente.objects.create(
                produto=produto,
                imagem=arquivo,
                enviado_por=request.user,
                observacoes_envio=observacoes
            )
        
        messages.success(request, f'{len(arquivos)} foto(s) enviada(s) com sucesso!')
        return redirect('enviar_fotos')
    
    # GET
    produtos = ProdutoMae.objects.all().order_by('nome')
    
    # Estatísticas do usuário
    stats = {
        'total_enviadas': ImagemProdutoPendente.objects.filter(enviado_por=request.user).count(),
        'aprovadas': ImagemProdutoPendente.objects.filter(enviado_por=request.user, status='aprovada').count(),
        'pendentes': ImagemProdutoPendente.objects.filter(enviado_por=request.user, status='pendente').count(),
    }
    
    context = {
        'produtos': produtos,
        'stats': stats,
    }
    
    return render(request, 'verifik/enviar_fotos.html', context)


@login_required
def revisar_fotos(request):
    """Interface para revisar e aprovar fotos (apenas admin)"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    # Filtros
    status_filtro = request.GET.get('status', 'pendente')
    produto_id = request.GET.get('produto')
    
    imagens = ImagemProdutoPendente.objects.all()
    
    if status_filtro:
        imagens = imagens.filter(status=status_filtro)
    
    if produto_id:
        imagens = imagens.filter(produto_id=produto_id)
    
    imagens = imagens.select_related('produto', 'enviado_por', 'aprovado_por')
    
    # Estatísticas
    stats = {
        'total_pendentes': ImagemProdutoPendente.objects.filter(status='pendente').count(),
        'total_aprovadas': ImagemProdutoPendente.objects.filter(status='aprovada').count(),
        'total_rejeitadas': ImagemProdutoPendente.objects.filter(status='rejeitada').count(),
    }
    
    produtos = ProdutoMae.objects.annotate(
        total_pendentes=Count('imagemprodutopendente', filter=Q(imagemprodutopendente__status='pendente'))
    ).filter(total_pendentes__gt=0)
    
    context = {
        'imagens': imagens,
        'stats': stats,
        'produtos_com_pendencias': produtos,
        'status_atual': status_filtro,
    }
    
    return render(request, 'verifik/revisar_fotos.html', context)


@login_required
def aprovar_imagem(request, imagem_id):
    """Aprovar uma imagem e mover para a base de treinamento"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
    
    if request.method == 'POST':
        qualidade = request.POST.get('qualidade', 3)
        observacoes = request.POST.get('observacoes', '')
        
        # Atualizar status
        imagem.status = 'aprovada'
        imagem.aprovado_por = request.user
        imagem.data_revisao = timezone.now()
        imagem.qualidade = qualidade
        imagem.observacoes_revisao = observacoes
        imagem.save()
        
        # Copiar para base de treinamento
        try:
            # Caminho da base de treinamento
            base_path = Path('assets/dataset/train') / imagem.produto.descricao_produto.replace(' ', '_')
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            novo_nome = f"{imagem.produto.descricao_produto.replace(' ', '_')}_{timestamp}.jpg"
            destino = base_path / novo_nome
            
            # Copiar arquivo
            shutil.copy2(imagem.imagem.path, destino)
            
            messages.success(request, f'Imagem aprovada e adicionada à base de treinamento!')
        except Exception as e:
            messages.warning(request, f'Imagem aprovada, mas erro ao copiar: {str(e)}')
        
        return redirect('revisar_fotos')
    
    context = {'imagem': imagem}
    return render(request, 'verifik/aprovar_imagem.html', context)


@login_required
def rejeitar_imagem(request, imagem_id):
    """Rejeitar uma imagem"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        imagem.status = 'rejeitada'
        imagem.aprovado_por = request.user
        imagem.data_revisao = timezone.now()
        imagem.observacoes_revisao = motivo
        imagem.save()
        
        messages.info(request, 'Imagem rejeitada')
        return redirect('revisar_fotos')
    
    context = {'imagem': imagem}
    return render(request, 'verifik/rejeitar_imagem.html', context)
