"""
Endpoints para gestión de alertas.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import Alert
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    alert_type: Optional[str] = Query(default=None, description="Tipo de alerta"),
    severity: Optional[str] = Query(default=None, description="Severidad"),
    status: Optional[str] = Query(default=None, description="Estado de la alerta"),
    user_id: Optional[int] = Query(default=None, description="ID del usuario"),
    days: int = Query(default=7, ge=1, le=365, description="Últimos N días"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista alertas con filtros.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(Alert).where(Alert.created_at >= start_date)
    
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if user_id:
        query = query.where(Alert.user_id == user_id)
    
    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/stats")
async def get_alerts_stats(
    days: int = Query(default=7, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Estadísticas de alertas.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total
    total_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= start_date)
    )
    total = total_result.scalar() or 0
    
    # Por severidad
    by_severity_result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.created_at >= start_date)
        .group_by(Alert.severity)
    )
    by_severity = {row[0]: row[1] for row in by_severity_result.all()}
    
    # Por estado
    by_status_result = await db.execute(
        select(Alert.status, func.count(Alert.id))
        .where(Alert.created_at >= start_date)
        .group_by(Alert.status)
    )
    by_status = {row[0]: row[1] for row in by_status_result.all()}
    
    return {
        "period_days": days,
        "total_alerts": total,
        "by_severity": by_severity,
        "by_status": by_status
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una alerta específica.
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Marca una alerta como leída.
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alert.status = "read"
    alert.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Alerta marcada como leída", "alert_id": alert_id}
