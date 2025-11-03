# Documentación API - Google Maps Reviews Scraper

## Índice

- [Introducción](#introducción)
- [Características](#características)
- [Arquitectura](#arquitectura)
- [Configuración Inicial](#configuración-inicial)
- [URL Base](#url-base)
- [Autenticación](#autenticación)
- [Módulos de la API](#módulos-de-la-api)
- [Formatos de Respuesta](#formatos-de-respuesta)
- [Códigos de Estado HTTP](#códigos-de-estado-http)
- [Documentación Interactiva](#documentación-interactiva)

---

## Introducción

**Google Maps Reviews Scraper API** es una API REST completa diseñada para extraer, almacenar, monitorear y gestionar reseñas de Google Maps de forma automatizada. Permite a los usuarios integrar fácilmente la extracción de reseñas en sus propios sistemas y recibir notificaciones en tiempo real a través de webhooks.

### ¿Para qué sirve?

- Extraer reseñas de cualquier lugar de Google Maps
- Monitorear automáticamente nuevas reseñas
- Recibir notificaciones instantáneas vía webhook
- Consultar y filtrar reseñas almacenadas
- Gestionar múltiples lugares y sucursales
- Integrar reseñas en dashboards y sistemas CRM

---

## Características

### ✨ Funcionalidades Principales

1. **Gestión de Lugares (CRUD completo)**
   - Registrar lugares para monitoreo
   - Actualizar configuración de monitoreo
   - Eliminar lugares
   - Consultar estadísticas por lugar

2. **Scraping de Reseñas**
   - Extracción manual bajo demanda
   - Procesamiento asíncrono (no bloquea)
   - Múltiples opciones de ordenamiento
   - Control de cantidad de reseñas a extraer

3. **Monitoreo Automático**
   - Revisión periódica programada
   - Detección de nuevas reseñas
   - Intervalos configurables por lugar
   - Sistema de scheduler integrado

4. **Sistema de Webhooks**
   - Notificaciones en tiempo real
   - Payload estructurado con datos completos
   - Reintentos automáticos
   - Prueba de webhooks

5. **Consulta Avanzada de Reseñas**
   - Filtros múltiples (rating, fecha, cliente, lugar)
   - Paginación eficiente
   - Ordenamiento personalizable
   - Búsqueda optimizada

6. **Procesamiento Asíncrono**
   - Cola de tareas con Redis Queue
   - Workers escalables
   - Monitoreo de estado de trabajos
   - Cancelación de tareas

---

## Arquitectura

### Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Framework API | FastAPI (Python) |
| Base de Datos | MongoDB |
| Cola de Tareas | Redis + RQ (Redis Queue) |
| Scraping | Playwright |
| Scheduler | APScheduler |
| Cliente HTTP | httpx |
| Contenedores | Docker + Docker Compose |

### Arquitectura de Servicios

```
┌─────────────────┐
│   Cliente HTTP  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              API FastAPI (Puerto 8000)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Places   │ │ Scraping │ │ Reviews  │            │
│  │ Endpoints│ │ Endpoints│ │ Endpoints│            │
│  └──────────┘ └──────────┘ └──────────┘            │
└───────┬──────────────────────┬──────────────────────┘
        │                      │
        ▼                      ▼
┌──────────────┐      ┌──────────────────┐
│   MongoDB    │      │  Redis Queue     │
│   (Datos)    │      │  (Tareas async)  │
└──────────────┘      └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Worker (RQ)     │
                      │  - Scraper       │
                      │  - Playwright    │
                      └──────────────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Google Maps     │
                      │  (Extracción)    │
                      └──────────────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Webhook URL     │
                      │  (Notificación)  │
                      └──────────────────┘
```

### Flujo de Datos

1. **Cliente → API**: Solicitud HTTP
2. **API → MongoDB**: Consulta/Almacenamiento
3. **API → Redis**: Encolar tarea de scraping
4. **Worker → Google Maps**: Extracción de reseñas
5. **Worker → MongoDB**: Guardar reseñas
6. **Worker → Webhook**: Notificación de nuevas reseñas

---

## Configuración Inicial

### Requisitos Previos

- Docker y Docker Compose (recomendado) **O**
- Python 3.10+
- MongoDB 4.4+
- Redis 6.0+

### Opción 1: Docker Compose (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd googlemaps-reviews-scraper-es

# 2. Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env si es necesario

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar que la API esté funcionando
curl http://localhost:8000/health
```

### Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Instalar navegador Playwright
playwright install chromium

# 3. Iniciar MongoDB
mongod --dbpath /ruta/a/datos

# 4. Iniciar Redis
redis-server

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env

# 6. Iniciar API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 7. En otra terminal, iniciar Worker
python worker.py
```

### Variables de Entorno Principales

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000

# MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB=googlemaps

# Redis
REDIS_URL=redis://localhost:6379/0

# Scraping
DEFAULT_REVIEWS_COUNT=100
HEADLESS_MODE=True

# Monitoreo
DEFAULT_CHECK_INTERVAL=60
ENABLE_MONITORING_ON_STARTUP=True

# Webhooks
WEBHOOK_TIMEOUT=10
WEBHOOK_MAX_RETRIES=3
```

---

## URL Base

### Entorno Local
```
http://localhost:8000
```

### Entorno Producción
```
https://tu-dominio.com
```

### Endpoints Principales

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Información de la API |
| `GET /health` | Health check |
| `GET /docs` | Documentación Swagger UI |
| `GET /redoc` | Documentación ReDoc |

---

## Autenticación

**Estado Actual**: La API **no requiere autenticación** en la versión actual.

> ⚠️ **Importante**: Para entornos de producción, se recomienda implementar autenticación mediante:
> - API Keys
> - JWT (JSON Web Tokens)
> - OAuth 2.0
>
> Contacta con el equipo de desarrollo para implementar autenticación antes de desplegar en producción.

---

## Módulos de la API

La API está organizada en 5 módulos principales:

### 1. 📍 Places (Lugares)
**Prefijo**: `/api/places`

Gestión completa de lugares para monitoreo.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/places/` | Registrar nuevo lugar |
| GET | `/api/places/` | Listar lugares con filtros |
| GET | `/api/places/{place_id}` | Obtener lugar específico |
| PUT | `/api/places/{place_id}` | Actualizar lugar |
| DELETE | `/api/places/{place_id}` | Eliminar lugar |
| GET | `/api/places/{place_id}/stats` | Estadísticas del lugar |

### 2. 🔄 Scraping
**Prefijo**: `/api/scraping`

Control de trabajos de scraping asíncronos.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/scraping/start` | Iniciar scraping |
| GET | `/api/scraping/status/{job_id}` | Estado del trabajo |
| GET | `/api/scraping/result/{job_id}` | Resultados del trabajo |
| DELETE | `/api/scraping/{job_id}` | Cancelar trabajo |
| GET | `/api/scraping/workers/status` | Estado de workers |

### 3. ⭐ Reviews (Reseñas)
**Prefijo**: `/api/reviews`

Consulta y gestión de reseñas almacenadas.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reviews/` | Listar reseñas con filtros |
| GET | `/api/reviews/{review_id}` | Obtener reseña específica |
| GET | `/api/reviews/by-place/{place_id}` | Reseñas de un lugar |
| GET | `/api/reviews/recent/all` | Reseñas más recientes |
| DELETE | `/api/reviews/{review_id}` | Eliminar reseña |

### 4. 📊 Monitor
**Prefijo**: `/api/monitor`

Control del sistema de monitoreo automático.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/monitor/status` | Estado del monitoreo |
| POST | `/api/monitor/start` | Iniciar monitoreo |
| POST | `/api/monitor/stop` | Detener monitoreo |
| POST | `/api/monitor/check-now` | Revisión inmediata |
| PUT | `/api/monitor/interval` | Actualizar intervalo |
| POST | `/api/monitor/test-webhook/{place_id}` | Probar webhook |

### 5. 🏥 General
**Prefijo**: `/`

Endpoints generales del sistema.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Health check |

---

## Formatos de Respuesta

### Respuestas Exitosas

Todas las respuestas exitosas retornan JSON con el siguiente formato:

```json
{
  "campo1": "valor",
  "campo2": 123,
  "campo3": {
    "subcampo": "valor"
  }
}
```

### Respuestas con Paginación

```json
{
  "total": 250,
  "page": 1,
  "page_size": 100,
  "total_pages": 3,
  "data": [ /* array de resultados */ ]
}
```

### Respuestas de Error

```json
{
  "detail": "Descripción del error"
}
```

**O** para errores de validación:

```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Códigos de Estado HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado exitosamente |
| 202 | Accepted | Solicitud aceptada (procesamiento asíncrono) |
| 204 | No Content | Eliminación exitosa |
| 400 | Bad Request | Parámetros inválidos |
| 404 | Not Found | Recurso no encontrado |
| 409 | Conflict | Recurso duplicado |
| 422 | Unprocessable Entity | Error de validación |
| 500 | Internal Server Error | Error del servidor |

---

## Documentación Interactiva

### Swagger UI
Documentación interactiva con interfaz visual para probar endpoints:

```
http://localhost:8000/docs
```

**Características**:
- Prueba de endpoints en tiempo real
- Schemas automáticos
- Ejemplos de request/response
- Descarga de especificación OpenAPI

### ReDoc
Documentación alternativa en formato de documentación:

```
http://localhost:8000/redoc
```

**Características**:
- Vista de documentación limpia
- Navegación por secciones
- Búsqueda de endpoints
- Exportación a PDF

### OpenAPI Schema (JSON)
Especificación OpenAPI 3.0 para generación de clientes:

```
http://localhost:8000/openapi.json
```

---

## Límites y Restricciones

### Paginación

| Parámetro | Valor por Defecto | Máximo |
|-----------|------------------|--------|
| `page_size` | 100 | 500 |
| `limit` | 100 | 500 |

### Scraping

| Parámetro | Valor por Defecto | Mínimo | Máximo |
|-----------|------------------|--------|--------|
| `max_reviews` | 100 | 1 | 1000 |
| `check_interval_minutes` | 60 | 5 | 10080 (1 semana) |

### Timeouts

| Operación | Timeout |
|-----------|---------|
| Scraping | 300 segundos (5 minutos) |
| Webhook | 10 segundos |
| API Request | 60 segundos |

### Workers

| Configuración | Valor |
|--------------|-------|
| Max Concurrent Scrapers | 3 |
| Job Result TTL | 3600 segundos (1 hora) |

---

## Próximos Pasos

1. 📚 Lee la [Guía de Inicio Rápido](QUICK_START.md)
2. 🔍 Consulta la [Referencia de Endpoints](API_ENDPOINTS.md)
3. 🔗 Revisa la [Guía de Integración](INTEGRATION_GUIDE.md)
4. 📦 Explora los [Modelos de Datos](DATA_MODELS.md)
5. 🔔 Configura [Webhooks](WEBHOOKS.md)

---

## Soporte

- **Documentación**: [docs/](.)
- **Issues**: Reportar problemas en el repositorio
- **API Interactiva**: http://localhost:8000/docs

---

## Changelog

### v1.0.0
- ✅ Migración de Selenium a Playwright
- ✅ Campos opcionales en Reviews (manejo de errores)
- ✅ Corrección de ordenamiento por "Más recientes"
- ✅ Optimización de scroll y extracción
- ✅ Sistema completo de webhooks
- ✅ Monitoreo automático con scheduler

---

**Última actualización**: 2025-11-03
