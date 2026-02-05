import { useQuery } from '@tanstack/react-query'
import { fetchHotspotsGeoJSON } from '../services/api'

interface UseHotspotsOptions {
  startDate?: string
  endDate?: string
  minLat?: number
  maxLat?: number
  minLon?: number
  maxLon?: number
}

/**
 * Hook para obtener focos de calor en formato GeoJSON.
 * Ideal para integración directa con MapLibre.
 */
export function useHotspots(options: UseHotspotsOptions = {}) {
  return useQuery({
    queryKey: ['hotspots', options],
    queryFn: () => fetchHotspotsGeoJSON(options),
    staleTime: 1000 * 60 * 5, // 5 minutos
    refetchInterval: 1000 * 60 * 10, // Refrescar cada 10 minutos
    refetchOnWindowFocus: true,
  })
}

/**
 * Hook para obtener estadísticas de focos de calor.
 */
export function useHotspotsStats(days: number = 7) {
  return useQuery({
    queryKey: ['hotspots-stats', days],
    queryFn: async () => {
      const response = await fetch(`/api/v1/hotspots/stats/summary?days=${days}`)
      if (!response.ok) throw new Error('Error fetching stats')
      return response.json()
    },
    staleTime: 1000 * 60 * 15, // 15 minutos
  })
}
