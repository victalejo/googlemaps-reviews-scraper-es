# Google Maps Reviews Scraper API

API REST para extraer reseñas de Google Maps a partir de la URL de un lugar específico. Sistema simplificado que se enfoca en scraping directo de reseñas sin complejidades adicionales.

## Características

- **Scraping directo**: Extrae reseñas de Google Maps usando solo la URL del lugar
- **API REST asíncrona**: Procesamiento en background con Redis Queue (RQ)
- **Almacenamiento en MongoDB**: Persistencia automática de reseñas con deduplicación
- **Múltiples opciones de ordenamiento**: Más recientes, más relevantes, mejor/peor valoradas
- **Paginación**: Consulta eficiente de reseñas almacenadas

## Requisitos

- Python >= 3.9
- MongoDB
- Redis
- ChromeDriver

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/yourusername/googlemaps-reviews-scraper-es.git
cd googlemaps-reviews-scraper-es
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar ChromeDriver

Descarga la versión correspondiente a tu Chrome desde [aquí](https://chromedriver.chromium.org/).

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

Edita `.env` según tu configuración local.

### 5. Iniciar servicios

**MongoDB:**
```bash
# Linux/Mac
sudo systemctl start mongod

# Windows: MongoDB ya se inicia como servicio
# O ejecuta: mongod --dbpath "C:\data\db"
```

**Redis:**
```bash
# Linux/Mac
redis-server

# Windows: Descarga Redis desde https://github.com/microsoftarchive/redis/releases
redis-server.exe
```

### 6. Iniciar worker de RQ

En una terminal separada:

```bash
python worker.py
```

### 7. Iniciar API

```bash
python -m app.main
```

La API estará disponible en `http://localhost:8000`

## Uso de la API

### Documentación interactiva

Una vez iniciada la API, accede a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints principales

#### 1. Iniciar scraping

```bash
POST /api/scraping/start
Content-Type: application/json

{
  "url": "https://www.google.com/maps/place/...",
  "max_reviews": 100,
  "sort_by": "newest"
}
```

**Parámetros:**
- `url` (requerido): URL de Google Maps del lugar
- `max_reviews` (opcional): Número máximo de reseñas (1-1000, default: 100)
- `sort_by` (opcional): `newest`, `most_relevant`, `highest_rating`, `lowest_rating` (default: `newest`)

**Respuesta:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "Scraping job queued successfully...",
  "created_at": "2024-01-01T12:00:00"
}
```

#### 2. Consultar estado del scraping

```bash
GET /api/scraping/status/{job_id}
```

**Respuesta:**
```json
{
  "job_id": "abc123",
  "status": "finished",
  "progress": "Completed: 100 reviews",
  "result_available": true
}
```

#### 3. Obtener resultados

```bash
GET /api/scraping/result/{job_id}
```

**Respuesta:**
```json
{
  "job_id": "abc123",
  "status": "finished",
  "reviews_count": 100,
  "reviews": [
    {
      "id_review": "ChZDSUhNMG9nS0VJQ0Fn...",
      "username": "John Doe",
      "rating": 5.0,
      "caption": "Great place!",
      "review_date": "2024-01-01T10:00:00",
      "retrieval_date": "2024-01-01T12:00:00",
      ...
    }
  ]
}
```

#### 4. Listar reseñas almacenadas

```bash
GET /api/reviews/?page=1&page_size=50&min_rating=4.0&sort_by=review_date&sort_order=desc
```

**Parámetros de consulta:**
- `page`: Número de página (default: 1)
- `page_size`: Registros por página (1-500, default: 100)
- `min_rating`: Calificación mínima (1.0-5.0)
- `max_rating`: Calificación máxima (1.0-5.0)
- `sort_by`: Campo de ordenamiento (`review_date`, `rating`, `retrieval_date`)
- `sort_order`: Orden (`asc` o `desc`)

#### 5. Obtener una reseña específica

```bash
GET /api/reviews/{id_review}
```

#### 6. Obtener reseñas recientes

```bash
GET /api/reviews/recent/all?limit=50
```

#### 7. Health check

```bash
GET /health
```

## Arquitectura

### Flujo de procesamiento

1. **Cliente** envía URL de Google Maps a `/api/scraping/start`
2. **API** encola el trabajo en **Redis Queue**
3. **Worker** procesa el scraping de forma asíncrona usando **Playwright**
4. **Reseñas** se guardan en **MongoDB** (deduplicación automática por `id_review`)
5. **Cliente** consulta estado y obtiene resultados

### Estructura de datos

#### Review
```python
{
  "id_review": str,           # ID único de Google Maps
  "username": str,            # Nombre del usuario
  "rating": float,            # Calificación (1.0-5.0)
  "caption": str,             # Texto de la reseña
  "review_date": datetime,    # Fecha de la reseña
  "retrieval_date": datetime, # Fecha de extracción
  "relative_date": str,       # "Hace 2 meses"
  "n_review_user": int,       # Número de reseñas del usuario
  "n_photo_user": int,        # Número de fotos del usuario
  "url_user": str            # URL del perfil del usuario
}
```

## Cómo obtener la URL correcta de Google Maps

1. Ve a Google Maps y busca un lugar
2. Haz clic en el **número de reseñas** entre paréntesis
3. Copia la URL que se genera

**Ejemplo de URL válida:**
```
https://www.google.com/maps/place/Restaurante+Ejemplo/@40.7128,-74.0060,17z/data=...
```

## Desarrollo

### Ejecutar con Docker

```bash
docker-compose up
```

### Estructura del proyecto

```
googlemaps-reviews-scraper-es/
├── app/
│   ├── api/              # Endpoints de la API
│   ├── services/         # Lógica de scraping
│   ├── tasks/            # Tareas asíncronas (RQ)
│   ├── models.py         # Modelos Pydantic
│   ├── config.py         # Configuración
│   ├── database.py       # Conexiones DB
│   └── main.py           # App FastAPI
├── googlemaps/           # Scraper core (Playwright)
├── worker.py             # Worker RQ
├── requirements.txt
├── .env.example
└── README.md
```

## Solución de problemas

### Error: "ChromeDriver not found"
- Descarga ChromeDriver y añade su ruta a `.env`: `CHROME_DRIVER_PATH=/path/to/chromedriver`

### Error: "Connection to MongoDB failed"
- Verifica que MongoDB esté corriendo: `systemctl status mongod`
- Verifica la URL en `.env`: `MONGODB_URL=mongodb://localhost:27017/`

### Error: "Connection to Redis failed"
- Verifica que Redis esté corriendo: `redis-cli ping` (debería retornar "PONG")
- Verifica la URL en `.env`: `REDIS_URL=redis://localhost:6379/0`

### Worker no procesa trabajos
- Verifica que `worker.py` esté corriendo
- Revisa los logs: `tail -f api.log`

## Créditos

Fork en español del proyecto original de [@gaspa93](https://github.com/gaspa93). Proyecto original: [googlemaps-scraper](https://github.com/gaspa93/googlemaps-scraper).

Artículos relacionados:
- [Scraping Google Maps Reviews in Python](https://medium.com/data-science/scraping-google-maps-reviews-in-python-2b153c655fc2)
- [Monitoring of Google Maps Reviews](https://medium.com/@mattiagasparini2/monitoring-of-google-maps-reviews-29e5d35f9d17)

## Licencia

Este proyecto mantiene la misma licencia del proyecto original.
