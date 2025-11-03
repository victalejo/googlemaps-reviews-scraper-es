# Modelos de Datos - Google Maps Reviews Scraper API

## Índice

- [Introducción](#introducción)
- [Modelo: Place (Lugar)](#modelo-place-lugar)
- [Modelo: Review (Reseña)](#modelo-review-reseña)
- [Modelo: ScrapingJob (Trabajo de Scraping)](#modelo-scrapingjob-trabajo-de-scraping)
- [Modelo: WebhookPayload (Payload de Webhook)](#modelo-webhookpayload-payload-de-webhook)
- [Índices de MongoDB](#índices-de-mongodb)
- [Validaciones](#validaciones)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## Introducción

Este documento describe en detalle todos los modelos de datos utilizados por la API. Los modelos están implementados usando Pydantic en Python y se almacenan en MongoDB.

### Convenciones

- **Tipos de datos**: Se usa la notación de Python/Pydantic
- **Nullable**: Campos que pueden ser `null`
- **Requerido**: Campos obligatorios al crear el recurso
- **Auto-generado**: Campos que el sistema genera automáticamente

---

## Modelo: Place (Lugar)

Representa un lugar de Google Maps que se está monitoreando.

### Estructura Completa

```python
{
  "place_id": "string (UUID)",           # Auto-generado, único
  "client_id": "string",                 # Requerido
  "branch_id": "string",                 # Requerido
  "url": "string",                       # Requerido, URL de Google Maps
  "webhook_url": "string",               # Requerido, URL HTTP/HTTPS
  "name": "string | null",               # Opcional
  "monitoring_enabled": "boolean",       # Default: true
  "check_interval_minutes": "integer",   # Default: 60, Min: 5, Max: 10080
  "last_check": "datetime | null",       # Auto-actualizado
  "last_review_count": "integer",        # Auto-actualizado, Default: 0
  "created_at": "datetime",              # Auto-generado
  "updated_at": "datetime"               # Auto-actualizado
}
```

### Campos Detallados

#### place_id
- **Tipo**: String (UUID v4)
- **Requerido**: No (auto-generado)
- **Único**: Sí
- **Descripción**: Identificador único del lugar en el sistema
- **Ejemplo**: `"550e8400-e29b-41d4-a716-446655440000"`

#### client_id
- **Tipo**: String
- **Requerido**: Sí
- **Descripción**: Identificador del cliente/empresa propietaria del lugar
- **Ejemplo**: `"cadena_restaurantes_abc"`
- **Uso**: Permite filtrar y agrupar lugares por cliente

#### branch_id
- **Tipo**: String
- **Requerido**: Sí
- **Descripción**: Identificador de la sucursal/ubicación específica
- **Ejemplo**: `"sucursal_centro"`
- **Uso**: Permite distinguir entre múltiples sucursales del mismo cliente

#### url
- **Tipo**: String (URL)
- **Requerido**: Sí
- **Validación**: Debe contener "google.com/maps"
- **Descripción**: URL completa del lugar en Google Maps
- **Ejemplo**: `"https://www.google.com/maps/place/Restaurante+ABC/@40.7128,-74.0060,15z"`

#### webhook_url
- **Tipo**: String (URL)
- **Requerido**: Sí
- **Validación**: Debe ser una URL válida HTTP o HTTPS
- **Descripción**: URL donde se enviarán notificaciones de nuevas reseñas
- **Ejemplo**: `"https://mi-sistema.com/api/webhooks/reviews"`

#### name
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: Nombre descriptivo del lugar
- **Ejemplo**: `"Restaurante ABC - Sucursal Centro"`
- **Uso**: Facilita identificación en listados y reportes

#### monitoring_enabled
- **Tipo**: Boolean
- **Requerido**: No
- **Default**: `true`
- **Descripción**: Si está activo el monitoreo automático para este lugar
- **Valores**: `true` = activo, `false` = pausado

#### check_interval_minutes
- **Tipo**: Integer
- **Requerido**: No
- **Default**: `60`
- **Mínimo**: `5`
- **Máximo**: `10080` (1 semana)
- **Descripción**: Intervalo en minutos entre revisiones automáticas
- **Ejemplo**: `30` = revisar cada 30 minutos

#### last_check
- **Tipo**: Datetime (ISO 8601) o null
- **Requerido**: No
- **Auto-actualizado**: Sí
- **Descripción**: Fecha y hora de la última revisión realizada
- **Ejemplo**: `"2025-11-03T09:30:00.000Z"`
- **Valor inicial**: `null`

#### last_review_count
- **Tipo**: Integer
- **Requerido**: No
- **Default**: `0`
- **Auto-actualizado**: Sí
- **Descripción**: Número total de reseñas detectadas en la última revisión
- **Uso**: Ayuda a detectar nuevas reseñas comparando con el conteo anterior

#### created_at
- **Tipo**: Datetime (ISO 8601)
- **Requerido**: No (auto-generado)
- **Descripción**: Fecha y hora de creación del registro
- **Ejemplo**: `"2025-11-01T08:00:00.000Z"`

#### updated_at
- **Tipo**: Datetime (ISO 8601)
- **Requerido**: No (auto-actualizado)
- **Descripción**: Fecha y hora de la última actualización
- **Ejemplo**: `"2025-11-03T10:15:00.000Z"`

### Ejemplo JSON Completo

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "cadena_restaurantes_abc",
  "branch_id": "sucursal_centro",
  "url": "https://www.google.com/maps/place/Restaurante+ABC/@40.7128,-74.0060,15z",
  "webhook_url": "https://mi-sistema.com/api/webhooks/reviews",
  "name": "Restaurante ABC - Sucursal Centro",
  "monitoring_enabled": true,
  "check_interval_minutes": 60,
  "last_check": "2025-11-03T09:00:00.000Z",
  "last_review_count": 152,
  "created_at": "2025-10-01T08:00:00.000Z",
  "updated_at": "2025-11-03T09:00:00.000Z"
}
```

### Restricciones de Unicidad

Un lugar es único por la combinación de:
- `url` + `client_id` + `branch_id`

No se permite registrar dos lugares con la misma combinación (retorna error 409 Conflict).

---

## Modelo: Review (Reseña)

Representa una reseña de Google Maps extraída y almacenada.

### Estructura Completa

```python
{
  "id_review": "string",                 # Requerido, único (ID de Google)
  "place_id": "string | null",           # Opcional, UUID del lugar
  "client_id": "string | null",          # Opcional
  "branch_id": "string | null",          # Opcional
  "caption": "string | null",            # Opcional, texto de la reseña
  "rating": "float | null",              # Opcional, 1.0-5.0
  "username": "string | null",           # Opcional
  "review_date": "datetime",             # Requerido, fecha de publicación
  "retrieval_date": "datetime",          # Requerido, fecha de extracción
  "relative_date": "string | null",      # Opcional, ej: "hace 3 días"
  "n_review_user": "integer | null",     # Opcional, total reseñas del usuario
  "n_photo_user": "integer | null",      # Opcional, total fotos del usuario
  "url_user": "string | null",           # Opcional, perfil del usuario
  "notified_via_webhook": "boolean",     # Default: false
  "webhook_sent_at": "datetime | null"   # Nullable, fecha de notificación
}
```

### Campos Detallados

#### id_review
- **Tipo**: String
- **Requerido**: Sí
- **Único**: Sí
- **Descripción**: Identificador único de la reseña en Google Maps
- **Ejemplo**: `"ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE"`
- **Nota**: Este ID es generado por Google y se extrae del HTML

#### place_id
- **Tipo**: String (UUID) o null
- **Requerido**: No
- **Descripción**: ID del lugar al que pertenece esta reseña
- **Ejemplo**: `"550e8400-e29b-41d4-a716-446655440000"`
- **Uso**: Vincula la reseña con un lugar registrado

#### client_id
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: ID del cliente (heredado del lugar)
- **Ejemplo**: `"cadena_restaurantes_abc"`
- **Uso**: Permite filtrar reseñas por cliente

#### branch_id
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: ID de la sucursal (heredado del lugar)
- **Ejemplo**: `"sucursal_centro"`
- **Uso**: Permite filtrar reseñas por sucursal

#### caption
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: Texto completo de la reseña
- **Ejemplo**: `"Excelente servicio y comida deliciosa. El personal es muy atento."`
- **Nota**: Puede ser `null` si la reseña solo tiene rating sin texto o si falla la extracción

#### rating
- **Tipo**: Float o null
- **Requerido**: No
- **Rango**: 1.0 - 5.0
- **Descripción**: Calificación en estrellas
- **Ejemplo**: `4.5`
- **Nota**: Puede ser `null` si falla la extracción

#### username
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: Nombre del usuario que publicó la reseña
- **Ejemplo**: `"María García"`
- **Nota**: Puede ser `null` si falla la extracción

#### review_date
- **Tipo**: Datetime (ISO 8601)
- **Requerido**: Sí
- **Descripción**: Fecha y hora en que se publicó la reseña en Google Maps
- **Ejemplo**: `"2025-11-02T18:30:00.000Z"`
- **Nota**: Se intenta extraer la fecha exacta del HTML

#### retrieval_date
- **Tipo**: Datetime (ISO 8601)
- **Requerido**: Sí
- **Descripción**: Fecha y hora en que se extrajo la reseña
- **Ejemplo**: `"2025-11-03T09:00:00.000Z"`
- **Uso**: Permite saber cuándo se capturó la reseña

#### relative_date
- **Tipo**: String o null
- **Requerido**: No
- **Descripción**: Fecha relativa como aparece en Google Maps
- **Ejemplo**: `"hace 3 días"`, `"Hace 1 semana"`, `"Hace 2 meses"`
- **Nota**: Se extrae tal cual del HTML de Google Maps

#### n_review_user
- **Tipo**: Integer o null
- **Requerido**: No
- **Descripción**: Número total de reseñas que ha publicado el usuario
- **Ejemplo**: `42`
- **Uso**: Indica qué tan activo es el revisor

#### n_photo_user
- **Tipo**: Integer o null
- **Requerido**: No
- **Descripción**: Número total de fotos que ha subido el usuario
- **Ejemplo**: `15`
- **Uso**: Indica el nivel de contribución del usuario

#### url_user
- **Tipo**: String (URL) o null
- **Requerido**: No
- **Descripción**: URL del perfil del usuario en Google Maps
- **Ejemplo**: `"https://www.google.com/maps/contrib/123456789012345678901"`
- **Uso**: Permite ver más información del revisor

#### notified_via_webhook
- **Tipo**: Boolean
- **Requerido**: No
- **Default**: `false`
- **Auto-actualizado**: Sí
- **Descripción**: Indica si esta reseña fue notificada vía webhook
- **Valores**: `true` = ya notificada, `false` = pendiente o no aplica

#### webhook_sent_at
- **Tipo**: Datetime (ISO 8601) o null
- **Requerido**: No
- **Auto-actualizado**: Sí
- **Descripción**: Fecha y hora en que se envió la notificación webhook
- **Ejemplo**: `"2025-11-03T09:01:30.000Z"`
- **Valor inicial**: `null`

### Ejemplo JSON Completo

```json
{
  "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "cadena_restaurantes_abc",
  "branch_id": "sucursal_centro",
  "caption": "Excelente servicio y comida deliciosa. El personal es muy atento y el ambiente es acogedor. Definitivamente volveré!",
  "rating": 5.0,
  "username": "María García",
  "review_date": "2025-11-02T18:30:00.000Z",
  "retrieval_date": "2025-11-03T09:00:00.000Z",
  "relative_date": "hace 1 día",
  "n_review_user": 42,
  "n_photo_user": 15,
  "url_user": "https://www.google.com/maps/contrib/987654321098765432109",
  "notified_via_webhook": true,
  "webhook_sent_at": "2025-11-03T09:01:30.000Z"
}
```

### Campos Opcionales

Los siguientes campos son opcionales porque la extracción puede fallar en ciertos casos:

- `caption`: Reseñas que solo tienen rating sin texto
- `rating`: Errores en el scraping
- `username`: Perfiles anónimos o errores de extracción
- `n_review_user`, `n_photo_user`, `url_user`: No siempre disponibles en el HTML

---

## Modelo: ScrapingJob (Trabajo de Scraping)

Representa el estado de un trabajo de scraping asíncrono.

### Estructura Completa

```python
{
  "job_id": "string",                    # Auto-generado, único
  "status": "string",                    # queued | started | finished | failed
  "progress": "string | null",           # Mensaje de progreso
  "error": "string | null",              # Mensaje de error si falla
  "result_available": "boolean",         # Si los resultados están disponibles
  "created_at": "datetime",              # Auto-generado
  "started_at": "datetime | null",       # Auto-actualizado
  "finished_at": "datetime | null"       # Auto-actualizado
}
```

### Estados Posibles

| Estado | Descripción |
|--------|-------------|
| `queued` | En cola, esperando ser procesado |
| `started` | En ejecución actualmente |
| `finished` | Completado exitosamente |
| `failed` | Falló (ver campo `error`) |

### Ejemplo JSON

```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "finished",
  "progress": "Completed: 50/50 reviews extracted",
  "error": null,
  "result_available": true,
  "created_at": "2025-11-03T10:50:00.000Z",
  "started_at": "2025-11-03T10:50:15.000Z",
  "finished_at": "2025-11-03T10:52:30.000Z"
}
```

---

## Modelo: WebhookPayload (Payload de Webhook)

Estructura del payload enviado en las notificaciones webhook.

### Estructura Completa

```python
{
  "event": "string",                     # Tipo de evento (siempre "new_reviews")
  "client_id": "string",                 # ID del cliente
  "branch_id": "string",                 # ID de la sucursal
  "place_id": "string",                  # UUID del lugar
  "place_name": "string | null",         # Nombre del lugar
  "place_url": "string",                 # URL de Google Maps
  "new_reviews_count": "integer",        # Cantidad de nuevas reseñas
  "timestamp": "datetime",               # Fecha y hora del evento
  "reviews": [                           # Array de reseñas nuevas
    {
      /* Objeto Review completo (ver arriba) */
    }
  ]
}
```

### Ejemplo JSON Completo

```json
{
  "event": "new_reviews",
  "client_id": "cadena_restaurantes_abc",
  "branch_id": "sucursal_centro",
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "place_name": "Restaurante ABC - Sucursal Centro",
  "place_url": "https://www.google.com/maps/place/Restaurante+ABC/@40.7128,-74.0060,15z",
  "new_reviews_count": 3,
  "timestamp": "2025-11-03T10:05:00.000Z",
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
      "place_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "cadena_restaurantes_abc",
      "branch_id": "sucursal_centro",
      "caption": "Excelente servicio!",
      "rating": 5.0,
      "username": "Juan Pérez",
      "review_date": "2025-11-02T15:30:00.000Z",
      "retrieval_date": "2025-11-03T10:00:00.000Z",
      "relative_date": "hace 1 día",
      "n_review_user": 25,
      "n_photo_user": 8,
      "url_user": "https://www.google.com/maps/contrib/123456789",
      "notified_via_webhook": false,
      "webhook_sent_at": null
    },
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNhd3ZhZ0RREAE",
      "place_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "cadena_restaurantes_abc",
      "branch_id": "sucursal_centro",
      "caption": "Buena comida pero servicio lento",
      "rating": 3.0,
      "username": "María López",
      "review_date": "2025-11-02T20:15:00.000Z",
      "retrieval_date": "2025-11-03T10:00:00.000Z",
      "relative_date": "hace 1 día",
      "n_review_user": 12,
      "n_photo_user": 3,
      "url_user": "https://www.google.com/maps/contrib/987654321",
      "notified_via_webhook": false,
      "webhook_sent_at": null
    }
  ]
}
```

---

## Índices de MongoDB

Los índices optimizan las consultas a la base de datos.

### Colección: `places`

```javascript
// Índices únicos
{ "place_id": 1 }  // UNIQUE

// Índices simples
{ "client_id": 1 }
{ "branch_id": 1 }
{ "monitoring_enabled": 1 }
{ "last_check": 1 }
{ "created_at": -1 }

// Índices compuestos
{ "client_id": 1, "branch_id": 1 }
{ "url": 1, "client_id": 1, "branch_id": 1 }  // UNIQUE
```

### Colección: `reviews`

```javascript
// Índices únicos
{ "id_review": 1 }  // UNIQUE

// Índices simples
{ "place_id": 1 }
{ "client_id": 1 }
{ "branch_id": 1 }
{ "rating": 1 }
{ "review_date": -1 }
{ "retrieval_date": -1 }
{ "notified_via_webhook": 1 }

// Índices compuestos
{ "client_id": 1, "branch_id": 1 }
{ "place_id": 1, "review_date": -1 }
{ "place_id": 1, "retrieval_date": -1 }
```

**Nota**: `-1` indica orden descendente, `1` indica orden ascendente.

---

## Validaciones

### Validaciones de Place

```python
# URL debe contener google.com/maps
assert "google.com/maps" in url, "URL must be a Google Maps URL"

# webhook_url debe ser HTTP/HTTPS válido
assert webhook_url.startswith(("http://", "https://")), "Invalid webhook URL"

# check_interval_minutes rango
assert 5 <= check_interval_minutes <= 10080, "Interval must be between 5 and 10080 minutes"

# No duplicados
assert not exists(url, client_id, branch_id), "Place already exists"
```

### Validaciones de Review

```python
# id_review debe ser único
assert not exists(id_review), "Review already exists"

# rating rango (si existe)
if rating is not None:
    assert 1.0 <= rating <= 5.0, "Rating must be between 1.0 and 5.0"

# review_date requerido
assert review_date is not None, "Review date is required"
```

### Validaciones de Scraping

```python
# max_reviews rango
assert 1 <= max_reviews <= 1000, "max_reviews must be between 1 and 1000"

# sort_by valores permitidos
assert sort_by in ["newest", "most_relevant", "highest_rating", "lowest_rating"]

# URL válida
assert "google.com/maps" in url, "Invalid Google Maps URL"
```

---

## Ejemplos de Uso

### Crear un Place

```python
place_data = {
    "client_id": "mi_empresa",
    "branch_id": "oficina_principal",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://mi-servidor.com/webhook",
    "name": "Mi Empresa - Oficina Principal",
    "check_interval_minutes": 30,
    "monitoring_enabled": True
}

# POST /api/places/
response = requests.post("http://localhost:8000/api/places/", json=place_data)
place = response.json()
print(place["place_id"])  # 550e8400-e29b-41d4-a716-446655440000
```

### Filtrar Reviews por Rating

```python
# Obtener solo reseñas con rating >= 4
params = {
    "client_id": "mi_empresa",
    "min_rating": 4.0,
    "page_size": 50
}

response = requests.get("http://localhost:8000/api/reviews/", params=params)
data = response.json()

for review in data["reviews"]:
    print(f"{review['username']}: {review['rating']}★")
```

### Procesar Webhook

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_json()

    # Validar tipo de evento
    if payload['event'] != 'new_reviews':
        return {"status": "ignored"}, 200

    # Procesar cada reseña
    for review in payload['reviews']:
        # Guardar en BD propia
        save_to_database(review)

        # Enviar notificación si es negativa
        if review['rating'] and review['rating'] <= 2:
            send_alert(
                f"⚠️ Reseña negativa: {review['rating']}★\n"
                f"Usuario: {review['username']}\n"
                f"Comentario: {review['caption']}"
            )

    return {"status": "success"}, 200
```

---

## Schema TypeScript (para Frontend)

Si estás integrando con un frontend TypeScript/JavaScript:

```typescript
// Place model
interface Place {
  place_id: string;
  client_id: string;
  branch_id: string;
  url: string;
  webhook_url: string;
  name?: string | null;
  monitoring_enabled: boolean;
  check_interval_minutes: number;
  last_check?: string | null;  // ISO 8601
  last_review_count: number;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}

// Review model
interface Review {
  id_review: string;
  place_id?: string | null;
  client_id?: string | null;
  branch_id?: string | null;
  caption?: string | null;
  rating?: number | null;
  username?: string | null;
  review_date: string;  // ISO 8601
  retrieval_date: string;  // ISO 8601
  relative_date?: string | null;
  n_review_user?: number | null;
  n_photo_user?: number | null;
  url_user?: string | null;
  notified_via_webhook: boolean;
  webhook_sent_at?: string | null;  // ISO 8601
}

// Webhook payload model
interface WebhookPayload {
  event: 'new_reviews';
  client_id: string;
  branch_id: string;
  place_id: string;
  place_name?: string | null;
  place_url: string;
  new_reviews_count: number;
  timestamp: string;  // ISO 8601
  reviews: Review[];
}

// Pagination response
interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  reviews: T[];
}
```

---

## Notas Importantes

### Manejo de Campos Null

Varios campos en `Review` son opcionales (`null`) porque:
1. **Reseñas sin texto**: Algunas reseñas solo tienen rating sin comentario
2. **Errores de scraping**: Ocasionalmente la extracción puede fallar para ciertos campos
3. **Cambios en Google Maps**: El HTML puede variar y algunos datos no estar disponibles

**Recomendación**: Siempre validar que los campos existen antes de usarlos:

```python
# ✅ Correcto
if review.get('caption'):
    print(review['caption'])

# ❌ Incorrecto (puede lanzar error)
print(review['caption'].upper())
```

### Timezone

Todas las fechas están en **UTC (Coordinated Universal Time)** con formato ISO 8601:
- Formato: `"2025-11-03T10:30:00.000Z"`
- Sufijo `Z` indica UTC

Para convertir a timezone local (Python):

```python
from datetime import datetime
import pytz

utc_date = datetime.fromisoformat(review['review_date'].replace('Z', '+00:00'))
local_tz = pytz.timezone('America/Mexico_City')
local_date = utc_date.astimezone(local_tz)
```

---

**Última actualización**: 2025-11-03
