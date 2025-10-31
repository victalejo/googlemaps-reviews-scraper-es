# Instrucciones de Despliegue - Servidor Remoto Docker

**Fecha**: 31 de Octubre, 2025
**Problema Resuelto**: Worker no procesaba jobs (se quedaban en "queued")

---

## 🔧 Problema Identificado

El worker en el servidor remoto **NO conectaba al mismo Redis que la API**:

- **API**: Conecta a Redis externo usando variable `REDIS_URL` ✅
- **Worker**: Conecta a Redis interno hardcoded `redis://redis:6379/0` ❌

**Resultado**: Los jobs se encolaban en un Redis y el worker escuchaba en otro Redis diferente.

---

## ✅ Solución Aplicada

### Cambios Realizados

1. **Dockerfile** - Ahora copia `worker.py` al contenedor
2. **docker-compose.yml** - Worker usa `python worker.py` en lugar de comando hardcoded
3. **worker.py** - Lee `REDIS_URL` de las variables de entorno automáticamente

---

## 📋 Instrucciones para Servidor Remoto

### Paso 1: Actualizar el Código

```bash
# Ir al directorio del proyecto
cd /ruta/al/proyecto

# Hacer pull de los últimos cambios
git pull origin main
```

**O si no usas Git**, sube estos archivos modificados:
- `Dockerfile`
- `docker-compose.yml`

### Paso 2: Verificar Variables de Entorno

Asegúrate que el archivo `.env` o las variables de entorno del servidor tengan:

```bash
# Redis externo (tu URL específica)
REDIS_URL=redis://default:br9p6ja5cwdv7mdd@gmapsscrapper-cola-uzdghs:6379

# MongoDB
MONGODB_URL=<tu_url_de_mongodb>
MONGODB_DB=googlemaps

# Otras configuraciones
HEADLESS_MODE=True
LOG_LEVEL=INFO
```

### Paso 3: Reconstruir y Reiniciar el Worker

```bash
# Detener el worker actual
docker-compose stop worker

# Reconstruir la imagen con los cambios
docker-compose build worker

# Iniciar el worker
docker-compose up -d worker
```

**IMPORTANTE**: Es necesario hacer `build` para que el `worker.py` se copie al contenedor.

### Paso 4: Verificar que Funciona

#### A. Ver los logs del worker

```bash
docker-compose logs worker --tail=30 -f
```

**Deberías ver**:
```
2025-10-31 17:40:55,172 - __main__ - INFO - Starting RQ Worker...
2025-10-31 17:40:55,173 - __main__ - INFO - Redis URL: redis://default:br9p6ja5cwdv7mdd@gmapsscrapper-cola-uzdghs:6379
2025-10-31 17:40:55,173 - __main__ - INFO - Queue: scraping_tasks
2025-10-31 17:40:55,176 - __main__ - INFO - Successfully connected to Redis
2025-10-31 17:40:55,177 - __main__ - INFO - Worker 'worker-scraping_tasks' started and listening for jobs...
```

✅ **Señal de éxito**: El worker muestra tu URL de Redis externa correcta

❌ **Si ves otra URL**: El worker todavía está usando el comando antiguo

#### B. Probar un scraping

Envía un job de prueba desde tu aplicación o con curl:

```bash
curl -X POST "http://tu-servidor:8000/api/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.google.com/maps/place/...",
    "max_reviews": 5,
    "sort_by": "newest",
    "save_to_db": true
  }'
```

Guarda el `job_id` que retorna y consulta el status:

```bash
curl "http://tu-servidor:8000/api/scraping/status/{job_id}"
```

**Deberías ver la transición**:
1. `"status": "queued"` (inicial)
2. `"status": "started"` (procesando)
3. `"status": "finished"` (completado) ✅

#### C. Ver logs del job procesado

```bash
docker-compose logs worker | grep "Job OK"
```

Deberías ver:
```
scraping_tasks: Job OK (7e93dd77-9460-485c-a3be-364a0d74b1b7)
```

---

## 🔍 Diagnóstico de Problemas

### Problema: Worker muestra URL incorrecta

**Síntoma**: En los logs ves `Redis URL: redis://redis:6379/0` en lugar de tu URL externa

**Causa**: El worker no se reconstruyó correctamente

**Solución**:
```bash
# Forzar rebuild completo
docker-compose down worker
docker-compose build --no-cache worker
docker-compose up -d worker
```

### Problema: Jobs siguen en "queued"

**Diagnóstico**:
```bash
# 1. Verificar que el worker está corriendo
docker-compose ps worker

# 2. Ver logs del worker
docker-compose logs worker --tail=50

# 3. Verificar que conectó a Redis
docker-compose logs worker | grep "Successfully connected"

# 4. Verificar que está escuchando
docker-compose logs worker | grep "Listening on"
```

**Soluciones comunes**:
- Worker no corriendo → `docker-compose up -d worker`
- Worker crasheando → Revisar logs completos para errores
- Redis URL incorrecta → Verificar variables de entorno

### Problema: Error de conexión a Redis

**Síntoma**: `Failed to connect to Redis: ...`

**Verificar**:
1. La URL de Redis es correcta en las variables de entorno
2. Redis está accesible desde el contenedor del worker
3. Las credenciales son correctas

```bash
# Probar conexión desde el contenedor
docker-compose exec worker python -c "
from redis import Redis
import os
redis_url = os.getenv('REDIS_URL')
print(f'Testing: {redis_url}')
r = Redis.from_url(redis_url)
r.ping()
print('OK')
"
```

---

## 📊 Diferencias: Antes vs Después

### Antes (NO Funcionaba)

**docker-compose.yml**:
```yaml
command: rq worker scraping_tasks --url redis://redis:6379/0
```

**Problema**:
- URL hardcoded en el comando
- No usa variables de entorno
- Worker conecta a Redis interno (que no existe en servidor remoto)

### Después (Funciona)

**docker-compose.yml**:
```yaml
command: python worker.py
```

**Solución**:
- `worker.py` lee `settings.redis_url`
- `settings.redis_url` lee variable `REDIS_URL`
- Worker conecta al mismo Redis que la API ✅

---

## ✨ Verificación Final

Una vez desplegado, ejecuta este checklist:

- [ ] `docker-compose ps` muestra worker con estado "Up"
- [ ] Logs muestran: "Starting RQ Worker..."
- [ ] Logs muestran: "Successfully connected to Redis"
- [ ] Logs muestran tu URL de Redis externa correcta
- [ ] Logs muestran: "Listening on scraping_tasks..."
- [ ] Un job de prueba pasa de "queued" a "finished"
- [ ] Los resultados del job son accesibles via API

Si todos los checks pasan: **🎉 ¡DESPLIEGUE EXITOSO!**

---

## 📞 Comandos Útiles

### Ver logs en tiempo real
```bash
docker-compose logs worker -f
```

### Reiniciar worker
```bash
docker-compose restart worker
```

### Ver estado de todos los servicios
```bash
docker-compose ps
```

### Ver últimos 50 logs del worker
```bash
docker-compose logs worker --tail=50
```

### Eliminar y recrear worker
```bash
docker-compose rm -sf worker
docker-compose up -d worker
```

---

## 🚀 Resultado Esperado

Después de seguir estos pasos:

✅ Worker conecta al Redis externo correcto
✅ Jobs se procesan inmediatamente (no se quedan en "queued")
✅ El scraping funciona y extrae reviews
✅ Los resultados son accesibles via API
✅ Sistema completamente funcional

---

**Última actualización**: 31 de Octubre, 2025
**Estado**: ✅ Probado y funcionando en local, listo para servidor remoto
