from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import PostoVibra, PrecoVibra


# @login_required  # Removido temporariamente para teste
def dashboard_vibra(request):
    """Dashboard principal com preços da Vibra por produto"""
    
    # Pegar últimas 24 horas
    ultimas_24h = timezone.now() - timedelta(hours=24)
    
    # Produtos únicos com preços recentes
    produtos = PrecoVibra.objects.filter(
        data_coleta__gte=ultimas_24h,
        disponivel=True
    ).values('produto_nome', 'produto_codigo').distinct()
    
    # Para cada produto, pegar preços de todos os postos
    dados_produtos = []
    for produto in produtos:
        precos = PrecoVibra.objects.filter(
            produto_nome=produto['produto_nome'],
            data_coleta__gte=ultimas_24h,
            disponivel=True
        ).select_related('posto').order_by('preco')
        
        if precos.exists():
            # Estatísticas
            preco_min = precos.aggregate(Min('preco'))['preco__min']
            preco_max = precos.aggregate(Max('preco'))['preco__max']
            preco_med = precos.aggregate(Avg('preco'))['preco__avg']
            
            dados_produtos.append({
                'nome': produto['produto_nome'],
                'codigo': produto['produto_codigo'],
                'precos': precos,
                'preco_min': preco_min,
                'preco_max': preco_max,
                'preco_medio': preco_med,
                'variacao': preco_max - preco_min if preco_max and preco_min else 0,
                'total_postos': precos.count()
            })
    
    # Ordenar por nome de produto
    dados_produtos.sort(key=lambda x: x['nome'])
    
    # Últim a atualização
    ultima_coleta = PrecoVibra.objects.filter(
        disponivel=True
    ).order_by('-data_coleta').first()
    
    context = {
        'produtos': dados_produtos,
        'total_produtos': len(dados_produtos),
        'ultima_atualizacao': ultima_coleta.data_coleta if ultima_coleta else None,
    }
    
    return render(request, 'fuel_prices/dashboard_vibra.html', context)


# @login_required  # Removido temporariamente para teste
def dashboard_por_posto(request):
    """Dashboard com preços agrupados por posto"""
    
    ultimas_24h = timezone.now() - timedelta(hours=24)
    
    postos = PostoVibra.objects.filter(ativo=True).prefetch_related(
        'precos'
    )
    
    dados_postos = []
    for posto in postos:
        precos_recentes = posto.precos.filter(
            data_coleta__gte=ultimas_24h,
            disponivel=True
        ).order_by('produto_nome')
        
        if precos_recentes.exists():
            dados_postos.append({
                'posto': posto,
                'precos': precos_recentes,
                'total_produtos': precos_recentes.count(),
                'ultima_coleta': precos_recentes.order_by('-data_coleta').first().data_coleta
            })
    
    context = {
        'postos': dados_postos,
        'total_postos': len(dados_postos),
    }
    
    return render(request, 'fuel_prices/dashboard_por_posto.html', context)
