# Referencia de Endpoints - API Google Maps Reviews Scraper

## Índice

- [Places (Lugares)](#places-lugares)
- [Scraping](#scraping)
- [Reviews (Reseñas)](#reviews-reseñas)
- [Monitor](#monitor)
- [General](#general)
- [Códigos de Error](#códigos-de-error)

---

## Places (Lugares)

### POST /api/places/

Registra un nuevo lugar para monitoreo de reseñas.

**Parámetros de Entrada (JSON Body)**

| Campo | Tipo | Requerido | Descripción | Validación |
|-------|------|-----------|-------------|------------|
| `client_id` | string | ✅ | Identificador del cliente | - |
| `branch_id` | string | ✅ | Identificador de la sucursal | - |
| `url` | string | ✅ | URL de Google Maps del lugar | Debe contener "google.com/maps" |
| `webhook_url` | string | ✅ | URL para recibir notificaciones | URL válida HTTP/HTTPS |
| `name` | string | ❌ | Nombre del lugar | - |
| `check_interval_minutes` | integer | ❌ | Intervalo de monitoreo en minutos | Min: 5, Max: 10080, Default: 60 |
| `monitoring_enabled` | boolean | ❌ | Activar monitoreo automático | Default: true |

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/places/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "restaurante_abc",
    "branch_id": "sucursal_centro",
    "url": "https://www.google.com/maps/place/Mi+Restaurante/@40.7128,-74.0060,15z",
    "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
    "name": "Restaurante ABC - Centro",
    "check_interval_minutes": 60,
    "monitoring_enabled": true
  }'
```

**Respuesta Exitosa (201 Created)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "restaurante_abc",
  "branch_id": "sucursal_centro",
  "url": "https://www.google.com/maps/place/Mi+Restaurante/@40.7128,-74.0060,15z",
  "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
  "name": "Restaurante ABC - Centro",
  "monitoring_enabled": true,
  "check_interval_minutes": 60,
  "last_check": null,
  "last_review_count": 0,
  "created_at": "2025-11-03T10:30:00.000Z",
  "updated_at": "2025-11-03T10:30:00.000Z"
}
```

**Errores Posibles**

- `400 Bad Request`: URL inválida o parámetros incorrectos
- `409 Conflict`: Ya existe un lugar con la misma URL, client_id y branch_id
- `422 Unprocessable Entity`: Error de validación

---

### GET /api/places/

Lista todos los lugares registrados con filtros opcionales y paginación.

**Parámetros Query**

| Parámetro | Tipo | Requerido | Descripción | Default |
|-----------|------|-----------|-------------|---------|
| `client_id` | string | ❌ | Filtrar por cliente | - |
| `branch_id` | string | ❌ | Filtrar por sucursal | - |
| `monitoring_enabled` | boolean | ❌ | Filtrar por estado de monitoreo | - |
| `skip` | integer | ❌ | Número de registros a omitir | 0 |
| `limit` | integer | ❌ | Máximo de registros a retornar | 100 (max: 500) |

**Ejemplo de Request**

```bash
# Obtener todos los lugares del cliente "restaurante_abc"
curl "http://localhost:8000/api/places/?client_id=restaurante_abc&limit=50"

# Obtener lugares con monitoreo activado
curl "http://localhost:8000/api/places/?monitoring_enabled=true"
```

**Respuesta Exitosa (200 OK)**

```json
[
  {
    "place_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_id": "restaurante_abc",
    "branch_id": "sucursal_centro",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
    "name": "Restaurante ABC - Centro",
    "monitoring_enabled": true,
    "check_interval_minutes": 60,
    "last_check": "2025-11-03T09:00:00.000Z",
    "last_review_count": 152,
    "created_at": "2025-10-01T08:00:00.000Z",
    "updated_at": "2025-11-03T09:00:00.000Z"
  }
]
```

---

### GET /api/places/{place_id}

Obtiene la información de un lugar específico.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/places/550e8400-e29b-41d4-a716-446655440000"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "restaurante_abc",
  "branch_id": "sucursal_centro",
  "url": "https://www.google.com/maps/place/...",
  "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
  "name": "Restaurante ABC - Centro",
  "monitoring_enabled": true,
  "check_interval_minutes": 60,
  "last_check": "2025-11-03T09:00:00.000Z",
  "last_review_count": 152,
  "created_at": "2025-10-01T08:00:00.000Z",
  "updated_at": "2025-11-03T09:00:00.000Z"
}
```

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado

---

### PUT /api/places/{place_id}

Actualiza la configuración de un lugar existente.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Parámetros de Entrada (JSON Body) - Todos opcionales**

| Campo | Tipo | Descripción | Validación |
|-------|------|-------------|------------|
| `webhook_url` | string | Nueva URL del webhook | URL válida HTTP/HTTPS |
| `name` | string | Nuevo nombre del lugar | - |
| `check_interval_minutes` | integer | Nuevo intervalo de monitoreo | Min: 5, Max: 10080 |
| `monitoring_enabled` | boolean | Activar/desactivar monitoreo | - |

**Ejemplo de Request**

```bash
curl -X PUT "http://localhost:8000/api/places/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "check_interval_minutes": 30,
    "monitoring_enabled": false
  }'
```

**Respuesta Exitosa (200 OK)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "restaurante_abc",
  "branch_id": "sucursal_centro",
  "url": "https://www.google.com/maps/place/...",
  "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
  "name": "Restaurante ABC - Centro",
  "monitoring_enabled": false,
  "check_interval_minutes": 30,
  "last_check": "2025-11-03T09:00:00.000Z",
  "last_review_count": 152,
  "created_at": "2025-10-01T08:00:00.000Z",
  "updated_at": "2025-11-03T10:45:00.000Z"
}
```

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado
- `400 Bad Request`: Parámetros inválidos

---

### DELETE /api/places/{place_id}

Elimina un lugar del sistema.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Ejemplo de Request**

```bash
curl -X DELETE "http://localhost:8000/api/places/550e8400-e29b-41d4-a716-446655440000"
```

**Respuesta Exitosa (204 No Content)**

Sin contenido en el body.

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado

> ⚠️ **Nota**: Esta operación NO elimina las reseñas asociadas al lugar. Las reseñas permanecen en la base de datos.

---

### GET /api/places/{place_id}/stats

Obtiene estadísticas de un lugar específico.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/places/550e8400-e29b-41d4-a716-446655440000/stats"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "place_name": "Restaurante ABC - Centro",
  "monitoring_enabled": true,
  "last_check": "2025-11-03T09:00:00.000Z",
  "total_reviews": 152,
  "average_rating": 4.5,
  "latest_review_date": "2025-11-02T18:30:00.000Z",
  "oldest_review_date": "2024-03-15T10:00:00.000Z"
}
```

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado

---

## Scraping

### POST /api/scraping/start

Inicia un trabajo de scraping asíncrono para extraer reseñas de Google Maps.

**Parámetros de Entrada (JSON Body)**

| Campo | Tipo | Requerido | Descripción | Validación |
|-------|------|-----------|-------------|------------|
| `url` | string | ✅ | URL de Google Maps del lugar | Debe contener "google.com/maps" |
| `max_reviews` | integer | ❌ | Máximo de reseñas a extraer | Min: 1, Max: 1000, Default: 100 |
| `sort_by` | string | ❌ | Tipo de ordenamiento | Ver tabla abajo, Default: "newest" |
| `client_id` | string | ❌ | Identificador del cliente | - |
| `branch_id` | string | ❌ | Identificador de la sucursal | - |
| `save_to_db` | boolean | ❌ | Guardar en base de datos | Default: true |

**Valores permitidos para `sort_by`**

| Valor | Descripción |
|-------|-------------|
| `newest` | Más recientes (recomendado) |
| `most_relevant` | Más relevantes |
| `highest_rating` | Mejor valoradas |
| `lowest_rating` | Peor valoradas |

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.google.com/maps/place/Mi+Restaurante/@40.7128,-74.0060,15z",
    "max_reviews": 50,
    "sort_by": "newest",
    "client_id": "restaurante_abc",
    "branch_id": "sucursal_centro",
    "save_to_db": true
  }'
```

**Respuesta Exitosa (202 Accepted)**

```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "queued",
  "message": "Scraping job queued successfully. Use /api/scraping/status/{job_id} to check progress.",
  "created_at": "2025-11-03T10:50:00.000Z"
}
```

**Errores Posibles**

- `400 Bad Request`: URL inválida o parámetros incorrectos
- `422 Unprocessable Entity`: Error de validación

---

### GET /api/scraping/status/{job_id}

Consulta el estado de un trabajo de scraping.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `job_id` | string | ID del trabajo retornado al iniciar scraping |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/scraping/status/abc123-def456-ghi789"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "started",
  "progress": "Extracting reviews... 25/50",
  "error": null,
  "result_available": false,
  "created_at": "2025-11-03T10:50:00.000Z",
  "started_at": "2025-11-03T10:50:15.000Z",
  "finished_at": null
}
```

**Posibles valores de `status`**

| Estado | Descripción |
|--------|-------------|
| `queued` | En cola, esperando procesamiento |
| `started` | En ejecución |
| `finished` | Completado exitosamente |
| `failed` | Falló (ver campo `error`) |

**Errores Posibles**

- `404 Not Found`: Trabajo no encontrado

---

### GET /api/scraping/result/{job_id}

Obtiene los resultados de un trabajo completado.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `job_id` | string | ID del trabajo |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/scraping/result/abc123-def456-ghi789"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "finished",
  "reviews_count": 50,
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
      "place_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "restaurante_abc",
      "branch_id": "sucursal_centro",
      "caption": "Excelente servicio y comida deliciosa!",
      "rating": 5.0,
      "username": "Juan Pérez",
      "review_date": "2025-11-01T15:30:00.000Z",
      "retrieval_date": "2025-11-03T10:51:00.000Z",
      "relative_date": "hace 2 días",
      "n_review_user": 25,
      "n_photo_user": 8,
      "url_user": "https://www.google.com/maps/contrib/123456789",
      "notified_via_webhook": false,
      "webhook_sent_at": null
    }
  ],
  "error": null
}
```

**Errores Posibles**

- `404 Not Found`: Trabajo no encontrado o resultados no disponibles
- `400 Bad Request`: Trabajo aún no completado

---

### DELETE /api/scraping/{job_id}

Cancela un trabajo de scraping en cola.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `job_id` | string | ID del trabajo |

**Ejemplo de Request**

```bash
curl -X DELETE "http://localhost:8000/api/scraping/abc123-def456-ghi789"
```

**Respuesta Exitosa (204 No Content)**

Sin contenido en el body.

**Errores Posibles**

- `404 Not Found`: Trabajo no encontrado
- `400 Bad Request`: No se puede cancelar (ya iniciado o completado)

> ⚠️ **Nota**: Solo se pueden cancelar trabajos en estado `queued`. Los trabajos ya iniciados no se pueden cancelar.

---

### GET /api/scraping/workers/status

Obtiene información sobre los workers activos y la cola de tareas.

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/scraping/workers/status"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "total_workers": 1,
  "workers": [
    {
      "name": "worker-1",
      "state": "busy",
      "current_job": "abc123-def456-ghi789",
      "successful_jobs": 145,
      "failed_jobs": 3,
      "total_working_time": 12345.67
    }
  ],
  "queue_name": "scraping_tasks",
  "queued_jobs": 5,
  "started_jobs": 1,
  "finished_jobs": 145,
  "failed_jobs": 3
}
```

---

## Reviews (Reseñas)

### GET /api/reviews/

Lista reseñas con filtros avanzados y paginación.

**Parámetros Query**

| Parámetro | Tipo | Requerido | Descripción | Default |
|-----------|------|-----------|-------------|---------|
| `page` | integer | ❌ | Número de página | 1 |
| `page_size` | integer | ❌ | Registros por página | 100 (max: 500) |
| `place_id` | string | ❌ | Filtrar por lugar | - |
| `client_id` | string | ❌ | Filtrar por cliente | - |
| `branch_id` | string | ❌ | Filtrar por sucursal | - |
| `min_rating` | float | ❌ | Rating mínimo (1-5) | - |
| `max_rating` | float | ❌ | Rating máximo (1-5) | - |
| `sort_by` | string | ❌ | Campo de ordenamiento | `review_date` |
| `sort_order` | string | ❌ | Orden (asc/desc) | `desc` |

**Valores permitidos para `sort_by`**

| Valor | Descripción |
|-------|-------------|
| `review_date` | Fecha de la reseña |
| `rating` | Calificación |
| `retrieval_date` | Fecha de extracción |

**Ejemplo de Request**

```bash
# Obtener reseñas con rating >= 4
curl "http://localhost:8000/api/reviews/?min_rating=4&page_size=50"

