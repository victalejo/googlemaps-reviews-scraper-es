# Guía de Despliegue con Docker Compose

**Sistema**: Google Maps Reviews Scraper API
**Fecha**: 31 de Octubre, 2025

---

## 🚀 Despliegue Rápido (3 comandos)

```bash
# 1. Copiar archivo de configuración
cp .env.prod.example .env

# 2. Editar .env con tus configuraciones
nano .env

# 3. Levantar todos los servicios
docker-compose -f docker-compose.prod.yml up -d --build
```

¡Listo! Tu API estará corriendo en `http://localhost:8000`

---

## 📋 Despliegue Paso a Paso

### Paso 1: Preparar el Servidor

```bash
# Clonar el repositorio (si aún no lo tienes)
git clone <tu-repo>
cd googlemaps-reviews-scraper-es

# O actualizar si ya existe
git pull origin main
```

### Paso 2: Configurar Variables de Entorno

**Opción A: MongoDB y Redis Incluidos (Recomendado para empezar)**

```bash
cp .env.prod.example .env
```

El `.env` por defecto usa MongoDB y Redis incluidos en el docker-compose:
```bash
MONGODB_URL=mongodb://mongodb:27017/
REDIS_URL=redis://redis:6379/0
HEADLESS_MODE=True
LOG_LEVEL=INFO
```

**Opción B: MongoDB y Redis Externos (Producción avanzada)**

Si ya tienes MongoDB y Redis en servicios gestionados:

```bash
cp .env.prod.example .env
nano .env
```

Edita con tus URLs reales:
```bash
MONGODB_URL=mongodb://usuario:password@tu-mongodb-host:27017/
REDIS_URL=redis://default:password@tu-redis-host:6379
HEADLESS_MODE=True
LOG_LEVEL=INFO
```

### Paso 3: Levantar los Servicios

```bash
# Build y start en modo detached
docker-compose -f docker-compose.prod.yml up -d --build
```

Esto levantará **4 servicios**:
1. 🗄️ **MongoDB** - Base de datos (puerto 27017)
2. 🔴 **Redis** - Cola de tareas (puerto 6379)
3. 🌐 **API** - FastAPI application (puerto 8000)
4. ⚙️ **Worker** - Procesador de jobs en background

### Paso 4: Verificar que Todo Funciona

#### Ver el estado de los servicios:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Deberías ver los 4 servicios con estado **"Up (healthy)"**:
```
NAME                        STATUS
googlemaps-api-prod         Up (healthy)
googlemaps-worker-prod      Up (healthy)
googlemaps-mongodb-prod     Up (healthy)
googlemaps-redis-prod       Up (healthy)
```

#### Ver los logs:
```bash
# Logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Logs solo de la API
docker-compose -f docker-compose.prod.yml logs -f api

# Logs solo del Worker
docker-compose -f docker-compose.prod.yml logs -f worker
```

#### Probar el health check:
```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true,
  "error": null
}
```

#### Ver la documentación de la API:
Abre en tu navegador: http://localhost:8000/docs

---

## 🔍 Verificación del Worker

El worker debe mostrar en sus logs:

```bash
docker-compose -f docker-compose.prod.yml logs worker
```

Busca estas líneas:
```
Starting Worker...
Redis URL: redis://redis:6379/0
Successfully connected to Redis
Worker 'worker-scraping_tasks' started and listening for jobs...
*** Listening on scraping_tasks...
```

✅ **Si ves eso = Worker funcionando correctamente**

---

## 🧪 Prueba de Scraping

### 1. Encolar un job de scraping:

```bash
curl -X POST "http://localhost:8000/api/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.google.com/maps/place/La+BTK+Bellas+Artes/@19.4338211,-99.1455109,17z/data=!3m2!4b1!5s0x85d1f92b275f933b:0xbf641e762a5ca480!4m6!3m5!1s0x85d1f96b83b19901:0xc83c8fcab37f08ab!8m2!3d19.4338211!4d-99.1429306!16s%2Fg%2F11gxvsgx0g",
    "max_reviews": 5,
    "sort_by": "newest",
    "save_to_db": true
  }'
```

Respuesta:
```json
{
  "job_id": "abc123-def456-...",
  "status": "queued",
  "message": "Scraping job enqueued successfully"
}
```

### 2. Consultar el status del job:

```bash
# Reemplaza JOB_ID con el que obtuviste
curl "http://localhost:8000/api/scraping/status/JOB_ID"
```

Deberías ver la transición:
- `"status": "queued"` → `"status": "started"` → `"status": "finished"` ✅

### 3. Obtener los resultados:

```bash
curl "http://localhost:8000/api/scraping/result/JOB_ID"
```

Deberías ver las reviews extraídas ✅

---

## 🛠️ Comandos Útiles

### Ver logs en tiempo real:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Reiniciar un servicio:
```bash
docker-compose -f docker-compose.prod.yml restart api
docker-compose -f docker-compose.prod.yml restart worker
```

### Detener todos los servicios:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Detener y eliminar volúmenes (⚠️ borra datos):
```bash
docker-compose -f docker-compose.prod.yml down -v
```

### Rebuild sin cache:
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Ver el uso de recursos:
```bash
docker stats
```

