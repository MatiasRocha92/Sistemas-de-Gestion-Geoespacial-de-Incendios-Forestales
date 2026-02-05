"""
Configuración de conexión a la base de datos PostgreSQL con soporte async.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# =============================================================================
# Engine Asíncrono (para FastAPI)
# =============================================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session Factory Asíncrona
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# =============================================================================
# Engine Síncrono (para Alembic y tareas background)
# =============================================================================
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# =============================================================================
# Base para modelos SQLAlchemy
# =============================================================================
Base = declarative_base()


# =============================================================================
# Dependency para inyectar sesión de BD en endpoints
# =============================================================================
async def get_db() -> AsyncSession:
    """
    Dependency que proporciona una sesión de base de datos.
    Uso: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
