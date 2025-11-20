"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ===== USER SCHEMAS =====
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== STORE SCHEMAS =====
class StoreBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: str = "Recife"
    state: str = "PE"


class StoreCreate(StoreBase):
    plan: str = "basic"  # basic, professional, enterprise


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: int
    owner_id: int
    is_active: bool
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== CAMERA SCHEMAS =====
class CameraBase(BaseModel):
    name: str
    ip_address: str
    location: Optional[str] = None


class CameraCreate(CameraBase):
    rtsp_url: Optional[str] = None
    store_id: int


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    rtsp_url: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class CameraResponse(CameraBase):
    id: int
    store_id: int
    is_active: bool
    rtsp_url: Optional[str] = None
    last_ping: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== PRODUCT SCHEMAS =====
class ProductBase(BaseModel):
    name: str
    barcode: str
    category: Optional[str] = None
    price: Optional[float] = None


class ProductCreate(ProductBase):
    store_id: int
    image_url: Optional[str] = None
    yolo_class_id: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    yolo_class_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    store_id: int
    is_active: bool
    yolo_class_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== DETECTION SCHEMAS =====
class DetectionBase(BaseModel):
    camera_id: int
    store_id: int
    products_detected: List[Dict[str, Any]]
    products_in_pdv: List[Dict[str, Any]]
    mismatch: bool
    mismatch_details: Optional[str] = None


class DetectionCreate(DetectionBase):
    image_path: Optional[str] = None
    confidence_score: Optional[float] = None


class DetectionUpdate(BaseModel):
    reviewed: Optional[bool] = None
    false_positive: Optional[bool] = None
    notes: Optional[str] = None


class DetectionResponse(DetectionBase):
    id: int
    timestamp: datetime
    image_path: Optional[str] = None
    confidence_score: Optional[float] = None
    reviewed: bool
    false_positive: bool

    class Config:
        from_attributes = True


# ===== ALERT SCHEMAS =====
class AlertCreate(BaseModel):
    detection_id: int
    user_id: int
    message: str
    severity: str = "medium"


class AlertResponse(BaseModel):
    id: int
    detection_id: int
    user_id: int
    message: str
    severity: str
    sent: bool
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== AUTH SCHEMAS =====
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
