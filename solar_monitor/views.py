from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum, Max, Min, Count
from .models import UsinaSolar, LeituraUsina, AlertaUsina, RelatorioMensal


@login_required
def dashboard(request):
    """Dashboard principal do monitoramento solar"""
    usinas = UsinaSolar.objects.filter(ativa=True)
    
    # Estatísticas gerais
    total_capacidade = usinas.aggregate(total=Sum('capacidade_kwp'))['total'] or 0
    total_usinas = usinas.count()
    
    # Última hora
    ultima_hora = timezone.now() - timedelta(hours=1)
    leituras_recentes = LeituraUsina.objects.filter(
        timestamp__gte=ultima_hora,
        usina__ativa=True
    )
    
    potencia_atual_total = leituras_recentes.values('usina').annotate(
        ultima=Max('timestamp')
    ).aggregate(total=Sum('potencia_atual_kw'))['total'] or 0
    
    # Alertas não resolvidos
    alertas_pendentes = AlertaUsina.objects.filter(
        resolvido=False,
        usina__ativa=True
    ).order_by('-timestamp')[:5]
    
    # Dados de hoje
    hoje = timezone.now().date()
    energia_hoje = LeituraUsina.objects.filter(
        timestamp__date=hoje,
        usina__ativa=True
    ).aggregate(total=Sum('energia_dia_kwh'))['total'] or 0
    
    context = {
        'usinas': usinas,
        'total_capacidade': total_capacidade,
        'total_usinas': total_usinas,
        'potencia_atual_total': potencia_atual_total,
        'energia_hoje': energia_hoje,
        'alertas_pendentes': alertas_pendentes,
    }
    
    return render(request, 'solar_monitor/dashboard.html', context)


@login_required
def usina_detalhes(request, usina_id):
    """Detalhes de uma usina específica"""
    usina = get_object_or_404(UsinaSolar, id=usina_id)
    
    # Última leitura
    ultima_leitura = usina.leituras.first()
    
    # Leituras do dia
    hoje = timezone.now().date()
    leituras_hoje = usina.leituras.filter(timestamp__date=hoje)
    
    # Estatísticas do dia
    stats_hoje = leituras_hoje.aggregate(
        max_potencia=Max('potencia_atual_kw'),
        media_eficiencia=Avg('eficiencia_percent'),
        total_energia=Sum('energia_dia_kwh')
    )
    
    # Últimos 7 dias
    semana_atras = timezone.now() - timedelta(days=7)
    leituras_semana = usina.leituras.filter(timestamp__gte=semana_atras)
    
    # Alertas recentes
    alertas_recentes = usina.alertas.filter(resolvido=False)[:10]
    
    context = {
        'usina': usina,
        'ultima_leitura': ultima_leitura,
        'stats_hoje': stats_hoje,
        'leituras_hoje': leituras_hoje[:50],
        'alertas_recentes': alertas_recentes,
    }
    
    return render(request, 'solar_monitor/usina_detalhes.html', context)


@login_required
def api_leituras_realtime(request, usina_id):
    """API JSON para dados em tempo real"""
    usina = get_object_or_404(UsinaSolar, id=usina_id)
    
    # Últimas 100 leituras
    leituras = usina.leituras.all()[:100]
    
    dados = {
        'usina': {
            'id': usina.id,
            'nome': usina.nome,
            'capacidade_kwp': float(usina.capacidade_kwp),
        },
        'leituras': [
            {
                'timestamp': l.timestamp.isoformat(),
                'potencia_atual_kw': float(l.potencia_atual_kw),
                'energia_dia_kwh': float(l.energia_dia_kwh),
                'eficiencia_percent': float(l.eficiencia_percent) if l.eficiencia_percent else None,
                'temperatura_modulo_c': float(l.temperatura_modulo_c) if l.temperatura_modulo_c else None,
                'status': l.status,
            }
            for l in leituras
        ]
    }
    
    return JsonResponse(dados)


@login_required
def api_status_geral(request):
    """API JSON para status geral de todas as usinas"""
    usinas = UsinaSolar.objects.filter(ativa=True)
    
    dados = []
    for usina in usinas:
        ultima = usina.ultima_leitura
        dados.append({
            'id': usina.id,
            'nome': usina.nome,
            'capacidade_kwp': float(usina.capacidade_kwp),
            'localizacao': usina.localizacao,
            'status': ultima.status if ultima else 'offline',
            'potencia_atual_kw': float(ultima.potencia_atual_kw) if ultima else 0,
            'energia_dia_kwh': float(ultima.energia_dia_kwh) if ultima else 0,
            'ultima_atualizacao': ultima.timestamp.isoformat() if ultima else None,
        })
    
    return JsonResponse({'usinas': dados})


@login_required
def relatorios(request):
    """Página de relatórios mensais"""
    usinas = UsinaSolar.objects.filter(ativa=True)
    
    # Filtros
    usina_id = request.GET.get('usina')
    ano = request.GET.get('ano', timezone.now().year)
    
    relatorios_query = RelatorioMensal.objects.all()
    
    if usina_id:
        relatorios_query = relatorios_query.filter(usina_id=usina_id)
    
    if ano:
        relatorios_query = relatorios_query.filter(ano=ano)
    
    relatorios_lista = relatorios_query.order_by('-ano', '-mes')[:12]
    
    context = {
        'usinas': usinas,
        'relatorios': relatorios_lista,
        'ano_selecionado': ano,
        'usina_selecionada': usina_id,
    }
    
    return render(request, 'solar_monitor/relatorios.html', context)


@login_required
def alertas(request):
    """Página de gestão de alertas"""
    filtro = request.GET.get('filtro', 'pendentes')
    
    if filtro == 'todos':
        alertas_lista = AlertaUsina.objects.all()
    elif filtro == 'resolvidos':
        alertas_lista = AlertaUsina.objects.filter(resolvido=True)
    else:  # pendentes
        alertas_lista = AlertaUsina.objects.filter(resolvido=False)
    
    alertas_lista = alertas_lista.select_related('usina').order_by('-timestamp')[:100]
    
    # Estatísticas
    stats = {
        'total': AlertaUsina.objects.count(),
        'pendentes': AlertaUsina.objects.filter(resolvido=False).count(),
        'criticos': AlertaUsina.objects.filter(tipo='critico', resolvido=False).count(),
    }
    
    context = {
        'alertas': alertas_lista,
        'filtro': filtro,
        'stats': stats,
    }
    
    return render(request, 'solar_monitor/alertas.html', context)

