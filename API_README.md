# Google Maps Reviews Scraper API

API REST completa con FastAPI para scraping y monitoreo de reseñas de Google Maps con sistema de webhooks.

## Características

- ✅ API REST con FastAPI
- ✅ Scraping asíncrono con RQ (Redis Queue)
- ✅ Monitoreo continuo automático con APScheduler
- ✅ Sistema de webhooks para notificaciones en tiempo real
- ✅ CRUD completo de lugares a monitorear
- ✅ Consulta de reseñas con paginación (100 resultados por defecto)
- ✅ Almacenamiento en MongoDB
- ✅ Dockerizado para fácil deploy
- ✅ Respuestas solo JSON

## Requisitos

- Docker y Docker Compose (recomendado)
- O manualmente: Python 3.11+, MongoDB, Redis, Chrome/ChromeDriver

## Inicio Rápido con Docker

1. **Clonar el repositorio y configurar entorno:**
```bash
cp .env.example .env
# Editar .env según tus necesidades
```

2. **Iniciar todos los servicios:**
```bash
docker-compose up -d
```

Esto iniciará:
- **API FastAPI** en http://localhost:8000
- **MongoDB** en localhost:27017
- **Redis** en localhost:6379
- **RQ Worker** para procesar tareas de scraping en background

3. **Ver logs:**
```bash
docker-compose logs -f api
docker-compose logs -f worker
```

4. **Acceder a la documentación interactiva:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Inicio Manual (sin Docker)

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Iniciar MongoDB y Redis:**
```bash
# MongoDB
mongod --dbpath /path/to/data

# Redis
redis-server
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env
```

4. **Iniciar la API:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. **Iniciar el worker RQ (en otra terminal):**
```bash
python worker.py
```

## Endpoints Principales

### 1. Gestión de Lugares (CRUD)

#### Registrar un lugar para monitoreo
```bash
POST /api/places/
```
```json
{
  "client_id": "cliente123",
  "branch_id": "sucursal456",
  "url": "https://www.google.com/maps/place/...",
  "webhook_url": "https://tu-servidor.com/webhook",
  "name": "Mi Restaurante",
  "check_interval_minutes": 60,
  "monitoring_enabled": true
}
```

#### Listar todos los lugares
```bash
GET /api/places/?client_id=cliente123&branch_id=sucursal456
```

#### Obtener un lugar específico
```bash
GET /api/places/{place_id}
```

#### Actualizar un lugar
```bash
PUT /api/places/{place_id}
```
```json
{
  "webhook_url": "https://nuevo-webhook.com",
  "monitoring_enabled": false
}
```

#### Eliminar un lugar
```bash
DELETE /api/places/{place_id}
```

#### Estadísticas de un lugar
```bash
GET /api/places/{place_id}/stats
```

### 2. Scraping Manual

#### Iniciar scraping asíncrono
```bash
POST /api/scraping/start
```
```json
{
  "url": "https://www.google.com/maps/place/...",
  "max_reviews": 100,
  "sort_by": "newest",
  "client_id": "cliente123",
  "branch_id": "sucursal456",
  "save_to_db": true
}
```

Respuesta:
```json
{
  "job_id": "abc123-def456",
  "status": "queued",
  "message": "Scraping job queued successfully..."
}
```

#### Consultar estado de scraping
```bash
GET /api/scraping/status/{job_id}
```

#### Obtener resultados de scraping
```bash
GET /api/scraping/result/{job_id}
```

#### Cancelar un trabajo
```bash
DELETE /api/scraping/{job_id}
```

#### Ver estado de workers
```bash
GET /api/scraping/workers/status
```

### 3. Consultar Reseñas

#### Listar reseñas con paginación
```bash
GET /api/reviews/?page=1&page_size=100&place_id=xxx&min_rating=4
```

