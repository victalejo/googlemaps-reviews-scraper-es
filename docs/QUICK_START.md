# Inicio Rápido - Google Maps Reviews Scraper API

## Guía de 5 Minutos

Esta guía te ayudará a empezar a usar la API en menos de 5 minutos.

---

## Paso 1: Iniciar la API (30 segundos)

### Opción A: Docker Compose (Recomendado)

```bash
# Clonar el repositorio (si no lo tienes)
git clone <repo-url>
cd googlemaps-reviews-scraper-es

# Iniciar todos los servicios
docker-compose up -d

# Verificar que está funcionando
curl http://localhost:8000/health
```

**Respuesta esperada**:
```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true,
  "error": null
}
```

### Opción B: Instalación Manual

```bash
# Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# Iniciar MongoDB y Redis
# (según tu sistema operativo)

# Iniciar API
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Iniciar Worker (en otra terminal)
python worker.py &
```

---

## Paso 2: Registrar tu Primer Lugar (1 minuto)

Necesitas una URL de Google Maps de un lugar. Por ejemplo:
- Busca un restaurante/negocio en Google Maps
- Copia la URL completa

```bash
curl -X POST "http://localhost:8000/api/places/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "mi_empresa",
    "branch_id": "principal",
    "url": "TU_URL_DE_GOOGLE_MAPS_AQUI",
    "webhook_url": "https://webhook.site/unique-id",
    "name": "Mi Primer Lugar",
    "monitoring_enabled": true
  }'
```

> 💡 **Tip**: Usa [webhook.site](https://webhook.site) para obtener una URL de webhook temporal para pruebas.

**Respuesta**:
```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "mi_empresa",
  "branch_id": "principal",
  "url": "https://www.google.com/maps/place/...",
  "webhook_url": "https://webhook.site/unique-id",
  "name": "Mi Primer Lugar",
  "monitoring_enabled": true,
  "check_interval_minutes": 60,
  "last_check": null,
  "last_review_count": 0,
  "created_at": "2025-11-03T10:00:00.000Z",
  "updated_at": "2025-11-03T10:00:00.000Z"
}
```

**Guarda el `place_id` - lo necesitarás después!**

---

## Paso 3: Extraer Reseñas (2 minutos)

### Iniciar Scraping

```bash
curl -X POST "http://localhost:8000/api/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "TU_URL_DE_GOOGLE_MAPS",
    "max_reviews": 20,
    "sort_by": "newest",
    "client_id": "mi_empresa",
    "branch_id": "principal",
    "save_to_db": true
  }'
```

**Respuesta**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "queued",
  "message": "Scraping job queued successfully...",
  "created_at": "2025-11-03T10:05:00.000Z"
}
```

**Guarda el `job_id`!**

### Consultar Estado

```bash
# Reemplaza abc123-def456-ghi789 con tu job_id
curl "http://localhost:8000/api/scraping/status/abc123-def456-ghi789"
```

**Mientras está en proceso**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "started",
  "progress": "Extracting reviews... 10/20",
  "result_available": false
}
```

**Cuando termine**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "finished",
  "result_available": true
}
```

### Obtener Resultados

```bash
curl "http://localhost:8000/api/scraping/result/abc123-def456-ghi789"
```

**Respuesta** (extracto):
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "finished",
  "reviews_count": 20,
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
      "caption": "Excelente servicio!",
      "rating": 5.0,
      "username": "Juan Pérez",
      "review_date": "2025-11-02T15:30:00.000Z",
      ...
    },
    ...
  ]
}
```

---

## Paso 4: Consultar Reseñas Almacenadas (30 segundos)

### Ver Todas las Reseñas

```bash
curl "http://localhost:8000/api/reviews/?page=1&page_size=10"
```

### Filtrar por Cliente

```bash
curl "http://localhost:8000/api/reviews/?client_id=mi_empresa"
```

### Solo Reseñas con Rating >= 4

```bash
curl "http://localhost:8000/api/reviews/?min_rating=4"
```

### Últimas 10 Reseñas

```bash
curl "http://localhost:8000/api/reviews/recent/all?limit=10"
```

---

## Paso 5: Ver Estadísticas (30 segundos)

```bash
# Reemplaza PLACE_ID con tu place_id del Paso 2
curl "http://localhost:8000/api/places/PLACE_ID/stats"
```

**Respuesta**:
```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "place_name": "Mi Primer Lugar",
  "monitoring_enabled": true,
  "last_check": "2025-11-03T10:05:00.000Z",
  "total_reviews": 20,
  "average_rating": 4.3,
  "latest_review_date": "2025-11-02T18:30:00.000Z",
  "oldest_review_date": "2024-06-15T10:00:00.000Z"
}
```

---

## ¡Felicidades! 🎉

Ya sabes lo básico. Ahora puedes:

### Monitoreo Automático

