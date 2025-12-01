"""
Views para visualizar imagens anotadas
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from verifik.models import ImagemProduto


@login_required
def listar_imagens_anotadas(request):
    """Lista todas as imagens anotadas com visualização em galeria"""
    imagens = ImagemAnotada.objects.all().order_by('-id')
    
    context = {
        'imagens': imagens,
        'total': imagens.count(),
    }
    
    return render(request, 'verifik/listar_imagens_anotadas.html', context)


@login_required
def visualizar_imagem_anotada(request, img_id):
    """Visualiza uma imagem anotada com seus bboxes"""
    imagem = get_object_or_404(ImagemAnotada, id=img_id)
    anotacoes = imagem.anotacoes.all()
    
    context = {
        'imagem': imagem,
        'anotacoes': anotacoes,
        'total_anotacoes': anotacoes.count(),
    }
    
    return render(request, 'verifik/visualizar_imagem_anotada.html', context)
