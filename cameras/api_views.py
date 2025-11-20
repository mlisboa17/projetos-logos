from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Avg
from .models import Camera, Event, Alert, CameraSchedule, AIModel, CameraStatus
from .serializers import (
    CameraSerializer, EventSerializer, AlertSerializer,
    CameraScheduleSerializer, AIModelSerializer, CameraStatsSerializer
)


class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet para Cameras"""
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra cameras baseado na organização"""
        user = self.request.user
        
        if user.is_super_admin or user.is_superuser:
            return Camera.objects.all()
        
        return Camera.objects.filter(organization=user.organization)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas gerais das câmeras"""
        queryset = self.get_queryset()
        
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_cameras': queryset.count(),
            'online_cameras': queryset.filter(status=CameraStatus.ONLINE).count(),
            'offline_cameras': queryset.filter(status=CameraStatus.OFFLINE).count(),
            'total_events_today': Event.objects.filter(
                camera__in=queryset,
                detected_at__date=today
            ).count(),
            'total_events_week': Event.objects.filter(
                camera__in=queryset,
                detected_at__gte=week_ago
            ).count(),
            'unacknowledged_events': Event.objects.filter(
                camera__in=queryset,
                acknowledged=False
            ).count(),
            'avg_uptime': queryset.aggregate(Avg('uptime_percentage'))['uptime_percentage__avg'] or 0
        }
        
        serializer = CameraStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_recording(self, request, pk=None):
        """Iniciar gravação"""
        camera = self.get_object()
        camera.is_recording = True
        camera.save()
        
        return Response({
            'status': 'success',
            'message': f'Gravação iniciada para {camera.name}'
        })
    
    @action(detail=True, methods=['post'])
    def stop_recording(self, request, pk=None):
        """Parar gravação"""
        camera = self.get_object()
        camera.is_recording = False
        camera.save()
        
        return Response({
            'status': 'success',
            'message': f'Gravação parada para {camera.name}'
        })
    
    @action(detail=True, methods=['post'])
    def enable_ai(self, request, pk=None):
        """Habilitar IA"""
        camera = self.get_object()
        camera.ai_enabled = True
        camera.save()
        
        return Response({
            'status': 'success',
            'message': f'IA habilitada para {camera.name}'
        })
    
    @action(detail=True, methods=['post'])
    def disable_ai(self, request, pk=None):
        """Desabilitar IA"""
        camera = self.get_object()
        camera.ai_enabled = False
        camera.save()
        
        return Response({
            'status': 'success',
            'message': f'IA desabilitada para {camera.name}'
        })
    
    @action(detail=True, methods=['get'])
    def live_stream(self, request, pk=None):
        """Retorna URL do stream ao vivo"""
        camera = self.get_object()
        
        if camera.status != CameraStatus.ONLINE:
            return Response(
                {'detail': 'Câmera offline'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            'stream_url': camera.stream_url,
            'camera': CameraSerializer(camera).data
        })


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet para Events"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra events baseado na organização"""
        user = self.request.user
        
        if user.is_super_admin or user.is_superuser:
            queryset = Event.objects.all()
        else:
            queryset = Event.objects.filter(camera__organization=user.organization)
        
        # Filtros via query params
        event_type = self.request.query_params.get('event_type')
        severity = self.request.query_params.get('severity')
        acknowledged = self.request.query_params.get('acknowledged')
        camera_id = self.request.query_params.get('camera')
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Reconhecer evento"""
        event = self.get_object()
        action_taken = request.data.get('action_taken', '')
        
        event.acknowledged = True
        event.acknowledged_by = request.user
        event.acknowledged_at = timezone.now()
        event.action_taken = action_taken
        event.save()
        
        return Response({
            'status': 'success',
            'message': 'Evento reconhecido',
            'event': EventSerializer(event).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_false_positive(self, request, pk=None):
        """Marcar como falso positivo"""
        event = self.get_object()
        event.false_positive = True
        event.acknowledged = True
        event.acknowledged_by = request.user
        event.acknowledged_at = timezone.now()
        event.save()
        
        return Response({
            'status': 'success',
            'message': 'Evento marcado como falso positivo'
        })
    
    @action(detail=False, methods=['get'])
    def unacknowledged(self, request):
        """Lista eventos não reconhecidos"""
        queryset = self.get_queryset().filter(acknowledged=False)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet para Alerts"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra alerts do usuário"""
        user = self.request.user
        
        if user.is_super_admin or user.is_superuser:
            return Alert.objects.all()
        
        return Alert.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marcar alerta como lido"""
        alert = self.get_object()
        alert.read = True
        alert.read_at = timezone.now()
        alert.save()
        
        return Response({
            'status': 'success',
            'message': 'Alerta marcado como lido'
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todos alertas como lidos"""
        count = self.get_queryset().filter(read=False).update(
            read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'message': f'{count} alertas marcados como lidos'
        })
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Lista alertas não lidos"""
        queryset = self.get_queryset().filter(read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CameraScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet para CameraSchedule"""
    queryset = CameraSchedule.objects.all()
    serializer_class = CameraScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra schedules baseado na organização"""
        user = self.request.user
        
        if user.is_super_admin or user.is_superuser:
            return CameraSchedule.objects.all()
        
        return CameraSchedule.objects.filter(camera__organization=user.organization)


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para AIModel (somente leitura)"""
    queryset = AIModel.objects.filter(is_active=True)
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra modelos disponíveis"""
        user = self.request.user
        
        # Retorna modelos globais + modelos da organização
        return AIModel.objects.filter(
            Q(organization__isnull=True) | Q(organization=user.organization),
            is_active=True
        )
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Retorna modelo padrão"""
        model = self.get_queryset().filter(is_default=True).first()
        
        if not model:
            return Response(
                {'detail': 'Nenhum modelo padrão configurado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(model)
        return Response(serializer.data)
