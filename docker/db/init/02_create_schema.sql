-- =============================================================================
-- Esquema de Base de Datos: Sistema de Gestión de Incendios Forestales
-- =============================================================================

-- =============================================================================
-- TABLA: users
-- Usuarios del sistema (analistas, coordinadores, brigadistas)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Datos personales
    full_name VARCHAR(255),
    phone VARCHAR(50),
    
    -- Rol y permisos
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',  -- viewer, analyst, coordinator, brigadier, admin
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Ubicación del usuario (para brigadistas)
    last_known_location GEOMETRY(POINT, 4326),
    last_location_update TIMESTAMPTZ,
    
    -- Preferencias de notificación
    telegram_chat_id VARCHAR(100),
    notify_by_email BOOLEAN DEFAULT TRUE,
    notify_by_telegram BOOLEAN DEFAULT FALSE,
    notify_by_push BOOLEAN DEFAULT TRUE,
    
    -- Zona de interés (polígono de área asignada)
    area_of_interest GEOMETRY(POLYGON, 4326),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_location ON users USING GIST(last_known_location);
CREATE INDEX IF NOT EXISTS idx_users_area ON users USING GIST(area_of_interest);

-- =============================================================================
-- TABLA: hotspots (Focos de Calor)
-- Datos de detecciones satelitales - Tabla particionada por fecha
-- =============================================================================
CREATE TABLE IF NOT EXISTS hotspots (
    id BIGSERIAL,
    
    -- Ubicación geoespacial
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- Información del satélite
    satellite VARCHAR(50) NOT NULL,           -- VIIRS-SNPP, VIIRS-NOAA20, MODIS-AQUA, MODIS-TERRA, GOES-16
    instrument VARCHAR(50),                    -- VIIRS, MODIS, ABI
    
    -- Datos de adquisición
    acq_date DATE NOT NULL,                   -- Fecha de adquisición
    acq_time TIME,                            -- Hora de adquisición UTC
    acquired_at TIMESTAMPTZ,                  -- Timestamp completo
    
    -- Métricas de detección
    brightness DOUBLE PRECISION,              -- Temperatura de brillo (Kelvin)
    bright_t31 DOUBLE PRECISION,              -- Temperatura banda 31 (MODIS)
    bright_ti4 DOUBLE PRECISION,              -- Temperatura banda I4 (VIIRS)
    bright_ti5 DOUBLE PRECISION,              -- Temperatura banda I5 (VIIRS)
    
    -- Potencia radiativa del fuego
    frp DOUBLE PRECISION,                     -- Fire Radiative Power (MW)
    
    -- Confianza de la detección
    confidence VARCHAR(20),                   -- low, nominal, high (VIIRS)
    confidence_pct INTEGER,                   -- 0-100% (MODIS)
    
    -- Clasificación
    type INTEGER,                             -- 0: presunto veg fire, 1: volcán activo, 2: industria, 3: otro
    daynight VARCHAR(1),                      -- D: día, N: noche
    
    -- Identificador de origen
    source_system VARCHAR(50) DEFAULT 'FIRMS',
    external_id VARCHAR(255),
    
    -- Metadatos
    scan DOUBLE PRECISION,                    -- Tamaño scan (km)
    track DOUBLE PRECISION,                   -- Tamaño track (km)
    version VARCHAR(20),                      -- Versión del algoritmo
    
    -- Estado del foco
    status VARCHAR(50) DEFAULT 'active',      -- active, contained, extinguished, false_alarm
    verified_by INTEGER REFERENCES users(id),
    verified_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, acq_date)
) PARTITION BY RANGE (acq_date);

-- Crear particiones para los próximos meses (ejemplo: 2025)
CREATE TABLE IF NOT EXISTS hotspots_2024_h2 PARTITION OF hotspots
    FOR VALUES FROM ('2024-07-01') TO ('2025-01-01');

CREATE TABLE IF NOT EXISTS hotspots_2025_q1 PARTITION OF hotspots
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE IF NOT EXISTS hotspots_2025_q2 PARTITION OF hotspots
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

CREATE TABLE IF NOT EXISTS hotspots_2025_q3 PARTITION OF hotspots
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE IF NOT EXISTS hotspots_2025_q4 PARTITION OF hotspots
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS hotspots_2026_q1 PARTITION OF hotspots
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');

CREATE TABLE IF NOT EXISTS hotspots_2026_q2 PARTITION OF hotspots
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

-- Índices para hotspots (se aplican a todas las particiones)
CREATE INDEX IF NOT EXISTS idx_hotspots_location ON hotspots USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_hotspots_acq_date ON hotspots(acq_date DESC);
CREATE INDEX IF NOT EXISTS idx_hotspots_satellite ON hotspots(satellite);
CREATE INDEX IF NOT EXISTS idx_hotspots_status ON hotspots(status);
CREATE INDEX IF NOT EXISTS idx_hotspots_frp ON hotspots(frp DESC);
CREATE INDEX IF NOT EXISTS idx_hotspots_acquired_at ON hotspots(acquired_at DESC);

