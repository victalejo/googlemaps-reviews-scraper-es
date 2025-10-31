# Guía de Despliegue en Plataforma Cloud

**Fecha**: 31 de Octubre, 2025
**Problema**: Jobs se quedan en "queued" porque el Worker no está desplegado

---

## 🚨 IMPORTANTE: Necesitas 2 Servicios

Tu aplicación requiere **DOS servicios separados** corriendo al mismo tiempo:

1. **🌐 API Service** - Recibe requests HTTP (FastAPI)
2. **⚙️ Worker Service** - Procesa jobs en background (RQ Worker)

**Si solo despliegas la API**, los jobs se quedarán en "queued" para siempre porque no hay nadie procesándolos.

---

## 📋 Opción 1: Dos Servicios con Mismo Dockerfile (Recomendado)

Despliega el mismo código dos veces con **comandos diferentes**:

### Servicio 1: API

| Configuración | Valor |
|---------------|-------|
| **Nombre** | `googlemaps-api` |
| **Dockerfile** | `Dockerfile` |
| **Variables de Entorno** | Ver sección abajo |
| **Puerto** | Exponer puerto (ej: 8000) |
| **Comando de Inicio** | Sin configurar (usa default) o vacio |

### Servicio 2: Worker

| Configuración | Valor |
|---------------|-------|
| **Nombre** | `googlemaps-worker` |
| **Dockerfile** | `Dockerfile` (el mismo) |
| **Variables de Entorno** | Ver sección abajo + `SERVICE_TYPE=worker` |
| **Puerto** | No exponer puerto |
| **Comando de Inicio** | Sin configurar (usa default con SERVICE_TYPE) |

### Variables de Entorno (AMBOS servicios)

```bash
# Redis (tu URL específica)
REDIS_URL=redis://default:br9p6ja5cwdv7mdd@gmapsscrapper-cola-uzdghs:6379

# MongoDB
MONGODB_URL=mongodb://mongo:orwewsqdmfg3gb0z@gmapsscrapper-db-tqezyl:27017
MONGODB_DB=googlemaps

# Configuración
HEADLESS_MODE=True
LOG_LEVEL=INFO
```

**ADICIONAL para el Worker**:
```bash
SERVICE_TYPE=worker
```

---

## 📋 Opción 2: Usando Procfile (Railway, Heroku, etc.)

Si tu plataforma soporta `Procfile`, puedes usar el archivo `Procfile` incluido:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: python worker.py
```

**Pasos**:
1. El `Procfile` ya está en el repositorio
2. Tu plataforma debe detectarlo automáticamente
3. Necesitas **habilitar/escalar el worker** manualmente en el dashboard

### En Railway:
1. Despliega el proyecto
2. Ve a "Settings" → "Deploy"
3. Railway detecta el Procfile
4. Crea un servicio separado para `worker`
5. Activa/escala el worker service

### En Render:
1. Crea un "Web Service" (para `web`)
2. Crea un "Background Worker" (para `worker`)
3. Ambos usan el mismo repositorio
4. Render usa el Procfile automáticamente

### En Heroku:
1. Despliega la app
2. Escala el worker: `heroku ps:scale worker=1`

---

## 📋 Opción 3: Comando de Inicio Manual

Si tu plataforma no soporta Procfile, crea dos servicios manualmente:

### Servicio API
**Comando de inicio**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Servicio Worker
**Comando de inicio**:
```bash
python worker.py
```

---

## 🔍 Verificación: ¿Cómo sé si el Worker está corriendo?

### 1. Ver los Logs del Worker

Deberías ver algo como:
```
2025-10-31 17:40:55,172 - __main__ - INFO - Starting RQ Worker...
2025-10-31 17:40:55,173 - __main__ - INFO - Redis URL: redis://default:br9p6ja5cwdv7mdd@...
2025-10-31 17:40:55,176 - __main__ - INFO - Successfully connected to Redis
2025-10-31 17:40:55,177 - __main__ - INFO - Worker 'worker-scraping_tasks' started and listening for jobs...
```

✅ **Si ves esto = Worker funcionando**
❌ **Si no hay logs del worker = Worker NO desplegado**

### 2. Hacer una Prueba de Scraping

```bash
curl -X POST "https://tu-api.com/api/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.google.com/maps/place/...",
    "max_reviews": 5,
    "sort_by": "newest"
  }'
