"""
Database models for VerifiK system
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User/Customer model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    stores = relationship("Store", back_populates="owner")


class Store(Base):
    """Store/Location model"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String, default="Recife")
    state = Column(String, default="PE")
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="basic")  # basic, professional, enterprise
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="stores")
    cameras = relationship("Camera", back_populates="store")
    products = relationship("Product", back_populates="store")
    detections = relationship("Detection", back_populates="store")


class Camera(Base):
    """Camera device model"""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    rtsp_url = Column(String)  # rtsp://user:pass@ip:port/stream
    location = Column(String)  # checkout_1, checkout_2, etc
    store_id = Column(Integer, ForeignKey("stores.id"))
    is_active = Column(Boolean, default=True)
    last_ping = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="cameras")
    detections = relationship("Detection", back_populates="camera")


class Product(Base):
    """Product catalog model"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    barcode = Column(String, unique=True, index=True)
    category = Column(String)
    price = Column(Float)
    image_url = Column(String)
    store_id = Column(Integer, ForeignKey("stores.id"))
    yolo_class_id = Column(Integer)  # ID da classe no modelo YOLOv8 treinado
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store = relationship("Store", back_populates="products")


class Detection(Base):
    """Detection event model - logs when AI detects a mismatch"""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    store_id = Column(Integer, ForeignKey("stores.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Detection details
    products_detected = Column(JSON)  # [{"name": "Coca-Cola", "confidence": 0.95}, ...]
    products_in_pdv = Column(JSON)    # [{"name": "Água", "price": 2.50}, ...]
    mismatch = Column(Boolean, default=False)
    mismatch_details = Column(Text)
    
    # Evidence
    image_path = Column(String)  # Path to saved frame
    confidence_score = Column(Float)
    
    # Status
    reviewed = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    camera = relationship("Camera", back_populates="detections")
    store = relationship("Store", back_populates="detections")


class Alert(Base):
    """Alert/Notification model"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
