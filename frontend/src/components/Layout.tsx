import { Outlet, NavLink } from "react-router-dom";
import "./Layout.css";

/**
 * Layout principal de la aplicación.
 * Incluye header con navegación y área de contenido principal.
 */
function Layout() {
  return (
    <div className="layout">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <span className="header-logo">🔥</span>
          <h1 className="header-title">FireWatch</h1>
          <span className="header-subtitle">
            Sistema de Gestión de Incendios
          </span>
        </div>

        <nav className="header-nav">
          <NavLink
            to="/"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="nav-icon">🗺️</span>
            Mapa
          </NavLink>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </NavLink>
        </nav>

        <div className="header-actions">
          <button className="btn-icon" title="Notificaciones">
            🔔
          </button>
          <button className="btn-icon" title="Configuración">
            ⚙️
          </button>
        </div>
      </header>

      {/* Contenido Principal */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
