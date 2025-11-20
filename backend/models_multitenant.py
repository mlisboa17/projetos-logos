"""
Multi-tenant database models for LOGOS Platform
Arquitetura preparada para SaaS - servir Grupo Lisboa + outros clientes
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from database import Base


# ============= ENUMS =============

class SubscriptionPlan(str, enum.Enum):
    """Planos de assinatura do LOGOS"""
    FREE = "free"              # Gratuito (trial 30 dias)
    BASIC = "basic"            # Básico: 1 loja, 5 usuários
    PROFESSIONAL = "professional"  # Profissional: 5 lojas, 20 usuários
    ENTERPRISE = "enterprise"  # Enterprise: ilimitado + suporte dedicado


class SubscriptionStatus(str, enum.Enum):
    """Status da assinatura"""
    ACTIVE = "active"          # Ativa e paga
    TRIAL = "trial"            # Período de teste
    SUSPENDED = "suspended"    # Suspensa por falta de pagamento
    CANCELLED = "cancelled"    # Cancelada pelo cliente
    EXPIRED = "expired"        # Expirada


class OrganizationType(str, enum.Enum):
    """Tipos de empresa cliente"""
    GAS_STATION = "gas_station"      # Posto de combustível
    CONVENIENCE = "convenience"      # Loja de conveniência
    RESTAURANT = "restaurant"        # Restaurante
    FRANCHISE = "franchise"          # Franquia (Subway, etc)
    DELIVERY = "delivery"            # Delivery (Zé Delivery, etc)
    SOLAR = "solar"                 # Energia solar
    RETAIL = "retail"               # Varejo geral
    HOLDING = "holding"             # Holding (como Grupo Lisboa)
    OTHER = "other"


class ERPType(str, enum.Enum):
    """Tipos de ERP suportados"""
    WEBPOSTOS = "webpostos"            # WebPostos (Postos Lisboa + outros postos)
    LINX = "linx"                      # Linx Sistemas (postos)
    BLING = "bling"                    # Bling ERP (e-commerce/varejo)
    TINY = "tiny"                      # Tiny ERP
    SAP = "sap"                        # SAP Business One
    TOTVS = "totvs"                    # TOTVS Protheus
    SANKHYA = "sankhya"                # Sankhya
    OMIE = "omie"                      # Omie
    CONTA_AZUL = "conta_azul"          # Conta Azul
    SENIOR = "senior"                  # Senior Sistemas
    IFOOD = "ifood"                    # iFood (delivery)
    UBER_EATS = "uber_eats"            # Uber Eats
    RAPPI = "rappi"                    # Rappi
    ZE_DELIVERY = "ze_delivery"        # Zé Delivery
    SUBWAY_PORTAL = "subway_portal"    # Portal Franqueado Subway
    CUSTOM = "custom"                  # ERP customizado


# ============= MULTI-TENANT MODELS =============

class Organization(Base):
    """
    Empresa cliente do LOGOS (multi-tenant)
    Cada organização é um cliente separado com seus próprios dados
    """
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dados da empresa
    name = Column(String, nullable=False)  # Ex: "Grupo Lisboa", "Rede XYZ Postos"
    slug = Column(String, unique=True, nullable=False, index=True)  # Ex: "grupo-lisboa"
    type = Column(Enum(OrganizationType), nullable=False)
    cnpj = Column(String, unique=True)
    
    # Contato
    email = Column(String, nullable=False)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    
    # Assinatura e Plano
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.TRIAL)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    subscription_started_at = Column(DateTime, default=datetime.utcnow)
    subscription_expires_at = Column(DateTime)
    
    # Limites do plano (soft limits - podem ser customizados)
    max_stores = Column(Integer, default=1)       # Máximo de lojas/postos
    max_users = Column(Integer, default=5)        # Máximo de usuários
    max_cameras = Column(Integer, default=4)      # Máximo de câmeras (VerifiK)
    max_erp_integrations = Column(Integer, default=2)  # Máximo de ERPs
    
    # Personalização (white-label)
    logo_url = Column(String)  # Logo da empresa cliente
    primary_color = Column(String, default="#D4AF37")  # Cor primária do tema
    secondary_color = Column(String, default="#1B4D3E")  # Cor secundária
    custom_domain = Column(String)  # Ex: "dashboard.grupolisboa.com.br"
    
    # Billing
    monthly_price = Column(Float, default=0.0)  # Preço mensal em R$
    payment_gateway_customer_id = Column(String)  # ID no gateway de pagamento
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="organization", cascade="all, delete-orphan")
    erp_integrations = relationship("ERPIntegration", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    """Usuário do sistema (pertence a uma organização)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Credenciais
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Dados pessoais
    full_name = Column(String, nullable=False)
    phone = Column(String)
    avatar_url = Column(String)
    
    # Permissões
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Admin dentro da organização
    is_super_admin = Column(Boolean, default=False)  # Super admin do LOGOS (Grupo Lisboa)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    organization = relationship("Organization", back_populates="users")
    stores = relationship("Store", back_populates="owner")


