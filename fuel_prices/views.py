from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Avg, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import subprocess
import json
import os
import threading
from .models import PostoVibra, PrecoVibra


def home(request):
    """Página inicial do sistema"""
    return render(request, 'home.html')


def dashboard_consolidado(request):
    """
    Dashboard FUEL PRICES - Preços de combustíveis dos postos Vibra
    Matriz: Produtos (linhas) × Postos (colunas)
    Navegação por datas específicas (sem modo "ao vivo")
    """
    from datetime import datetime, date, timedelta
    
    # Buscar todas as datas disponíveis (últimos 30 dias)
    datas_disponiveis_query = PrecoVibra.objects.filter(
        data_coleta__gte=timezone.now() - timedelta(days=30),
        disponivel=True
    ).dates('data_coleta', 'day', order='DESC')
    
    datas_disponiveis_list = list(datas_disponiveis_query)
    
    # Determinar qual data mostrar
    data_param = request.GET.get('data')
    
    if data_param:
        # Data específica solicitada
        try:
            data_filtro = datetime.strptime(data_param, '%Y-%m-%d').date()
        except ValueError:
            # Data inválida, usar a mais recente
            data_filtro = datas_disponiveis_list[0] if datas_disponiveis_list else date.today()
    else:
        # Sem parâmetro: mostrar a data mais recente disponível
        data_filtro = datas_disponiveis_list[0] if datas_disponiveis_list else date.today()
    
    # Definir intervalo do dia completo
    inicio = timezone.make_aware(datetime.combine(data_filtro, datetime.min.time()))
    fim = timezone.make_aware(datetime.combine(data_filtro, datetime.max.time()))
    
    # Calcular data anterior e próxima para navegação
    data_anterior = None
    data_proxima = None
    
    for i, data_disponivel in enumerate(datas_disponiveis_list):
        if data_disponivel == data_filtro:
            # Data anterior (mais antiga)
            if i + 1 < len(datas_disponiveis_list):
                data_anterior = datas_disponiveis_list[i + 1]
            # Data próxima (mais recente)
            if i - 1 >= 0:
                data_proxima = datas_disponiveis_list[i - 1]
            break
    
    # Buscar postos com preços nesta data
    postos = PostoVibra.objects.filter(
        ativo=True,
        precos__data_coleta__gte=inicio,
        precos__data_coleta__lte=fim,
        precos__disponivel=True
    ).distinct().order_by('codigo_vibra')
    
    # Adicionar última data de coleta para cada posto
    postos_com_data = []
    for posto in postos:
        ultima_coleta_posto = PrecoVibra.objects.filter(
            posto=posto,
            data_coleta__gte=inicio,
            disponivel=True
        ).order_by('-data_coleta').first()
        
        posto.ultima_coleta = ultima_coleta_posto.data_coleta if ultima_coleta_posto else None
        postos_com_data.append(posto)
    
    # Pegar TODOS os produtos únicos do período
    produtos_nomes = PrecoVibra.objects.filter(
        data_coleta__gte=inicio,
        data_coleta__lte=fim,
        disponivel=True
    ).values_list('produto_nome', flat=True).distinct().order_by('produto_nome')
    
    # Construir matriz de preços (PRODUTO × POSTO)
    matriz_precos = []
    
    for produto_nome in produtos_nomes:
        linha = {
            'produto': produto_nome,
            'postos': {},  # {cnpj: {preco, prazo, data}}
            'preco_min': None,
            'preco_max': None,
            'preco_medio': None,
            'variacao_percentual': 0,
        }
        
        # Para cada posto, pegar o preço MAIS RECENTE deste produto no período
        precos_valores = []
        
        for posto in postos_com_data:
            preco_mais_recente = PrecoVibra.objects.filter(
                posto=posto,
                produto_nome=produto_nome,
                data_coleta__gte=inicio,
                data_coleta__lte=fim,
                disponivel=True
            ).order_by('-data_coleta').first()
            
            if preco_mais_recente:
                preco_float = float(preco_mais_recente.preco)
                linha['postos'][posto.cnpj] = {
                    'preco': preco_float,
                    'prazo': preco_mais_recente.prazo_pagamento,
                    'data': preco_mais_recente.data_coleta,
                    'posto_nome': posto.nome_fantasia or posto.razao_social,
                }
                precos_valores.append(preco_float)
        
        # Calcular min/max/média/variação e classes CSS
        if precos_valores:
            linha['preco_min'] = min(precos_valores)
            linha['preco_max'] = max(precos_valores)
            linha['preco_medio'] = sum(precos_valores) / len(precos_valores)
            
            if linha['preco_min'] > 0:
                linha['variacao_percentual'] = ((linha['preco_max'] - linha['preco_min']) / linha['preco_min']) * 100
            
            # Adicionar classe CSS para cada preço
            # NOVA LÓGICA: Usa a MÉDIA como referência
            for cnpj, info in linha['postos'].items():
                preco = info['preco']
                media = linha['preco_medio']
                
                # Calcular diferença percentual em relação à média
                diff_media = ((preco - media) / media) * 100 if media > 0 else 0
                
                if preco == linha['preco_min']:
                    info['css_class'] = 'preco-min'  # Verde forte (melhor preço)
                elif preco == linha['preco_max']:
                    info['css_class'] = 'preco-max'  # Vermelho forte (pior preço)
                elif diff_media <= -2:  # 2% abaixo da média
                    info['css_class'] = 'preco-baixo'  # Verde claro
                elif diff_media <= -0.5:  # Até 0.5% abaixo da média
                    info['css_class'] = 'preco-medio-baixo'  # Amarelo claro
                elif diff_media <= 0.5:  # Próximo da média (±0.5%)
                    info['css_class'] = 'preco-medio'  # Neutro
                elif diff_media <= 2:  # Até 2% acima da média
                    info['css_class'] = 'preco-medio-alto'  # Laranja claro
                else:  # Mais de 2% acima da média
                    info['css_class'] = 'preco-alto'  # Vermelho claro
                
                # Adicionar informação de diferença para exibir
                info['diff_media'] = diff_media
        
        # Só adicionar produtos que têm pelo menos 1 preço
        if linha['postos']:
            matriz_precos.append(linha)
    
    # Estatísticas gerais
    total_postos = len(postos_com_data)
    total_produtos = len(matriz_precos)
    total_precos = PrecoVibra.objects.filter(
        data_coleta__gte=inicio,
        data_coleta__lte=fim,
        disponivel=True
    ).count()
    
    # Última atualização no período
    ultima_coleta = PrecoVibra.objects.filter(
        data_coleta__gte=inicio,
        data_coleta__lte=fim,
        disponivel=True
    ).order_by('-data_coleta').first()
    
    # Montar lista de datas disponíveis para o dropdown
    datas_disponiveis = []
    for data_obj in datas_disponiveis_list:
        datas_disponiveis.append({
            'data': data_obj.strftime('%Y-%m-%d'),
            'label': data_obj.strftime('%d/%m/%Y'),
            'selected': data_filtro == data_obj
        })
    
    context = {
        'postos': postos_com_data,
        'matriz_precos': matriz_precos,
        'total_postos': total_postos,
        'total_produtos': total_produtos,
        'total_precos': total_precos,
        'ultima_atualizacao': ultima_coleta.data_coleta if ultima_coleta else None,
        'data_atual': data_filtro,
        'data_anterior': data_anterior,
        'data_proxima': data_proxima,
        'datas_disponiveis': datas_disponiveis,
        'eh_data_mais_recente': (data_filtro == datas_disponiveis_list[0]) if datas_disponiveis_list else True,
    }
    
    return render(request, 'fuel_prices/dashboard_consolidado.html', context)


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
    
    # Última atualização
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


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def executar_scraper(request):
    """
    Executa o scraper para os postos selecionados em background
    """
    print(f"\n🔵 executar_scraper chamado - Método: {request.method}")
    print(f"🔵 Headers: {dict(request.headers)}")
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)
    
    try:
        # Pegar códigos Vibra dos postos selecionados (JSON)
        import json as json_module
        
        print(f"🔵 Request body: {request.body}")
        
        data = json_module.loads(request.body)
        codigos_selecionados = data.get('postos', [])
        
        print(f"🔵 Postos selecionados: {codigos_selecionados}")
        
        if not codigos_selecionados:
            return JsonResponse({'status': 'error', 'message': 'Nenhum posto selecionado'})
        
        # Executar scraper em background
        def run_scraper_background(codigos):
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                scraper_path = os.path.join(base_dir, 'fuel_prices', 'scrapers', 'vibra_scraper.py')
                
                print(f"\n🚀 Iniciando scraper para {len(codigos)} posto(s): {', '.join(codigos)}")
                
                # Executar scraper passando os códigos como argumentos
                # Exemplo: python vibra_scraper.py --postos 95406 107469
                cmd = ['python', scraper_path, '--postos'] + codigos
                
                print(f"🔵 Comando: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(base_dir, 'fuel_prices', 'scrapers'),
                    timeout=1800  # 30 minutos timeout
                )
                
                if result.returncode == 0:
                    print("✅ Scraper concluído e dados importados!")
                    print(f"Output: {result.stdout}")
                else:
                    print(f"❌ Erro no scraper: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Erro ao executar scraper: {e}")
                import traceback
                traceback.print_exc()
        
        # Iniciar em thread separada
        thread = threading.Thread(target=run_scraper_background, args=(codigos_selecionados,))
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'status': 'iniciado',
            'message': f'Scraper iniciado para {len(codigos_selecionados)} posto(s). Aguarde a atualização...'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao iniciar scraper: {str(e)}'
        })


