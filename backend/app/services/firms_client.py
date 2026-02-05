# =============================================================================
# Cliente HTTP para NASA FIRMS API
# =============================================================================
"""
Cliente para consumir la API de NASA FIRMS (Fire Information for Resource 
Management System).

Documentación API: https://firms.modaps.eosdis.nasa.gov/api/data_availability/

Sensores disponibles:
- VIIRS_SNPP_NRT: VIIRS en Suomi NPP (Near Real-Time)
- VIIRS_NOAA20_NRT: VIIRS en NOAA-20 (Near Real-Time)  
- VIIRS_NOAA21_NRT: VIIRS en NOAA-21 (Near Real-Time)
- MODIS_NRT: MODIS Combined Terra/Aqua (Near Real-Time)

Formatos: CSV, JSON, GeoJSON, KML
"""

import csv
import io
from datetime import datetime, date, time as dt_time
from typing import List, Optional, Dict, Any, Literal

import httpx
from loguru import logger

from app.core.config import settings
from app.schemas.hotspot import FIRMSDataRow, FIRMSIngestionResult


# Mapeo de sensores a nombres en la API
SENSOR_MAP = {
    "VIIRS_SNPP_NRT": "VIIRS_SNPP_NRT",
    "VIIRS_NOAA20_NRT": "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT": "VIIRS_NOAA21_NRT",
    "MODIS_NRT": "MODIS_NRT",
    # Aliases para facilidad de uso
    "VIIRS": "VIIRS_SNPP_NRT",
    "MODIS": "MODIS_NRT",
}

# Columnas esperadas por sensor
VIIRS_COLUMNS = [
    "latitude", "longitude", "bright_ti4", "scan", "track", 
    "acq_date", "acq_time", "satellite", "instrument", "confidence",
    "version", "bright_ti5", "frp", "daynight"
]

MODIS_COLUMNS = [
    "latitude", "longitude", "brightness", "scan", "track",
    "acq_date", "acq_time", "satellite", "instrument", "confidence",
    "version", "bright_t31", "frp", "daynight", "type"
]