-- =============================================================================
-- TABLA: weather_data
-- Datos meteorológicos asociados a focos de calor
-- =============================================================================
CREATE TABLE IF NOT EXISTS weather_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- Referencia al foco de calor
    hotspot_id BIGINT,
    
    -- Ubicación y tiempo
    location GEOMETRY(POINT, 4326) NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    
    -- Variables meteorológicas
    temperature_2m DOUBLE PRECISION,          -- Temperatura a 2m (°C)
    relative_humidity_2m DOUBLE PRECISION,    -- Humedad relativa (%)
    wind_speed_10m DOUBLE PRECISION,          -- Velocidad del viento a 10m (km/h)
    wind_direction_10m DOUBLE PRECISION,      -- Dirección del viento (grados)
    wind_gusts_10m DOUBLE PRECISION,          -- Ráfagas de viento (km/h)
    precipitation DOUBLE PRECISION,           -- Precipitación (mm)
    
    -- Índices calculados (FWI Components)
    ffmc DOUBLE PRECISION,                    -- Fine Fuel Moisture Code
    dmc DOUBLE PRECISION,                     -- Duff Moisture Code
    dc DOUBLE PRECISION,                      -- Drought Code
    isi DOUBLE PRECISION,                     -- Initial Spread Index
    bui DOUBLE PRECISION,                     -- Buildup Index
    fwi DOUBLE PRECISION,                     -- Fire Weather Index
    
    -- Fuente de datos
    source VARCHAR(50) DEFAULT 'open_meteo',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para weather_data
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_data(observation_time DESC);
CREATE INDEX IF NOT EXISTS idx_weather_hotspot ON weather_data(hotspot_id);
CREATE INDEX IF NOT EXISTS idx_weather_fwi ON weather_data(fwi DESC);

-- =============================================================================
-- TABLA: alerts
-- Alertas enviadas a usuarios
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    
    -- Tipo de alerta
    alert_type VARCHAR(50) NOT NULL,          -- new_fire, fire_update, fire_contained, high_risk_area
    severity VARCHAR(20) NOT NULL,            -- low, medium, high, critical
    
    -- Información del evento
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Referencia al foco (puede ser null para alertas de riesgo)
    hotspot_id BIGINT,
    
    -- Área afectada
    affected_area GEOMETRY(POLYGON, 4326),
    center_point GEOMETRY(POINT, 4326),
    
    -- Destinatario
    user_id INTEGER REFERENCES users(id),
    
    -- Estado de la alerta
    status VARCHAR(50) DEFAULT 'pending',     -- pending, sent, delivered, read, failed
    
    -- Canales de envío
    sent_by_email BOOLEAN DEFAULT FALSE,
    sent_by_telegram BOOLEAN DEFAULT FALSE,
    sent_by_push BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_hotspot ON alerts(hotspot_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_area ON alerts USING GIST(affected_area);

-- =============================================================================
-- TABLA: fire_risk_zones
-- Zonas de riesgo calculadas (capas de FWI)
-- =============================================================================
CREATE TABLE IF NOT EXISTS fire_risk_zones (
    id SERIAL PRIMARY KEY,
    
    -- Geometría de la zona
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    
    -- Nivel de riesgo
    risk_level VARCHAR(20) NOT NULL,          -- very_low, low, moderate, high, very_high, extreme
    fwi_value DOUBLE PRECISION,
    
    -- Período de validez
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    
    -- Metadata
    calculation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para fire_risk_zones
CREATE INDEX IF NOT EXISTS idx_risk_zones_geom ON fire_risk_zones USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_risk_zones_level ON fire_risk_zones(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_zones_valid ON fire_risk_zones(valid_from, valid_to);

-- =============================================================================
-- FUNCIONES Y TRIGGERS
-- =============================================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para alerts
CREATE TRIGGER update_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- DATOS INICIALES
-- =============================================================================

-- Usuario administrador por defecto (password: admin123 - CAMBIAR EN PRODUCCIÓN)
INSERT INTO users (email, username, hashed_password, full_name, role, is_active, is_verified)
VALUES (
    'admin@firewatch.local',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VLOKxIvBJsxHGy',  -- bcrypt hash of 'admin123'
    'Administrador del Sistema',
    'admin',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✓ Esquema de base de datos creado exitosamente';
    RAISE NOTICE '✓ Tablas particionadas configuradas para 2024-2026';
    RAISE NOTICE '✓ Usuario administrador creado (admin@firewatch.local / admin123)';
END $$;
