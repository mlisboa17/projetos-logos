"""
Models para app Cameras - Sistema VerifiK
Sistema de monitoramento inteligente com IA (YOLOv8)
"""
from django.db import models
from django.conf import settings
from accounts.models import Organization, User
from erp_hub.models import Store


class CameraStatus(models.TextChoices):
    ONLINE = 'online', 'Online'
    OFFLINE = 'offline', 'Offline'
    ERROR = 'error', 'Erro'
    MAINTENANCE = 'maintenance', 'Manutenção'


class EventType(models.TextChoices):
    # Segurança
    INTRUSION = 'intrusion', 'Invasão Detectada'
    LOITERING = 'loitering', 'Pessoa Parada Suspeita'
    CROWD = 'crowd', 'Aglomeração'
    
    # Operacional
    QUEUE = 'queue', 'Fila Detectada'
    SPILLAGE = 'spillage', 'Derramamento de Produto'
    FIRE = 'fire', 'Fumaça/Fogo Detectado'
    
    # Veículos
    WRONG_WAY = 'wrong_way', 'Veículo Contramão'
    PARKING_VIOLATION = 'parking_violation', 'Estacionamento Irregular'
    ABANDONED_VEHICLE = 'abandoned_vehicle', 'Veículo Abandonado'
    
    # Perdas
    SHELF_EMPTY = 'shelf_empty', 'Prateleira Vazia'
    THEFT = 'theft', 'Possível Furto'
    
    # Outros
    CUSTOM = 'custom', 'Evento Customizado'


class EventSeverity(models.TextChoices):
    LOW = 'low', 'Baixa'
    MEDIUM = 'medium', 'Média'
    HIGH = 'high', 'Alta'
    CRITICAL = 'critical', 'Crítica'


class Camera(models.Model):
    """Câmera de segurança conectada ao sistema"""
    
    # Relacionamentos
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        verbose_name='Organização'
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        verbose_name='Loja',
        related_name='cameras'
    )
    
    # Dados da câmera
    name = models.CharField('Nome', max_length=200)
    code = models.CharField('Código', max_length=50, unique=True)
    location = models.CharField('Localização', max_length=200, help_text='Ex: Caixa 1, Pista 3, Estoque')
    description = models.TextField('Descrição', blank=True)
    
    # Conexão
    stream_url = models.CharField('URL Stream', max_length=500, help_text='rtsp://usuario:senha@ip:porta/stream')
    ip_address = models.GenericIPAddressField('Endereço IP')
    port = models.IntegerField('Porta', default=554)
    username = models.CharField('Usuário', max_length=100, blank=True)
    password = models.CharField('Senha', max_length=100, blank=True)
    
    # Status e configuração
    status = models.CharField(
        'Status',
        max_length=20,
        choices=CameraStatus.choices,
        default=CameraStatus.OFFLINE
    )
    is_active = models.BooleanField('Ativa', default=True)
    is_recording = models.BooleanField('Gravando', default=False)
    
    # IA - YOLOv8 Configuration
    ai_enabled = models.BooleanField('IA Habilitada', default=True)
    ai_model = models.CharField('Modelo IA', max_length=50, default='yolov8n.pt')
    confidence_threshold = models.FloatField('Threshold Confiança', default=0.5, help_text='0.0 a 1.0')
    detection_fps = models.IntegerField('FPS Detecção', default=5, help_text='Frames por segundo para análise')
    
    # Classes para detectar (JSON array)
    detection_classes = models.JSONField(
        'Classes para Detectar',
        default=list,
        help_text='["person", "car", "truck", "fire", "smoke"]'
    )
    
    # Área de interesse (ROI - Region of Interest)
    roi_polygon = models.JSONField(
        'Polígono ROI',
        null=True,
        blank=True,
        help_text='Coordenadas do polígono: [[x1,y1], [x2,y2], ...]'
    )
    
    # Gravação
    storage_path = models.CharField('Caminho Gravação', max_length=500, blank=True)
    retention_days = models.IntegerField('Dias Retenção', default=30)
    
    # Estatísticas
    last_frame_at = models.DateTimeField('Último Frame', null=True, blank=True)
    total_events = models.IntegerField('Total de Eventos', default=0)
    uptime_percentage = models.FloatField('Uptime %', default=0.0)
    
    # Metadata
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Câmera'
        verbose_name_plural = 'Câmeras'
        ordering = ['store', 'name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['store', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.store.name})"
    
    @property
    def is_online(self):
        return self.status == CameraStatus.ONLINE


class Event(models.Model):
    """Evento detectado pela IA"""
    
    # Relacionamentos
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Câmera'
    )
    
    # Tipo e severidade
    event_type = models.CharField(
        'Tipo de Evento',
        max_length=50,
        choices=EventType.choices
    )
    severity = models.CharField(
        'Severidade',
        max_length=20,
        choices=EventSeverity.choices,
        default=EventSeverity.MEDIUM
    )
    
    # Detecção
    confidence = models.FloatField('Confiança', help_text='Confiança da IA (0.0 a 1.0)')
    detected_objects = models.JSONField(
        'Objetos Detectados',
        help_text='Lista de objetos detectados com bounding boxes'
    )
    
    # Captura
    snapshot_path = models.CharField('Caminho Snapshot', max_length=500)
    video_clip_path = models.CharField('Caminho Vídeo', max_length=500, blank=True)
    
    # Timestamp
    detected_at = models.DateTimeField('Detectado em', auto_now_add=True)
    
    # Resposta
    acknowledged = models.BooleanField('Reconhecido', default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_events',
        verbose_name='Reconhecido por'
    )
    acknowledged_at = models.DateTimeField('Reconhecido em', null=True, blank=True)
    
    # Ação tomada
    action_taken = models.TextField('Ação Tomada', blank=True)
    false_positive = models.BooleanField('Falso Positivo', default=False)
    
    # Metadata
    metadata = models.JSONField('Metadados', default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['camera', '-detected_at']),
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['acknowledged', '-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.camera.name} ({self.detected_at})"


class Alert(models.Model):
    """Alerta enviado aos usuários"""
    
    # Relacionamentos
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Evento'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='camera_alerts',
        verbose_name='Usuário'
    )
    
    # Canal de notificação
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
        ('system', 'Sistema'),
    ]
    channel = models.CharField('Canal', max_length=20, choices=CHANNEL_CHOICES)
    
    # Status
    sent = models.BooleanField('Enviado', default=False)
    sent_at = models.DateTimeField('Enviado em', null=True, blank=True)
    
    read = models.BooleanField('Lido', default=False)
    read_at = models.DateTimeField('Lido em', null=True, blank=True)
    
    # Mensagem
    subject = models.CharField('Assunto', max_length=200)
    message = models.TextField('Mensagem')
    
    # Metadata
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['sent', 'read']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.user.username}"


