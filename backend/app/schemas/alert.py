"""
Schemas Pydantic para alertas.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    """Schema base para alertas."""
    alert_type: str = Field(..., description="Tipo: new_fire, fire_update, fire_contained, high_risk_area")
    severity: str = Field(..., description="Severidad: low, medium, high, critical")
    title: str
    message: Optional[str] = None


class AlertCreate(AlertBase):
    """Schema para crear alerta."""
    hotspot_id: Optional[int] = None
    user_id: Optional[int] = None
    metadata: Optional[dict] = None


class AlertResponse(AlertBase):
    """Schema de respuesta para alertas."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hotspot_id: Optional[int] = None
    user_id: Optional[int] = None
    
    # Estado
    status: str
    
    # Canales de envío
    sent_by_email: bool
    sent_by_telegram: bool
    sent_by_push: bool
    
    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Any] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