# Obtener reseñas de un cliente específico
curl "http://localhost:8000/api/reviews/?client_id=restaurante_abc&page=1"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "total": 250,
  "page": 1,
  "page_size": 50,
  "total_pages": 5,
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
      "place_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "restaurante_abc",
      "branch_id": "sucursal_centro",
      "caption": "Excelente servicio!",
      "rating": 5.0,
      "username": "María García",
      "review_date": "2025-11-02T18:30:00.000Z",
      "retrieval_date": "2025-11-03T09:00:00.000Z",
      "relative_date": "hace 1 día",
      "n_review_user": 42,
      "n_photo_user": 15,
      "url_user": "https://www.google.com/maps/contrib/987654321",
      "notified_via_webhook": true,
      "webhook_sent_at": "2025-11-03T09:01:30.000Z"
    }
  ]
}
```

---

### GET /api/reviews/{review_id}

Obtiene una reseña específica.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `review_id` | string | ID de la reseña |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/reviews/ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "restaurante_abc",
  "branch_id": "sucursal_centro",
  "caption": "Excelente servicio!",
  "rating": 5.0,
  "username": "María García",
  "review_date": "2025-11-02T18:30:00.000Z",
  "retrieval_date": "2025-11-03T09:00:00.000Z",
  "relative_date": "hace 1 día",
  "n_review_user": 42,
  "n_photo_user": 15,
  "url_user": "https://www.google.com/maps/contrib/987654321",
  "notified_via_webhook": true,
  "webhook_sent_at": "2025-11-03T09:01:30.000Z"
}
```

