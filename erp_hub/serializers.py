from rest_framework import serializers
from .models import ERPIntegration, Store, SyncLog


class ERPIntegrationSerializer(serializers.ModelSerializer):
    """Serializer para ERPIntegration"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    erp_type_display = serializers.CharField(source='get_erp_type_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)
    
    class Meta:
        model = ERPIntegration
        fields = [
            'id', 'organization', 'organization_name', 'erp_type', 
            'erp_type_display', 'name', 'api_url', 'api_key', 'username',
            'password', 'extra_config', 'is_active', 'sync_frequency',
            'last_sync_at', 'sync_status', 'sync_status_display',
            'sync_error', 'field_mapping', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'api_key': {'write_only': True}
        }


class StoreSerializer(serializers.ModelSerializer):
    """Serializer para Store"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    
    class Meta:
        model = Store
        fields = [
            'id', 'organization', 'organization_name', 'name', 'code',
            'address', 'city', 'state', 'latitude', 'longitude',
            'manager', 'manager_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer para SyncLog"""
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SyncLog
        fields = [
            'id', 'integration', 'integration_name', 'started_at',
            'finished_at', 'status', 'status_display', 'records_processed',
            'records_created', 'records_updated', 'records_failed',
            'error_message', 'details'
        ]
        read_only_fields = ['id']
