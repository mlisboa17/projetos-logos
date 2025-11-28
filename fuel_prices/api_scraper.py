"""
API Views para receber dados do scraper standalone
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import PostoVibra, PrecoVibra


@csrf_exempt
@require_http_methods(["POST"])
def receber_dados_scraper(request):
    """
    Endpoint para receber dados do scraper standalone
    
    Formato esperado:
    {
        "posto": {
            "codigo_vibra": "95406",
            "cnpj": "04284939000186",
            "razao_social": "AUTO POSTO CASA CAIADA LTDA",
            "nome_fantasia": "AP CASA CAIADA"
        },
        "produtos": [
            {
                "nome": "ETANOL COMUM",
                "preco": "Preço: R$ 3,6377",
                "prazo": "30 dias",
                "base": "Base Suape"
            }
        ],
        "data_coleta": "2025-11-28T15:30:00",
        "modalidade": "FOB"
    }
    """
    try:
        # Parse do JSON
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        if 'posto' not in data or 'produtos' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Dados obrigatórios ausentes: posto, produtos'
            }, status=400)
        
        posto_info = data['posto']
        produtos_lista = data['produtos']
        modalidade = data.get('modalidade', 'FOB')
        
        # Validar posto
        required_posto_fields = ['codigo_vibra', 'cnpj', 'razao_social', 'nome_fantasia']
        for field in required_posto_fields:
            if field not in posto_info:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Campo obrigatório do posto ausente: {field}'
                }, status=400)
        
        # Criar ou atualizar posto
        posto, created = PostoVibra.objects.get_or_create(
            cnpj=posto_info['cnpj'],
            defaults={
                'codigo_vibra': posto_info['codigo_vibra'],
                'razao_social': posto_info['razao_social'],
                'nome_fantasia': posto_info['nome_fantasia'],
                'ativo': True
            }
        )
        
        if not created:
            # Atualizar informações se já existe
            posto.codigo_vibra = posto_info['codigo_vibra']
            posto.razao_social = posto_info['razao_social']
            posto.nome_fantasia = posto_info['nome_fantasia']
            posto.ativo = True
            posto.save()
        
        # Processar produtos
        precos_salvos = 0
        precos_erros = 0
        
        for produto in produtos_lista:
            try:
                # Converter preço de string para decimal
                # Formato: "Preço: R$ 3,6377" -> 3.6377
                preco_str = produto.get('preco', '')
                if not preco_str:
                    precos_erros += 1
                    continue
                
                # Limpar e converter preço
                preco_limpo = preco_str.replace('Preço:', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    preco_decimal = float(preco_limpo)
                except ValueError:
                    print(f"Erro ao converter preço: {preco_str} -> {preco_limpo}")
                    precos_erros += 1
                    continue
                
                # Criar registro de preço
                PrecoVibra.objects.create(
                    posto=posto,
                    produto_nome=produto.get('nome', ''),
                    produto_codigo='',  # Scraper não coleta código
                    preco=preco_decimal,
                    prazo_pagamento=produto.get('prazo', ''),
                    base_distribuicao=produto.get('base', ''),
                    modalidade=modalidade,
                    data_coleta=timezone.now(),
                    disponivel=True
                )
                precos_salvos += 1
                
            except Exception as e:
                print(f"Erro ao processar produto {produto.get('nome', 'N/A')}: {e}")
                precos_erros += 1
                continue
        
        return JsonResponse({
            'status': 'success',
            'message': 'Dados recebidos e salvos com sucesso',
            'detalhes': {
                'posto_codigo': posto.codigo_vibra,
                'posto_nome': posto.nome_fantasia,
                'posto_criado': created,
                'precos_salvos': precos_salvos,
                'precos_erros': precos_erros,
                'total_produtos': len(produtos_lista)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def status_sistema(request):
    """
    Endpoint para verificar se o sistema principal está funcionando
    """
    from django.db import connection
    
    try:
        # Testar conexão com banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Contar registros recentes
        total_postos = PostoVibra.objects.filter(ativo=True).count()
        total_precos = PrecoVibra.objects.filter(
            data_coleta__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return JsonResponse({
            'status': 'online',
            'sistema': 'Fuel Prices - Sistema Principal',
            'versao': '1.0',
            'database': 'conectado',
            'estatisticas': {
                'postos_ativos': total_postos,
                'precos_ultima_semana': total_precos
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro no sistema: {str(e)}'
        }, status=500)