class FIRMSClient:
    """
    Cliente HTTP asíncrono para consumir la API de NASA FIRMS.
    
    Uso:
        async with FIRMSClient() as client:
            data = await client.fetch_country_data("ARG", sensor="VIIRS_SNPP_NRT", days=1)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0
    ):
        """
        Inicializa el cliente FIRMS.
        
        Args:
            api_key: Clave de API de NASA FIRMS (MAP_KEY)
            base_url: URL base de la API
            timeout: Timeout para requests HTTP en segundos
        """
        self.api_key = api_key or settings.NASA_FIRMS_API_KEY
        self.base_url = base_url or settings.NASA_FIRMS_BASE_URL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        if not self.api_key:
            logger.warning("⚠️ NASA FIRMS API Key no configurada. La ingesta no funcionará.")
    
    async def __aenter__(self) -> "FIRMSClient":
        """Context manager entry - abre el cliente HTTP."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            headers={
                "User-Agent": "FireWatch-System/1.0",
                "Accept": "text/csv, application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cierra el cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_sensor_name(self, sensor: str) -> str:
        """Obtiene el nombre correcto del sensor para la API."""
        return SENSOR_MAP.get(sensor.upper(), sensor)
    
    def _build_country_url(
        self,
        country_code: str,
        sensor: str,
        days: int,
        format: Literal["csv", "json", "geojson"] = "csv"
    ) -> str:
        """
        Construye la URL para consultar datos por país.
        
        Formato: /api/country/{format}/{MAP_KEY}/{sensor}/{country}/{days}
        
        Args:
            country_code: Código ISO 3166-1 alpha-3 del país (ej: ARG, BRA, CHL)
            sensor: Nombre del sensor
            days: Número de días (1-10)
            format: Formato de respuesta
            
        Returns:
            URL completa para la consulta
        """
        sensor_name = self._get_sensor_name(sensor)
        days = min(max(1, days), 10)  # Clamp entre 1 y 10
        
        return f"{self.base_url}/api/country/{format}/{self.api_key}/{sensor_name}/{country_code}/{days}"
    
    def _build_area_url(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        sensor: str,
        days: int,
        format: Literal["csv", "json", "geojson"] = "csv"
    ) -> str:
        """
        Construye la URL para consultar datos por área (bounding box).
        
        Formato: /api/area/{format}/{MAP_KEY}/{sensor}/{west},{south},{east},{north}/{days}
        """
        sensor_name = self._get_sensor_name(sensor)
        days = min(max(1, days), 10)
        
        # Formato: west,south,east,north (min_lon, min_lat, max_lon, max_lat)
        bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        
        return f"{self.base_url}/api/area/{format}/{self.api_key}/{sensor_name}/{bbox}/{days}"
    
    def _parse_csv_row(self, row: Dict[str, str], sensor: str) -> Optional[FIRMSDataRow]:
        """
        Parsea una fila CSV a un objeto FIRMSDataRow.
        
        Args:
            row: Diccionario con los datos de la fila
            sensor: Nombre del sensor para determinar campos
            
        Returns:
            FIRMSDataRow o None si hay error
        """
        try:
            # Campos comunes
            data = {
                "latitude": float(row.get("latitude", 0)),
                "longitude": float(row.get("longitude", 0)),
                "acq_date": row.get("acq_date", ""),
                "acq_time": row.get("acq_time", "0000"),
                "satellite": row.get("satellite", sensor.split("_")[0]),
                "instrument": row.get("instrument"),
                "version": row.get("version"),
                "daynight": row.get("daynight"),
            }
            
            # FRP (Fire Radiative Power)
            if row.get("frp"):
                try:
                    data["frp"] = float(row["frp"])
                except ValueError:
                    pass
            
            # Scan y Track
            for field in ["scan", "track"]:
                if row.get(field):
                    try:
                        data[field] = float(row[field])
                    except ValueError:
                        pass
            
            # Campos específicos VIIRS
            if "VIIRS" in sensor.upper():
                for field in ["bright_ti4", "bright_ti5"]:
                    if row.get(field):
                        try:
                            data[field] = float(row[field])
                        except ValueError:
                            pass
                data["confidence"] = row.get("confidence")  # low, nominal, high
            
            # Campos específicos MODIS
            if "MODIS" in sensor.upper():
                for field in ["brightness", "bright_t31"]:
                    if row.get(field):
                        try:
                            data[field] = float(row[field])
                        except ValueError:
                            pass
                # MODIS usa confidence numérico
                if row.get("confidence"):
                    try:
                        data["confidence_pct"] = int(row["confidence"])
                    except ValueError:
                        pass
                if row.get("type"):
                    try:
                        data["type"] = int(row["type"])
                    except ValueError:
                        pass
            
            return FIRMSDataRow(**data)
            
        except Exception as e:
            logger.warning(f"Error parseando fila CSV: {e} - Row: {row}")
            return None
    
    async def fetch_country_data(
        self,
        country_code: str = "ARG",
        sensor: str = "VIIRS_SNPP_NRT",
        days: int = 1
    ) -> List[FIRMSDataRow]:
        """
        Obtiene datos de focos de calor para un país.
        
        Args:
            country_code: Código ISO del país (default: ARG para Argentina)
            sensor: Sensor a consultar
            days: Número de días de datos (1-10)
            
        Returns:
            Lista de FIRMSDataRow con los datos parseados
        """
        if not self.api_key:
            logger.error("❌ NASA FIRMS API Key no configurada")
            return []
        
        if not self._client:
            raise RuntimeError("Cliente no inicializado. Usar 'async with FIRMSClient() as client:'")
        
        url = self._build_country_url(country_code, sensor, days)
        logger.info(f"🛰️ Consultando FIRMS: {sensor} - {country_code} - {days} días")
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            
            # Parsear CSV
            content = response.text
            reader = csv.DictReader(io.StringIO(content))
            
            results = []
            for row in reader:
                parsed = self._parse_csv_row(row, sensor)
                if parsed:
                    results.append(parsed)
            
            logger.info(f"✓ Obtenidos {len(results)} registros de {sensor}")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"❌ Error de conexión: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return []
    
    async def fetch_area_data(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        sensor: str = "VIIRS_SNPP_NRT",
        days: int = 1
    ) -> List[FIRMSDataRow]:
        """
        Obtiene datos de focos de calor para un área rectangular (bounding box).
        
        Args:
            min_lat: Latitud mínima (sur)
            max_lat: Latitud máxima (norte)
            min_lon: Longitud mínima (oeste)
            max_lon: Longitud máxima (este)
            sensor: Sensor a consultar
            days: Número de días de datos (1-10)
            
        Returns:
            Lista de FIRMSDataRow con los datos parseados
        """
        if not self.api_key:
            logger.error("❌ NASA FIRMS API Key no configurada")
            return []
        
        if not self._client:
            raise RuntimeError("Cliente no inicializado. Usar 'async with FIRMSClient() as client:'")
        
        url = self._build_area_url(min_lat, max_lat, min_lon, max_lon, sensor, days)
        logger.info(f"🛰️ Consultando FIRMS por área: [{min_lon},{min_lat}] - [{max_lon},{max_lat}]")
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            
            content = response.text
            reader = csv.DictReader(io.StringIO(content))
            
            results = []
            for row in reader:
                parsed = self._parse_csv_row(row, sensor)
                if parsed:
                    results.append(parsed)
            
            logger.info(f"✓ Obtenidos {len(results)} registros por área")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"❌ Error de conexión: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return []
    
    async def fetch_all_sensors(
        self,
        country_code: str = "ARG",
        days: int = 1,
        sensors: Optional[List[str]] = None
    ) -> Dict[str, List[FIRMSDataRow]]:
        """
        Obtiene datos de múltiples sensores para un país.
        
        Args:
            country_code: Código ISO del país
            days: Días de datos
            sensors: Lista de sensores (default: todos NRT)
            
        Returns:
            Diccionario sensor -> lista de datos
        """
        if sensors is None:
            sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]
        
        results = {}
        for sensor in sensors:
            data = await self.fetch_country_data(country_code, sensor, days)
            results[sensor] = data
        
        total = sum(len(d) for d in results.values())
        logger.info(f"📊 Total de registros obtenidos de todos los sensores: {total}")
        
        return results


# Cliente singleton para reutilizar
async def get_firms_client() -> FIRMSClient:
    """Factory function para obtener un cliente FIRMS."""
    return FIRMSClient()
