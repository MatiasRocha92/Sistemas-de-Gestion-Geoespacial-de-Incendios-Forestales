"""
Endpoints de health check y estado del sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check básico.
    """
    return {"status": "healthy", "service": "firewatch-api"}


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check detallado con verificación de servicios.
    """
    services = {}
    
    # Verificar PostgreSQL
    try:
        result = await db.execute(text("SELECT 1"))
        services["database"] = {
            "status": "operational",
            "type": "PostgreSQL + PostGIS"
        }
    except Exception as e:
        services["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Verificar Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        services["redis"] = {
            "status": "operational",
            "type": "Redis Stack"
        }
        await redis_client.close()
    except Exception as e:
        services["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determinar estado general
    all_operational = all(
        s.get("status") == "operational" 
        for s in services.values()
    )
    
    return {
        "status": "healthy" if all_operational else "degraded",
        "environment": settings.ENVIRONMENT,
        "services": services
    }
