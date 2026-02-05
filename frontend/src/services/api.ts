import axios from 'axios'

// Cliente Axios configurado
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para logging en desarrollo
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.config.url}`, response.data)
    }
    return response
  },
  (error) => {
    console.error('❌ API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// =============================================================================
// Hotspots API
// =============================================================================

export interface HotspotsQueryParams {
  startDate?: string
  endDate?: string
  minLat?: number
  maxLat?: number
  minLon?: number
  maxLon?: number
  satellite?: string
  limit?: number
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSON.Feature[]
  metadata?: {
    total: number
    start_date: string
    end_date: string
  }
}

/**
 * Obtiene focos de calor en formato GeoJSON.
 */
export async function fetchHotspotsGeoJSON(
  params: HotspotsQueryParams = {}
): Promise<GeoJSONFeatureCollection> {
  try {
    const response = await api.get<GeoJSONFeatureCollection>('/hotspots/geojson', {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
        min_lat: params.minLat,
        max_lat: params.maxLat,
        min_lon: params.minLon,
        max_lon: params.maxLon,
        limit: params.limit || 5000,
      },
    })
    return response.data
  } catch (error) {
    // En desarrollo, retornar datos mock si el backend no está disponible
    if (import.meta.env.DEV) {
      console.warn('⚠️ Backend no disponible, usando datos de ejemplo')
      return getMockHotspots()
    }
    throw error
  }
}

/**
 * Datos mock para desarrollo sin backend.
 */
function getMockHotspots(): GeoJSONFeatureCollection {
  // Generar puntos aleatorios en Argentina para demo
  const features: GeoJSON.Feature[] = []
  
  // Zonas típicas de incendios en Argentina
  const zones = [
    { name: 'Delta del Paraná', lat: -33.5, lon: -59.5, count: 15 },
    { name: 'Córdoba', lat: -31.4, lon: -64.2, count: 10 },
    { name: 'Chaco', lat: -26.0, lon: -60.5, count: 8 },
    { name: 'Patagonia', lat: -42.0, lon: -71.0, count: 5 },
  ]

  zones.forEach((zone) => {
    for (let i = 0; i < zone.count; i++) {
      const lat = zone.lat + (Math.random() - 0.5) * 2
      const lon = zone.lon + (Math.random() - 0.5) * 2
      const frp = Math.random() * 150

      features.push({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [lon, lat],
        },
        properties: {
          id: features.length + 1,
          satellite: ['VIIRS-SNPP', 'VIIRS-NOAA20', 'MODIS-AQUA'][Math.floor(Math.random() * 3)],
          acq_date: new Date().toISOString().split('T')[0],
          acq_time: `${Math.floor(Math.random() * 24).toString().padStart(2, '0')}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`,
          brightness: 300 + Math.random() * 100,
          frp: Math.round(frp * 10) / 10,
          confidence: ['low', 'nominal', 'high'][Math.floor(Math.random() * 3)],
          status: 'active',
        },
      })
    }
  })

  return {
    type: 'FeatureCollection',
    features,
    metadata: {
      total: features.length,
      start_date: new Date(Date.now() - 86400000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
  }
}

// =============================================================================
// Health API
// =============================================================================

export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

export default api
