# 🔥 Sistema de Gestión Geoespacial de Incendios Forestales

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://postgresql.org)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4+-00FF00.svg)](https://postgis.net)

> Plataforma de análisis y gestión geoespacial de incendios forestales para Argentina y Latinoamérica.

## 📋 Descripción

Este sistema proporciona herramientas para la **prevención**, **detección** y **recuperación** de incendios forestales, integrando:

- 🛰️ **Datos Satelitales**: NASA FIRMS (VIIRS, MODIS), GOES-16/17
- 🌡️ **Datos Meteorológicos**: Open-Meteo API, SMN Argentina
- 📊 **Índices de Riesgo**: Fire Weather Index (FWI) - Sistema CFFDRS
- 🗺️ **Visualización Geoespacial**: MapLibre GL JS con renderizado WebGL
- 📱 **Alertas en Tiempo Real**: WebSockets, Telegram, Push Notifications

## 🏗️ Arquitectura

```
├── backend/          # API FastAPI (Python 3.12+)
│   ├── app/
│   │   ├── api/      # Endpoints REST/WebSocket
│   │   ├── core/     # Configuración y seguridad
│   │   ├── db/       # Modelos y conexión a BD
│   │   ├── services/ # Lógica de negocio
│   │   └── tasks/    # Trabajos programados (Celery/Airflow)
│   └── tests/
├── frontend/         # React 18+ con MapLibre
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   └── public/
├── docker/           # Configuraciones Docker adicionales
├── scripts/          # Scripts de utilidad
└── docs/             # Documentación técnica
```

## 🚀 Inicio Rápido

### Prerrequisitos

- [Docker](https://www.docker.com/get-started) y Docker Compose
- [Git](https://git-scm.com/)
- (Opcional para desarrollo local) Python 3.12+, Node.js 20+

### Instalación

1. **Clonar el repositorio**:

   ```bash
   git clone https://github.com/MatiasRocha92/Sistemas-de-Gestion-Geoespacial-de-Incendios-Forestales.git
   cd Sistemas-de-Gestion-Geoespacial-de-Incendios-Forestales
   ```

2. **Configurar variables de entorno**:

   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales (NASA FIRMS API Key, etc.)
   ```

3. **Iniciar con Docker Compose**:

   ```bash
   docker-compose up -d
   ```

4. **Acceder a los servicios**:
   - 🌐 **Frontend**: http://localhost:3000
   - 🔧 **Backend API**: http://localhost:8000
   - 📚 **API Docs**: http://localhost:8000/docs
   - 🗄️ **PostgreSQL**: localhost:5432
   - 📮 **Redis**: localhost:6379

## 📦 Stack Tecnológico

| Capa                | Tecnología                  | Justificación                                           |
| ------------------- | --------------------------- | ------------------------------------------------------- |
| **Backend**         | Python 3.12+ / FastAPI      | Ecosistema científico (cffdrs, rasterio) + Async nativo |
| **Base de Datos**   | PostgreSQL 16 + PostGIS 3.4 | Consultas espaciales complejas                          |
| **Caché/Real-time** | Redis Stack                 | Geofencing sub-milisegundo, Pub/Sub                     |
| **Frontend**        | React 18 + TypeScript       | Ecosistema de componentes maduro                        |
| **Mapas**           | MapLibre GL JS              | Renderizado GPU, Open Source, 3D                        |
| **Tiles**           | PMTiles                     | Arquitectura Serverless, bajo costo                     |

## 🔥 Características Principales

### Fase 1 - MVP

- [x] Ingesta de datos NASA FIRMS
- [x] Visualización de focos de calor
- [x] Alertas por Telegram

### Fase 2 - Ciencia e Inteligencia

- [ ] Cálculo de índices FWI (CFFDRS)
- [ ] Mapas de riesgo predictivos
- [ ] Integración GOES-16 para alertas rápidas

### Fase 3 - Escala

- [ ] Modo offline para brigadistas
- [ ] Análisis de severidad post-incendio (Sentinel-2)
- [ ] Integración CONAE/SMN

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor, lee [CONTRIBUTING.md](docs/CONTRIBUTING.md) para más detalles.

---

**Desarrollado con ❤️ para la protección de los bosques argentinos y latinoamericanos.**
