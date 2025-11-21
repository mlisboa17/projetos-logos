"""
╔══════════════════════════════════════════════════════════════════╗
║                      MODELS - ACCOUNTS APP                       ║
║            Sistema de Autenticação e Multi-Organização           ║
╚══════════════════════════════════════════════════════════════════╝

📚 O QUE É ESTE ARQUIVO:
------------------------
Define a estrutura de dados (models) para:
  - 🏢 Organizations: Empresas/Postos do Grupo Lisboa
  - 👤 Users: Usuários do sistema (extensão do User do Django)
  - 🔗 UserOrganization: Relação entre User e Organization (permissões)

🔧 COMO FUNCIONA MULTI-TENANT:
------------------------------
Um usuário pode ter acesso a VÁRIAS organizações (postos):
  - João trabalha em 3 postos diferentes
  - Em cada posto, ele tem permissões diferentes
  - Pode trocar entre organizações sem fazer logout

Exemplo:
  User: joao@email.com
  Organizations:
    - Posto Centro: Admin (pode tudo)
    - Posto Norte: Apenas VerifiK
    - Posto Sul: Apenas relatórios

📖 CONCEITOS IMPORTANTES:
-------------------------
1. AbstractUser: Classe base do Django para criar User customizado
2. ForeignKey: Relacionamento N-para-1 (muitos Users para 1 Organization)
3. ManyToManyField: Relacionamento N-para-N (via tabela intermediária)
4. Choices: Opções limitadas para um campo (dropdown no admin)
5. Meta: Configurações extras do modelo (verbose_name, ordering)

📚 DOCUMENTAÇÃO:
----------------
https://docs.djangoproject.com/en/5.2/topics/db/models/
https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


# ============================================================
# 📋 ENUMERAÇÕES (Choices)
# ============================================================
# TextChoices: Define opções limitadas para campos
# Vantagem: Validação automática, dropdown no admin

class SubscriptionPlan(models.TextChoices):
    """
    Planos de assinatura disponíveis
    
    Formato: CONSTANTE = 'valor_db', 'Label Legível'
    """
    FREE = 'free', 'Gratuito (Trial)'          # 🆓 Teste grátis
    BASIC = 'basic', 'Básico'                  # 💰 Plano básico
    PROFESSIONAL = 'professional', 'Profissional'  # 💎 Plano profissional
    ENTERPRISE = 'enterprise', 'Enterprise'    # 🏢 Plano empresarial


class SubscriptionStatus(models.TextChoices):
    """
    Status da assinatura
    
    Ciclo de vida:
    TRIAL → ACTIVE → SUSPENDED/CANCELLED/EXPIRED
    """
    ACTIVE = 'active', 'Ativo'          # ✅ Pagando normalmente
    TRIAL = 'trial', 'Trial'            # 🆓 Período de teste
    SUSPENDED = 'suspended', 'Suspenso' # ⏸️ Pagamento atrasado
    CANCELLED = 'cancelled', 'Cancelado'  # ❌ Cliente cancelou
    EXPIRED = 'expired', 'Expirado'     # ⏱️ Trial acabou


class OrganizationType(models.TextChoices):
    """
    Tipos de organizações/empresas
    
    Diferentes tipos podem ter features diferentes no futuro
    """
    GAS_STATION = 'gas_station', 'Posto de Combustível'  # ⛽
    CONVENIENCE = 'convenience', 'Loja de Conveniência'  # 🏪
    RESTAURANT = 'restaurant', 'Restaurante'             # 🍽️
    FRANCHISE = 'franchise', 'Franquia'                  # 🏢
    DELIVERY = 'delivery', 'Delivery'                    # 🚚
    SOLAR = 'solar', 'Energia Solar'                     # ☀️
    RETAIL = 'retail', 'Varejo'                          # 🛒
    HOLDING = 'holding', 'Holding'                       # 🏛️
    OTHER = 'other', 'Outro'                             # ❓

# ============================================================
# 🏢 MODEL: ORGANIZATION
# ============================================================

class Organization(models.Model):
    """
    Organização/Empresa cliente do LOGOS
    
    ╔══════════════════════════════════════════════════════════╗
    ║  O QUE É:                                                ║
    ║  Representa uma empresa do Grupo Lisboa                  ║
    ║  Exemplos: Posto Centro, Posto Norte, Loja Sul          ║
    ║                                                          ║
    ║  MULTI-TENANT:                                           ║
    ║  Cada Organization é um "inquilino" separado no sistema  ║
    ║  Dados são isolados por organização                      ║
    ╚══════════════════════════════════════════════════════════╝
    
    Relacionamentos:
    ----------------
    - N Users (via UserOrganization)
    - N Cameras (câmeras instaladas nesta empresa)
    - N Stores (lojas/filiais desta empresa)
    
    Campos principais:
    ------------------
    - name: Nome da empresa
    - cnpj: CNPJ único (identificação fiscal)
    - subscription_plan: Qual plano está assinando
    - max_users/cameras/stores: Limites do plano
    """
    
    # ──────────────────────────────────────────────────────────
    # 📝 DADOS BÁSICOS
    # ──────────────────────────────────────────────────────────
    
    name = models.CharField(
        'Nome',
        max_length=200,
        help_text='Nome da organização (ex: Posto Lisboa Centro)'
    )
    
    slug = models.SlugField(
        'Slug',
        unique=True,
        max_length=100,
        help_text='URL amigável (gerado automaticamente do nome)'
        # Exemplo: "Posto Lisboa" → "posto-lisboa"
    )
    
    type = models.CharField(
        'Tipo',
        max_length=20,
        choices=OrganizationType.choices,
        help_text='Tipo de negócio'
    )
    
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,  # Formato: 00.000.000/0000-00
        unique=True,     # Cada CNPJ só pode existir uma vez
        null=True,
        blank=True,
        help_text='CNPJ da empresa (único no sistema)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📞 CONTATO
    # ──────────────────────────────────────────────────────────
    
    email = models.EmailField(
        'Email',
        help_text='Email de contato da organização'
    )
    
    phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        help_text='Telefone comercial'
    )
    
    address = models.CharField(
        'Endereço',
        max_length=300,
        blank=True,
        help_text='Endereço completo'
    )
    
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('Estado', max_length=2, blank=True)  # UF: SP, RJ, MG...
    
    # ──────────────────────────────────────────────────────────
    # 💰 ASSINATURA E BILLING
    # ──────────────────────────────────────────────────────────
    
    subscription_plan = models.CharField(
        'Plano',
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE,
        help_text='Plano de assinatura contratado'
    )
    
    subscription_status = models.CharField(
        'Status',
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
        help_text='Status atual da assinatura'
    )
    
    subscription_started_at = models.DateTimeField(
        'Iniciou em',
        auto_now_add=True,
        help_text='Data de início da assinatura'
    )
    
    subscription_expires_at = models.DateTimeField(
        'Expira em',
        null=True,
        blank=True,
        help_text='Data de expiração (trial ou suspensão)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📊 LIMITES DO PLANO
    # ──────────────────────────────────────────────────────────
    # Cada plano tem limites diferentes de recursos
    
    max_stores = models.IntegerField(
        'Máx. Lojas',
        default=1,
        help_text='Máximo de lojas/filiais permitidas'
    )
    
    max_users = models.IntegerField(
        'Máx. Usuários',
        default=5,
        help_text='Máximo de usuários simultâneos'
    )
    
    max_cameras = models.IntegerField(
        'Máx. Câmeras',
        default=4,
        help_text='Máximo de câmeras ativas'
    )
    
    max_erp_integrations = models.IntegerField(
        'Máx. ERPs',
        default=2,
        help_text='Máximo de integrações com ERPs'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🎨 WHITE-LABEL (Personalização)
    # ──────────────────────────────────────────────────────────
    # Permite customizar visual para cada organização
    
    logo = models.ImageField(
        'Logo',
        upload_to='organizations/logos/',
        null=True,
        blank=True,
        help_text='Logo da empresa (aparece no sistema)'
    )
    
    primary_color = models.CharField(
        'Cor Primária',
        max_length=7,  # Formato: #RRGGBB
        default='#D4AF37',  # Dourado
        help_text='Cor principal da interface (hex)'
    )
    
    secondary_color = models.CharField(
        'Cor Secundária',
        max_length=7,
        default='#1B4D3E',  # Verde escuro
        help_text='Cor secundária da interface (hex)'
    )
    
    custom_domain = models.CharField(
        'Domínio Customizado',
        max_length=100,
        blank=True,
        help_text='Domínio próprio (ex: posto.grupolisboa.com.br)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 💵 BILLING
    # ──────────────────────────────────────────────────────────
    
    monthly_price = models.DecimalField(
        'Mensalidade',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Valor mensal em reais (R$)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA (Dados de controle)
    # ──────────────────────────────────────────────────────────
    
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Se False, organização está desativada'
    )
    
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        help_text='Data de criação do registro'
        # auto_now_add: Define automaticamente no INSERT
    )
    
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True,
        help_text='Data da última modificação'
        # auto_now: Atualiza automaticamente em todo UPDATE
    )
    
    # ──────────────────────────────────────────────────────────
    # ⚙️ META (Configurações do modelo)
    # ──────────────────────────────────────────────────────────
    
    class Meta:
        verbose_name = 'Organização'
        verbose_name_plural = 'Organizações'
        ordering = ['-created_at']  # Mais recentes primeiro
    
    def __str__(self):
        """
        Representação em string do objeto
        Aparece no admin, selects, etc.
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve método save para adicionar lógica custom
        
        O que faz:
        - Gera slug automaticamente se não existir
        - Exemplo: name="Posto Lisboa" → slug="posto-lisboa"
        """
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

