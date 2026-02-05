"""
Endpoints para gestión de focos de calor (hotspots).
Incluye consultas geoespaciales y filtros.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from geoalchemy2.functions import ST_MakeEnvelope, ST_Contains, ST_AsGeoJSON

from app.db.session import get_db
from app.db.models import Hotspot
from app.schemas.hotspot import (
    HotspotResponse, 
    HotspotGeoJSON, 
    HotspotListResponse,
    IngestionRequest,
    BulkIngestionResult,
    FIRMSIngestionResult
)
from app.services.ingestion_service import HotspotIngestionService
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=HotspotListResponse)
async def get_hotspots(
    # Filtros temporales
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha inicial (YYYY-MM-DD). Por defecto: últimas 24 horas"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha final (YYYY-MM-DD). Por defecto: hoy"
    ),
    
    # Filtros geoespaciales (bounding box)
    min_lat: Optional[float] = Query(
        default=None,
        ge=-90, le=90,
        description="Latitud mínima del bounding box"
    ),
    max_lat: Optional[float] = Query(
        default=None,
        ge=-90, le=90,
        description="Latitud máxima del bounding box"
    ),
    min_lon: Optional[float] = Query(
        default=None,
        ge=-180, le=180,
        description="Longitud mínima del bounding box"
    ),
    max_lon: Optional[float] = Query(
        default=None,
        ge=-180, le=180,
        description="Longitud máxima del bounding box"
    ),
    
    # Filtros de atributos
    satellite: Optional[str] = Query(
        default=None,
        description="Filtrar por satélite (VIIRS-SNPP, MODIS-AQUA, etc.)"
    ),
    confidence: Optional[str] = Query(
        default=None,
        description="Nivel de confianza (low, nominal, high)"
    ),
    min_frp: Optional[float] = Query(
        default=None,
        ge=0,
        description="Potencia radiativa mínima (MW)"
    ),
    status: Optional[str] = Query(
        default=None,
        description="Estado del foco (active, contained, extinguished)"
    ),
    
    # Paginación
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=100, ge=1, le=1000, description="Elementos por página"),
    
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene lista de focos de calor con filtros geoespaciales y temporales.
    
    ## Filtros disponibles:
    - **Temporal**: Por rango de fechas
    - **Espacial**: Por bounding box (rectángulo geográfico)
    - **Atributos**: Por satélite, confianza, potencia radiativa, estado
    
    ## Ejemplo de uso:
    ```
    GET /api/v1/hotspots?min_lat=-35&max_lat=-30&min_lon=-60&max_lon=-55&start_date=2025-01-01
    ```
    """
    # Valores por defecto para fechas
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=1)
    
    # Construir query base
    query = select(Hotspot).where(
        and_(
            Hotspot.acq_date >= start_date,
            Hotspot.acq_date <= end_date
        )
    )
    
    # Aplicar filtro de bounding box si se proporciona
    if all([min_lat, max_lat, min_lon, max_lon]):
        bbox = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        query = query.where(ST_Contains(bbox, Hotspot.location))
    
    # Aplicar filtros de atributos
    if satellite:
        query = query.where(Hotspot.satellite == satellite)
    if confidence:
        query = query.where(Hotspot.confidence == confidence)
    if min_frp is not None:
        query = query.where(Hotspot.frp >= min_frp)
    if status:
        query = query.where(Hotspot.status == status)
    
    # Ordenar por fecha de adquisición (más recientes primero)
    query = query.order_by(Hotspot.acquired_at.desc())
    
    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Aplicar paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Ejecutar query
    result = await db.execute(query)
    hotspots = result.scalars().all()
    
    return HotspotListResponse(
        items=[HotspotResponse.model_validate(h) for h in hotspots],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/geojson")
async def get_hotspots_geojson(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    min_lat: Optional[float] = Query(default=None, ge=-90, le=90),
    max_lat: Optional[float] = Query(default=None, ge=-90, le=90),
    min_lon: Optional[float] = Query(default=None, ge=-180, le=180),
    max_lon: Optional[float] = Query(default=None, ge=-180, le=180),
    limit: int = Query(default=5000, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna focos de calor en formato GeoJSON para visualización en mapa.
    
    Optimizado para renderizado directo en MapLibre GL JS.
    """
    # Valores por defecto
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=1)
    
    # Query con conversión a GeoJSON
    query = select(
        Hotspot.id,
        ST_AsGeoJSON(Hotspot.location).label("geometry"),
        Hotspot.latitude,
        Hotspot.longitude,
        Hotspot.satellite,
        Hotspot.acq_date,
        Hotspot.acq_time,
        Hotspot.brightness,
        Hotspot.frp,
        Hotspot.confidence,
        Hotspot.status
    ).where(
        and_(
            Hotspot.acq_date >= start_date,
            Hotspot.acq_date <= end_date
        )
    )
    
    # Filtro espacial
    if all([min_lat, max_lat, min_lon, max_lon]):
        bbox = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        query = query.where(ST_Contains(bbox, Hotspot.location))
    
    query = query.order_by(Hotspot.acquired_at.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Construir FeatureCollection
    features = []
    for row in rows:
        import json
        feature = {
            "type": "Feature",
            "geometry": json.loads(row.geometry) if row.geometry else None,
            "properties": {
                "id": row.id,
                "satellite": row.satellite,
                "acq_date": str(row.acq_date),
                "acq_time": str(row.acq_time) if row.acq_time else None,
                "brightness": row.brightness,
                "frp": row.frp,
                "confidence": row.confidence,
                "status": row.status
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total": len(features),
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    }


@router.get("/{hotspot_id}", response_model=HotspotResponse)
async def get_hotspot(
    hotspot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene detalles de un foco de calor específico.
    """
    result = await db.execute(
        select(Hotspot).where(Hotspot.id == hotspot_id)
    )
    hotspot = result.scalar_one_or_none()
    
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot no encontrado")
    
    return HotspotResponse.model_validate(hotspot)


@router.get("/stats/summary")
async def get_hotspots_stats(
    days: int = Query(default=7, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene estadísticas resumidas de focos de calor.
    """
    start_date = date.today() - timedelta(days=days)
    
    # Total de focos
    total_query = select(func.count(Hotspot.id)).where(
        Hotspot.acq_date >= start_date
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # Por satélite
    by_satellite_query = select(
        Hotspot.satellite,
        func.count(Hotspot.id).label("count")
    ).where(
        Hotspot.acq_date >= start_date
    ).group_by(Hotspot.satellite)
    
    satellite_result = await db.execute(by_satellite_query)
    by_satellite = {row.satellite: row.count for row in satellite_result.all()}
    
    # Por día
    by_day_query = select(
        Hotspot.acq_date,
        func.count(Hotspot.id).label("count")
    ).where(
        Hotspot.acq_date >= start_date
    ).group_by(Hotspot.acq_date).order_by(Hotspot.acq_date)
    
    day_result = await db.execute(by_day_query)
    by_day = {str(row.acq_date): row.count for row in day_result.all()}
    
    return {
        "period_days": days,
        "total_hotspots": total,
        "by_satellite": by_satellite,
        "by_day": by_day
    }


# =============================================================================
# ENDPOINTS DE INGESTA (Tarea 1.1)
# =============================================================================

@router.post("/ingest", response_model=BulkIngestionResult)
async def ingest_firms_data(
    request: IngestionRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta la ingesta de datos de focos de calor desde NASA FIRMS.
    
    ## Descripción
    Este endpoint consulta la API de NASA FIRMS para obtener datos de focos
    de calor detectados por satélite, los parsea y los almacena en la base
    de datos PostgreSQL/PostGIS.
    
    ## Sensores disponibles:
    - **VIIRS_SNPP_NRT**: VIIRS en Suomi NPP (Near Real-Time)
    - **VIIRS_NOAA20_NRT**: VIIRS en NOAA-20 (Near Real-Time)
    - **MODIS_NRT**: MODIS Combined Terra/Aqua (Near Real-Time)
    
    ## Países soportados (ejemplos):
    - ARG: Argentina
    - BRA: Brasil
    - CHL: Chile
    - PRY: Paraguay
    - URY: Uruguay
    
    ## Notas:
    - Requiere configurar NASA_FIRMS_API_KEY en variables de entorno
    - Máximo 10 días de datos por consulta (límite de la API)
    - Los duplicados se detectan automáticamente por (lat, lon, fecha, hora, satélite)
    
    ## Ejemplo de uso:
    ```json
    POST /api/v1/hotspots/ingest
    {
        "country_code": "ARG",
        "days": 1,
        "sensors": ["VIIRS_SNPP_NRT", "MODIS_NRT"]
    }
    ```
    """
    # Verificar que la API key esté configurada
    if not settings.NASA_FIRMS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="NASA FIRMS API Key no configurada. Configurar NASA_FIRMS_API_KEY en .env"
        )
    
    # Valores por defecto si no se proporciona request
    if request is None:
        request = IngestionRequest()
    
    # Ejecutar ingesta
    service = HotspotIngestionService(db)
    result = await service.ingest_all_sensors(
        country_code=request.country_code,
        days=request.days,
        sensors=request.sensors
    )
    
    return result


@router.post("/ingest/quick")
async def quick_ingest(
    country: str = Query(default="ARG", min_length=3, max_length=3),
    days: int = Query(default=1, ge=1, le=10),
    sensor: str = Query(default="VIIRS_SNPP_NRT"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingesta rápida de un solo sensor (útil para pruebas).
    
    Usa query parameters en lugar de body JSON para facilitar testing.
    """
    if not settings.NASA_FIRMS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="NASA FIRMS API Key no configurada"
        )
    
    service = HotspotIngestionService(db)
    result = await service.ingest_from_firms(
        country_code=country,
        sensor=sensor,
        days=days
    )
    
    return result
