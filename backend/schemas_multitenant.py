"""
Pydantic schemas for multi-tenant LOGOS Platform
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============= ENUMS =============

class SubscriptionPlanEnum(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrganizationTypeEnum(str, Enum):
    GAS_STATION = "gas_station"
    CONVENIENCE = "convenience"
    RESTAURANT = "restaurant"
    FRANCHISE = "franchise"
    DELIVERY = "delivery"
    SOLAR = "solar"
    RETAIL = "retail"
    HOLDING = "holding"
    OTHER = "other"


class ERPTypeEnum(str, Enum):
    WEBPOSTOS = "webpostos"
    LINX = "linx"
    BLING = "bling"
    TINY = "tiny"
    SAP = "sap"
    TOTVS = "totvs"
    SANKHYA = "sankhya"
    OMIE = "omie"
    CONTA_AZUL = "conta_azul"
    SENIOR = "senior"
    IFOOD = "ifood"
    UBER_EATS = "uber_eats"
    RAPPI = "rappi"
    ZE_DELIVERY = "ze_delivery"
    SUBWAY_PORTAL = "subway_portal"
    CUSTOM = "custom"


# ============= ORGANIZATION SCHEMAS =============

class OrganizationBase(BaseModel):
    name: str
    slug: str
    type: OrganizationTypeEnum
    cnpj: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema para criar nova organização (onboarding)"""
    subscription_plan: SubscriptionPlanEnum = SubscriptionPlanEnum.TRIAL
    
    # Dados do primeiro admin
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    
    @validator('slug')
    def slug_must_be_lowercase(cls, v):
        return v.lower().replace(' ', '-')


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: int
    subscription_plan: SubscriptionPlanEnum
    subscription_status: SubscriptionStatusEnum
    subscription_started_at: datetime
    subscription_expires_at: Optional[datetime] = None
    max_stores: int
    max_users: int
    max_cameras: int
    max_erp_integrations: int
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    custom_domain: Optional[str] = None
    monthly_price: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= USER SCHEMAS (atualizado para multi-tenant) =============

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    organization_id: int
    is_admin: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    organization_id: int
    is_active: bool
    is_admin: bool
    is_super_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= ERP INTEGRATION SCHEMAS =============

class ERPIntegrationBase(BaseModel):
    erp_type: ERPTypeEnum
    name: str
    description: Optional[str] = None
    api_url: Optional[str] = None
    sync_frequency: int = 30  # minutos


class ERPIntegrationCreate(ERPIntegrationBase):
    organization_id: int
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[dict] = None


class ERPIntegrationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[dict] = None
    sync_frequency: Optional[int] = None
    is_active: Optional[bool] = None


class ERPIntegrationResponse(ERPIntegrationBase):
    id: int
    organization_id: int
    is_active: bool
    last_sync_at: Optional[datetime] = None
    sync_status: Optional[str] = None
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Não expor credenciais na resposta
    class Config:
        from_attributes = True


# ============= SUBSCRIPTION SCHEMAS =============

class SubscriptionUpdate(BaseModel):
    """Atualizar assinatura (upgrade/downgrade)"""
    subscription_plan: SubscriptionPlanEnum
    max_stores: Optional[int] = None
    max_users: Optional[int] = None
    max_cameras: Optional[int] = None
    max_erp_integrations: Optional[int] = None


class SubscriptionStatusUpdate(BaseModel):
    """Atualizar status da assinatura"""
    subscription_status: SubscriptionStatusEnum
    subscription_expires_at: Optional[datetime] = None


# ============= AUTH SCHEMAS =============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organization_id: int
    organization_slug: str


class TokenData(BaseModel):
    email: Optional[str] = None
    organization_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_slug: Optional[str] = None  # Para multi-tenant


# ============= ONBOARDING SCHEMAS =============

class OnboardingRequest(BaseModel):
    """Request completo para onboarding de novo cliente"""
    # Dados da empresa
    company_name: str
    company_slug: str
    company_type: OrganizationTypeEnum
    cnpj: Optional[str] = None
    
    # Contato
    email: EmailStr
    phone: str
    address: Optional[str] = None
    city: str = "Recife"
    state: str = "PE"
    
    # Primeiro admin
    admin_name: str
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    
    # Plano escolhido
    subscription_plan: SubscriptionPlanEnum = SubscriptionPlanEnum.TRIAL
    
    @validator('company_slug')
    def slug_validation(cls, v):
        # Apenas letras minúsculas, números e hífens
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug deve conter apenas letras minúsculas, números e hífens')
        return v


class OnboardingResponse(BaseModel):
    """Resposta do onboarding"""
    organization: OrganizationResponse
    admin_user: UserResponse
    access_token: str
    message: str = "Organização criada com sucesso! Bem-vindo ao LOGOS."