class Store(Base):
    """Loja/Posto de combustível (pertence a uma organização)"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Dados da loja
    name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String, default="Recife")
    state = Column(String, default="PE")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Responsável
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    organization = relationship("Organization", back_populates="stores")
    owner = relationship("User", back_populates="stores")
    cameras = relationship("Camera", back_populates="store")
    products = relationship("Product", back_populates="store")
    detections = relationship("Detection", back_populates="store")


class ERPIntegration(Base):
    """Integrações com ERPs externos"""
    __tablename__ = "erp_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Tipo e configuração
    erp_type = Column(Enum(ERPType), nullable=False)
    name = Column(String, nullable=False)  # Ex: "Linx - Posto Centro"
    description = Column(String)
    
    # Credenciais (devem ser criptografadas no código)
    api_url = Column(String)  # URL da API do ERP
    api_key = Column(Text)    # Chave de API (encrypted)
    username = Column(String)  # Username (encrypted)
    password = Column(Text)    # Password (encrypted)
    extra_config = Column(JSON)  # Configurações adicionais
    
    # Status de sincronização
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String)  # success, error, pending
    sync_error = Column(Text)  # Mensagem de erro se houver
    sync_frequency = Column(Integer, default=30)  # Minutos entre sincronizações
    
    # Mapeamento de campos
    field_mapping = Column(JSON)  # Mapeamento de campos do ERP para LOGOS
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    organization = relationship("Organization", back_populates="erp_integrations")


# ============= VERIFIK MODELS (mantidos para compatibilidade) =============

class Camera(Base):
    """Camera de monitoramento (VerifiK)"""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    
    # Configuração
    name = Column(String, nullable=False)
    ip_address = Column(String)
    rtsp_url = Column(String)
    location = Column(String)  # Ex: "Caixa 1", "Entrada"
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    store = relationship("Store", back_populates="cameras")
    detections = relationship("Detection", back_populates="camera")


class Product(Base):
    """Produto cadastrado"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    
    # Dados do produto
    name = Column(String, nullable=False)
    barcode = Column(String, unique=True)
    category = Column(String)
    price = Column(Float)
    
    # YOLOv8
    yolo_class_id = Column(Integer)  # ID da classe no modelo treinado
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    store = relationship("Store", back_populates="products")


class Detection(Base):
    """Detecção de produtos pela câmera"""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    
    # Dados da detecção
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    products_detected = Column(JSON)  # Lista de produtos detectados pela câmera
    products_in_pdv = Column(JSON)    # Lista de produtos registrados no PDV
    mismatch = Column(Boolean, default=False)  # Discrepância?
    confidence_score = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    store = relationship("Store", back_populates="detections")
    camera = relationship("Camera", back_populates="detections")
    alerts = relationship("Alert", back_populates="detection")


class Alert(Base):
    """Alertas de discrepância"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Dados do alerta
    message = Column(String, nullable=False)
    severity = Column(String, default="warning")  # info, warning, critical
    is_resolved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    detection = relationship("Detection", back_populates="alerts")
    user = relationship("User")
