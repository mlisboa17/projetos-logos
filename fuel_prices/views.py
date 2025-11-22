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
    Dashboard consolidado com matriz de preços:
    Produtos nas linhas, Postos nas colunas
    """
    ultimas_24h = timezone.now() - timedelta(hours=24)
    
    # Pegar todos os postos ativos com preços
    postos = PostoVibra.objects.filter(
        ativo=True,
        precos__data_coleta__gte=ultimas_24h,
        precos__disponivel=True
    ).distinct().order_by('nome_fantasia')
    
    # Pegar todos os produtos únicos
    produtos_nomes = PrecoVibra.objects.filter(
        data_coleta__gte=ultimas_24h,
        disponivel=True
    ).values_list('produto_nome', flat=True).distinct().order_by('produto_nome')
    
    # Construir matriz de preços
    produtos_comparacao = {}
    
    for produto_nome in produtos_nomes:
        # Pegar todos os preços deste produto
        precos = PrecoVibra.objects.filter(
            produto_nome=produto_nome,
            data_coleta__gte=ultimas_24h,
            disponivel=True
        ).select_related('posto')
        
        if not precos.exists():
            continue
        
        # Organizar preços por CNPJ do posto
        precos_por_posto = {}
        precos_valores = []
        
        for preco in precos:
            cnpj = preco.posto.cnpj
            precos_por_posto[cnpj] = {
                'preco': float(preco.preco),
                'prazo': preco.prazo_pagamento,
                'base': preco.base_distribuicao,
            }
            precos_valores.append(float(preco.preco))
        
        # Calcular estatísticas
        preco_min = min(precos_valores) if precos_valores else 0
        preco_max = max(precos_valores) if precos_valores else 0
        variacao = ((preco_max - preco_min) / preco_min * 100) if preco_min > 0 else 0
        
        produtos_comparacao[produto_nome] = {
            'precos_por_posto': precos_por_posto,
            'preco_min': preco_min,
            'preco_max': preco_max,
            'variacao': variacao,
        }
    
    # Estatísticas gerais
    total_postos = postos.count()
    total_produtos = len(produtos_comparacao)
    total_precos = PrecoVibra.objects.filter(
        data_coleta__gte=ultimas_24h,
        disponivel=True
    ).count()
    
    # Última atualização
    ultima_coleta = PrecoVibra.objects.filter(
        disponivel=True
    ).order_by('-data_coleta').first()
    
    # Todos os postos cadastrados (para o modal de scraper)
    todos_postos = PostoVibra.objects.filter(ativo=True).order_by('nome_fantasia')
    
    context = {
        'postos': postos,
        'todos_postos': todos_postos,
        'produtos_comparacao': produtos_comparacao,
        'total_postos': total_postos,
        'total_produtos': total_produtos,
        'total_precos': total_precos,
        'ultima_atualizacao': ultima_coleta.data_coleta.strftime('%d/%m/%Y %H:%M') if ultima_coleta else None,
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


def executar_scraper(request):
    """
    Executa o scraper para os postos selecionados em background
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)
    
    try:
        # Pegar CNPJs dos postos selecionados
        cnpjs_selecionados = request.POST.getlist('postos')
        
        if not cnpjs_selecionados:
            return JsonResponse({'status': 'error', 'message': 'Nenhum posto selecionado'})
        
        # Variável para armazenar status da execução
        execution_status = {'success': False, 'error': None}
        
        # Função para executar em background
        def run_scraper_background(cnpjs, status_dict):
            try:
                # Caminho do script de scraper
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                scraper_path = os.path.join(base_dir, 'fuel_prices', 'scrapers', 'vibra_scraper.py')
                
                # Criar arquivo temporário com lista de CNPJs
                temp_file = os.path.join(base_dir, f'temp_postos_{threading.get_ident()}.json')
                with open(temp_file, 'w') as f:
                    json.dump(cnpjs, f)
                
                print(f"\n🚀 Iniciando scraper para {len(cnpjs)} posto(s)...")
                
                # Executar scraper
                result = subprocess.run(
                    ['python', scraper_path, '--cnpjs-file', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutos timeout
                )
                
                # Remover arquivo temporário
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                # Se scraper foi bem sucedido, executar importação
                if result.returncode == 0:
                    print("✅ Scraper concluído. Importando dados...")
                    import_script = os.path.join(base_dir, 'import_vibra_data.py')
                    import_result = subprocess.run(
                        ['python', import_script],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if import_result.returncode == 0:
                        print("✅ Importação concluída com sucesso!")
                        status_dict['success'] = True
                    else:
                        print(f"❌ Erro na importação: {import_result.stderr}")
                        status_dict['error'] = f"Erro na importação: {import_result.stderr}"
                else:
                    print(f"❌ Erro no scraper: {result.stderr}")
                    status_dict['error'] = f"Erro no scraper: {result.stderr}"
                    
            except subprocess.TimeoutExpired:
                print("❌ Timeout: Scraper demorou muito tempo")
                status_dict['error'] = "Timeout: O scraper demorou muito tempo (mais de 10 minutos)"
            except Exception as e:
                print(f"❌ Erro no scraper background: {e}")
                status_dict['error'] = str(e)
        
        # Iniciar thread em background
        thread = threading.Thread(target=run_scraper_background, args=(cnpjs_selecionados, execution_status))
        thread.daemon = True
        thread.start()
        
        # Retornar resposta imediata
        return JsonResponse({
            'status': 'started',
            'message': 'Coleta iniciada em background',
            'postos_selecionados': len(cnpjs_selecionados),
            'tempo_estimado': len(cnpjs_selecionados) * 2
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao iniciar scraper: {str(e)}'
        })
