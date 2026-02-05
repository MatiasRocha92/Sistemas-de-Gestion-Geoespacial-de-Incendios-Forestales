"""
Configuración central del backend.
Carga variables de entorno y define settings globales.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno.
    """
    
    # ==========================================================================
    # Información del Proyecto
    # ==========================================================================
    PROJECT_NAME: str = "Sistema de Gestión de Incendios Forestales"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ==========================================================================
    # Base de Datos
    # ==========================================================================
    DATABASE_URL: str = "postgresql+asyncpg://firewatch:firewatch_secret@localhost:5432/firewatch_db"
    DATABASE_URL_SYNC: str = "postgresql://firewatch:firewatch_secret@localhost:5432/firewatch_db"
    
    # ==========================================================================
    # Redis
    # ==========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ==========================================================================
    # Seguridad
    # ==========================================================================
    SECRET_KEY: str = "your_super_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    ALGORITHM: str = "HS256"
    
    # ==========================================================================
    # CORS
    # ==========================================================================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """Convierte string de origins en lista."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ==========================================================================
    # APIs Externas
    # ==========================================================================
    # NASA FIRMS
    NASA_FIRMS_API_KEY: str = ""
    NASA_FIRMS_BASE_URL: str = "https://firms.modaps.eosdis.nasa.gov/api"
    
    # Open-Meteo
    OPEN_METEO_API_KEY: str = ""
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    # ==========================================================================
    # Configuración de Ingesta
    # ==========================================================================
    # País por defecto para consultas FIRMS
    DEFAULT_COUNTRY_CODE: str = "ARG"
    
    # Días de datos a consultar por defecto
    DEFAULT_FIRMS_DAYS: int = 1
    
    # Intervalo de ingesta en minutos
    INGESTION_INTERVAL_MINUTES: int = 180  # 3 horas
    
    # ==========================================================================
    # Límites y Paginación
    # ==========================================================================
    MAX_HOTSPOTS_PER_QUERY: int = 10000
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Instancia global de settings
settings = Settings()
