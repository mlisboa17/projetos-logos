"""
Django Admin para ERP Hub
"""
from django.contrib import admin
from .models import ERPIntegration, Store, SyncLog


@admin.register(ERPIntegration)
class ERPIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'erp_type', 'is_active', 'last_sync_at', 'sync_status']
    list_filter = ['erp_type', 'is_active', 'sync_status', 'organization']
    search_fields = ['name', 'description', 'organization__name']
    readonly_fields = ['last_sync_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('organization', 'erp_type', 'name', 'description')
        }),
        ('Credenciais', {
            'fields': ('api_url', 'api_key', 'username', 'password', 'extra_config'),
            'classes': ('collapse',)
        }),
        ('Sincronização', {
            'fields': ('is_active', 'sync_frequency', 'last_sync_at', 'sync_status', 'sync_error')
        }),
        ('Mapeamento', {
            'fields': ('field_mapping',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_super_admin:
            return qs
        return qs.filter(organization__users=request.user)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'city', 'state', 'manager', 'is_active']
    list_filter = ['organization', 'city', 'state', 'is_active']
    search_fields = ['name', 'code', 'address', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('organization', 'name', 'code', 'manager')
        }),
        ('Localização', {
            'fields': ('address', 'city', 'state', 'latitude', 'longitude')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['integration', 'started_at', 'finished_at', 'status', 'records_processed']
    list_filter = ['status', 'integration__erp_type', 'started_at']
    search_fields = ['integration__name', 'error_message']
    readonly_fields = ['started_at', 'finished_at', 'status', 'records_processed', 
                       'records_created', 'records_updated', 'records_failed']
    
    fieldsets = (
        ('Integração', {
            'fields': ('integration',)
        }),
        ('Execução', {
            'fields': ('started_at', 'finished_at', 'status')
        }),
        ('Estatísticas', {
            'fields': ('records_processed', 'records_created', 'records_updated', 'records_failed')
        }),
        ('Detalhes', {
            'fields': ('error_message', 'details'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Logs são criados automaticamente

