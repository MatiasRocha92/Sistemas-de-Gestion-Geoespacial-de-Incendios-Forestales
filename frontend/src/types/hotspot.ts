/**
 * Tipos para Hotspots (Focos de Calor)
 */

export interface Hotspot {
  id: number
  latitude: number
  longitude: number
  satellite: string
  instrument?: string
  acq_date: string
  acq_time?: string
  acquired_at?: string
  brightness?: number
  bright_t31?: number
  bright_ti4?: number
  bright_ti5?: number
  frp?: number
  confidence?: 'low' | 'nominal' | 'high'
  confidence_pct?: number
  type?: number
  daynight?: 'D' | 'N'
  scan?: number
  track?: number
  version?: string
  source_system?: string
  status?: 'active' | 'contained' | 'extinguished' | 'false_alarm'
  created_at?: string
}

export interface HotspotListResponse {
  items: Hotspot[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface HotspotStats {
  period_days: number
  total_hotspots: number
  by_satellite: Record<string, number>
  by_day: Record<string, number>
}
