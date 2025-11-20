from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Camera, Event, Alert, AIModel


@login_required
def dashboard(request):
    """Dashboard principal do VerifiK"""
    user = request.user
    organization = user.organization
    
    # Estatísticas de câmeras
    cameras = Camera.objects.filter(organization=organization)
    cameras_online = cameras.filter(status='online').count()
    cameras_total = cameras.count()
    cameras_ai_enabled = cameras.filter(ai_enabled=True).count()
    
    # Eventos recentes (últimas 24h)
    from django.utils import timezone
    from datetime import timedelta
    
    last_24h = timezone.now() - timedelta(hours=24)
    events_24h = Event.objects.filter(
        camera__organization=organization,
        detected_at__gte=last_24h
    )
    
    events_total = events_24h.count()
    events_critical = events_24h.filter(severity='critical').count()
    events_unacknowledged = events_24h.filter(acknowledged=False).count()
    
    # Alertas não lidos
    alerts_unread = Alert.objects.filter(
        user=user,
        read=False
    ).count()
    
    # Modelos IA disponíveis
    ai_models = AIModel.objects.filter(is_active=True)
    
    # Últimos eventos
    recent_events = Event.objects.filter(
        camera__organization=organization
    ).select_related('camera').order_by('-detected_at')[:10]
    
    # Câmeras para grid
    camera_list = cameras.select_related('store', 'ai_model').order_by('name')
    
    context = {
        'cameras_online': cameras_online,
        'cameras_total': cameras_total,
        'cameras_ai_enabled': cameras_ai_enabled,
        'events_total': events_total,
        'events_critical': events_critical,
        'events_unacknowledged': events_unacknowledged,
        'alerts_unread': alerts_unread,
        'ai_models': ai_models,
        'recent_events': recent_events,
        'camera_list': camera_list,
    }
    
    return render(request, 'cameras/dashboard.html', context)


@login_required
def camera_detail(request, camera_id):
    """Detalhes de uma câmera específica"""
    camera = Camera.objects.get(id=camera_id, organization=request.user.organization)
    
    # Eventos da câmera (últimos 7 dias)
    from django.utils import timezone
    from datetime import timedelta
    
    last_7_days = timezone.now() - timedelta(days=7)
    events = Event.objects.filter(
        camera=camera,
        detected_at__gte=last_7_days
    ).order_by('-detected_at')[:50]
    
    # Estatísticas
    events_by_type = events.values('event_type').annotate(count=Count('id'))
    events_by_severity = events.values('severity').annotate(count=Count('id'))
    
    context = {
        'camera': camera,
        'events': events,
        'events_by_type': events_by_type,
        'events_by_severity': events_by_severity,
    }
    
    return render(request, 'cameras/camera_detail.html', context)


@login_required
def events_list(request):
    """Lista de eventos com filtros"""
    organization = request.user.organization
    events = Event.objects.filter(camera__organization=organization)
    
    # Filtros
    event_type = request.GET.get('event_type')
    severity = request.GET.get('severity')
    camera_id = request.GET.get('camera')
    acknowledged = request.GET.get('acknowledged')
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    if severity:
        events = events.filter(severity=severity)
    
    if camera_id:
        events = events.filter(camera_id=camera_id)
    
    if acknowledged == 'true':
        events = events.filter(acknowledged=True)
    elif acknowledged == 'false':
        events = events.filter(acknowledged=False)
    
    events = events.select_related('camera').order_by('-detected_at')[:100]
    
    # Para os filtros
    cameras = Camera.objects.filter(organization=organization)
    
    context = {
        'events': events,
        'cameras': cameras,
        'selected_type': event_type,
        'selected_severity': severity,
        'selected_camera': camera_id,
        'selected_acknowledged': acknowledged,
    }
    
    return render(request, 'cameras/events_list.html', context)