```

Guarda el `job_id` y consulta el status cada 2 segundos:

```bash
curl "https://tu-api.com/api/scraping/status/{job_id}"
```

**Comportamiento esperado**:
- Primero: `"status": "queued"` ⏳
- Después: `"status": "started"` 🔄 (significa que el worker lo tomó)
- Finalmente: `"status": "finished"` ✅

**Si se queda en "queued" para siempre**: Worker NO está corriendo ❌

---

## 🎯 Instrucciones Específicas por Plataforma

### Railway

1. **Conecta tu repositorio** en Railway
2. **Detecta el Procfile** automáticamente
3. En el dashboard verás **dos servicios**:
   - `web` (API)
   - `worker` (Worker)
4. Asegúrate que **ambos estén activos**
5. Configura las variables de entorno en **ambos servicios**

### Render

1. Crea un **Web Service**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. Crea un **Background Worker**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python worker.py`

3. Ambos servicios deben usar el **mismo repo** y **mismas variables de entorno**

### DigitalOcean App Platform

1. En `App Spec`, define dos componentes:

```yaml
services:
- name: api
  dockerfile_path: Dockerfile
  http_port: 8000
  run_command: uvicorn app.main:app --host 0.0.0.0 --port 8000

- name: worker
  dockerfile_path: Dockerfile
  run_command: python worker.py
```

### Google Cloud Run

**Problema**: Cloud Run no soporta workers background directamente.

**Solución**: Usa Cloud Run para la API + Cloud Tasks o Pub/Sub para el worker, o considera otra plataforma.

### AWS ECS/Fargate

Define dos **Task Definitions**:

1. **Task API**:
   - Imagen: Tu Dockerfile
   - Command: `["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`
   - Port: 8000

2. **Task Worker**:
   - Imagen: Tu Dockerfile (la misma)
   - Command: `["python", "worker.py"]`
   - Port: Ninguno

---

## 🐳 Docker Compose (Desarrollo Local)

Para desarrollo local, `docker-compose.yml` ya está configurado correctamente:

```bash
docker-compose up -d
```

Esto inicia automáticamente:
- API en puerto 8001
- Worker en background
- MongoDB en puerto 27017
- Redis en puerto 6380

---

## 🔧 Troubleshooting

### Problema: Solo veo logs de la API, no del Worker

**Causa**: Solo desplegaste un servicio (la API)

**Solución**: Crea el servicio Worker como se indica arriba

### Problema: Worker no se conecta a Redis

**Síntoma**: En logs del worker: `Failed to connect to Redis`

**Causa**: Variable `REDIS_URL` incorrecta o no configurada

**Solución**: Verifica que la variable `REDIS_URL` sea **exactamente la misma** en API y Worker

### Problema: Jobs se quedan en "queued"

**Causa**: Worker no está corriendo o no está conectado al mismo Redis

**Checklist**:
- [ ] Servicio Worker está desplegado ✓
- [ ] Logs del Worker muestran "Successfully connected to Redis" ✓
- [ ] `REDIS_URL` es la misma en API y Worker ✓
- [ ] Worker muestra "Listening on scraping_tasks..." ✓

### Problema: Worker crashea inmediatamente

**Diagnóstico**:
```bash
# Ver logs completos del worker
# (comando depende de tu plataforma)
```

**Causas comunes**:
- Chrome no puede ejecutarse en el contenedor → Verifica que `HEADLESS_MODE=True`
- Falta alguna dependencia → Verifica que `requirements.txt` esté completo
- Variables de entorno incorrectas → Verifica todas las variables

---

## 📊 Checklist Final de Despliegue

Antes de decir "está funcionando", verifica:

- [ ] API responde en `/health` con status 200
- [ ] API conecta a MongoDB (ver logs de startup)
- [ ] API conecta a Redis (ver logs de startup)
- [ ] Worker service está desplegado y corriendo
- [ ] Worker logs muestran "Starting RQ Worker..."
- [ ] Worker logs muestran "Successfully connected to Redis"
- [ ] Worker logs muestran URL correcta de Redis
- [ ] Worker logs muestran "Listening on scraping_tasks..."
- [ ] Hacer test de scraping: job pasa de "queued" a "started"
- [ ] Job completa exitosamente: status "finished"
- [ ] Resultados accesibles via API

Si todos los checks pasan: **🎉 Sistema funcionando correctamente**

---

## 📞 Comandos Útiles

### Ver logs del API
```bash
# Railway
railway logs --service api

# Render
# Desde el dashboard → Logs

# Docker directo
docker logs <container_id> -f
```

### Ver logs del Worker
```bash
# Railway
railway logs --service worker

# Render
# Desde el dashboard → Background Worker → Logs

# Docker directo
docker logs <worker_container_id> -f
```

---

## ✅ Resumen

**TL;DR**:
1. Necesitas **2 servicios**, no 1
2. Ambos usan el mismo código/Dockerfile
3. Servicio 1: API (`uvicorn`)
4. Servicio 2: Worker (`python worker.py` o `SERVICE_TYPE=worker`)
5. Ambos con las **mismas variables de entorno**
6. Especialmente `REDIS_URL` debe ser **idéntica**

---

**Última actualización**: 31 de Octubre, 2025
