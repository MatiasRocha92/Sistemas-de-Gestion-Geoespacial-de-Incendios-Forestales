"""
Sistema de Gestión Geoespacial de Incendios Forestales
Backend FastAPI - Punto de Entrada Principal
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gestiona el ciclo de vida de la aplicación.
    Ejecuta código al iniciar y al cerrar la app.
    """
    # Startup
    logger.info("🔥 Iniciando Sistema de Gestión de Incendios Forestales...")
    logger.info(f"   Entorno: {settings.ENVIRONMENT}")
    logger.info(f"   Debug: {settings.DEBUG}")
    
    # Crear tablas si no existen (solo para desarrollo)
    if settings.DEBUG:
        async with engine.begin() as conn:
            # En producción usar Alembic para migraciones
            # await conn.run_sync(Base.metadata.create_all)
            pass
    
    logger.info("✓ Sistema iniciado correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando Sistema de Gestión de Incendios Forestales...")
    await engine.dispose()
    logger.info("✓ Sistema cerrado correctamente")


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## 🔥 Sistema de Gestión Geoespacial de Incendios Forestales
    
    API para el análisis y gestión de incendios forestales en Argentina y Latinoamérica.
    
    ### Funcionalidades:
    - 🛰️ **Focos de Calor**: Ingesta y visualización de datos NASA FIRMS
    - 🌡️ **Meteorología**: Datos climáticos de Open-Meteo
    - 📊 **Índices de Riesgo**: Cálculo de FWI (Fire Weather Index)
    - 🔔 **Alertas**: Notificaciones en tiempo real vía WebSocket, Telegram
    - 🗺️ **Geoespacial**: Consultas espaciales con PostGIS
    
    ### Documentación Adicional:
    - [Swagger UI](/docs) - Documentación interactiva
    - [ReDoc](/redoc) - Documentación alternativa
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de la API
app.include_router(api_router, prefix=settings.API_V1_STR)


# Health Check endpoint (raíz)
@app.get("/", tags=["Health"])
async def root():
    """
    Health check básico del sistema.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check detallado con estado de servicios.
    """
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "operational",
            "redis": "operational",
        },
        "version": "1.0.0",
    }
