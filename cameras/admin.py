from django.contrib import admin
from .models import Camera, Event, Alert, CameraSchedule, AIModel


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'store', 'status', 'is_active', 'ai_enabled', 'total_events']
    list_filter = ['status', 'is_active', 'ai_enabled', 'organization', 'store']
    search_fields = ['name', 'code', 'location', 'ip_address']
    readonly_fields = ['total_events', 'last_frame_at', 'uptime_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('organization', 'store', 'name', 'code', 'location', 'description')
        }),
        ('Conexão', {
            'fields': ('stream_url', 'ip_address', 'port', 'username', 'password')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'is_recording')
        }),
        ('Configuração IA', {
            'fields': ('ai_enabled', 'ai_model', 'confidence_threshold', 'detection_fps', 
                      'detection_classes', 'roi_polygon'),
            'classes': ['collapse']
        }),
        ('Gravação', {
            'fields': ('storage_path', 'retention_days'),
            'classes': ['collapse']
        }),
        ('Estatísticas', {
            'fields': ('last_frame_at', 'total_events', 'uptime_percentage', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_super_admin:
            return qs
        return qs.filter(organization=request.user.organization)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'camera', 'severity', 'confidence', 'detected_at', 
                    'acknowledged', 'false_positive']
    list_filter = ['event_type', 'severity', 'acknowledged', 'false_positive', 'detected_at']
    search_fields = ['camera__name', 'action_taken']
    readonly_fields = ['detected_at', 'snapshot_path', 'video_clip_path', 'detected_objects']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Evento', {
            'fields': ('camera', 'event_type', 'severity', 'confidence')
        }),
        ('Detecção', {
            'fields': ('detected_objects', 'snapshot_path', 'video_clip_path', 'detected_at')
        }),
        ('Resposta', {
            'fields': ('acknowledged', 'acknowledged_by', 'acknowledged_at', 
                      'action_taken', 'false_positive')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ['collapse']
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_super_admin:
            return qs
        return qs.filter(camera__organization=request.user.organization)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'channel', 'sent', 'read', 'created_at']
    list_filter = ['channel', 'sent', 'read', 'created_at']
    search_fields = ['subject', 'message', 'user__username']
    readonly_fields = ['event', 'sent_at', 'read_at', 'created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_super_admin:
            return qs
        return qs.filter(user__organization=request.user.organization)


@admin.register(CameraSchedule)
class CameraScheduleAdmin(admin.ModelAdmin):
    list_display = ['camera', 'weekday', 'start_time', 'end_time', 
                    'enable_recording', 'enable_detection', 'is_active']
    list_filter = ['weekday', 'is_active', 'enable_recording', 'enable_detection']
    search_fields = ['camera__name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_super_admin:
            return qs
        return qs.filter(camera__organization=request.user.organization)


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'model_type', 'accuracy', 'is_active', 'is_default']
    list_filter = ['model_type', 'is_active', 'is_default']
    search_fields = ['name', 'version']
    readonly_fields = ['avg_inference_time', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações', {
            'fields': ('organization', 'name', 'version', 'model_file', 'model_type')
        }),
        ('Configuração', {
            'fields': ('classes', 'is_active', 'is_default')
        }),
        ('Performance', {
            'fields': ('avg_inference_time', 'accuracy', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
