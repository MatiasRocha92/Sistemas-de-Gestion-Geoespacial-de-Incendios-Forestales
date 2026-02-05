import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { useHotspots } from "../hooks/useHotspots";
import "./MapPage.css";

/**
 * Página principal del mapa con focos de calor.
 */
function MapPage() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const { data: hotspotsData, isLoading, error } = useHotspots();

  // Inicializar mapa
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution:
              '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          },
        },
        layers: [
          {
            id: "osm-tiles",
            type: "raster",
            source: "osm",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [-64.0, -34.0], // Centro de Argentina
      zoom: 4,
      minZoom: 3,
      maxZoom: 18,
    });

    // Controles
    map.current.addControl(new maplibregl.NavigationControl(), "top-right");
    map.current.addControl(
      new maplibregl.ScaleControl({ maxWidth: 200 }),
      "bottom-left",
    );
    map.current.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      "top-right",
    );

    map.current.on("load", () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  // Agregar capa de hotspots cuando hay datos
  useEffect(() => {
    if (!map.current || !mapLoaded || !hotspotsData?.features) return;

    const sourceId = "hotspots-source";
    const layerId = "hotspots-layer";

    // Actualizar o crear source
    const source = map.current.getSource(sourceId) as maplibregl.GeoJSONSource;

    if (source) {
      source.setData(hotspotsData);
    } else {
      map.current.addSource(sourceId, {
        type: "geojson",
        data: hotspotsData,
      });

      // Capa de puntos de calor con gradiente de color según FRP
      map.current.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "frp"],
            0,
            4,
            50,
            8,
            100,
            12,
            500,
            18,
          ],
          "circle-color": [
            "interpolate",
            ["linear"],
            ["get", "frp"],
            0,
            "#fbbf24", // Amarillo - bajo
            20,
            "#f97316", // Naranja - moderado
            50,
            "#ef4444", // Rojo - alto
            100,
            "#dc2626", // Rojo oscuro - muy alto
            200,
            "#7c2d12", // Marrón - extremo
          ],
          "circle-opacity": 0.8,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#fff",
          "circle-stroke-opacity": 0.5,
        },
      });

      // Popup al hacer click
      map.current.on("click", layerId, (e) => {
        if (!e.features?.[0]) return;

        const props = e.features[0].properties as Record<string, unknown>;
        const coordinates = (
          e.features[0].geometry as GeoJSON.Point
        ).coordinates.slice() as [number, number];

        const popupContent = `
          <div class="hotspot-popup">
            <h3>🔥 Foco de Calor</h3>
            <div class="popup-row">
              <span class="label">Satélite:</span>
              <span class="value">${props.satellite || "N/A"}</span>
            </div>
            <div class="popup-row">
              <span class="label">Fecha:</span>
              <span class="value">${props.acq_date || "N/A"}</span>
            </div>
            <div class="popup-row">
              <span class="label">Hora:</span>
              <span class="value">${props.acq_time || "N/A"}</span>
            </div>
            <div class="popup-row">
              <span class="label">FRP (MW):</span>
              <span class="value">${props.frp || "N/A"}</span>
            </div>
            <div class="popup-row">
              <span class="label">Confianza:</span>
              <span class="value confidence-${props.confidence}">${props.confidence || "N/A"}</span>
            </div>
          </div>
        `;

        new maplibregl.Popup()
          .setLngLat(coordinates)
          .setHTML(popupContent)
          .addTo(map.current!);
      });

      // Cambiar cursor al hover
      map.current.on("mouseenter", layerId, () => {
        if (map.current) map.current.getCanvas().style.cursor = "pointer";
      });

      map.current.on("mouseleave", layerId, () => {
        if (map.current) map.current.getCanvas().style.cursor = "";
      });
    }
  }, [mapLoaded, hotspotsData]);

  return (
    <div className="map-page">
      {/* Panel lateral */}
      <aside className="map-sidebar">
        <div className="sidebar-header">
          <h2>Focos de Calor</h2>
          <span className="badge">
            {isLoading ? "..." : hotspotsData?.features?.length || 0}
          </span>
        </div>

        <div className="sidebar-content">
          {isLoading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Cargando datos satelitales...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <span className="error-icon">⚠️</span>
              <p>Error al cargar datos</p>
              <small>{(error as Error).message}</small>
            </div>
          )}

          {!isLoading && !error && (
            <>
              <div className="legend">
                <h4>Intensidad (FRP)</h4>
                <div className="legend-items">
                  <div className="legend-item">
                    <span
                      className="legend-color"
                      style={{ background: "#fbbf24" }}
                    ></span>
                    <span>Bajo (&lt;20 MW)</span>
                  </div>
                  <div className="legend-item">
                    <span
                      className="legend-color"
                      style={{ background: "#f97316" }}
                    ></span>
                    <span>Moderado (20-50 MW)</span>
                  </div>
                  <div className="legend-item">
                    <span
                      className="legend-color"
                      style={{ background: "#ef4444" }}
                    ></span>
                    <span>Alto (50-100 MW)</span>
                  </div>
                  <div className="legend-item">
                    <span
                      className="legend-color"
                      style={{ background: "#dc2626" }}
                    ></span>
                    <span>Muy Alto (&gt;100 MW)</span>
                  </div>
                </div>
              </div>

              <div className="data-info">
                <p>
                  <strong>Fuente:</strong> NASA FIRMS
                </p>
                <p>
                  <strong>Última actualización:</strong>{" "}
                  {new Date().toLocaleString("es-AR")}
                </p>
              </div>
            </>
          )}
        </div>
      </aside>

      {/* Contenedor del mapa */}
      <div className="map-container" ref={mapContainer} />
    </div>
  );
}

export default MapPage;
