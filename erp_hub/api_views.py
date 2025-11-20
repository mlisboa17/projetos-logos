from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ERPIntegration, Store, SyncLog
from .serializers import ERPIntegrationSerializer, StoreSerializer, SyncLogSerializer


class ERPIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet para ERPIntegration"""
    queryset = ERPIntegration.objects.all()
    serializer_class = ERPIntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra ERPs baseado na organização do usuário"""
        user = self.request.user
        
        # Super admin vê todos
        if user.is_super_admin or user.is_superuser:
            return ERPIntegration.objects.all()
        
        # Usuários veem apenas ERPs da sua organização
        return ERPIntegration.objects.filter(organization=user.organization)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Testa conexão com o ERP"""
        integration = self.get_object()
        
        # TODO: Implementar teste de conexão real
        return Response({
            "status": "success",
            "message": f"Conexão com {integration.name} testada com sucesso!",
            "erp_type": integration.erp_type
        })
    
    @action(detail=True, methods=['post'])
    def sync_now(self, request, pk=None):
        """Inicia sincronização manual"""
        integration = self.get_object()
        
        if not integration.is_active:
            return Response(
                {"detail": "Integração está inativa."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implementar sincronização real (Celery task)
        return Response({
            "status": "started",
            "message": f"Sincronização iniciada para {integration.name}",
            "integration_id": integration.id
        })


class StoreViewSet(viewsets.ModelViewSet):
    """ViewSet para Store"""
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra stores baseado na organização do usuário"""
        user = self.request.user
        
        # Super admin vê todas
        if user.is_super_admin or user.is_superuser:
            return Store.objects.all()
        
        # Usuários veem apenas lojas da sua organização
        return Store.objects.filter(organization=user.organization)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Retorna lojas próximas (requer lat/lng na query)"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {"detail": "Parâmetros 'lat' e 'lng' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implementar busca geográfica real
        stores = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(stores, many=True)
        
        return Response(serializer.data)


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para SyncLog (apenas leitura)"""
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra logs baseado na organização do usuário"""
        user = self.request.user
        
        # Super admin vê todos
        if user.is_super_admin or user.is_superuser:
            return SyncLog.objects.all()
        
        # Usuários veem apenas logs de ERPs da sua organização
        return SyncLog.objects.filter(
            integration__organization=user.organization
        )
