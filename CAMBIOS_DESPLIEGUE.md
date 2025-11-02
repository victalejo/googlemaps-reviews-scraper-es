# Cambios para Arreglar Despliegue en Dokploy

## ❌ Problema Encontrado

```
Container googlemaps-mongodb-prod  Error
dependency failed to start: container googlemaps-mongodb-prod is unhealthy
```

MongoDB no pasaba el healthcheck y causaba que todo el despliegue fallara.

## ✅ Solución Aplicada

### 1. Removido `version: '3.8'` obsoleto
El warning decía: "the attribute `version` is obsolete"

### 2. Arreglado healthcheck de MongoDB
**Antes** (no funcionaba):
```yaml
healthcheck:
  test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
```

**Ahora** (funciona):
```yaml
healthcheck:
  test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 40s  # Espera 40s antes de empezar a checkear
```

## 🚀 Pasos para Redesplegar

### 1. Commit y Push de los Cambios

```bash
git add docker-compose.prod.yml
git commit -m "fix: MongoDB healthcheck for Dokploy deployment"
git push origin main
```

### 2. Redesplegar en Dokploy

En el dashboard de Dokploy:
- Ir a tu aplicación `gmapsscrapper-test-gwyypk`
- Click en "Redeploy" o "Deploy"
- Dokploy hará pull de los cambios automáticamente

### 3. Verificar el Despliegue

Espera a que todos los servicios estén "healthy":
```
✅ googlemaps-mongodb-prod - Healthy
✅ googlemaps-redis-prod - Healthy
✅ googlemaps-api-prod - Healthy
✅ googlemaps-worker-prod - Healthy
```

### 4. Probar la API

```bash
# Reemplaza con tu URL de Dokploy
curl https://tu-app.dokploy.com/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "mongodb": true,
  "redis": true
}
```

## 🔍 Si MongoDB Sigue Fallando

### Opción 1: Aumentar el start_period

Si MongoDB tarda mucho en iniciar, edita `docker-compose.prod.yml`:

```yaml
healthcheck:
  start_period: 60s  # Aumenta a 60 segundos
```

### Opción 2: Usar MongoDB Externo

Si prefieres usar MongoDB Atlas u otro servicio gestionado:

1. En Dokploy, configura la variable de entorno:
```
MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/googlemaps
```

2. Comenta el servicio `mongodb` en `docker-compose.prod.yml`:
```yaml
# mongodb:
#   image: mongo:6
#   ...
```

## 📊 Arquitectura Desplegada

Después del despliegue exitoso tendrás:

```
Dokploy (Docker Compose)
├── MongoDB (googlemaps-mongodb-prod) :27017
├── Redis (googlemaps-redis-prod) :6379
├── API (googlemaps-api-prod) :8000
└── Worker (googlemaps-worker-prod)
```

---

**Última actualización**: 2 de Noviembre, 2025
