"""
API para alimentar sistema Logus/Price com dados coletados
Fornece endpoints para consultar preços de combustível em formato padronizado
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from .models import PrecoVibra, PostoVibra
from django.db.models import Q, Max
import json


@csrf_exempt
def api_precos_atual(request):
    """
    API para obter preços atuais de combustível
    
    GET /fuel_prices/api/precos-atual/
    
    Retorna preços mais recentes de cada posto/produto
    """
    try:
        # Buscar preços das últimas 24 horas
        ontem = timezone.now() - timedelta(days=1)
        
        # Obter preços mais recentes por posto e produto
        precos_recentes = PrecoVibra.objects.filter(
            data_coleta__gte=ontem
        ).values(
            'posto__nome_fantasia',
            'posto__codigo_vibra', 
            'posto__cnpj',
            'produto_nome',
            'produto_codigo'
        ).annotate(
            data_mais_recente=Max('data_coleta')
        )
        
        # Buscar dados completos dos preços mais recentes
        precos_finais = []
        for item in precos_recentes:
            preco_obj = PrecoVibra.objects.filter(
                posto__nome_fantasia=item['posto__nome_fantasia'],
                produto_nome=item['produto_nome'],
                data_coleta=item['data_mais_recente']
            ).first()
            
            if preco_obj:
                precos_finais.append({
                    'posto': {
                        'nome': preco_obj.posto.nome_fantasia,
                        'codigo': preco_obj.posto.codigo_vibra,
                        'cnpj': preco_obj.posto.cnpj,
                        'razao_social': preco_obj.posto.razao_social
                    },
                    'combustivel': {
                        'nome': preco_obj.produto_nome,
                        'codigo': preco_obj.produto_codigo
                    },
                    'preco': {
                        'valor': float(preco_obj.preco),
                        'prazo_pagamento': preco_obj.prazo_pagamento,
                        'modalidade': preco_obj.modalidade,
                        'base_distribuicao': preco_obj.base_distribuicao
                    },
                    'coleta': {
                        'data_hora': preco_obj.data_coleta.isoformat(),
                        'disponivel': preco_obj.disponivel
                    }
                })
        
        response = {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'total_precos': len(precos_finais),
            'periodo_coleta': '24 horas',
            'dados': precos_finais
        }
        
        return JsonResponse(response, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt  
def api_precos_posto(request, codigo_posto):
    """
    API para obter preços de um posto específico
    
    GET /fuel_prices/api/precos-posto/<codigo>/
    """
    try:
        # Buscar posto
        try:
            posto = PostoVibra.objects.get(codigo_vibra=codigo_posto)
        except PostoVibra.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Posto com código {codigo_posto} não encontrado'
            }, status=404)
        
        # Buscar preços das últimas 24 horas
        ontem = timezone.now() - timedelta(days=1)
        precos = PrecoVibra.objects.filter(
            posto=posto,
            data_coleta__gte=ontem
        ).order_by('-data_coleta')
        
        dados_precos = []
        for preco in precos:
            dados_precos.append({
                'combustivel': {
                    'nome': preco.produto_nome,
                    'codigo': preco.produto_codigo
                },
                'preco': {
                    'valor': float(preco.preco),
                    'prazo_pagamento': preco.prazo_pagamento,
                    'modalidade': preco.modalidade,
                    'base_distribuicao': preco.base_distribuicao
                },
                'coleta': {
                    'data_hora': preco.data_coleta.isoformat(),
                    'disponivel': preco.disponivel
                }
            })
        
        response = {
            'status': 'success',
            'posto': {
                'nome': posto.nome_fantasia,
                'codigo': posto.codigo_vibra,
                'cnpj': posto.cnpj,
                'razao_social': posto.razao_social
            },
            'timestamp': timezone.now().isoformat(),
            'total_precos': len(dados_precos),
            'dados': dados_precos
        }
        
        return JsonResponse(response, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
def api_resumo_postos(request):
    """
    API para obter resumo de todos os postos
    
    GET /fuel_prices/api/resumo-postos/
    """
    try:
        # Buscar todos os postos ativos
        postos = PostoVibra.objects.filter(ativo=True)
        
        resumo_postos = []
        for posto in postos:
            # Contar preços das últimas 24 horas
            ontem = timezone.now() - timedelta(days=1)
            total_precos_recentes = PrecoVibra.objects.filter(
                posto=posto,
                data_coleta__gte=ontem
            ).count()
            
            # Última coleta
            ultimo_preco = PrecoVibra.objects.filter(
                posto=posto
            ).order_by('-data_coleta').first()
            
            resumo_postos.append({
                'codigo': posto.codigo_vibra,
                'nome': posto.nome_fantasia,
                'cnpj': posto.cnpj,
                'razao_social': posto.razao_social,
                'ativo': posto.ativo,
                'estatisticas': {
                    'precos_24h': total_precos_recentes,
                    'ultima_coleta': ultimo_preco.data_coleta.isoformat() if ultimo_preco else None,
                    'tem_dados_recentes': total_precos_recentes > 0
                }
            })
        
        response = {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'total_postos': len(resumo_postos),
            'dados': resumo_postos
        }
        
        return JsonResponse(response, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
def api_logus_feed(request):
    """
    API específica para alimentar sistema Logus/Price
    Formato otimizado para integração
    
    GET /fuel_prices/api/logus-feed/
    """
    try:
        # Buscar preços das últimas 6 horas (dados mais frescos)
        periodo = timezone.now() - timedelta(hours=6)
        
        # Query otimizada para o feed do Logus
        precos_logus = PrecoVibra.objects.filter(
            data_coleta__gte=periodo,
            disponivel=True
        ).select_related('posto').order_by('-data_coleta')
        
        # Agrupar por posto para melhor organização
        feed_data = {}
        
        for preco in precos_logus:
            posto_codigo = preco.posto.codigo_vibra
            
            if posto_codigo not in feed_data:
                feed_data[posto_codigo] = {
                    'posto_info': {
                        'codigo': preco.posto.codigo_vibra,
                        'nome': preco.posto.nome_fantasia,
                        'cnpj': preco.posto.cnpj,
                        'razao_social': preco.posto.razao_social
                    },
                    'combustiveis': []
                }
            
            # Adicionar combustível
            feed_data[posto_codigo]['combustiveis'].append({
                'produto': preco.produto_nome,
                'codigo_produto': preco.produto_codigo,
                'preco_unitario': float(preco.preco),
                'prazo_dias': preco.prazo_pagamento,
                'modalidade_frete': preco.modalidade,
                'base_distribuicao': preco.base_distribuicao,
                'data_coleta': preco.data_coleta.isoformat(),
                'timestamp_unix': int(preco.data_coleta.timestamp())
            })
        
        # Converter para lista
        postos_lista = list(feed_data.values())
        
        response = {
            'sistema': 'Fuel Prices - Feed Logus',
            'versao': '1.0',
            'status': 'online',
            'timestamp_geracao': timezone.now().isoformat(),
            'periodo_dados': '6 horas',
            'total_postos': len(postos_lista),
            'total_precos': sum(len(posto['combustiveis']) for posto in postos_lista),
            'postos': postos_lista
        }
        
        return JsonResponse(response, safe=False, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            'sistema': 'Fuel Prices - Feed Logus',
            'status': 'error',
            'erro': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)