# Guía de Integración - Google Maps Reviews Scraper API

## Índice

- [Introducción](#introducción)
- [Casos de Uso Principales](#casos-de-uso-principales)
- [Integración Básica](#integración-básica)
- [Ejemplos por Lenguaje](#ejemplos-por-lenguaje)
- [Flujos de Trabajo Completos](#flujos-de-trabajo-completos)
- [Manejo de Webhooks](#manejo-de-webhooks)
- [Mejores Prácticas](#mejores-prácticas)
- [Troubleshooting](#troubleshooting)

---

## Introducción

Esta guía te ayudará a integrar la API de Google Maps Reviews Scraper en tu sistema, ya sea un CRM, dashboard de analytics, sistema de notificaciones, o cualquier aplicación que necesite gestionar reseñas de Google Maps.

### Prerrequisitos

- API ejecutándose en `http://localhost:8000` (o tu servidor)
- Conocimientos básicos de HTTP/REST APIs
- Un servidor público para recibir webhooks (opcional)

---

## Casos de Uso Principales

### 1. Monitoreo Continuo de Reseñas

**Escenario**: Tienes múltiples restaurantes/sucursales y quieres recibir notificaciones automáticas cuando lleguen nuevas reseñas.

**Flujo**:
1. Registrar cada lugar con su webhook
2. El sistema monitorea automáticamente cada X minutos
3. Cuando hay nuevas reseñas, recibes un POST en tu webhook
4. Tu sistema procesa las reseñas (notificar, almacenar, etc.)

### 2. Extracción Bajo Demanda

**Escenario**: Un usuario de tu sistema quiere ver las reseñas de un lugar específico ahora mismo.

**Flujo**:
1. Usuario solicita ver reseñas
2. Tu sistema hace POST a `/api/scraping/start`
3. Consultas el estado periódicamente
4. Cuando termina, obtienes y muestras las reseñas

### 3. Dashboard de Analytics

**Escenario**: Quieres mostrar estadísticas y gráficos de reseñas.

**Flujo**:
1. Consultas `/api/reviews/` con filtros
2. Procesas los datos (promedios, tendencias, etc.)
3. Visualizas en gráficos/tablas

---

## Integración Básica

### Paso 1: Verificar Conectividad

```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true,
  "error": null
}
```

### Paso 2: Registrar tu Primer Lugar

```bash
curl -X POST "http://localhost:8000/api/places/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "mi_cliente",
    "branch_id": "sucursal_1",
    "url": "https://www.google.com/maps/place/...",
    "webhook_url": "https://mi-servidor.com/webhook",
    "name": "Mi Primer Lugar",
    "monitoring_enabled": true
  }'
```

### Paso 3: Verificar que el Lugar fue Registrado

```bash
curl "http://localhost:8000/api/places/?client_id=mi_cliente"
```

---

## Ejemplos por Lenguaje

### Python

#### Instalación de Dependencias

```bash
pip install requests
```

#### Ejemplo Completo

```python
import requests
import time
from typing import Dict, List, Optional

class GoogleMapsReviewsClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict:
        """Verificar estado de la API"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def register_place(
        self,
        client_id: str,
        branch_id: str,
        url: str,
        webhook_url: str,
        name: Optional[str] = None,
        check_interval_minutes: int = 60,
        monitoring_enabled: bool = True
    ) -> Dict:
        """Registrar un nuevo lugar"""
        payload = {
            "client_id": client_id,
            "branch_id": branch_id,
            "url": url,
            "webhook_url": webhook_url,
            "name": name,
            "check_interval_minutes": check_interval_minutes,
            "monitoring_enabled": monitoring_enabled
        }

        response = self.session.post(
            f"{self.base_url}/api/places/",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_places(
        self,
        client_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        monitoring_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Listar lugares con filtros"""
        params = {
            "skip": skip,
            "limit": limit
        }

        if client_id:
            params["client_id"] = client_id
        if branch_id:
            params["branch_id"] = branch_id
        if monitoring_enabled is not None:
            params["monitoring_enabled"] = monitoring_enabled

        response = self.session.get(
            f"{self.base_url}/api/places/",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def start_scraping(
        self,
        url: str,
        max_reviews: int = 100,
        sort_by: str = "newest",
        client_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict:
        """Iniciar scraping de reseñas"""
        payload = {
            "url": url,
            "max_reviews": max_reviews,
            "sort_by": sort_by,
            "save_to_db": save_to_db
        }

        if client_id:
            payload["client_id"] = client_id
        if branch_id:
            payload["branch_id"] = branch_id

        response = self.session.post(
            f"{self.base_url}/api/scraping/start",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_scraping_status(self, job_id: str) -> Dict:
        """Consultar estado de un trabajo"""
        response = self.session.get(
            f"{self.base_url}/api/scraping/status/{job_id}"
        )
        response.raise_for_status()
        return response.json()

    def get_scraping_result(self, job_id: str) -> Dict:
        """Obtener resultados de un trabajo"""
        response = self.session.get(
            f"{self.base_url}/api/scraping/result/{job_id}"
        )
        response.raise_for_status()
        return response.json()

    def wait_for_scraping(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict:
        """
        Esperar a que termine un trabajo de scraping

        Args:
            job_id: ID del trabajo
            timeout: Tiempo máximo de espera en segundos
            poll_interval: Intervalo entre consultas en segundos

        Returns:
            Resultados del scraping

        Raises:
            TimeoutError: Si excede el timeout
            Exception: Si el trabajo falla
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Scraping job {job_id} exceeded timeout of {timeout}s"
                )

            status = self.get_scraping_status(job_id)

            if status["status"] == "finished":
                return self.get_scraping_result(job_id)

            if status["status"] == "failed":
                raise Exception(
                    f"Scraping job {job_id} failed: {status.get('error')}"
                )

            time.sleep(poll_interval)

    def get_reviews(
        self,
        page: int = 1,
        page_size: int = 100,
        place_id: Optional[str] = None,
        client_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort_by: str = "review_date",
        sort_order: str = "desc"
    ) -> Dict:
        """Consultar reseñas con filtros"""
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order
        }

        if place_id:
            params["place_id"] = place_id
        if client_id:
            params["client_id"] = client_id
        if branch_id:
            params["branch_id"] = branch_id
        if min_rating:
            params["min_rating"] = min_rating
        if max_rating:
            params["max_rating"] = max_rating

        response = self.session.get(
            f"{self.base_url}/api/reviews/",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_place_stats(self, place_id: str) -> Dict:
        """Obtener estadísticas de un lugar"""
        response = self.session.get(
            f"{self.base_url}/api/places/{place_id}/stats"
        )
        response.raise_for_status()
        return response.json()


# Ejemplo de uso
if __name__ == "__main__":
    client = GoogleMapsReviewsClient()

    # 1. Verificar salud
    health = client.health_check()
    print(f"API Status: {health['status']}")

    # 2. Registrar lugar
    place = client.register_place(
        client_id="restaurant_xyz",
        branch_id="downtown",
        url="https://www.google.com/maps/place/...",
        webhook_url="https://mi-servidor.com/webhook",
        name="Restaurante XYZ - Centro"
    )
    print(f"Place registered: {place['place_id']}")

    # 3. Iniciar scraping
    job = client.start_scraping(
        url=place["url"],
        max_reviews=50,
        client_id="restaurant_xyz",
        branch_id="downtown"
    )
    print(f"Scraping started: {job['job_id']}")

    # 4. Esperar resultados
    try:
        result = client.wait_for_scraping(job["job_id"])
        print(f"Scraping completed: {result['reviews_count']} reviews")

        # Mostrar primeras 5 reseñas
        for review in result["reviews"][:5]:
            print(f"- {review['username']}: {review['rating']}★ - {review['caption'][:50]}...")

    except TimeoutError as e:
        print(f"Error: {e}")

    # 5. Consultar estadísticas
    stats = client.get_place_stats(place["place_id"])
    print(f"\nEstadísticas:")
    print(f"- Total reviews: {stats['total_reviews']}")
    print(f"- Average rating: {stats['average_rating']}")
```

---

### JavaScript/Node.js

#### Instalación de Dependencias

```bash
npm install axios
```

#### Ejemplo Completo

```javascript
const axios = require('axios');

class GoogleMapsReviewsClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL: baseURL,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async registerPlace({
    clientId,
    branchId,
    url,
    webhookUrl,
    name = null,
    checkIntervalMinutes = 60,
    monitoringEnabled = true
  }) {
    const response = await this.client.post('/api/places/', {
      client_id: clientId,
      branch_id: branchId,
      url: url,
      webhook_url: webhookUrl,
      name: name,
      check_interval_minutes: checkIntervalMinutes,
      monitoring_enabled: monitoringEnabled
    });
    return response.data;
  }

  async getPlaces({ clientId, branchId, monitoringEnabled, skip = 0, limit = 100 } = {}) {
    const params = { skip, limit };
    if (clientId) params.client_id = clientId;
    if (branchId) params.branch_id = branchId;
    if (monitoringEnabled !== undefined) params.monitoring_enabled = monitoringEnabled;

    const response = await this.client.get('/api/places/', { params });
    return response.data;
  }

  async startScraping({
    url,
    maxReviews = 100,
    sortBy = 'newest',
    clientId = null,
    branchId = null,
    saveToDB = true
  }) {
    const payload = {
      url,
      max_reviews: maxReviews,
      sort_by: sortBy,
      save_to_db: saveToDB
    };

    if (clientId) payload.client_id = clientId;
    if (branchId) payload.branch_id = branchId;

    const response = await this.client.post('/api/scraping/start', payload);
    return response.data;
  }

  async getScrapingStatus(jobId) {
    const response = await this.client.get(`/api/scraping/status/${jobId}`);
    return response.data;
  }

  async getScrapingResult(jobId) {
    const response = await this.client.get(`/api/scraping/result/${jobId}`);
    return response.data;
  }

  async waitForScraping(jobId, timeout = 300000, pollInterval = 5000) {
    const startTime = Date.now();

    while (true) {
      const elapsed = Date.now() - startTime;
      if (elapsed > timeout) {
        throw new Error(`Scraping job ${jobId} exceeded timeout of ${timeout}ms`);
      }

      const status = await this.getScrapingStatus(jobId);

      if (status.status === 'finished') {
        return await this.getScrapingResult(jobId);
      }

      if (status.status === 'failed') {
        throw new Error(`Scraping job ${jobId} failed: ${status.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }

  async getReviews({
    page = 1,
    pageSize = 100,
    placeId,
    clientId,
    branchId,
    minRating,
    maxRating,
    sortBy = 'review_date',
    sortOrder = 'desc'
  } = {}) {
    const params = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder
    };

    if (placeId) params.place_id = placeId;
    if (clientId) params.client_id = clientId;
    if (branchId) params.branch_id = branchId;
    if (minRating) params.min_rating = minRating;
    if (maxRating) params.max_rating = maxRating;

    const response = await this.client.get('/api/reviews/', { params });
    return response.data;
  }

  async getPlaceStats(placeId) {
    const response = await this.client.get(`/api/places/${placeId}/stats`);
    return response.data;
  }
}

// Ejemplo de uso
(async () => {
  const client = new GoogleMapsReviewsClient();

  try {
    // 1. Verificar salud
    const health = await client.healthCheck();
    console.log(`API Status: ${health.status}`);

    // 2. Registrar lugar
    const place = await client.registerPlace({
      clientId: 'restaurant_xyz',
      branchId: 'downtown',
      url: 'https://www.google.com/maps/place/...',
      webhookUrl: 'https://mi-servidor.com/webhook',
      name: 'Restaurante XYZ - Centro'
    });
    console.log(`Place registered: ${place.place_id}`);

    // 3. Iniciar scraping
    const job = await client.startScraping({
      url: place.url,
      maxReviews: 50,
      clientId: 'restaurant_xyz',
      branchId: 'downtown'
    });
    console.log(`Scraping started: ${job.job_id}`);

    // 4. Esperar resultados
    const result = await client.waitForScraping(job.job_id);
    console.log(`Scraping completed: ${result.reviews_count} reviews`);

    // Mostrar primeras 5 reseñas
    result.reviews.slice(0, 5).forEach(review => {
      console.log(`- ${review.username}: ${review.rating}★ - ${review.caption.substring(0, 50)}...`);
    });

    // 5. Consultar estadísticas
    const stats = await client.getPlaceStats(place.place_id);
    console.log('\nEstadísticas:');
    console.log(`- Total reviews: ${stats.total_reviews}`);
    console.log(`- Average rating: ${stats.average_rating}`);

  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

---

### PHP

```php
<?php

class GoogleMapsReviewsClient {
    private $baseUrl;

    public function __construct($baseUrl = 'http://localhost:8000') {
        $this->baseUrl = $baseUrl;
    }

    private function request($method, $endpoint, $data = null) {
        $url = $this->baseUrl . $endpoint;

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);

        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Content-Length: ' . strlen(json_encode($data))
            ]);
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode >= 400) {
            throw new Exception("HTTP Error $httpCode: $response");
        }

        return json_decode($response, true);
    }

    public function healthCheck() {
        return $this->request('GET', '/health');
    }

    public function registerPlace($clientId, $branchId, $url, $webhookUrl, $name = null) {
        $data = [
            'client_id' => $clientId,
            'branch_id' => $branchId,
            'url' => $url,
            'webhook_url' => $webhookUrl,
            'name' => $name,
            'monitoring_enabled' => true
        ];

        return $this->request('POST', '/api/places/', $data);
    }

    public function startScraping($url, $maxReviews = 100, $clientId = null, $branchId = null) {
        $data = [
            'url' => $url,
            'max_reviews' => $maxReviews,
            'sort_by' => 'newest',
            'save_to_db' => true
        ];

        if ($clientId) $data['client_id'] = $clientId;
        if ($branchId) $data['branch_id'] = $branchId;

        return $this->request('POST', '/api/scraping/start', $data);
    }

    public function getScrapingStatus($jobId) {
        return $this->request('GET', "/api/scraping/status/$jobId");
    }

    public function getScrapingResult($jobId) {
        return $this->request('GET', "/api/scraping/result/$jobId");
    }

    public function waitForScraping($jobId, $timeout = 300, $pollInterval = 5) {
        $startTime = time();

        while (true) {
            $elapsed = time() - $startTime;
            if ($elapsed > $timeout) {
                throw new Exception("Scraping job $jobId exceeded timeout");
            }

            $status = $this->getScrapingStatus($jobId);

            if ($status['status'] === 'finished') {
                return $this->getScrapingResult($jobId);
            }

            if ($status['status'] === 'failed') {
                throw new Exception("Scraping job failed: " . $status['error']);
            }

            sleep($pollInterval);
        }
    }

    public function getReviews($params = []) {
        $queryString = http_build_query($params);
        return $this->request('GET', '/api/reviews/?' . $queryString);
    }
}

// Ejemplo de uso
$client = new GoogleMapsReviewsClient();

try {
    // Verificar salud
    $health = $client->healthCheck();
    echo "API Status: " . $health['status'] . "\n";

    // Registrar lugar
    $place = $client->registerPlace(
        'restaurant_xyz',
        'downtown',
        'https://www.google.com/maps/place/...',
        'https://mi-servidor.com/webhook',
        'Restaurante XYZ - Centro'
    );
    echo "Place registered: " . $place['place_id'] . "\n";

    // Iniciar scraping
    $job = $client->startScraping($place['url'], 50, 'restaurant_xyz', 'downtown');
    echo "Scraping started: " . $job['job_id'] . "\n";

    // Esperar resultados
    $result = $client->waitForScraping($job['job_id']);
    echo "Scraping completed: " . $result['reviews_count'] . " reviews\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

---

## Flujos de Trabajo Completos

### Flujo 1: Monitoreo Automático con Webhooks

```python
# 1. Registrar lugares para monitoreo
places_to_monitor = [
    {
        "client_id": "cadena_restaurantes",
        "branch_id": "sucursal_1",
        "url": "https://www.google.com/maps/place/...",
        "webhook_url": "https://mi-crm.com/webhooks/reviews",
        "name": "Sucursal Centro"
    },
    {
        "client_id": "cadena_restaurantes",
        "branch_id": "sucursal_2",
        "url": "https://www.google.com/maps/place/...",
        "webhook_url": "https://mi-crm.com/webhooks/reviews",
        "name": "Sucursal Norte"
    }
]

client = GoogleMapsReviewsClient()

for place_data in places_to_monitor:
    place = client.register_place(**place_data)
    print(f"✓ Registrado: {place['name']} - {place['place_id']}")

# 2. El sistema automáticamente monitoreará cada lugar
# 3. Cuando haya nuevas reseñas, recibirás un POST en tu webhook
# 4. Implementa un endpoint para recibir webhooks (ver sección Manejo de Webhooks)
```

### Flujo 2: Extracción On-Demand con Polling

```python
import time

def extract_reviews_sync(client, url, max_reviews=100):
    """
    Extrae reseñas de forma síncrona esperando el resultado
    """
    print(f"Iniciando extracción de {max_reviews} reseñas...")

    # Iniciar scraping
    job = client.start_scraping(url=url, max_reviews=max_reviews)
    job_id = job['job_id']
    print(f"Job ID: {job_id}")

    # Polling del estado
    while True:
        status = client.get_scraping_status(job_id)
        print(f"Estado: {status['status']} - {status.get('progress', '')}")

        if status['status'] == 'finished':
            result = client.get_scraping_result(job_id)
            print(f"✓ Completado: {result['reviews_count']} reseñas extraídas")
            return result['reviews']

        if status['status'] == 'failed':
            raise Exception(f"Error: {status.get('error')}")

        time.sleep(5)  # Esperar 5 segundos antes de consultar de nuevo

# Uso
client = GoogleMapsReviewsClient()
reviews = extract_reviews_sync(
    client,
    "https://www.google.com/maps/place/...",
    max_reviews=50
)

# Procesar reseñas
for review in reviews:
    print(f"{review['username']}: {review['rating']}★")
```

### Flujo 3: Dashboard de Analytics

```python
def generate_dashboard_data(client, client_id):
    """
    Genera datos para un dashboard de analytics
    """
    # 1. Obtener todos los lugares del cliente
    places = client.get_places(client_id=client_id)

    dashboard = {
        "total_places": len(places),
        "places_stats": [],
        "overall_stats": {
            "total_reviews": 0,
            "average_rating": 0,
            "reviews_by_rating": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }
    }

    # 2. Obtener estadísticas por lugar
    for place in places:
        stats = client.get_place_stats(place['place_id'])
        dashboard["places_stats"].append({
            "name": place['name'],
            "total_reviews": stats['total_reviews'],
            "average_rating": stats['average_rating']
        })
        dashboard["overall_stats"]["total_reviews"] += stats['total_reviews']

    # 3. Obtener distribución de ratings
    reviews = client.get_reviews(client_id=client_id, page_size=500)

    total_rating = 0
    for review in reviews['reviews']:
        rating = int(review['rating'])
        dashboard["overall_stats"]["reviews_by_rating"][rating] += 1
        total_rating += review['rating']

    if reviews['total'] > 0:
        dashboard["overall_stats"]["average_rating"] = round(
            total_rating / reviews['total'], 2
        )

    return dashboard

# Uso
client = GoogleMapsReviewsClient()
dashboard = generate_dashboard_data(client, "cadena_restaurantes")

print(f"Total de lugares: {dashboard['total_places']}")
print(f"Total de reseñas: {dashboard['overall_stats']['total_reviews']}")
print(f"Rating promedio: {dashboard['overall_stats']['average_rating']}★")
print("\nDistribución de ratings:")
for rating, count in dashboard['overall_stats']['reviews_by_rating'].items():
    print(f"  {rating}★: {count} reseñas")
```

---

## Manejo de Webhooks

### Endpoint de Webhook (Flask - Python)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/google-reviews', methods=['POST'])
def handle_google_reviews_webhook():
    """
    Endpoint para recibir notificaciones de nuevas reseñas
    """
    try:
        data = request.get_json()

        # Validar que es el evento correcto
        if data.get('event') != 'new_reviews':
            return jsonify({"status": "ignored"}), 200

        # Extraer información
        client_id = data['client_id']
        branch_id = data['branch_id']
        place_name = data['place_name']
        new_reviews_count = data['new_reviews_count']
        reviews = data['reviews']

        print(f"🔔 Nuevas reseñas para {place_name}:")
        print(f"   Cliente: {client_id}, Sucursal: {branch_id}")
        print(f"   Cantidad: {new_reviews_count}")

        # Procesar cada reseña
        for review in reviews:
            print(f"   - {review['username']}: {review['rating']}★")
            print(f"     {review['caption'][:100]}...")

            # Aquí puedes:
            # - Guardar en tu base de datos
            # - Enviar notificación al manager
            # - Enviar email/SMS
            # - Actualizar dashboard en tiempo real
            # - Responder automáticamente a reseñas negativas

            # Ejemplo: Alertar si es una reseña negativa
            if review['rating'] <= 2:
                send_alert_to_manager(
                    client_id,
                    branch_id,
                    review
                )

        # Retornar 200 para confirmar recepción
        return jsonify({
            "status": "success",
            "processed": new_reviews_count
        }), 200

    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def send_alert_to_manager(client_id, branch_id, review):
    """
    Enviar alerta cuando hay una reseña negativa
    """
    # Implementar lógica de notificación
    # (email, SMS, push notification, etc.)
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Endpoint de Webhook (Express - Node.js)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhooks/google-reviews', (req, res) => {
  try {
    const data = req.body;

    // Validar evento
    if (data.event !== 'new_reviews') {
      return res.json({ status: 'ignored' });
    }

    const { client_id, branch_id, place_name, new_reviews_count, reviews } = data;

    console.log(`🔔 Nuevas reseñas para ${place_name}:`);
    console.log(`   Cliente: ${client_id}, Sucursal: ${branch_id}`);
    console.log(`   Cantidad: ${new_reviews_count}`);

    // Procesar reseñas
    reviews.forEach(review => {
      console.log(`   - ${review.username}: ${review.rating}★`);
      console.log(`     ${review.caption.substring(0, 100)}...`);

      // Alertar si es negativa
      if (review.rating <= 2) {
        sendAlertToManager(client_id, branch_id, review);
      }
    });

    res.json({
      status: 'success',
      processed: new_reviews_count
    });

  } catch (error) {
    console.error('Error procesando webhook:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

function sendAlertToManager(clientId, branchId, review) {
  // Implementar notificación
}

app.listen(5000, () => {
  console.log('Webhook server listening on port 5000');
});
```

---

## Mejores Prácticas

### 1. Manejo de Errores

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_retry_session(retries=3, backoff_factor=0.3):
    """
    Crear sesión con reintentos automáticos
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Uso
session = create_retry_session()
try:
    response = session.get('http://localhost:8000/api/places/')
    response.raise_for_status()
    places = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")
```

### 2. Paginación Eficiente

```python
def get_all_reviews(client, client_id, page_size=100):
    """
    Obtener todas las reseñas paginando automáticamente
    """
    all_reviews = []
    page = 1

    while True:
        response = client.get_reviews(
            client_id=client_id,
            page=page,
            page_size=page_size
        )

        all_reviews.extend(response['reviews'])

        # Verificar si hay más páginas
        if page >= response['total_pages']:
            break

        page += 1

    return all_reviews
```

### 3. Caché de Resultados

```python
import time
from functools import wraps

def cached(ttl_seconds=300):
    """
    Decorator para cachear resultados
    """
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result

            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper
    return decorator

# Uso
@cached(ttl_seconds=600)  # Cache por 10 minutos
def get_place_stats_cached(client, place_id):
    return client.get_place_stats(place_id)
```

### 4. Validación de URLs de Google Maps

```python
import re

def validate_google_maps_url(url):
    """
    Validar que la URL es de Google Maps
    """
    pattern = r'https?://(?:www\.)?google\.com/maps/place/'
    if not re.match(pattern, url):
        raise ValueError("URL inválida. Debe ser una URL de Google Maps Place")
    return True
```

---

## Troubleshooting

### Problema: Webhook no recibe notificaciones

**Solución**:
1. Verificar que el webhook_url es accesible públicamente
2. Probar el webhook manualmente:
   ```bash
   curl -X POST "http://localhost:8000/api/monitor/test-webhook/{place_id}"
   ```
3. Verificar logs del servidor webhook
4. Asegurar que retorna status 200

### Problema: Scraping se queda en "queued"

**Solución**:
1. Verificar que el worker está ejecutándose:
   ```bash
   curl "http://localhost:8000/api/scraping/workers/status"
   ```
2. Iniciar worker si no está activo:
   ```bash
   python worker.py
   ```

### Problema: Timeout en scraping

**Solución**:
1. Reducir `max_reviews`
2. Aumentar `SCRAPING_TIMEOUT` en variables de entorno
3. Verificar conectividad a Google Maps

### Problema: Reseñas duplicadas

**Solución**:
- El sistema previene duplicados por `id_review`
- Si persiste, verificar que `save_to_db=True`
- Revisar logs de MongoDB

---

## Recursos Adicionales

- [Documentación Principal](API_DOCUMENTATION.md)
- [Referencia de Endpoints](API_ENDPOINTS.md)
- [Modelos de Datos](DATA_MODELS.md)
- [Guía de Webhooks](WEBHOOKS.md)
- [Inicio Rápido](QUICK_START.md)

---

**Última actualización**: 2025-11-03
