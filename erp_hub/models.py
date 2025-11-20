"""
Models para ERP Hub - Integrações com ERPs externos
"""
from django.db import models
from django.conf import settings


class ERPType(models.TextChoices):
    """Tipos de ERP suportados"""
    WEBPOSTOS = 'webpostos', 'WebPostos'
    LINX = 'linx', 'Linx Sistemas'
    BLING = 'bling', 'Bling ERP'
    TINY = 'tiny', 'Tiny ERP'
    SAP = 'sap', 'SAP Business One'
    TOTVS = 'totvs', 'TOTVS Protheus'
    SANKHYA = 'sankhya', 'Sankhya'
    OMIE = 'omie', 'Omie'
    CONTA_AZUL = 'conta_azul', 'Conta Azul'
    SENIOR = 'senior', 'Senior Sistemas'
    IFOOD = 'ifood', 'iFood'
    UBER_EATS = 'uber_eats', 'Uber Eats'
    RAPPI = 'rappi', 'Rappi'
    ZE_DELIVERY = 'ze_delivery', 'Zé Delivery'
    SUBWAY_PORTAL = 'subway_portal', 'Portal Subway'
    CUSTOM = 'custom', 'ERP Customizado'


class ERPIntegration(models.Model):
    """Integração com ERP externo"""
    
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='erp_integrations',
        verbose_name='Organização'
    )
    
    # Tipo e configuração
    erp_type = models.CharField('Tipo de ERP', max_length=20, choices=ERPType.choices)
    name = models.CharField('Nome', max_length=200, help_text='Ex: WebPostos - Posto Centro')
    description = models.TextField('Descrição', blank=True)
    
    # Credenciais (serão criptografadas no código)
    api_url = models.URLField('URL da API', blank=True)
    api_key = models.TextField('API Key', blank=True)
    username = models.CharField('Usuário', max_length=200, blank=True)
    password = models.CharField('Senha', max_length=200, blank=True)
    extra_config = models.JSONField('Configuração Extra', default=dict, blank=True)
    
    # Sincronização
    is_active = models.BooleanField('Ativo', default=True)
    sync_frequency = models.IntegerField('Frequência Sync (min)', default=30)
    last_sync_at = models.DateTimeField('Última Sincronização', null=True, blank=True)
    sync_status = models.CharField('Status Sync', max_length=20, blank=True)
    sync_error = models.TextField('Erro de Sync', blank=True)
    
    # Mapeamento de campos
    field_mapping = models.JSONField('Mapeamento de Campos', default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Integração ERP'
        verbose_name_plural = 'Integrações ERP'
        ordering = ['-created_at']
        unique_together = [['organization', 'erp_type', 'name']]
    
    def __str__(self):
        return f"{self.get_erp_type_display()} - {self.name}"


class Store(models.Model):
    """Loja/Posto pertencente a uma organização"""
    
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='stores',
        verbose_name='Organização'
    )
    
    # Dados da loja
    name = models.CharField('Nome', max_length=200)
    code = models.CharField('Código', max_length=50, blank=True)
    
    # Localização
    address = models.CharField('Endereço', max_length=300, blank=True)
    city = models.CharField('Cidade', max_length=100, default='Recife')
    state = models.CharField('Estado', max_length=2, default='PE')
    latitude = models.DecimalField('Latitude', max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Responsável
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_stores',
        verbose_name='Gerente'
    )
    
    # Status
    is_active = models.BooleanField('Ativo', default=True)
    
    # Metadata
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Loja/Posto'
        verbose_name_plural = 'Lojas/Postos'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class SyncLog(models.Model):
    """Log de sincronizações com ERPs"""
    
    integration = models.ForeignKey(
        ERPIntegration,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name='Integração'
    )
    
    started_at = models.DateTimeField('Iniciou em', auto_now_add=True)
    finished_at = models.DateTimeField('Terminou em', null=True, blank=True)
    
    status = models.CharField('Status', max_length=20, choices=[
        ('running', 'Executando'),
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('partial', 'Parcial'),
    ])
    
    records_processed = models.IntegerField('Registros Processados', default=0)
    records_created = models.IntegerField('Registros Criados', default=0)
    records_updated = models.IntegerField('Registros Atualizados', default=0)
    records_failed = models.IntegerField('Registros com Erro', default=0)
    
    error_message = models.TextField('Mensagem de Erro', blank=True)
    details = models.JSONField('Detalhes', default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Log de Sincronização'
        verbose_name_plural = 'Logs de Sincronização'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.integration.name} - {self.started_at.strftime('%d/%m/%Y %H:%M')}"

