# Documentación - Google Maps Reviews Scraper API

Bienvenido a la documentación completa de la API de Google Maps Reviews Scraper.

---

## 📚 Guías Disponibles

### 🚀 [Inicio Rápido](QUICK_START.md)
**Tiempo: 5 minutos**

Guía paso a paso para empezar a usar la API inmediatamente:
- Iniciar la API
- Registrar tu primer lugar
- Extraer reseñas
- Consultar resultados
- Ver estadísticas

👉 **Empieza aquí si es tu primera vez**

---

### 📖 [Documentación Principal](API_DOCUMENTATION.md)
**Lectura: 15 minutos**

Visión general completa del sistema:
- Introducción y características
- Arquitectura del sistema
- Stack tecnológico
- Configuración inicial
- URL base y autenticación
- Módulos de la API
- Límites y restricciones

👉 **Lee esto para entender el sistema completo**

---

### 🔌 [Referencia de Endpoints](API_ENDPOINTS.md)
**Referencia completa**

Documentación detallada de todos los endpoints:
- **Places**: CRUD de lugares y estadísticas
- **Scraping**: Control de trabajos asíncronos
- **Reviews**: Consulta y gestión de reseñas
- **Monitor**: Sistema de monitoreo automático
- **General**: Health checks y utilidades

Cada endpoint incluye:
- Descripción detallada
- Parámetros de entrada/salida
- Ejemplos de request/response
- Códigos de error
- Validaciones

👉 **Consulta cuando necesites detalles específicos de un endpoint**

---

### 🔗 [Guía de Integración](INTEGRATION_GUIDE.md)
**Ejemplos prácticos**

Aprende a integrar la API en tu sistema:
- Casos de uso principales
- Ejemplos completos en Python, JavaScript, PHP
- Flujos de trabajo completos
- Clientes reutilizables
- Manejo de errores
- Paginación eficiente
- Caché de resultados
- Mejores prácticas

👉 **Usa esto para implementar la integración en tu aplicación**

---

### 📦 [Modelos de Datos](DATA_MODELS.md)
**Referencia de estructuras**

Especificación completa de todos los modelos:
- **Place**: Lugares monitoreados
- **Review**: Reseñas extraídas
- **ScrapingJob**: Trabajos de scraping
- **WebhookPayload**: Notificaciones webhook

Incluye:
- Estructura completa de cada modelo
- Descripción de todos los campos
- Tipos de datos y validaciones
- Ejemplos JSON
- Índices de MongoDB
- Schemas TypeScript

👉 **Referencia para entender la estructura de datos**

---

### 🔔 [Guía de Webhooks](WEBHOOKS.md)
**Sistema de notificaciones**

Todo sobre webhooks y notificaciones en tiempo real:
- ¿Qué son los webhooks?
- Configuración paso a paso
- Estructura del payload
- Implementación de endpoints (Python, Node.js, PHP)
- Seguridad y validación
- Reintentos y manejo de errores
- Ejemplos de integración (Slack, Email)
- Mejores prácticas

👉 **Esencial para recibir notificaciones automáticas**

---

## 🎯 ¿Qué Necesitas?

### Quiero empezar rápido
➡️ [Inicio Rápido](QUICK_START.md)

### Quiero entender cómo funciona el sistema
➡️ [Documentación Principal](API_DOCUMENTATION.md)

### Necesito detalles de un endpoint específico
➡️ [Referencia de Endpoints](API_ENDPOINTS.md)

### Quiero integrar la API en mi aplicación
➡️ [Guía de Integración](INTEGRATION_GUIDE.md)

### Necesito saber qué datos maneja la API
➡️ [Modelos de Datos](DATA_MODELS.md)

### Quiero recibir notificaciones automáticas
➡️ [Guía de Webhooks](WEBHOOKS.md)

---

## 🌐 Documentación Interactiva

Además de estos documentos, la API incluye documentación interactiva:

### Swagger UI
```
http://localhost:8000/docs
```

Interfaz visual para:
- Explorar todos los endpoints
- Probar requests en tiempo real
- Ver schemas automáticos
- Descargar especificación OpenAPI

### ReDoc
```
http://localhost:8000/redoc
```

Documentación alternativa con:
- Vista limpia y organizada
- Búsqueda de endpoints
- Navegación por secciones
- Exportación a PDF

---

## 🔧 Casos de Uso Principales

### 1. Monitoreo Continuo
**Uso**: Mantener vigilancia constante sobre reseñas de múltiples lugares

**Documentos relevantes**:
- [Inicio Rápido](QUICK_START.md) - Paso 2: Registrar lugar
- [Guía de Webhooks](WEBHOOKS.md) - Recibir notificaciones
- [API Endpoints](API_ENDPOINTS.md) - Places y Monitor

