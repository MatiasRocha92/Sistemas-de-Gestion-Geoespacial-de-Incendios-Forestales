# =============================================================================
# Frontend React - Sistema de Gestión de Incendios Forestales
# Node 20 + Vite + TypeScript + MapLibre
# =============================================================================

# =============================================================================
# Stage: Base
# =============================================================================
FROM node:20-alpine as base

WORKDIR /app

# Instalar dependencias del sistema
RUN apk add --no-cache libc6-compat

# =============================================================================
# Stage: Dependencies
# =============================================================================
FROM base as dependencies

# Copiar archivos de configuración
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# =============================================================================
# Stage: Development
# =============================================================================
FROM dependencies as development

# Copiar código fuente
COPY . .

# Puerto de desarrollo
EXPOSE 5173

# Comando para desarrollo con hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# Stage: Builder
# =============================================================================
FROM dependencies as builder

# Copiar código fuente
COPY . .

# Build de producción
RUN npm run build

# =============================================================================
# Stage: Production (nginx)
# =============================================================================
FROM nginx:alpine as production

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos de build
COPY --from=builder /app/dist /usr/share/nginx/html

# Puerto de producción
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