El lugar que registraste en el Paso 2 se monitorea automáticamente cada 60 minutos. Cuando haya nuevas reseñas, recibirás un webhook en la URL que configuraste.

### Probar Webhook

```bash
curl -X POST "http://localhost:8000/api/monitor/test-webhook/PLACE_ID"
```

Ve a [webhook.site](https://webhook.site) y verás la notificación de prueba.

---

## Ejemplos Rápidos

### Python

```python
import requests

# Configuración
API_URL = "http://localhost:8000"

# Registrar lugar
response = requests.post(f"{API_URL}/api/places/", json={
    "client_id": "mi_empresa",
    "branch_id": "principal",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://webhook.site/unique-id",
    "name": "Mi Lugar"
})
place = response.json()
print(f"Place ID: {place['place_id']}")

# Iniciar scraping
response = requests.post(f"{API_URL}/api/scraping/start", json={
    "url": place["url"],
    "max_reviews": 50
})
job = response.json()
print(f"Job ID: {job['job_id']}")

# Consultar reseñas
response = requests.get(f"{API_URL}/api/reviews/", params={
    "client_id": "mi_empresa",
    "min_rating": 4
})
data = response.json()
print(f"Total de reseñas >=4★: {data['total']}")
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';

// Registrar lugar
const response = await fetch(`${API_URL}/api/places/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_id: 'mi_empresa',
    branch_id: 'principal',
    url: 'https://www.google.com/maps/place/...',
    webhook_url: 'https://webhook.site/unique-id',
    name: 'Mi Lugar'
  })
});
const place = await response.json();
console.log('Place ID:', place.place_id);