def api_precos_por_data(request):
    """
    API para retornar preços de uma data específica
    Parâmetro GET: data (formato YYYY-MM-DD)
    """
    from datetime import datetime, date
    
    data_param = request.GET.get('data')
    if not data_param:
        return JsonResponse({
            'status': 'error',
            'message': 'Parâmetro data é obrigatório'
        })
    
    try:
        data_selecionada = datetime.strptime(data_param, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'message': 'Formato de data inválido. Use YYYY-MM-DD'
        })
    
    # Não permitir datas futuras
    if data_selecionada > date.today():
        return JsonResponse({
            'status': 'error',
            'message': 'Não é possível consultar datas futuras'
        })
    
    # Definir range de datas (dia completo)
    inicio_dia = timezone.make_aware(datetime.combine(data_selecionada, datetime.min.time()))
    fim_dia = timezone.make_aware(datetime.combine(data_selecionada, datetime.max.time()))
    
    # Buscar preços
    precos = PrecoVibra.objects.filter(
        data_coleta__gte=inicio_dia,
        data_coleta__lte=fim_dia,
        disponivel=True
    ).select_related('posto').order_by('produto_nome')
    
    if not precos.exists():
        return JsonResponse({
            'status': 'error',
            'message': f'Nenhum dado encontrado para {data_selecionada.strftime("%d/%m/%Y")}'
        })
    
    # Organizar dados por produto
    produtos_dict = {}
    postos_set = set()
    
    for preco in precos:
        produto = preco.produto_nome
        posto_id = preco.posto.id
        postos_set.add(preco.posto.id)
        
        if produto not in produtos_dict:
            produtos_dict[produto] = {}
        
        produtos_dict[produto][posto_id] = {
            'preco': float(preco.preco),
            'prazo': preco.prazo_pagamento,
            'base': preco.base_distribuicao,
            'posto_nome': preco.posto.nome_fantasia,
        }
    
    # Estatísticas
    estatisticas = {
        'total_produtos': len(produtos_dict),
        'total_postos': len(postos_set),
        'total_precos': precos.count(),
    }
    
    return JsonResponse({
        'status': 'success',
        'data': data_selecionada.strftime('%Y-%m-%d'),
        'produtos': produtos_dict,
        'postos': list(postos_set),
        'estatisticas': estatisticas,
    })
