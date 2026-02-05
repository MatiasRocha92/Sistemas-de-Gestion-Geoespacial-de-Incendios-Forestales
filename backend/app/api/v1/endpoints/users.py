"""
Endpoints para gestión de usuarios.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserCreate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    role: Optional[str] = Query(default=None, description="Filtrar por rol"),
    is_active: Optional[bool] = Query(default=None, description="Filtrar por estado activo"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema.
    """
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    """
    Obtiene el usuario actual (requiere autenticación).
    TODO: Implementar autenticación JWT.
    """
    raise HTTPException(
        status_code=501,
        detail="Autenticación no implementada aún"
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un usuario por ID.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse.model_validate(user)
