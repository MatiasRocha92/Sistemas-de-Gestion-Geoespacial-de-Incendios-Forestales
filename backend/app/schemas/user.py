"""
Schemas Pydantic para usuarios.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Schema base para usuarios."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema para crear usuario."""
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "viewer"


class UserUpdate(BaseModel):
    """Schema para actualizar usuario."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    notify_by_email: Optional[bool] = None
    notify_by_telegram: Optional[bool] = None
    notify_by_push: Optional[bool] = None
    telegram_chat_id: Optional[str] = None


class UserResponse(UserBase):
    """Schema de respuesta para usuarios."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    
    # Notificaciones
    notify_by_email: bool
    notify_by_telegram: bool
    notify_by_push: bool
    telegram_chat_id: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
