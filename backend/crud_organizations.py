"""
CRUD operations for Organizations (multi-tenant)
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import re
from models_multitenant import Organization, User, SubscriptionPlan, SubscriptionStatus, OrganizationType
from schemas_multitenant import OrganizationCreate, OrganizationUpdate
from crud_users import hash_password


def create_slug(name: str) -> str:
    """Criar slug a partir do nome da organização"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Remove caracteres especiais
    slug = re.sub(r'\s+', '-', slug)  # Substitui espaços por hífens
    slug = re.sub(r'-+', '-', slug)  # Remove hífens duplicados
    return slug.strip('-')


def get_organization(db: Session, organization_id: int) -> Optional[Organization]:
    """Buscar organização por ID"""
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
    """Buscar organização por slug"""
    return db.query(Organization).filter(Organization.slug == slug).first()


def get_organization_by_cnpj(db: Session, cnpj: str) -> Optional[Organization]:
    """Buscar organização por CNPJ"""
    return db.query(Organization).filter(Organization.cnpj == cnpj).first()


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[Organization]:
    """Listar todas as organizações"""
    query = db.query(Organization)
    
    if active_only:
        query = query.filter(Organization.is_active == True)
    
    return query.offset(skip).limit(limit).all()


def create_organization(
    db: Session,
    org_data: OrganizationCreate
) -> tuple[Organization, User]:
    """
    Criar nova organização + primeiro admin (onboarding)
    
    Retorna: (organization, admin_user)
    """
    # Verificar se slug já existe
    existing_org = get_organization_by_slug(db, org_data.slug)
    if existing_org:
        raise ValueError(f"Organização com slug '{org_data.slug}' já existe")
    
    # Verificar CNPJ duplicado
    if org_data.cnpj:
        existing_cnpj = get_organization_by_cnpj(db, org_data.cnpj)
        if existing_cnpj:
            raise ValueError(f"CNPJ {org_data.cnpj} já cadastrado")
    
    # Definir limites do plano
    plan_limits = {
        SubscriptionPlan.FREE: {
            "max_stores": 1,
            "max_users": 5,
            "max_cameras": 2,
            "max_erp_integrations": 1,
            "monthly_price": 0.0,
            "trial_days": 30
        },
        SubscriptionPlan.BASIC: {
            "max_stores": 3,
            "max_users": 15,
            "max_cameras": 8,
            "max_erp_integrations": 3,
            "monthly_price": 497.0,
            "trial_days": 0
        },
        SubscriptionPlan.PROFESSIONAL: {
            "max_stores": 10,
            "max_users": 50,
            "max_cameras": 40,
            "max_erp_integrations": 10,
            "monthly_price": 1497.0,
            "trial_days": 0
        },
        SubscriptionPlan.ENTERPRISE: {
            "max_stores": 999,
            "max_users": 999,
            "max_cameras": 999,
            "max_erp_integrations": 999,
            "monthly_price": 0.0,  # Preço customizado
            "trial_days": 0
        }
    }
    
    limits = plan_limits[org_data.subscription_plan]
    
    # Calcular data de expiração (trial)
    subscription_expires_at = None
    subscription_status = SubscriptionStatus.ACTIVE
    
    if org_data.subscription_plan == SubscriptionPlan.FREE:
        subscription_status = SubscriptionStatus.TRIAL
        subscription_expires_at = datetime.utcnow() + timedelta(days=limits["trial_days"])
    
    # Criar organização
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug,
        type=org_data.type,
        cnpj=org_data.cnpj,
        email=org_data.email,
        phone=org_data.phone,
        address=org_data.address,
        city=org_data.city,
        state=org_data.state,
        subscription_plan=org_data.subscription_plan,
        subscription_status=subscription_status,
        subscription_expires_at=subscription_expires_at,
        max_stores=limits["max_stores"],
        max_users=limits["max_users"],
        max_cameras=limits["max_cameras"],
        max_erp_integrations=limits["max_erp_integrations"],
        monthly_price=limits["monthly_price"]
    )
    
    db.add(organization)
    db.flush()  # Gera o ID sem fazer commit
    
    # Criar primeiro admin
    admin_user = User(
        organization_id=organization.id,
        email=org_data.admin_email,
        hashed_password=hash_password(org_data.admin_password),
        full_name=org_data.admin_name,
        is_admin=True,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(organization)
    db.refresh(admin_user)
    
    return organization, admin_user


def update_organization(
    db: Session,
    organization_id: int,
    org_data: OrganizationUpdate
) -> Optional[Organization]:
    """Atualizar dados da organização"""
    organization = get_organization(db, organization_id)
    if not organization:
        return None
    
    update_data = org_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    organization.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(organization)
    return organization


def upgrade_subscription(
    db: Session,
    organization_id: int,
    new_plan: SubscriptionPlan
) -> Optional[Organization]:
    """Fazer upgrade/downgrade do plano"""
    organization = get_organization(db, organization_id)
    if not organization:
        return None
    
    # Definir novos limites
    plan_limits = {
        SubscriptionPlan.BASIC: {
            "max_stores": 3,
            "max_users": 15,
            "max_cameras": 8,
            "max_erp_integrations": 3,
            "monthly_price": 497.0
        },
        SubscriptionPlan.PROFESSIONAL: {
            "max_stores": 10,
            "max_users": 50,
            "max_cameras": 40,
            "max_erp_integrations": 10,
            "monthly_price": 1497.0
        },
        SubscriptionPlan.ENTERPRISE: {
            "max_stores": 999,
            "max_users": 999,
            "max_cameras": 999,
            "max_erp_integrations": 999,
            "monthly_price": 0.0
        }
    }
    
    if new_plan in plan_limits:
        limits = plan_limits[new_plan]
        
        organization.subscription_plan = new_plan
        organization.subscription_status = SubscriptionStatus.ACTIVE
        organization.max_stores = limits["max_stores"]
        organization.max_users = limits["max_users"]
        organization.max_cameras = limits["max_cameras"]
        organization.max_erp_integrations = limits["max_erp_integrations"]
        organization.monthly_price = limits["monthly_price"]
        organization.subscription_expires_at = None  # Planos pagos não expiram
        organization.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(organization)
    
    return organization


def suspend_organization(db: Session, organization_id: int) -> Optional[Organization]:
    """Suspender organização (falta de pagamento)"""
    organization = get_organization(db, organization_id)
    if not organization:
        return None
    
    organization.subscription_status = SubscriptionStatus.SUSPENDED
    organization.is_active = False
    organization.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(organization)
    return organization


def reactivate_organization(db: Session, organization_id: int) -> Optional[Organization]:
    """Reativar organização suspensa"""
    organization = get_organization(db, organization_id)
    if not organization:
        return None
    
    organization.subscription_status = SubscriptionStatus.ACTIVE
    organization.is_active = True
    organization.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(organization)
    return organization


def delete_organization(db: Session, organization_id: int) -> bool:
    """
    Deletar organização (soft delete - apenas marca como inativa)
    Apenas super admins podem fazer isso
    """
    organization = get_organization(db, organization_id)
    if not organization:
        return False
    
    organization.is_active = False
    organization.subscription_status = SubscriptionStatus.CANCELLED
    organization.updated_at = datetime.utcnow()
    
    db.commit()
    return True


def check_organization_limits(db: Session, organization_id: int) -> dict:
    """
    Verificar uso atual vs limites do plano
    
    Retorna:
    {
        "stores": {"current": 5, "limit": 10, "ok": True},
        "users": {"current": 23, "limit": 50, "ok": True},
        ...
    }
    """
    organization = get_organization(db, organization_id)
    if not organization:
        return {}
    
    # Contar uso atual
    current_stores = db.query(User).filter(User.organization_id == organization_id).count()
    current_users = len(organization.users)
    # current_cameras e current_erps viriam das tabelas correspondentes
    
    return {
        "stores": {
            "current": current_stores,
            "limit": organization.max_stores,
            "ok": current_stores < organization.max_stores
        },
        "users": {
            "current": current_users,
            "limit": organization.max_users,
            "ok": current_users < organization.max_users
        },
        "cameras": {
            "current": 0,  # TODO: implementar contagem
            "limit": organization.max_cameras,
            "ok": True
        },
        "erp_integrations": {
            "current": len(organization.erp_integrations),
            "limit": organization.max_erp_integrations,
            "ok": len(organization.erp_integrations) < organization.max_erp_integrations
        }
    }