class CameraSchedule(models.Model):
    """Agendamento de gravação/detecção"""
    
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Câmera'
    )
    
    # Dia da semana (0=Segunda, 6=Domingo)
    WEEKDAY_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    weekday = models.IntegerField('Dia da Semana', choices=WEEKDAY_CHOICES)
    
    # Horários
    start_time = models.TimeField('Hora Início')
    end_time = models.TimeField('Hora Fim')
    
    # Ações
    enable_recording = models.BooleanField('Habilitar Gravação', default=True)
    enable_detection = models.BooleanField('Habilitar Detecção IA', default=True)
    
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.camera.name} - {self.get_weekday_display()} ({self.start_time}-{self.end_time})"


class AIModel(models.Model):
    """Modelos de IA disponíveis"""
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name='Organização',
        null=True,
        blank=True,
        help_text='Deixe vazio para modelo global'
    )
    
    name = models.CharField('Nome', max_length=100)
    version = models.CharField('Versão', max_length=50)
    model_file = models.CharField('Arquivo Modelo', max_length=200, help_text='Ex: yolov8n.pt')
    
    # Tipo
    MODEL_TYPE_CHOICES = [
        ('detection', 'Detecção de Objetos'),
        ('segmentation', 'Segmentação'),
        ('classification', 'Classificação'),
        ('pose', 'Detecção de Pose'),
    ]
    model_type = models.CharField('Tipo', max_length=20, choices=MODEL_TYPE_CHOICES)
    
    # Classes que detecta
    classes = models.JSONField('Classes', default=list)
    
    # Performance
    avg_inference_time = models.FloatField('Tempo Inferência (ms)', default=0)
    accuracy = models.FloatField('Acurácia %', default=0)
    
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Modelo IA'
        verbose_name_plural = 'Modelos IA'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