### Acceder a un contenedor:
```bash
# Entrar al contenedor de la API
docker-compose -f docker-compose.prod.yml exec api bash

# Entrar al contenedor del Worker
docker-compose -f docker-compose.prod.yml exec worker bash

# Acceder a MongoDB
docker-compose -f docker-compose.prod.yml exec mongodb mongosh

# Acceder a Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli
```

---

## 🔧 Troubleshooting

### Problema: Puertos en uso

**Síntoma**: `Error: port is already allocated`

**Solución**: Cambiar el puerto en docker-compose.prod.yml

```yaml
# En lugar de 8000:8000, usar otro puerto externo
ports:
  - "8001:8000"  # Ahora accedes en http://localhost:8001
```

### Problema: Worker no procesa jobs

**Diagnóstico**:
```bash
# Ver logs del worker
docker-compose -f docker-compose.prod.yml logs worker

# Verificar que conecta a Redis
docker-compose -f docker-compose.prod.yml logs worker | grep "Successfully connected"

# Ver si está escuchando
docker-compose -f docker-compose.prod.yml logs worker | grep "Listening"
```

**Solución**: Asegúrate que:
- Worker muestra "Successfully connected to Redis"
- Worker muestra "Listening on scraping_tasks..."
- REDIS_URL es la misma en API y Worker

### Problema: MongoDB no se conecta

**Diagnóstico**:
```bash
# Ver logs de MongoDB
docker-compose -f docker-compose.prod.yml logs mongodb

# Probar conexión manual
docker-compose -f docker-compose.prod.yml exec mongodb mongosh
```

**Solución**: Espera a que MongoDB termine de inicializar (puede tomar 30-60 segundos la primera vez)

### Problema: API no responde

**Diagnóstico**:
```bash
# Ver logs de la API
docker-compose -f docker-compose.prod.yml logs api

# Verificar health
curl http://localhost:8000/health
```

**Solución**: Revisa los logs para ver errores específicos

---

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐      ┌──────────────┐                 │
│  │   MongoDB   │◄─────┤   FastAPI    │ :8000           │
│  │   :27017    │      │     API      │◄─── HTTP        │
│  └─────────────┘      └──────┬───────┘    Requests     │
│         ▲                     │                          │
│         │              Enqueue Jobs                      │
│         │                     │                          │
│         │             ┌───────▼───────┐                 │
│         │             │     Redis     │                 │
│         │             │     :6379     │                 │
│         │             └───────┬───────┘                 │
│         │                     │                          │
│         │              Process Jobs                      │
│         │                     │                          │
│         │             ┌───────▼───────┐                 │
│         └─────────────┤   RQ Worker   │                 │
│                       │  (Background) │                 │
│                       └───────────────┘                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Flujo de Datos**:
1. Usuario hace POST a `/api/scraping/start`
2. API encola job en Redis
3. Worker toma el job de Redis
4. Worker ejecuta scraping con Selenium
5. Worker guarda reviews en MongoDB
6. Usuario consulta resultados desde API

---

## 🔒 Seguridad en Producción

### Recomendaciones:

1. **Cambiar puertos por defecto** si están expuestos públicamente
2. **Usar HTTPS** con un reverse proxy (Nginx, Caddy, Traefik)
3. **Agregar autenticación** a la API (JWT, API Keys)
4. **Firewall**: Solo exponer el puerto de la API, no MongoDB/Redis
5. **Backups**: Configurar backups automáticos de MongoDB
6. **Límites de rate**: Implementar rate limiting
7. **Monitoreo**: Configurar alertas (Prometheus, Grafana)

### Ejemplo con Nginx como Reverse Proxy:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📦 Backups

### Backup de MongoDB:

```bash
# Backup manual
docker-compose -f docker-compose.prod.yml exec mongodb mongodump --out=/data/backup

# Copiar backup al host
docker cp googlemaps-mongodb-prod:/data/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Restore de MongoDB:

```bash
# Restaurar desde backup
docker-compose -f docker-compose.prod.yml exec mongodb mongorestore /data/backup
```

---

## 🎯 Checklist de Despliegue

Antes de considerar el despliegue exitoso:

- [ ] `docker-compose ps` muestra 4 servicios "Up (healthy)"
- [ ] `/health` responde con status 200 y todos los checks en true
- [ ] API logs muestran "Application startup complete"
- [ ] Worker logs muestran "Successfully connected to Redis"
- [ ] Worker logs muestran "Listening on scraping_tasks..."
- [ ] Test de scraping: job pasa de "queued" a "finished"
- [ ] Reviews se extraen correctamente (mínimo 1 review)
- [ ] `/docs` muestra la documentación de Swagger
- [ ] MongoDB contiene las reviews en la colección correcta
- [ ] Reinicio del servidor mantiene los servicios funcionando

Si todos los checks pasan: **🎉 ¡Sistema en producción!**

---

## 📞 Soporte

Para problemas o dudas:
1. Revisar logs: `docker-compose -f docker-compose.prod.yml logs`
2. Ver troubleshooting arriba
3. Consultar documentación en `/docs`

---

**Última actualización**: 31 de Octubre, 2025
**Versión**: 1.0.0
**Estado**: ✅ Producción Ready
