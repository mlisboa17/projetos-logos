"""
Models para app Accounts - Multi-tenant
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class SubscriptionPlan(models.TextChoices):
    FREE = 'free', 'Gratuito (Trial)'
    BASIC = 'basic', 'Básico'
    PROFESSIONAL = 'professional', 'Profissional'
    ENTERPRISE = 'enterprise', 'Enterprise'


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Ativo'
    TRIAL = 'trial', 'Trial'
    SUSPENDED = 'suspended', 'Suspenso'
    CANCELLED = 'cancelled', 'Cancelado'
    EXPIRED = 'expired', 'Expirado'


class OrganizationType(models.TextChoices):
    GAS_STATION = 'gas_station', 'Posto de Combustível'
    CONVENIENCE = 'convenience', 'Loja de Conveniência'
    RESTAURANT = 'restaurant', 'Restaurante'
    FRANCHISE = 'franchise', 'Franquia'
    DELIVERY = 'delivery', 'Delivery'
    SOLAR = 'solar', 'Energia Solar'
    RETAIL = 'retail', 'Varejo'
    HOLDING = 'holding', 'Holding'
    OTHER = 'other', 'Outro'


class Organization(models.Model):
    """Empresa cliente do LOGOS (multi-tenant)"""
    
    # Dados básicos
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug', unique=True, max_length=100)
    type = models.CharField('Tipo', max_length=20, choices=OrganizationType.choices)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True, null=True, blank=True)
    
    # Contato
    email = models.EmailField('Email')
    phone = models.CharField('Telefone', max_length=20, blank=True)
    address = models.CharField('Endereço', max_length=300, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('Estado', max_length=2, blank=True)
    
    # Assinatura
    subscription_plan = models.CharField(
        'Plano', max_length=20, 
        choices=SubscriptionPlan.choices, 
        default=SubscriptionPlan.FREE
    )
    subscription_status = models.CharField(
        'Status', max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL
    )
    subscription_started_at = models.DateTimeField('Iniciou em', auto_now_add=True)
    subscription_expires_at = models.DateTimeField('Expira em', null=True, blank=True)
    
    # Limites do plano
    max_stores = models.IntegerField('Máx. Lojas', default=1)
    max_users = models.IntegerField('Máx. Usuários', default=5)
    max_cameras = models.IntegerField('Máx. Câmeras', default=4)
    max_erp_integrations = models.IntegerField('Máx. ERPs', default=2)
    
    # White-label
    logo = models.ImageField('Logo', upload_to='organizations/logos/', null=True, blank=True)
    primary_color = models.CharField('Cor Primária', max_length=7, default='#D4AF37')
    secondary_color = models.CharField('Cor Secundária', max_length=7, default='#1B4D3E')
    custom_domain = models.CharField('Domínio Customizado', max_length=100, blank=True)
    
    # Billing
    monthly_price = models.DecimalField('Mensalidade', max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Organização'
        verbose_name_plural = 'Organizações'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class User(AbstractUser):
    """Usuário do sistema (pode ter acesso a múltiplas organizações)"""
    
    # REMOVIDO: organization ForeignKey (agora usa ManyToMany via UserOrganization)
    # organizations: acessado via user.organizations_access.all()
    
    phone = models.CharField('Telefone', max_length=20, blank=True)
    avatar = models.ImageField('Avatar', upload_to='users/avatars/', null=True, blank=True)
    
    # Organização ativa no momento (para filtrar dados)
    active_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_users',
        verbose_name='Organização Ativa'
    )
    
    # Permissões globais
    is_super_admin = models.BooleanField('Super Admin LOGOS', default=False)
    
    last_login_at = models.DateTimeField('Último Login', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-date_joined']
    
    def __str__(self):
        org_name = self.active_organization.name if self.active_organization else "Sem org"
        return f"{self.get_full_name()} ({org_name})"
    
    def get_organizations(self):
        """Retorna todas as organizações que o usuário tem acesso"""
        return Organization.objects.filter(user_organizations__user=self)


class UserOrganization(models.Model):
    """Relacionamento entre usuário e organização com permissões específicas"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations_access')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_organizations')
    
    # Permissões específicas para esta organização
    is_org_admin = models.BooleanField('Admin da Organização', default=False)
    can_access_verifik = models.BooleanField('Acesso VerifiK', default=False)
    can_access_erp_hub = models.BooleanField('Acesso ERP Hub', default=False)
    can_access_fuel_prices = models.BooleanField('Acesso Fuel Prices', default=False)
    can_manage_users = models.BooleanField('Gerenciar Usuários', default=False)
    can_view_reports = models.BooleanField('Ver Relatórios', default=False)
    can_edit_settings = models.BooleanField('Editar Configurações', default=False)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Acesso à Organização'
        verbose_name_plural = 'Acessos às Organizações'
        unique_together = [['user', 'organization']]
        ordering = ['organization__name']
    
    def __str__(self):
        return f"{self.user.username} @ {self.organization.name}"

