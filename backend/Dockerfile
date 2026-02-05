# =============================================================================
# Backend FastAPI - Sistema de Gestión de Incendios Forestales
# Python 3.12 + Dependencias Geoespaciales
# =============================================================================
FROM python:3.12-slim as base

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema para geoespacial
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# =============================================================================
# Stage: Dependencies
# =============================================================================
FROM base as dependencies

# Copiar solo requirements para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================================
# Stage: Development
# =============================================================================
FROM dependencies as development

# Instalar dependencias de desarrollo
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Copiar código fuente
COPY . .

# Puerto de la aplicación
EXPOSE 8000

# Comando por defecto (desarrollo con hot-reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Stage: Production
# =============================================================================
FROM dependencies as production

# Copiar código fuente
COPY . .

# Usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Puerto de la aplicación
EXPOSE 8000

# Comando para producción (con workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
