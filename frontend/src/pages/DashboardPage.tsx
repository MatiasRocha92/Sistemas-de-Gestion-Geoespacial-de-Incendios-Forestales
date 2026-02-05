import "./DashboardPage.css";

/**
 * Página de Dashboard con estadísticas.
 */
function DashboardPage() {
  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Resumen de actividad de incendios forestales</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🔥</div>
          <div className="stat-content">
            <span className="stat-value">--</span>
            <span className="stat-label">Focos Activos</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <span className="stat-value">--</span>
            <span className="stat-label">Alertas Hoy</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🌡️</div>
          <div className="stat-content">
            <span className="stat-value">--</span>
            <span className="stat-label">FWI Promedio</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📍</div>
          <div className="stat-content">
            <span className="stat-value">--</span>
            <span className="stat-label">Provincias Afectadas</span>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="card">
          <h3>Actividad por Día (Últimos 7 días)</h3>
          <div className="chart-placeholder">
            <p>📊 Gráfico de líneas - Próximamente</p>
          </div>
        </div>

        <div className="card">
          <h3>Distribución por Satélite</h3>
          <div className="chart-placeholder">
            <p>🥧 Gráfico circular - Próximamente</p>
          </div>
        </div>
      </div>

      <div className="dashboard-notice">
        <p>
          ℹ️ Dashboard en desarrollo. Los datos se actualizarán automáticamente
          cuando se configure la conexión con el backend.
        </p>
      </div>
    </div>
  );
}

export default DashboardPage;
