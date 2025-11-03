# Guía de Webhooks - Google Maps Reviews Scraper API

## Índice

- [Introducción](#introducción)
- [¿Qué son los Webhooks?](#qué-son-los-webhooks)
- [Configuración](#configuración)
- [Estructura del Payload](#estructura-del-payload)
- [Implementación del Endpoint](#implementación-del-endpoint)
- [Seguridad](#seguridad)
- [Reintentos y Manejo de Errores](#reintentos-y-manejo-de-errores)
- [Pruebas](#pruebas)
- [Ejemplos Completos](#ejemplos-completos)
- [Mejores Prácticas](#mejores-prácticas)
- [Troubleshooting](#troubleshooting)

---

## Introducción

Los webhooks son el mecanismo principal para recibir notificaciones en tiempo real cuando se detectan nuevas reseñas en los lugares que estás monitoreando. En lugar de consultar constantemente la API (polling), el sistema te notifica automáticamente.

### Ventajas

- ✅ **Notificaciones en tiempo real**: Recibe información inmediatamente
- ✅ **Eficiencia**: No necesitas hacer polling constante
- ✅ **Automatización**: Procesa nuevas reseñas automáticamente
- ✅ **Escalabilidad**: Maneja múltiples lugares sin overhead

---

## ¿Qué son los Webhooks?

Un webhook es una URL HTTP en tu servidor que recibe notificaciones POST cuando ocurre un evento (en este caso, nuevas reseñas detectadas).

### Flujo de Trabajo

```
┌─────────────────────┐
│  Sistema Scraper    │
│  (Monitoreo activo) │
└──────────┬──────────┘
           │
           │ 1. Detecta nuevas reseñas
           ▼
┌─────────────────────┐
│  Preparar payload   │
│  con nuevas reseñas │
└──────────┬──────────┘
           │
           │ 2. HTTP POST
           ▼
┌─────────────────────┐
│  TU WEBHOOK URL     │
│  (tu servidor)      │
└──────────┬──────────┘
           │
           │ 3. Procesar datos
           ▼
┌─────────────────────┐
│  - Guardar en BD    │
│  - Notificar equipo │
│  - Análisis         │
│  - etc.             │
└─────────────────────┘
```

---

## Configuración

### Paso 1: Crear Endpoint en tu Servidor

Tu servidor debe exponer una URL pública que acepte solicitudes POST.

**Requisitos**:
- ✅ Accesible públicamente (no localhost para producción)
- ✅ Acepta método POST
- ✅ Content-Type: application/json
- ✅ Retorna status 2xx (200-299) para confirmación

### Paso 2: Registrar la URL en el Place

Al crear o actualizar un lugar, proporciona la URL del webhook:

```bash
curl -X POST "http://localhost:8000/api/places/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "mi_cliente",
    "branch_id": "sucursal_1",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://mi-servidor.com/api/webhooks/google-reviews",
    "monitoring_enabled": true
  }'
```

### Paso 3: Verificar Configuración

Prueba tu webhook:

```bash
curl -X POST "http://localhost:8000/api/monitor/test-webhook/{place_id}"
```

---

## Estructura del Payload

### Payload Completo

Cuando se detectan nuevas reseñas, recibirás un POST con este formato:

```json
{
  "event": "new_reviews",
  "client_id": "mi_cliente",
  "branch_id": "sucursal_1",
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "place_name": "Restaurante ABC - Centro",
  "place_url": "https://www.google.com/maps/place/...",
  "new_reviews_count": 3,
  "timestamp": "2025-11-03T10:05:00.000Z",
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0FnSUNad3VhZkRREAE",
      "place_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "mi_cliente",
      "branch_id": "sucursal_1",
      "caption": "Excelente servicio y comida deliciosa!",
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
      "client_id": "mi_cliente",
      "branch_id": "sucursal_1",
      "caption": "Buena comida pero el servicio fue lento",
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

### Descripción de Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event` | string | Siempre "new_reviews" |
| `client_id` | string | ID del cliente |
| `branch_id` | string | ID de la sucursal |
| `place_id` | string | UUID del lugar |
| `place_name` | string/null | Nombre del lugar |
| `place_url` | string | URL de Google Maps |
| `new_reviews_count` | integer | Cantidad de nuevas reseñas |
| `timestamp` | datetime | Fecha/hora del evento (UTC) |
| `reviews` | array | Array de objetos Review |

---

## Implementación del Endpoint

### Python + Flask

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/api/webhooks/google-reviews', methods=['POST'])
def handle_google_reviews():
    """
    Endpoint para recibir notificaciones de nuevas reseñas
    """
    try:
        # 1. Parsear JSON
        payload = request.get_json()

        if not payload:
            return jsonify({"error": "Invalid JSON"}), 400

        # 2. Validar tipo de evento
        if payload.get('event') != 'new_reviews':
            logging.info(f"Ignored event: {payload.get('event')}")
            return jsonify({"status": "ignored"}), 200

        # 3. Extraer información
        client_id = payload['client_id']
        branch_id = payload['branch_id']
        place_name = payload.get('place_name', 'Unknown')
        new_reviews_count = payload['new_reviews_count']
        reviews = payload['reviews']

        logging.info(
            f"Received {new_reviews_count} new reviews for "
            f"{place_name} ({client_id}/{branch_id})"
        )

        # 4. Procesar cada reseña
        for review in reviews:
            process_review(review, client_id, branch_id)

        # 5. Retornar confirmación
        return jsonify({
            "status": "success",
            "processed": new_reviews_count
        }), 200

    except KeyError as e:
        logging.error(f"Missing field: {e}")
        return jsonify({"error": f"Missing field: {e}"}), 400

    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal error"}), 500


def process_review(review, client_id, branch_id):
    """
    Procesar una reseña individual
    """
    # Guardar en base de datos
    save_to_database(review)

    # Enviar notificación si es negativa
    if review.get('rating') and review['rating'] <= 2:
        send_alert_for_negative_review(review, client_id, branch_id)

    # Enviar notificación si es positiva
    elif review.get('rating') and review['rating'] >= 4:
        send_positive_review_notification(review, client_id, branch_id)

    # Actualizar métricas en tiempo real
    update_metrics(client_id, branch_id, review)


def save_to_database(review):
    """Guardar reseña en tu base de datos"""
    # Implementar según tu BD
    pass


def send_alert_for_negative_review(review, client_id, branch_id):
    """Alertar al equipo sobre reseña negativa"""
    message = (
        f"⚠️ Reseña Negativa Detectada\n\n"
        f"Cliente: {client_id}\n"
        f"Sucursal: {branch_id}\n"
        f"Rating: {review['rating']}★\n"
        f"Usuario: {review.get('username', 'Anónimo')}\n"
        f"Fecha: {review['review_date']}\n\n"
        f"Comentario:\n{review.get('caption', 'Sin comentario')}\n\n"
        f"Ver en Google Maps: {review.get('url_user', 'N/A')}"
    )

    # Enviar por email, SMS, Slack, etc.
    send_notification(message)


def send_positive_review_notification(review, client_id, branch_id):
    """Notificar reseña positiva"""
    # Implementar según necesidades
    pass


def update_metrics(client_id, branch_id, review):
    """Actualizar métricas en dashboard"""
    # Implementar según tu sistema de métricas
    pass


def send_notification(message):
    """Enviar notificación (email, SMS, Slack, etc.)"""
    # Implementar según tu sistema de notificaciones
    pass


if __name__ == '__main__':
    # Producción: usar gunicorn o similar
    app.run(host='0.0.0.0', port=5000)
```

### Node.js + Express

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/webhooks/google-reviews', async (req, res) => {
  try {
    const payload = req.body;

    // Validar evento
    if (payload.event !== 'new_reviews') {
      console.log(`Ignored event: ${payload.event}`);
      return res.json({ status: 'ignored' });
    }

    const {
      client_id,
      branch_id,
      place_name,
      new_reviews_count,
      reviews
    } = payload;

    console.log(
      `Received ${new_reviews_count} new reviews for ` +
      `${place_name} (${client_id}/${branch_id})`
    );

    // Procesar reseñas
    for (const review of reviews) {
      await processReview(review, client_id, branch_id);
    }

    res.json({
      status: 'success',
      processed: new_reviews_count
    });

  } catch (error) {
    console.error('Error processing webhook:', error);
    res.status(500).json({ error: 'Internal error' });
  }
});

async function processReview(review, clientId, branchId) {
  // Guardar en BD
  await saveToDatabase(review);

  // Alertar si es negativa
  if (review.rating && review.rating <= 2) {
    await sendAlertForNegativeReview(review, clientId, branchId);
  }

  // Actualizar métricas
  await updateMetrics(clientId, branchId, review);
}

async function saveToDatabase(review) {
  // Implementar según tu BD
}

async function sendAlertForNegativeReview(review, clientId, branchId) {
  const message = `
⚠️ Reseña Negativa Detectada

Cliente: ${clientId}
Sucursal: ${branchId}
Rating: ${review.rating}★
Usuario: ${review.username || 'Anónimo'}
Fecha: ${review.review_date}

Comentario:
${review.caption || 'Sin comentario'}
  `;

  await sendNotification(message);
}

async function updateMetrics(clientId, branchId, review) {
  // Implementar según tu sistema
}

async function sendNotification(message) {
  // Implementar (email, SMS, Slack, etc.)
}

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Webhook server listening on port ${PORT}`);
});
```

### PHP

```php
<?php

// webhook.php

// Configurar logging
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', '/var/log/webhook_errors.log');

// Leer JSON del body
$json = file_get_contents('php://input');
$payload = json_decode($json, true);

// Validar JSON
if (!$payload) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Validar evento
if (!isset($payload['event']) || $payload['event'] !== 'new_reviews') {
    http_response_code(200);
    echo json_encode(['status' => 'ignored']);
    exit;
}

try {
    $clientId = $payload['client_id'];
    $branchId = $payload['branch_id'];
    $placeName = $payload['place_name'] ?? 'Unknown';
    $newReviewsCount = $payload['new_reviews_count'];
    $reviews = $payload['reviews'];

    error_log("Received $newReviewsCount new reviews for $placeName");

    // Procesar cada reseña
    foreach ($reviews as $review) {
        processReview($review, $clientId, $branchId);
    }

    // Retornar éxito
    http_response_code(200);
    echo json_encode([
        'status' => 'success',
        'processed' => $newReviewsCount
    ]);

} catch (Exception $e) {
    error_log("Error processing webhook: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal error']);
}

function processReview($review, $clientId, $branchId) {
    // Guardar en base de datos
    saveToDatabase($review);

    // Alertar si es negativa
    if (isset($review['rating']) && $review['rating'] <= 2) {
        sendAlertForNegativeReview($review, $clientId, $branchId);
    }

    // Actualizar métricas
    updateMetrics($clientId, $branchId, $review);
}

function saveToDatabase($review) {
    // Implementar según tu BD
    // Ejemplo: MySQL/PostgreSQL
    /*
    $pdo = new PDO('mysql:host=localhost;dbname=mydb', 'user', 'pass');
    $stmt = $pdo->prepare(
        "INSERT INTO reviews (id_review, caption, rating, username, review_date)
         VALUES (?, ?, ?, ?, ?)"
    );
    $stmt->execute([
        $review['id_review'],
        $review['caption'],
        $review['rating'],
        $review['username'],
        $review['review_date']
    ]);
    */
}

function sendAlertForNegativeReview($review, $clientId, $branchId) {
    $message = sprintf(
        "⚠️ Reseña Negativa Detectada\n\n" .
        "Cliente: %s\n" .
        "Sucursal: %s\n" .
        "Rating: %.1f★\n" .
        "Usuario: %s\n" .
        "Comentario: %s",
        $clientId,
        $branchId,
        $review['rating'] ?? 0,
        $review['username'] ?? 'Anónimo',
        $review['caption'] ?? 'Sin comentario'
    );

    sendNotification($message);
}

function updateMetrics($clientId, $branchId, $review) {
    // Implementar
}

function sendNotification($message) {
    // Enviar email, SMS, etc.
    // Ejemplo: email simple
    // mail('admin@example.com', 'Nueva Reseña Negativa', $message);
}
?>
```

---

## Seguridad

### 1. Validación de IP (Opcional)

Puedes restringir qué IPs pueden llamar tu webhook:

```python
ALLOWED_IPS = ['123.45.67.89', '10.0.0.0/8']  # IP de tu servidor scraper

@app.before_request
def limit_remote_addr():
    if request.endpoint == 'handle_google_reviews':
        if request.remote_addr not in ALLOWED_IPS:
            abort(403)
```

### 2. Firma HMAC (Recomendado para Producción)

Agregar firma criptográfica para verificar autenticidad:

**Concepto**:
1. Servidor scraper firma el payload con clave secreta
2. Envía firma en header `X-Webhook-Signature`
3. Tu servidor valida la firma

```python
import hmac
import hashlib

SECRET_KEY = 'tu-clave-secreta-compartida'

@app.route('/api/webhooks/google-reviews', methods=['POST'])
def handle_google_reviews():
    # Obtener firma del header
    signature = request.headers.get('X-Webhook-Signature')

    if not signature:
        return jsonify({"error": "Missing signature"}), 401

    # Calcular firma esperada
    body = request.get_data()
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Comparar firmas
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Continuar procesamiento...
```

> **Nota**: Actualmente el sistema NO implementa firma HMAC. Es una mejora recomendada para producción.

### 3. HTTPS Obligatorio

En producción, usa **siempre HTTPS** para tu webhook:

```bash
# ✅ Correcto
webhook_url: "https://mi-servidor.com/webhook"

# ❌ Incorrecto (inseguro)
webhook_url: "http://mi-servidor.com/webhook"
```

### 4. Rate Limiting

Protege tu endpoint de abuso:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/webhooks/google-reviews', methods=['POST'])
@limiter.limit("30 per minute")
def handle_google_reviews():
    # ...
```

---

## Reintentos y Manejo de Errores

### Comportamiento de Reintentos

El sistema reintenta automáticamente el envío del webhook si falla:

| Configuración | Valor |
|--------------|-------|
| **Timeout** | 10 segundos |
| **Reintentos máximos** | 3 |
| **Delay entre reintentos** | 5 segundos |
| **Códigos de éxito** | 200-299 |

### Configuración (Variables de Entorno)

```bash
# En el servidor scraper (.env)
WEBHOOK_TIMEOUT=10          # segundos
WEBHOOK_MAX_RETRIES=3       # número de reintentos
WEBHOOK_RETRY_DELAY=5       # segundos entre reintentos
```

### Ejemplo de Secuencia de Reintentos

```
Intento 1: POST /webhook → Timeout (10s)
  ↓ Esperar 5s
Intento 2: POST /webhook → 500 Error
  ↓ Esperar 5s
Intento 3: POST /webhook → 200 OK ✓
```

### Tu Endpoint Debe

- ✅ **Responder rápido**: Idealmente < 2 segundos
- ✅ **Retornar 200-299**: Para confirmar recepción
- ✅ **Ser idempotente**: Manejar duplicados si hay reintentos
- ✅ **Procesar async**: No bloquear la respuesta

### Procesamiento Asíncrono Recomendado

```python
from flask import Flask
from rq import Queue
from redis import Redis

app = Flask(__name__)
redis_conn = Redis()
task_queue = Queue(connection=redis_conn)

@app.route('/api/webhooks/google-reviews', methods=['POST'])
def handle_google_reviews():
    payload = request.get_json()

    # Encolar procesamiento
    task_queue.enqueue(
        process_webhook_async,
        payload
    )

    # Retornar inmediatamente
    return jsonify({"status": "queued"}), 200


def process_webhook_async(payload):
    """
    Procesar webhook en background
    """
    for review in payload['reviews']:
        process_review(review)
```

---

## Pruebas

### Prueba Manual con cURL

```bash
# Enviar payload de prueba a tu webhook
curl -X POST "https://tu-servidor.com/api/webhooks/google-reviews" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "new_reviews",
    "client_id": "test_client",
    "branch_id": "test_branch",
    "place_id": "test-place-id",
    "place_name": "Lugar de Prueba",
    "place_url": "https://www.google.com/maps/place/...",
    "new_reviews_count": 1,
    "timestamp": "2025-11-03T10:00:00.000Z",
    "reviews": [
      {
        "id_review": "test-review-123",
        "caption": "Reseña de prueba",
        "rating": 5.0,
        "username": "Usuario Test",
        "review_date": "2025-11-03T09:00:00.000Z",
        "retrieval_date": "2025-11-03T10:00:00.000Z"
      }
    ]
  }'
```

### Prueba desde la API

```bash
# Probar webhook de un lugar registrado
curl -X POST "http://localhost:8000/api/monitor/test-webhook/{place_id}"
```

Respuesta esperada:

```json
{
  "place_id": "550e8400-e29b-41d4-a716-446655440000",
  "webhook_url": "https://tu-servidor.com/webhook",
  "test_result": {
    "success": true,
    "status_code": 200,
    "response_time_seconds": 0.234,
    "response_body": "{\"status\":\"success\"}",
    "error": null
  }
}
```

### Pruebas Unitarias (Python)

```python
import unittest
import json
from your_app import app

class WebhookTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_webhook_receives_new_reviews(self):
        payload = {
            "event": "new_reviews",
            "client_id": "test",
            "branch_id": "test",
            "place_id": "123",
            "place_name": "Test Place",
            "place_url": "https://maps.google.com/...",
            "new_reviews_count": 1,
            "timestamp": "2025-11-03T10:00:00Z",
            "reviews": [
                {
                    "id_review": "test-123",
                    "rating": 5.0,
                    "caption": "Great!",
                    "username": "Test User",
                    "review_date": "2025-11-03T09:00:00Z",
                    "retrieval_date": "2025-11-03T10:00:00Z"
                }
            ]
        }

        response = self.app.post(
            '/api/webhooks/google-reviews',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')

    def test_webhook_rejects_invalid_event(self):
        payload = {"event": "invalid_event"}

        response = self.app.post(
            '/api/webhooks/google-reviews',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ignored')
```

---

## Ejemplos Completos

### Integración con Slack

```python
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def send_slack_notification(review, client_id, branch_id):
    """
    Enviar notificación a Slack cuando hay nueva reseña
    """
    # Determinar emoji según rating
    emoji = {
        5: ":star:",
        4: ":sparkles:",
        3: ":neutral_face:",
        2: ":warning:",
        1: ":x:"
    }.get(int(review.get('rating', 3)), ":question:")

    # Construir mensaje
    message = {
        "text": f"{emoji} Nueva reseña detectada",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Nueva Reseña - {review.get('rating', 'N/A')}★"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Cliente:*\n{client_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sucursal:*\n{branch_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Usuario:*\n{review.get('username', 'Anónimo')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Fecha:*\n{review.get('relative_date', 'N/A')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Comentario:*\n{review.get('caption', '_Sin comentario_')}"
                }
            }
        ]
    }

    # Si hay URL del usuario, agregar botón
    if review.get('url_user'):
        message["blocks"].append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Ver en Google Maps"
                    },
                    "url": review['url_user']
                }
            ]
        })

    # Enviar a Slack
    response = requests.post(SLACK_WEBHOOK_URL, json=message)
    response.raise_for_status()
```

### Integración con Email (SendGrid)

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = 'tu-api-key'
FROM_EMAIL = 'notificaciones@tu-empresa.com'
TO_EMAIL = 'manager@tu-empresa.com'

def send_email_notification(review, client_id, branch_id, place_name):
    """
    Enviar email cuando hay reseña negativa
    """
    subject = f"⚠️ Reseña {review['rating']}★ - {place_name}"

    html_content = f"""
    <html>
      <body>
        <h2>Nueva Reseña Detectada</h2>

        <table style="border-collapse: collapse; width: 100%;">
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Lugar:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{place_name}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Cliente:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{client_id}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Sucursal:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{branch_id}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Rating:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{'⭐' * int(review['rating'])}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Usuario:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{review.get('username', 'Anónimo')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Fecha:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{review['review_date']}</td>
          </tr>
        </table>

        <h3>Comentario:</h3>
        <p style="background: #f5f5f5; padding: 15px; border-left: 4px solid #333;">
          {review.get('caption', '<em>Sin comentario</em>')}
        </p>

        <p>
          <a href="{review.get('url_user', '#')}" style="
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            display: inline-block;
            border-radius: 4px;
          ">Ver en Google Maps</a>
        </p>
      </body>
    </html>
    """

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
```

---

## Mejores Prácticas

### 1. Idempotencia

Tu webhook puede recibir el mismo payload múltiples veces (por reintentos). Implementa idempotencia:

```python
def process_review(review):
    # Verificar si ya existe
    if review_exists(review['id_review']):
        print(f"Review {review['id_review']} already processed, skipping")
        return

    # Procesar solo si es nueva
    save_to_database(review)
```

### 2. Logging Completo

Registra todo para debugging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    logging.info(f"Webhook received from {request.remote_addr}")
    logging.info(f"Payload: {request.get_json()}")

    try:
        # Procesar...
        logging.info("Webhook processed successfully")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
```

### 3. Monitoreo y Alertas

Monitorea la salud de tu webhook:

```python
import time
from prometheus_client import Counter, Histogram

webhook_requests_total = Counter(
    'webhook_requests_total',
    'Total webhook requests',
    ['status']
)

webhook_processing_duration = Histogram(
    'webhook_processing_duration_seconds',
    'Webhook processing duration'
)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    start_time = time.time()

    try:
        # Procesar...
        webhook_requests_total.labels(status='success').inc()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        webhook_requests_total.labels(status='error').inc()
        return jsonify({"error": str(e)}), 500

    finally:
        duration = time.time() - start_time
        webhook_processing_duration.observe(duration)
```

### 4. Validación de Datos

Valida siempre los datos recibidos:

```python
def validate_webhook_payload(payload):
    """
    Validar estructura del payload
    """
    required_fields = [
        'event', 'client_id', 'branch_id', 'place_id',
        'new_reviews_count', 'timestamp', 'reviews'
    ]

    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(payload['reviews'], list):
        raise ValueError("reviews must be an array")

    if payload['new_reviews_count'] != len(payload['reviews']):
        raise ValueError("new_reviews_count doesn't match reviews array length")

    return True
```

---

## Troubleshooting

### Problema: No recibo webhooks

**Verificar**:
1. ¿El webhook_url es accesible públicamente?
   ```bash
   curl https://tu-servidor.com/webhook
   ```

2. ¿El monitoreo está activo?
   ```bash
   curl http://localhost:8000/api/monitor/status
   ```

3. ¿Hay nuevas reseñas detectadas?
   ```bash
   # Ver logs del scraper
   docker-compose logs -f worker
   ```

4. Probar manualmente:
   ```bash
   curl -X POST "http://localhost:8000/api/monitor/test-webhook/{place_id}"
   ```

### Problema: Webhook retorna error

**Solución**:
- Tu endpoint debe retornar status 200-299
- Verificar logs de tu servidor
- Probar con cURL para debug

### Problema: Webhooks duplicados

**Causa**: Reintentos del sistema

**Solución**: Implementar idempotencia verificando `id_review` antes de procesar

### Problema: Timeout

**Causa**: Tu endpoint demora > 10 segundos

**Solución**:
- Procesar async (encolando tareas)
- Retornar 200 inmediatamente
- Optimizar consultas a BD

---

**Última actualización**: 2025-11-03