**Errores Posibles**

- `404 Not Found`: Reseña no encontrada

---

### GET /api/reviews/by-place/{place_id}

Obtiene reseñas de un lugar específico con paginación.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Parámetros Query**

| Parámetro | Tipo | Requerido | Descripción | Default |
|-----------|------|-----------|-------------|---------|
| `page` | integer | ❌ | Número de página | 1 |
| `page_size` | integer | ❌ | Registros por página | 100 (max: 500) |
| `min_rating` | float | ❌ | Rating mínimo (1-5) | - |
| `max_rating` | float | ❌ | Rating máximo (1-5) | - |

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/reviews/by-place/550e8400-e29b-41d4-a716-446655440000?page_size=20"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "total": 152,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "reviews": [ /* array de reseñas */ ]
}
```

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado

---

### GET /api/reviews/recent/all

Obtiene las reseñas más recientes del sistema.

**Parámetros Query**

| Parámetro | Tipo | Requerido | Descripción | Default |
|-----------|------|-----------|-------------|---------|
| `limit` | integer | ❌ | Número máximo de reseñas | 100 (max: 500) |
| `client_id` | string | ❌ | Filtrar por cliente | - |
| `branch_id` | string | ❌ | Filtrar por sucursal | - |

**Ejemplo de Request**

```bash
# Obtener las 50 reseñas más recientes
curl "http://localhost:8000/api/reviews/recent/all?limit=50"

