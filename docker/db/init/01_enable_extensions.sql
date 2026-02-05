-- =============================================================================
-- Script de Inicialización de Base de Datos PostgreSQL + PostGIS
-- Sistema de Gestión Geoespacial de Incendios Forestales
-- =============================================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para búsquedas de texto eficientes

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✓ PostGIS habilitado exitosamente';
    RAISE NOTICE '✓ Versión PostGIS: %', PostGIS_Version();
END $$;
