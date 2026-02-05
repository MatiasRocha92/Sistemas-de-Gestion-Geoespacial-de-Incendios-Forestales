"""
Router principal de la API v1.
Agrupa todos los endpoints del sistema.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import hotspots, health, users, alerts

api_router = APIRouter()

# Health y estado del sistema
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health & Status"]
)

# Focos de calor (hotspots)
api_router.include_router(
    hotspots.router,
    prefix="/hotspots",
    tags=["Focos de Calor"]
)

# Usuarios
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Usuarios"]
)

# Alertas
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alertas"]
)