# Últimas reseñas de un cliente
curl "http://localhost:8000/api/reviews/recent/all?client_id=restaurante_abc&limit=20"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "count": 50,
  "reviews": [ /* array de reseñas ordenadas por retrieval_date desc */ ]
}
```

---

### DELETE /api/reviews/{review_id}

Elimina una reseña del sistema.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `review_id` | string | ID de la reseña |

**Ejemplo de Request**

```bash
curl -X DELETE "http://localhost:8000/api/reviews/ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE"
```

**Respuesta Exitosa (204 No Content)**

Sin contenido en el body.

**Errores Posibles**

- `404 Not Found`: Reseña no encontrada

> ⚠️ **Advertencia**: Esta operación es irreversible. La reseña se elimina permanentemente.

---

## Monitor

### GET /api/monitor/status

Obtiene el estado actual del sistema de monitoreo automático.

**Ejemplo de Request**

```bash
curl "http://localhost:8000/api/monitor/status"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "monitoring_active": true,
  "total_places": 15,
  "enabled_places": 12,
  "last_check": "2025-11-03T09:00:00.000Z",
  "next_check": "2025-11-03T10:00:00.000Z"
}
```

---

### POST /api/monitor/start

Inicia o reanuda el monitoreo automático de lugares.

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/monitor/start"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "message": "Monitoring started successfully",
  "status": {
    "monitoring_active": true,
    "enabled_places": 12
  }
}
```

---

### POST /api/monitor/stop

Detiene el monitoreo automático.

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/monitor/stop"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "message": "Monitoring stopped successfully",
  "status": {
    "monitoring_active": false
  }
}
```

---

### POST /api/monitor/check-now

Ejecuta una revisión inmediata de todos los lugares sin afectar el calendario de monitoreo.

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/monitor/check-now"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "message": "Monitoring check executed",
  "result": {
    "places_checked": 12,
    "new_reviews_found": 5,
    "webhooks_sent": 3
  }
}
```

