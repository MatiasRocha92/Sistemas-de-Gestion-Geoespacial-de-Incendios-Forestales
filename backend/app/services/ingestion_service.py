# =============================================================================
# Servicio de Ingesta de Datos Satelitales
# =============================================================================
"""
Servicio para ingestar datos de focos de calor desde NASA FIRMS
y guardarlos en la base de datos PostgreSQL/PostGIS.

Este servicio:
1. Consulta la API de FIRMS para obtener nuevos focos de calor
2. Parsea y normaliza los datos
3. Detecta duplicados basándose en (lat, lon, acq_date, acq_time, satellite)
4. Inserta nuevos registros en la base de datos
5. Genera geometrías PostGIS para consultas espaciales
"""

from datetime import datetime, date, time as dt_time, timezone
from typing import List, Optional, Dict, Tuple

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from loguru import logger

from app.db.models import Hotspot
from app.services.firms_client import FIRMSClient
from app.schemas.hotspot import FIRMSDataRow, FIRMSIngestionResult, BulkIngestionResult
from app.core.config import settings


class HotspotIngestionService:
    """
    Servicio para ingestar y persistir datos de focos de calor.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.
        
        Args:
            db_session: Sesión async de SQLAlchemy
        """
        self.db = db_session
    
    def _parse_acq_time(self, time_str: str) -> Optional[dt_time]:
        """
        Parsea el tiempo de adquisición del formato HHMM a time.
        
        Args:
            time_str: Tiempo en formato "HHMM" (ej: "0342", "1456")
            
        Returns:
            Objeto time o None si no se puede parsear
        """
        try:
            if not time_str or len(time_str) < 4:
                return None
            
            # Pad con ceros a la izquierda si es necesario
            time_str = time_str.zfill(4)
            
            hours = int(time_str[:2])
            minutes = int(time_str[2:4])
            
            # Validar rangos
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return dt_time(hours, minutes)
            return None
            
        except (ValueError, TypeError):
            return None
    
    def _parse_acq_date(self, date_str: str) -> Optional[date]:
        """
        Parsea la fecha de adquisición.
        
        Args:
            date_str: Fecha en formato "YYYY-MM-DD"
            
        Returns:
            Objeto date o None si no se puede parsear
        """
        try:
            if not date_str:
                return None
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    
    def _create_external_id(self, data: FIRMSDataRow) -> str:
        """
        Crea un ID externo único para detectar duplicados.
        Basado en: latitud, longitud, fecha, hora, satélite
        
        Args:
            data: Datos del foco de calor
            
        Returns:
            String con el ID único
        """
        lat_str = f"{data.latitude:.5f}"
        lon_str = f"{data.longitude:.5f}"
        return f"{lat_str}_{lon_str}_{data.acq_date}_{data.acq_time}_{data.satellite}"
    
    def _convert_to_hotspot(self, data: FIRMSDataRow) -> Dict:
        """
        Convierte un FIRMSDataRow a un diccionario para inserción.
        
        Args:
            data: Datos parseados de FIRMS
            
        Returns:
            Diccionario con valores para el modelo Hotspot
        """
        acq_date = self._parse_acq_date(data.acq_date)
        acq_time = self._parse_acq_time(data.acq_time)
        
        # Crear timestamp completo si tenemos fecha y hora
        acquired_at = None
        if acq_date and acq_time:
            acquired_at = datetime.combine(acq_date, acq_time, tzinfo=timezone.utc)
        elif acq_date:
            acquired_at = datetime.combine(acq_date, dt_time(0, 0), tzinfo=timezone.utc)
        
        # Determinar instrumento basado en satélite
        instrument = data.instrument
        if not instrument:
            if "VIIRS" in data.satellite.upper():
                instrument = "VIIRS"
            elif "MODIS" in data.satellite.upper():
                instrument = "MODIS"
            elif any(s in data.satellite.upper() for s in ["TERRA", "AQUA"]):
                instrument = "MODIS"
            elif any(s in data.satellite.upper() for s in ["SNPP", "NOAA20", "NOAA21"]):
                instrument = "VIIRS"
        
        # Normalizar confianza
        confidence = data.confidence
        confidence_pct = data.confidence_pct
        
        # Si tenemos confidence de VIIRS, mapear a porcentaje aproximado
        if confidence and not confidence_pct:
            confidence_map = {"low": 30, "nominal": 70, "high": 95}
            confidence_pct = confidence_map.get(confidence.lower())
        
        return {
            # Ubicación - PostGIS WKT Point
            "location": f"SRID=4326;POINT({data.longitude} {data.latitude})",
            "latitude": data.latitude,
            "longitude": data.longitude,
            
            # Satélite
            "satellite": data.satellite,
            "instrument": instrument,
            
            # Tiempo
            "acq_date": acq_date,
            "acq_time": acq_time,
            "acquired_at": acquired_at,
            
            # Métricas
            "brightness": data.brightness,
            "bright_t31": data.bright_t31,
            "bright_ti4": data.bright_ti4,
            "bright_ti5": data.bright_ti5,
            "frp": data.frp,
            
            # Confianza
            "confidence": confidence,
            "confidence_pct": confidence_pct,
            
            # Clasificación
            "type": data.type,
            "daynight": data.daynight,
            
            # Origen
            "source_system": "FIRMS",
            "external_id": self._create_external_id(data),
            
            # Metadatos
            "scan": data.scan,
            "track": data.track,
            "version": data.version,
            
            # Estado inicial
            "status": "active",
            
            # Timestamps
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    async def check_existing_ids(self, external_ids: List[str]) -> set:
        """
        Verifica qué external_ids ya existen en la base de datos.
        
        Args:
            external_ids: Lista de IDs externos a verificar
            
        Returns:
            Set de IDs que ya existen
        """
        if not external_ids:
            return set()
        
        query = select(Hotspot.external_id).where(
            Hotspot.external_id.in_(external_ids)
        )
        
        result = await self.db.execute(query)
        existing = {row[0] for row in result.fetchall()}
        
        return existing
    
    async def bulk_insert_hotspots(self, hotspots_data: List[Dict]) -> int:
        """
        Inserta múltiples hotspots en lote, ignorando duplicados.
        
        Args:
            hotspots_data: Lista de diccionarios con datos de hotspots
            
        Returns:
            Número de registros insertados
        """
        if not hotspots_data:
            return 0
        
        try:
            # Usar INSERT ... ON CONFLICT DO NOTHING para ignorar duplicados
            stmt = insert(Hotspot).values(hotspots_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=['external_id'])
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            # rowcount puede no ser preciso en todos los drivers
            return result.rowcount if result.rowcount else len(hotspots_data)
            
        except Exception as e:
            logger.error(f"❌ Error en bulk insert: {e}")
            await self.db.rollback()
            raise
    
    async def ingest_from_firms(
        self,
        country_code: str = "ARG",
        sensor: str = "VIIRS_SNPP_NRT",
        days: int = 1
    ) -> FIRMSIngestionResult:
        """
        Ejecuta el proceso completo de ingesta desde FIRMS.
        
        Args:
            country_code: Código ISO del país
            sensor: Sensor a consultar
            days: Días de datos
            
        Returns:
            Resultado de la ingesta
        """
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"🔄 Iniciando ingesta: {sensor} - {country_code} - {days} días")
        
        try:
            # 1. Obtener datos de FIRMS
            async with FIRMSClient() as client:
                raw_data = await client.fetch_country_data(country_code, sensor, days)
            
            records_fetched = len(raw_data)
            
            if not raw_data:
                logger.info("ℹ️ No se obtuvieron datos de FIRMS")
                return FIRMSIngestionResult(
                    success=True,
                    sensor=sensor,
                    country=country_code,
                    days=days,
                    records_fetched=0,
                    records_inserted=0,
                    records_duplicates=0,
                    timestamp=start_time
                )
            
            # 2. Convertir a formato de base de datos
            hotspots_data = []
            external_ids = []
            
            for row in raw_data:
                converted = self._convert_to_hotspot(row)
                if converted["acq_date"] is not None:  # Solo si tenemos fecha válida
                    hotspots_data.append(converted)
                    external_ids.append(converted["external_id"])
            
            # 3. Detectar duplicados existentes
            existing_ids = await self.check_existing_ids(external_ids)
            records_duplicates = len(existing_ids)
            
            # 4. Filtrar nuevos registros
            new_hotspots = [
                h for h in hotspots_data 
                if h["external_id"] not in existing_ids
            ]
            
            # 5. Insertar nuevos registros
            records_inserted = 0
            if new_hotspots:
                records_inserted = await self.bulk_insert_hotspots(new_hotspots)
            
            logger.info(
                f"✅ Ingesta completada: {records_fetched} obtenidos, "
                f"{records_inserted} insertados, {records_duplicates} duplicados"
            )
            
            return FIRMSIngestionResult(
                success=True,
                sensor=sensor,
                country=country_code,
                days=days,
                records_fetched=records_fetched,
                records_inserted=records_inserted,
                records_duplicates=records_duplicates,
                timestamp=start_time
            )
            
        except Exception as e:
            logger.error(f"❌ Error en ingesta: {e}")
            return FIRMSIngestionResult(
                success=False,
                sensor=sensor,
                country=country_code,
                days=days,
                records_fetched=0,
                records_inserted=0,
                records_duplicates=0,
                timestamp=start_time,
                error_message=str(e)
            )
    
    async def ingest_all_sensors(
        self,
        country_code: str = "ARG",
        days: int = 1,
        sensors: Optional[List[str]] = None
    ) -> BulkIngestionResult:
        """
        Ingesta datos de múltiples sensores.
        
        Args:
            country_code: Código ISO del país
            days: Días de datos
            sensors: Lista de sensores (default: principales NRT)
            
        Returns:
            Resultado consolidado de todas las ingestas
        """
        start_time = datetime.now(timezone.utc)
        
        if sensors is None:
            sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]
        
        results = []
        total_fetched = 0
        total_inserted = 0
        total_duplicates = 0
        
        for sensor in sensors:
            result = await self.ingest_from_firms(country_code, sensor, days)
            results.append(result)
            total_fetched += result.records_fetched
            total_inserted += result.records_inserted
            total_duplicates += result.records_duplicates
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"📊 Ingesta total completada: {total_fetched} obtenidos, "
            f"{total_inserted} insertados, {total_duplicates} duplicados "
            f"({duration:.2f}s)"
        )
        
        return BulkIngestionResult(
            total_fetched=total_fetched,
            total_inserted=total_inserted,
            total_duplicates=total_duplicates,
            results=results,
            started_at=start_time,
            completed_at=end_time,
            duration_seconds=duration
        )


async def run_ingestion(
    db: AsyncSession,
    country_code: str = "ARG",
    days: int = 1
) -> BulkIngestionResult:
    """
    Función utilitaria para ejecutar una ingesta completa.
    
    Args:
        db: Sesión de base de datos
        country_code: Código del país
        days: Días de datos
        
    Returns:
        Resultado de la ingesta
    """
    service = HotspotIngestionService(db)
    return await service.ingest_all_sensors(country_code, days)