### 2. Extracción On-Demand
**Uso**: Obtener reseñas de un lugar cuando se necesite

**Documentos relevantes**:
- [Inicio Rápido](QUICK_START.md) - Paso 3: Extraer reseñas
- [API Endpoints](API_ENDPOINTS.md) - Scraping
- [Guía de Integración](INTEGRATION_GUIDE.md) - Flujo 2

### 3. Dashboard de Analytics
**Uso**: Visualizar estadísticas y métricas de reseñas

**Documentos relevantes**:
- [API Endpoints](API_ENDPOINTS.md) - Reviews y Stats
- [Guía de Integración](INTEGRATION_GUIDE.md) - Flujo 3
- [Modelos de Datos](DATA_MODELS.md) - Review

### 4. Sistema de Alertas
**Uso**: Notificar al equipo sobre reseñas negativas

**Documentos relevantes**:
- [Guía de Webhooks](WEBHOOKS.md) - Implementación completa
- [Guía de Integración](INTEGRATION_GUIDE.md) - Slack y Email
- [API Endpoints](API_ENDPOINTS.md) - Monitor

---

## 📊 Arquitectura del Sistema

```
┌──────────────────────────────────────────────────┐
│              CLIENTE (Tu Sistema)                │
│  - Dashboard                                     │
│  - CRM                                          │
│  - Sistema de notificaciones                    │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│            API REST (FastAPI)                    │
│  Endpoints:                                      │
│  - /api/places     (CRUD lugares)               │
│  - /api/scraping   (Jobs de scraping)           │
│  - /api/reviews    (Consultar reseñas)          │
│  - /api/monitor    (Control monitoreo)          │
└───────┬──────────────────────┬───────────────────┘
        │                      │
        ▼                      ▼
┌──────────────┐      ┌──────────────────┐
│   MongoDB    │      │   Redis Queue    │
│   (Datos)    │      │   (Tareas)       │
└──────────────┘      └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Workers (RQ)    │
                      │  - Playwright    │
                      │  - Scraper       │
                      └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Google Maps     │
                      └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │  Webhook URL     │
                      │  (Tu servidor)   │
                      └──────────────────┘
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Framework API | FastAPI | 0.115.0 |
| Base de Datos | MongoDB | 4.4+ |
| Cola de Tareas | Redis + RQ | 6.0+ / 1.16.2 |
| Scraping | Playwright | 1.40.0 |
| Scheduler | APScheduler | 3.10.4 |
| Cliente HTTP | httpx | 0.27.0 |
| Contenedores | Docker + Docker Compose | - |

---

## 📝 Changelog

### v1.0.0 (2025-11-03)
- ✅ Migración de Selenium a Playwright
- ✅ Campos opcionales en Reviews
- ✅ Corrección de ordenamiento por "Más recientes"
- ✅ Optimización de extracción y scroll
- ✅ Sistema completo de webhooks
- ✅ Monitoreo automático con scheduler
- ✅ Documentación completa

---

## 🆘 Soporte y Ayuda

### Documentación
- 📚 Lee las guías en [docs/](.)
- 🌐 Usa la documentación interactiva en `/docs`

### Problemas
- 🐛 Reporta issues en GitHub
- 📋 Consulta [Troubleshooting](QUICK_START.md#troubleshooting-rápido)

### Ejemplos
- 💻 Ver [Guía de Integración](INTEGRATION_GUIDE.md)
- 🔔 Ver [Ejemplos de Webhooks](WEBHOOKS.md#ejemplos-completos)

---

## 📄 Licencia

Este proyecto está bajo la licencia especificada en el repositorio.

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Revisa la documentación existente
2. Reporta bugs o sugiere mejoras vía Issues
3. Sigue las mejores prácticas del código existente

---

## 🎓 Recursos Adicionales

### Herramientas Recomendadas
- [Postman](https://www.postman.com/) - Cliente API
- [Insomnia](https://insomnia.rest/) - Cliente API alternativo
- [MongoDB Compass](https://www.mongodb.com/products/compass) - GUI para MongoDB
- [RedisInsight](https://redis.com/redis-enterprise/redis-insight/) - GUI para Redis

### Servicios para Webhooks de Prueba
- [webhook.site](https://webhook.site) - Inspeccionar webhooks
- [requestbin.com](https://requestbin.com) - Similar a webhook.site
- [ngrok](https://ngrok.com/) - Exponer localhost públicamente

### Lecturas Relacionadas
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Manual](https://docs.mongodb.com/manual/)
- [Playwright Documentation](https://playwright.dev/)
- [Redis Queue (RQ)](https://python-rq.org/)

---

**Última actualización**: 2025-11-03

**Versión de la API**: 1.0.0