// Iniciar scraping
const jobResponse = await fetch(`${API_URL}/api/scraping/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: place.url,
    max_reviews: 50
  })
});
const job = await jobResponse.json();
console.log('Job ID:', job.job_id);

// Consultar reseñas
const reviewsResponse = await fetch(
  `${API_URL}/api/reviews/?client_id=mi_empresa&min_rating=4`
);
const data = await reviewsResponse.json();
console.log('Total de reseñas >=4★:', data.total);
```

---

## Casos de Uso Comunes

### Caso 1: Monitorear Múltiples Sucursales

```bash
# Sucursal 1
curl -X POST "http://localhost:8000/api/places/" -H "Content-Type: application/json" -d '{
  "client_id": "cadena_restaurantes",
  "branch_id": "sucursal_centro",
  "url": "URL_SUCURSAL_1",
  "webhook_url": "https://tu-servidor.com/webhook",
  "name": "Restaurante - Centro"
}'

# Sucursal 2
curl -X POST "http://localhost:8000/api/places/" -H "Content-Type: application/json" -d '{
  "client_id": "cadena_restaurantes",
  "branch_id": "sucursal_norte",
  "url": "URL_SUCURSAL_2",
  "webhook_url": "https://tu-servidor.com/webhook",
  "name": "Restaurante - Norte"
}'

# Ver reseñas de todas las sucursales
curl "http://localhost:8000/api/reviews/?client_id=cadena_restaurantes"

# Ver reseñas solo de sucursal norte
curl "http://localhost:8000/api/reviews/?client_id=cadena_restaurantes&branch_id=sucursal_norte"
```

### Caso 2: Extraer Reseñas de Varios Lugares Rápidamente

```bash
# Lugar 1
curl -X POST "http://localhost:8000/api/scraping/start" -H "Content-Type: application/json" -d '{
  "url": "URL_LUGAR_1",
  "max_reviews": 100,
  "client_id": "cliente1",
  "branch_id": "lugar1"
}'

# Lugar 2
curl -X POST "http://localhost:8000/api/scraping/start" -H "Content-Type: application/json" -d '{
  "url": "URL_LUGAR_2",
  "max_reviews": 100,
  "client_id": "cliente1",
  "branch_id": "lugar2"
}'

# Los dos se procesan en paralelo (gracias al sistema de workers)
```

### Caso 3: Dashboard de Analytics

```bash
# 1. Obtener estadísticas de todos tus lugares
curl "http://localhost:8000/api/places/?client_id=mi_cliente"

# 2. Para cada lugar, obtener stats detalladas
curl "http://localhost:8000/api/places/PLACE_ID_1/stats"
curl "http://localhost:8000/api/places/PLACE_ID_2/stats"

# 3. Obtener reseñas recientes
curl "http://localhost:8000/api/reviews/recent/all?client_id=mi_cliente&limit=50"

# 4. Obtener solo reseñas negativas (<=2 estrellas)
curl "http://localhost:8000/api/reviews/?client_id=mi_cliente&max_rating=2"
```

---

## Documentación Interactiva

Abre tu navegador en:

### Swagger UI (Interfaz Interactiva)
```
http://localhost:8000/docs
```

Aquí puedes:
- 🔍 Ver todos los endpoints
- 🧪 Probar endpoints directamente
- 📋 Ver ejemplos de request/response
- 📥 Descargar especificación OpenAPI

### ReDoc (Documentación Legible)
```
http://localhost:8000/redoc
```

---

## Próximos Pasos

Ahora que conoces lo básico, profundiza en:

1. **[Guía de Integración](INTEGRATION_GUIDE.md)**
   - Ejemplos completos en Python, JavaScript, PHP
   - Flujos de trabajo avanzados
   - Clientes reutilizables

2. **[Referencia de Endpoints](API_ENDPOINTS.md)**
   - Todos los endpoints con detalles
   - Parámetros completos
   - Códigos de error

3. **[Modelos de Datos](DATA_MODELS.md)**
   - Estructura completa de Place y Review
   - Validaciones
   - Índices de MongoDB

4. **[Guía de Webhooks](WEBHOOKS.md)**
   - Implementación completa de endpoints
   - Seguridad y reintentos
   - Ejemplos de integración (Slack, Email)

5. **[Documentación Principal](API_DOCUMENTATION.md)**
   - Arquitectura del sistema
   - Configuración avanzada
   - Variables de entorno

---

## Troubleshooting Rápido

### La API no responde

```bash
# Verificar que los servicios están corriendo
docker-compose ps

# Ver logs
docker-compose logs -f api

# Reiniciar servicios
docker-compose restart
```

### El scraping no funciona

```bash
# Verificar que el worker está corriendo
curl "http://localhost:8000/api/scraping/workers/status"

# Ver logs del worker
docker-compose logs -f worker

# Reiniciar worker
docker-compose restart worker
```

### MongoDB no conecta

```bash
# Verificar salud
curl "http://localhost:8000/health"

# Ver logs de MongoDB
docker-compose logs mongodb

# Reiniciar MongoDB
docker-compose restart mongodb
```

### El webhook no recibe notificaciones

```bash
# 1. Verificar que el webhook_url es accesible
curl "https://tu-webhook-url.com"

# 2. Probar el webhook manualmente
curl -X POST "http://localhost:8000/api/monitor/test-webhook/PLACE_ID"

# 3. Verificar que el monitoreo está activo
curl "http://localhost:8000/api/monitor/status"

# 4. Si no está activo, iniciarlo
curl -X POST "http://localhost:8000/api/monitor/start"
```

---

## Comandos Útiles

### Docker Compose

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f worker

# Reiniciar un servicio
docker-compose restart api

# Ver estado de servicios
docker-compose ps

# Reconstruir imágenes
docker-compose build

# Eliminar todo (incluyendo volúmenes)
docker-compose down -v
```

### API

```bash
# Health check
curl http://localhost:8000/health

# Información de la API
curl http://localhost:8000/

# Listar lugares
curl http://localhost:8000/api/places/

# Estado del monitoreo
curl http://localhost:8000/api/monitor/status

# Estado de workers
curl http://localhost:8000/api/scraping/workers/status
```

---

## Tips y Trucos

### 1. Usar `jq` para Pretty Print

```bash
# Instalar jq
# Ubuntu/Debian: sudo apt-get install jq
# macOS: brew install jq

# Usar con la API
curl http://localhost:8000/api/reviews/ | jq '.'
curl http://localhost:8000/api/places/ | jq '.[] | {name, monitoring_enabled}'
```

### 2. Guardar Respuestas en Archivo

```bash
# Guardar todas las reseñas
curl "http://localhost:8000/api/reviews/?page_size=500" > reviews.json

# Guardar estadísticas
curl "http://localhost:8000/api/places/PLACE_ID/stats" > stats.json
```

### 3. Variables de Entorno en Bash

```bash
# Definir variables
export API_URL="http://localhost:8000"
export PLACE_ID="550e8400-e29b-41d4-a716-446655440000"

# Usar en comandos
curl "$API_URL/api/places/$PLACE_ID/stats"
```

### 4. Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh - Verificar nuevas reseñas cada 5 minutos

API_URL="http://localhost:8000"
CLIENT_ID="mi_cliente"

while true; do
  echo "Checking for new reviews..."

  # Obtener últimas reseñas
  curl -s "$API_URL/api/reviews/recent/all?client_id=$CLIENT_ID&limit=5" | \
    jq -r '.reviews[] | "\(.username): \(.rating)★ - \(.caption[0:50])"'

  echo "Next check in 5 minutes..."
  sleep 300
done
```

---

## Soporte

- 📚 **Documentación Completa**: [docs/](.)
- 🐛 **Reportar Problemas**: GitHub Issues
- 💬 **API Interactiva**: http://localhost:8000/docs

---

**¡Listo para empezar!** 🚀

Si tienes dudas, consulta la [documentación completa](API_DOCUMENTATION.md) o los [ejemplos de integración](INTEGRATION_GUIDE.md).

---

**Última actualización**: 2025-11-03
