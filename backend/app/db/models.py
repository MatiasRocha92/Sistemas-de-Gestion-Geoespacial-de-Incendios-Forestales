"""
Modelos SQLAlchemy para el sistema de gestión de incendios.
Definición de tablas con soporte geoespacial (GeoAlchemy2).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    DateTime, Date, Time, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.session import Base


class User(Base):
    """
    Modelo de usuarios del sistema.
    Roles: viewer, analyst, coordinator, brigadier, admin
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Datos personales
    full_name = Column(String(255))
    phone = Column(String(50))
    
    # Rol y permisos
    role = Column(String(50), default="viewer", nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Ubicación del usuario (para brigadistas)
    last_known_location = Column(Geometry("POINT", srid=4326))
    last_location_update = Column(DateTime(timezone=True))
    
    # Preferencias de notificación
    telegram_chat_id = Column(String(100))
    notify_by_email = Column(Boolean, default=True)
    notify_by_telegram = Column(Boolean, default=False)
    notify_by_push = Column(Boolean, default=True)
    
    # Zona de interés
    area_of_interest = Column(Geometry("POLYGON", srid=4326))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    alerts = relationship("Alert", back_populates="user")


class Hotspot(Base):
    """
    Modelo de focos de calor detectados por satélite.
    Datos provenientes de NASA FIRMS (VIIRS, MODIS) y GOES.
    """
    __tablename__ = "hotspots"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Ubicación geoespacial
    location = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Información del satélite
    satellite = Column(String(50), nullable=False, index=True)
    instrument = Column(String(50))
    
    # Datos de adquisición
    acq_date = Column(Date, nullable=False, primary_key=True, index=True)
    acq_time = Column(Time)
    acquired_at = Column(DateTime(timezone=True), index=True)
    
    # Métricas de detección
    brightness = Column(Float)  # Temperatura de brillo (Kelvin)
    bright_t31 = Column(Float)  # Temperatura banda 31 (MODIS)
    bright_ti4 = Column(Float)  # Temperatura banda I4 (VIIRS)
    bright_ti5 = Column(Float)  # Temperatura banda I5 (VIIRS)
    
    # Potencia radiativa del fuego
    frp = Column(Float, index=True)  # Fire Radiative Power (MW)
    
    # Confianza
    confidence = Column(String(20))  # low, nominal, high
    confidence_pct = Column(Integer)  # 0-100%
    
    # Clasificación
    type = Column(Integer)  # 0: veg fire, 1: volcán, 2: industria
    daynight = Column(String(1))  # D: día, N: noche
    
    # Origen
    source_system = Column(String(50), default="FIRMS")
    external_id = Column(String(255))
    
    # Metadatos
    scan = Column(Float)
    track = Column(Float)
    version = Column(String(20))
    
    # Estado
    status = Column(String(50), default="active", index=True)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class WeatherData(Base):
    """
    Modelo de datos meteorológicos.
    Incluye variables para cálculo de índices FWI.
    """
    __tablename__ = "weather_data"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Referencia al foco
    hotspot_id = Column(BigInteger)
    
    # Ubicación y tiempo
    location = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    observation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Variables meteorológicas
    temperature_2m = Column(Float)       # °C
    relative_humidity_2m = Column(Float)  # %
    wind_speed_10m = Column(Float)       # km/h
    wind_direction_10m = Column(Float)   # grados
    wind_gusts_10m = Column(Float)       # km/h
    precipitation = Column(Float)        # mm
    
    # Índices FWI
    ffmc = Column(Float)  # Fine Fuel Moisture Code
    dmc = Column(Float)   # Duff Moisture Code
    dc = Column(Float)    # Drought Code
    isi = Column(Float)   # Initial Spread Index
    bui = Column(Float)   # Buildup Index
    fwi = Column(Float)   # Fire Weather Index
    
    # Fuente
    source = Column(String(50), default="open_meteo")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Alert(Base):
    """
    Modelo de alertas enviadas a usuarios.
    """
    __tablename__ = "alerts"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Tipo y severidad
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Contenido
    title = Column(String(255), nullable=False)
    message = Column(Text)
    
    # Referencias
    hotspot_id = Column(BigInteger)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Área afectada
    affected_area = Column(Geometry("POLYGON", srid=4326))
    center_point = Column(Geometry("POINT", srid=4326))
    
    # Estado
    status = Column(String(50), default="pending", index=True)
    
    # Canales
    sent_by_email = Column(Boolean, default=False)
    sent_by_telegram = Column(Boolean, default=False)
    sent_by_push = Column(Boolean, default=False)
    
    # Tracking
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="alerts")


class FireRiskZone(Base):
    """
    Modelo de zonas de riesgo de incendio calculadas.
    """
    __tablename__ = "fire_risk_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Geometría
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False, index=True)
    
    # Nivel de riesgo
    risk_level = Column(String(20), nullable=False, index=True)
    fwi_value = Column(Float)
    
    # Período de validez
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)
    
    # Metadata
    calculation_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    model_version = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