Parámetros:
- `page`: Número de página (default: 1)
- `page_size`: Resultados por página (default: 100, max: 500)
- `place_id`: Filtrar por lugar
- `client_id`: Filtrar por cliente
- `branch_id`: Filtrar por sucursal
- `min_rating`: Rating mínimo
- `max_rating`: Rating máximo
- `sort_by`: review_date, rating, retrieval_date
- `sort_order`: asc, desc

#### Obtener una reseña específica
```bash
GET /api/reviews/{review_id}
```

#### Reseñas de un lugar específico
```bash
GET /api/reviews/by-place/{place_id}?page=1&page_size=100
```

#### Reseñas más recientes del sistema
```bash
GET /api/reviews/recent/all?limit=100&client_id=cliente123
```

### 4. Control de Monitoreo

#### Ver estado del monitoreo
```bash
GET /api/monitor/status
```

#### Iniciar/reanudar monitoreo
```bash
POST /api/monitor/start
```

#### Detener monitoreo
```bash
POST /api/monitor/stop
```

#### Ejecutar chequeo inmediato
```bash
POST /api/monitor/check-now
```

#### Actualizar intervalo de monitoreo
```bash
PUT /api/monitor/interval?minutes=30
```

#### Probar webhook de un lugar
```bash
POST /api/monitor/test-webhook/{place_id}
```

### 5. Health Check

```bash
GET /health
```

## Sistema de Webhooks

Cuando se detectan nuevas reseñas, el sistema envía automáticamente un POST a la URL configurada:

### Payload del Webhook

```json
{
  "event": "new_reviews",
  "client_id": "cliente123",
  "branch_id": "sucursal456",
  "place_id": "place-uuid",
  "place_name": "Mi Restaurante",
  "place_url": "https://www.google.com/maps/...",
  "new_reviews_count": 5,
  "timestamp": "2025-10-31T10:05:00",
  "reviews": [
    {
      "id_review": "review123",
      "place_id": "place-uuid",
      "client_id": "cliente123",
      "branch_id": "sucursal456",
      "caption": "Excelente servicio!",
      "rating": 5.0,
      "username": "Juan Pérez",
      "review_date": "2025-10-30T15:30:00",
      "retrieval_date": "2025-10-31T10:00:00",
      "relative_date": "hace 1 día",
      "n_review_user": 15,
      "url_user": "https://www.google.com/maps/contrib/..."
    }
  ]
}
```

### Implementar Endpoint de Webhook

Ejemplo en Python/FastAPI:
```python
@app.post("/webhook")
async def receive_webhook(payload: dict):
    client_id = payload["client_id"]
    branch_id = payload["branch_id"]
    new_reviews = payload["reviews"]

    # Procesar nuevas reseñas
    for review in new_reviews:
        print(f"Nueva reseña: {review['caption']}")
        # Tu lógica aquí...

    return {"status": "ok"}
```

## Flujo de Trabajo Completo

### Configuración Inicial

1. **Registrar un lugar:**
```bash
curl -X POST http://localhost:8000/api/places/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "cliente1",
    "branch_id": "sucursal1",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://mi-servidor.com/webhook",
    "name": "Mi Negocio",
    "check_interval_minutes": 60
  }'
```

2. **El sistema automáticamente:**
   - Registra el lugar en MongoDB
   - Lo incluye en el monitoreo periódico
   - Cada 60 minutos (configurable):
     - Revisa si hay nuevas reseñas
     - Guarda las nuevas en MongoDB
     - Envía webhook con las nuevas reseñas

### Scraping Manual

Si necesitas extraer reseñas inmediatamente:

```bash
# 1. Iniciar scraping
curl -X POST http://localhost:8000/api/scraping/start \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.google.com/maps/place/...",
    "max_reviews": 100,
    "sort_by": "newest"
  }'

# Respuesta: {"job_id": "abc123", "status": "queued"}

# 2. Verificar estado
curl http://localhost:8000/api/scraping/status/abc123

# 3. Obtener resultados cuando termine
curl http://localhost:8000/api/scraping/result/abc123
```

