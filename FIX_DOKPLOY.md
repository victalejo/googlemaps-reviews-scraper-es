# Fix para Problemas de Dokploy

**Fecha**: 2 de Noviembre, 2025

## Problemas Encontrados

### 1. Worker - Conflicto de Nombres
```
ValueError: There exists an active worker named 'worker-scraping_tasks' already
```

**Causa**: Workers previos no se limpiaron correctamente en Redis, causando conflictos de nombres.

**Solución**: Worker ahora usa nombre único con hostname + timestamp:
```python
worker_name = f"worker-{socket.gethostname()}-{int(time.time())}"
```

### 2. MongoDB - No Resuelve Hostname
```
mongodb:27017: [Errno -3] Temporary failure in name resolution
```

**Causa**: En Dokploy, los nombres de red pueden ser diferentes al usar `-p` para el proyecto.

**Solución**: Agregados aliases explícitos de red:
```yaml
networks:
  googlemaps-network:
    aliases:
      - mongodb
      - mongo
```

## Cambios Aplicados

### 1. [worker.py](worker.py#L48-L58)
- Worker usa nombre dinámico único
- Previene conflictos con workers fantasma

### 2. [docker-compose.prod.yml](docker-compose.prod.yml#L13-L31)
- Agregados aliases de red para MongoDB y Redis
- Asegura que los hostnames sean consistentes

### 3. [app/database.py](app/database.py#L61-L110)
- Agregado try/except en initialize_database()
- API inicia aunque MongoDB no esté disponible

### 4. [app/main.py](app/main.py#L35-L56)
- Removido raise en startup
- API continúa aunque haya errores de conexión

## Comandos para Redesplegar

```bash
git add .
git commit -m "fix: Worker nombre único y aliases de red para Dokploy"
git push origin main
```

Luego en Dokploy: Click en "Redeploy"

## Qué Esperar

### Logs del Worker (Correcto)
```
Starting Worker...
INFO - Starting RQ Worker...
INFO - Redis URL: redis://redis:6379/0
INFO - Successfully connected to Redis
INFO - Worker 'worker-googlemaps-worker-prod-1730562124' started and listening for jobs...
INFO - *** Listening on scraping_tasks...
```

### Logs de API (Correcto)
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

O si MongoDB no está listo aún:
```
WARNING: Database might not be available yet. Indexes will be created on first use.
WARNING: API will start anyway. Connections will be retried automatically.
INFO: Application startup complete.
```

### Logs de MongoDB (Correcto)
```
{"msg":"Waiting for connections","port":27017}
```

## Verificación Post-Despliegue

### 1. Ver logs de todos los servicios
```bash
# En Dokploy, ve a Logs de cada servicio
```

### 2. Verificar que la API responda
```bash
curl https://tu-dominio/health
```

Debería retornar:
```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true
}
```

O al menos:
```json
{
  "status": "degraded",
  "mongodb": false,  # Si MongoDB sigue iniciando
  "redis": true
}
```

### 3. Verificar Worker
El worker debe mostrar que está escuchando y NO debe tener el error de conflicto de nombres.

## Si MongoDB Sigue Sin Funcionar

### Opción A: Usar MongoDB Atlas (Recomendado)

1. Crea una cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crea un cluster gratuito
3. Obtén el connection string
4. En Dokploy, configura la variable de entorno:
   ```
   MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/googlemaps
   ```
5. Comenta el servicio mongodb en docker-compose.prod.yml

### Opción B: Debug MongoDB

Ver logs completos de MongoDB en Dokploy para identificar por qué está crasheando.

Posibles causas:
- Problema de permisos en el volumen
- Falta de recursos (RAM/CPU)
- Datos corruptos en volumen previo

Solución temporal: Eliminar el volumen `mongodb_data` y dejar que se cree nuevo.

---

**Última actualización**: 2 de Noviembre, 2025
**Status**: Cambios listos para despliegue
