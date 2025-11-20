from rest_framework import serializers
from .models import Camera, Event, Alert, CameraSchedule, AIModel


class CameraSerializer(serializers.ModelSerializer):
    """Serializer para Camera"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Camera
        fields = [
            'id', 'organization', 'organization_name', 'store', 'store_name',
            'name', 'code', 'location', 'description', 'stream_url',
            'ip_address', 'port', 'username', 'password', 'status',
            'status_display', 'is_active', 'is_recording', 'is_online',
            'ai_enabled', 'ai_model', 'confidence_threshold', 'detection_fps',
            'detection_classes', 'roi_polygon', 'storage_path', 'retention_days',
            'last_frame_at', 'total_events', 'uptime_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_events', 'last_frame_at', 'uptime_percentage', 
                           'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class EventSerializer(serializers.ModelSerializer):
    """Serializer para Event"""
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'camera', 'camera_name', 'event_type', 'event_type_display',
            'severity', 'severity_display', 'confidence', 'detected_objects',
            'snapshot_path', 'video_clip_path', 'detected_at',
            'acknowledged', 'acknowledged_by', 'acknowledged_by_name',
            'acknowledged_at', 'action_taken', 'false_positive', 'metadata'
        ]
        read_only_fields = ['id', 'detected_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para Alert"""
    event_type = serializers.CharField(source='event.get_event_type_display', read_only=True)
    camera_name = serializers.CharField(source='event.camera.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'event', 'event_type', 'camera_name', 'user',
            'channel', 'sent', 'sent_at', 'read', 'read_at',
            'subject', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'sent_at', 'read_at', 'created_at']


class CameraScheduleSerializer(serializers.ModelSerializer):
    """Serializer para CameraSchedule"""
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = CameraSchedule
        fields = [
            'id', 'camera', 'camera_name', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'enable_recording', 'enable_detection',
            'is_active'
        ]
        read_only_fields = ['id']


class AIModelSerializer(serializers.ModelSerializer):
    """Serializer para AIModel"""
    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    
    class Meta:
        model = AIModel
        fields = [
            'id', 'organization', 'name', 'version', 'model_file',
            'model_type', 'model_type_display', 'classes',
            'avg_inference_time', 'accuracy', 'is_active', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'avg_inference_time', 'created_at', 'updated_at']


class CameraStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de câmeras"""
    total_cameras = serializers.IntegerField()
    online_cameras = serializers.IntegerField()
    offline_cameras = serializers.IntegerField()
    total_events_today = serializers.IntegerField()
    total_events_week = serializers.IntegerField()
    unacknowledged_events = serializers.IntegerField()
    avg_uptime = serializers.FloatField()
