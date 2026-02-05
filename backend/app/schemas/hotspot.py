# =============================================================================
# Schemas Pydantic para Focos de Calor (Hotspots)
# =============================================================================
"""
Modelos Pydantic para validación y serialización de datos de hotspots.
Basados en la estructura de datos de NASA FIRMS.
"""

from datetime import date, time, datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field


class HotspotBase(BaseModel):
    """Schema base para hotspots."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitud")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud")
    satellite: str = Field(..., description="Satélite de origen")


class HotspotCreate(HotspotBase):
    """Schema para crear un hotspot."""
    instrument: Optional[str] = None
    acq_date: date
    acq_time: Optional[time] = None
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    bright_ti4: Optional[float] = None
    bright_ti5: Optional[float] = None
    frp: Optional[float] = None
    confidence: Optional[str] = None
    confidence_pct: Optional[int] = None
    type: Optional[int] = None
    daynight: Optional[str] = None
    scan: Optional[float] = None
    track: Optional[float] = None
    version: Optional[str] = None


class HotspotResponse(HotspotBase):
    """Schema de respuesta para hotspots."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    instrument: Optional[str] = None
    acq_date: date
    acq_time: Optional[time] = None
    acquired_at: Optional[datetime] = None
    
    # Métricas
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    bright_ti4: Optional[float] = None
    bright_ti5: Optional[float] = None
    frp: Optional[float] = Field(None, description="Fire Radiative Power (MW)")
    
    # Confianza
    confidence: Optional[str] = None
    confidence_pct: Optional[int] = None
    
    # Clasificación
    type: Optional[int] = None
    daynight: Optional[str] = None
    
    # Metadatos
    scan: Optional[float] = None
    track: Optional[float] = None
    version: Optional[str] = None
    source_system: Optional[str] = None
    
    # Estado
    status: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None


class HotspotGeoJSON(BaseModel):
    """Schema para representación GeoJSON de hotspot."""
    type: str = "Feature"
    geometry: dict
    properties: dict


class HotspotListResponse(BaseModel):
    """Schema de respuesta paginada de hotspots."""
    items: List[HotspotResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Schemas para Ingesta desde NASA FIRMS
# =============================================================================

class FIRMSDataRow(BaseModel):
    """
    Schema para una fila de datos CSV de NASA FIRMS.
    Soporta tanto formato VIIRS como MODIS.
    """
    model_config = ConfigDict(extra='ignore')
    
    # Campos comunes obligatorios
    latitude: float
    longitude: float
    acq_date: str  # Formato: YYYY-MM-DD
    acq_time: str  # Formato: HHMM
    satellite: str
    
    # Campos VIIRS
    bright_ti4: Optional[float] = None
    bright_ti5: Optional[float] = None
    confidence: Optional[str] = None  # low, nominal, high
    
    # Campos MODIS  
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    confidence_pct: Optional[int] = None  # 0-100
    
    # Campos comunes opcionales
    scan: Optional[float] = None
    track: Optional[float] = None
    instrument: Optional[str] = None
    version: Optional[str] = None
    frp: Optional[float] = None
    daynight: Optional[str] = None
    type: Optional[int] = None


class FIRMSIngestionResult(BaseModel):
    """Schema para el resultado de una operación de ingesta."""
    success: bool
    sensor: str
    country: str
    days: int
    records_fetched: int
    records_inserted: int
    records_duplicates: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class BulkIngestionResult(BaseModel):
    """Schema para el resultado de ingesta de múltiples sensores."""
    total_fetched: int = 0
    total_inserted: int = 0
    total_duplicates: int = 0
    results: List[FIRMSIngestionResult] = []
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


class IngestionRequest(BaseModel):
    """Schema para solicitar una ingesta de datos."""
    country_code: str = Field(
        default="ARG",
        min_length=3,
        max_length=3,
        description="Código ISO 3166-1 alpha-3 del país"
    )
    days: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Días de datos a ingestar (1-10)"
    )
    sensors: Optional[List[str]] = Field(
        default=None,
        description="Sensores específicos. Default: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, MODIS_NRT"
    )