---

### PUT /api/monitor/interval

Actualiza el intervalo global de monitoreo.

**Parámetros Query**

| Parámetro | Tipo | Requerido | Descripción | Validación |
|-----------|------|-----------|-------------|------------|
| `minutes` | integer | ✅ | Nuevo intervalo en minutos | Min: 5 |

**Ejemplo de Request**

```bash
curl -X PUT "http://localhost:8000/api/monitor/interval?minutes=30"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "message": "Monitoring interval updated to 30 minutes",
  "interval_minutes": 30,
  "status": {
    "monitoring_active": true,
    "next_check": "2025-11-03T11:30:00.000Z"
  }
}
```

**Errores Posibles**

- `400 Bad Request`: Intervalo inválido (menor a 5 minutos)

---

### POST /api/monitor/test-webhook/{place_id}

Prueba el webhook de un lugar enviando datos de ejemplo.

**Parámetros de Ruta**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `place_id` | string (UUID) | ID del lugar |

**Ejemplo de Request**

```bash
curl -X POST "http://localhost:8000/api/monitor/test-webhook/550e8400-e29b-41d4-a716-446655440000"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
  "test_result": {
    "success": true,
    "status_code": 200,
    "response_time_seconds": 0.345,
    "response_body": "{\"status\":\"ok\"}",
    "error": null
  }
}
```

**Respuesta con Error (200 OK)**

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "webhook_url": "https://mi-sistema.com/api/webhooks/google-reviews",
  "test_result": {
    "success": false,
    "status_code": 500,
    "response_time_seconds": 1.234,
    "response_body": null,
    "error": "Connection timeout"
  }
}
```

**Errores Posibles**

- `404 Not Found`: Lugar no encontrado

---

## General

### GET /

Endpoint raíz que proporciona información básica de la API.

**Ejemplo de Request**

```bash
curl "http://localhost:8000/"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "message": "Welcome to Google Maps Reviews Scraper API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

### GET /health

Health check que verifica el estado de los servicios principales.

**Ejemplo de Request**

```bash
curl "http://localhost:8000/health"
```

**Respuesta Exitosa (200 OK)**

```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true,
  "error": null
}
```

**Respuesta con Error (200 OK)**

```json
{
  "status": "unhealthy",
  "mongodb": true,
  "redis": false,
  "error": "Redis connection failed"
}
```

---

## Códigos de Error

### Errores Comunes

#### 400 Bad Request

**Causas**:
- Parámetros inválidos
- URL de Google Maps incorrecta
- Valores fuera de rango

**Ejemplo**:
```json
{
  "detail": "URL must contain 'google.com/maps'"
}
```

---

#### 404 Not Found

**Causas**:
- Recurso (lugar, reseña, trabajo) no existe
- ID inválido

**Ejemplo**:
```json
{
  "detail": "Place not found"
}
```

---

#### 409 Conflict

**Causas**:
- Recurso duplicado
- Lugar ya registrado con misma URL, client_id y branch_id

**Ejemplo**:
```json
{
  "detail": "A place with the same URL, client_id and branch_id already exists"
}
```

---

#### 422 Unprocessable Entity

**Causas**:
- Error de validación Pydantic
- Tipo de dato incorrecto
- Campo requerido faltante

**Ejemplo**:
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "check_interval_minutes"],
      "msg": "ensure this value is greater than or equal to 5",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 5}
    }
  ]
}
```

---

#### 500 Internal Server Error

**Causas**:
- Error interno del servidor
- Fallo en conexión a MongoDB o Redis
- Error no controlado en scraping

**Ejemplo**:
```json
{
  "detail": "Internal server error"
}
```

---

## Notas Adicionales

### Rate Limiting

Actualmente **no implementado**. Planificado para versiones futuras.

### Autenticación

Actualmente **no implementada**. Para entornos de producción, se recomienda implementar:
- API Keys en headers
- JWT tokens
- OAuth 2.0

### CORS

Configurado para permitir todos los orígenes (`*`). En producción, configurar orígenes específicos.

### Paginación

- Todos los endpoints de listado soportan paginación
- Límite máximo: 500 registros por página
- Default: 100 registros por página

### Timeouts

- Scraping: 300 segundos (5 minutos)
- Webhook: 10 segundos
- Requests API: 60 segundos

---

**Última actualización**: 2025-11-03