### Consultar Reseñas

```bash
# Ver todas las reseñas de un lugar
curl "http://localhost:8000/api/reviews/by-place/place-uuid?page=1&page_size=100"

# Filtrar por rating
curl "http://localhost:8000/api/reviews/?place_id=place-uuid&min_rating=4&page_size=50"

# Ver reseñas más recientes
curl "http://localhost:8000/api/reviews/recent/all?limit=20"
```

## Configuración Avanzada

### Variables de Entorno (.env)

Ver [.env.example](.env.example) para lista completa.

Configuraciones importantes:

- `DEFAULT_CHECK_INTERVAL`: Intervalo de monitoreo en minutos (default: 60)
- `ENABLE_MONITORING_ON_STARTUP`: Auto-iniciar monitoreo (default: true)
- `WEBHOOK_MAX_RETRIES`: Reintentos de webhook (default: 3)
- `DEFAULT_PAGE_SIZE`: Tamaño de página (default: 100)
- `HEADLESS_MODE`: Chrome sin interfaz (default: true en producción)

### Escalabilidad

Para procesar más lugares simultáneamente, aumenta el número de workers:

```yaml
# docker-compose.yml
services:
  worker:
    # ... configuración existente
    deploy:
      replicas: 3  # 3 workers en paralelo
```

O manualmente:
```bash
# Terminal 1
python worker.py

# Terminal 2
python worker.py

# Terminal 3
python worker.py
```

## Monitoreo y Logs

### Ver logs de la API
```bash
docker-compose logs -f api
```

### Ver logs del worker
```bash
docker-compose logs -f worker
```

### Archivos de log
- `api.log`: Log de la aplicación FastAPI
- `monitor.log`: Log del sistema de monitoreo

## Solución de Problemas

### El scraping falla con "ChromeDriver not found"
- En Docker: Ya está incluido automáticamente
- Manual: `webdriver-manager` lo descarga automáticamente en el primer uso

### Webhooks no llegan
1. Verificar URL con: `POST /api/monitor/test-webhook/{place_id}`
2. Revisar logs: `docker-compose logs -f api`
3. Verificar que el servidor destino esté accesible desde el contenedor

### MongoDB connection failed
```bash
# Verificar que MongoDB esté corriendo
docker-compose ps mongodb

# Ver logs
docker-compose logs mongodb
```

### Redis connection failed
```bash
# Verificar Redis
docker-compose ps redis

# Test manual
redis-cli ping
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE                              │
│  (Tu aplicación que recibe webhooks y consulta la API)     │
└────────────────┬───────────────────────────┬────────────────┘
                 │                           │
                 │ HTTP POST                 │ HTTP GET
                 │ (webhooks)                │ (consultas)
                 ↓                           ↓
        ┌─────────────────────────────────────────────┐
        │            FASTAPI API                      │
        │  - CRUD Places                              │
        │  - Scraping Jobs                            │
        │  - Reviews Query                            │
        │  - Monitor Control                          │
        └──┬──────────┬───────────┬──────────┬───────┘
           │          │           │          │
           ↓          ↓           ↓          ↓
      ┌────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
      │MongoDB │ │ Redis  │ │APSched  │ │  Worker  │
      │Reviews │ │  RQ    │ │Monitor  │ │  Scraper │
      │Places  │ │Jobs    │ │Tasks    │ │  Tasks   │
      └────────┘ └────────┘ └─────────┘ └──────────┘
                                              │
                                              ↓
                                    ┌─────────────────┐
                                    │ Google Maps     │
                                    │ (Selenium)      │
                                    └─────────────────┘
```

## Próximos Pasos

1. Personalizar configuración en `.env`
2. Registrar tus lugares con `POST /api/places/`
3. Implementar endpoint de webhook en tu servidor
4. Consultar reseñas con `GET /api/reviews/`
5. Monitorear estado con `GET /api/monitor/status`

## Soporte

Para más información, consulta:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
