# 🚀 Despliegue en Railway - Detector SQLi Backend

## 📋 Pre-requisitos

1. Cuenta en [Railway.app](https://railway.app)
2. CLI de Railway (opcional): `npm i -g @railway/cli`
3. Repositorio Git del proyecto

## 🚂 Pasos para Desplegar

### Opción 1: Despliegue desde GitHub (Recomendado)

1. **Conectar Repositorio**

   - Ve a [Railway Dashboard](https://railway.app/dashboard)
   - Click en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Autoriza Railway y selecciona tu repositorio

2. **Agregar Base de Datos PostgreSQL**

   - En tu proyecto, click en "+ New"
   - Selecciona "Database" → "Add PostgreSQL"
   - Railway creará automáticamente la variable `DATABASE_URL`

3. **Configurar Variables de Entorno**

   Ve a la pestaña "Variables" de tu servicio y agrega:

   ```
   SECRET_KEY=tu_clave_secreta_super_segura_cambiar_aqui
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60

   # Opcionales (ya tienen defaults)
   SECURITY_SCAN_ENABLED=true
   AUDIT_ENABLED=true
   REMOVE_UPLOADS_AFTER_ANALYSIS=true
   REPORT_RETENTION_DAYS=7
   ```

   **Nota:** `DATABASE_URL` y `PORT` son provistos automáticamente por Railway.

4. **Desplegar**

   - Railway detectará automáticamente el `Dockerfile`
   - El despliegue iniciará automáticamente
   - Espera a que el build termine (3-5 minutos)

5. **Verificar Despliegue**
   - Railway te dará una URL pública (ej: `https://tu-app.up.railway.app`)
   - Visita `https://tu-app.up.railway.app/health` para verificar
   - Revisa la documentación en `https://tu-app.up.railway.app/docs`

### Opción 2: Despliegue con Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Agregar PostgreSQL
railway add --database postgresql

# Configurar variables de entorno
railway variables set SECRET_KEY="tu_clave_secreta_aqui"

# Desplegar
railway up

# Ver logs
railway logs
```

## 🔧 Configuración Adicional

### CORS en Producción

Actualiza el archivo `app/main.py` para permitir tu dominio frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-frontend.vercel.app",  # Tu frontend
        "https://tu-app.up.railway.app"    # Tu backend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### Variables de Entorno Importantes

| Variable                      | Descripción             | Requerido                 | Default |
| ----------------------------- | ----------------------- | ------------------------- | ------- |
| `DATABASE_URL`                | URL de PostgreSQL       | ✅ Sí (Railway lo provee) | -       |
| `PORT`                        | Puerto de la aplicación | ✅ Sí (Railway lo provee) | 8000    |
| `SECRET_KEY`                  | Clave para JWT          | ✅ Sí                     | -       |
| `ALGORITHM`                   | Algoritmo JWT           | No                        | HS256   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración del token    | No                        | 60      |
| `SECURITY_SCAN_ENABLED`       | Escaneo de seguridad    | No                        | true    |
| `AUDIT_ENABLED`               | Logs de auditoría       | No                        | true    |

### Generar SECRET_KEY Segura

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

## 📊 Monitoreo

### Ver Logs en Tiempo Real

```bash
railway logs
```

### Métricas

- Ve al dashboard de Railway
- Sección "Metrics" para CPU, Memoria, Red

### Health Check

Railway monitorea automáticamente el endpoint `/health`

## 🔄 Actualizar Deployment

### Automático (GitHub)

- Haz push a tu rama principal
- Railway detecta cambios y redespliega automáticamente

### Manual (CLI)

```bash
railway up
```

## 🐛 Troubleshooting

### Error: "Application failed to respond"

**Solución:** Verifica que el puerto esté configurado correctamente:

```python
# config.py
PORT: int = int(os.getenv("PORT", 8000))
```

### Error: "Database connection failed"

**Solución:** Verifica que PostgreSQL esté agregado y `DATABASE_URL` exista:

```bash
railway variables
```

### Error: "Module not found"

**Solución:** Verifica que `requirements.txt` esté actualizado:

```bash
pip freeze > app/requirements.txt
```

### Build muy lento

**Solución:** Railway usa Docker, optimiza el Dockerfile con multi-stage builds.

## 🌐 Conectar Frontend

Actualiza tu frontend para usar la URL de Railway:

```javascript
// api-service.js
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://tu-app.up.railway.app/api/v1";
```

## 💾 Persistencia de Datos

**⚠️ Importante:** Railway no garantiza persistencia del sistema de archivos.

**Solución:**

- Usar Railway Volumes para archivos persistentes
- O usar servicios externos (AWS S3, Cloudinary) para uploads

```bash
# Agregar volumen
railway volume create storage
railway volume attach storage /app/uploads
```

## 🔐 Seguridad

### Recomendaciones

1. **Nunca** commits el archivo `.env` al repositorio
2. Usa secretos fuertes para `SECRET_KEY`
3. Configura CORS solo para dominios específicos
4. Habilita HTTPS (Railway lo hace automáticamente)
5. Revisa logs de auditoría regularmente

## 📞 Soporte

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/railwayapp/railway)

## ✅ Checklist de Despliegue

- [ ] PostgreSQL agregado a Railway
- [ ] `DATABASE_URL` disponible automáticamente
- [ ] `SECRET_KEY` configurada
- [ ] CORS actualizado con dominio de producción
- [ ] Health check funcionando (`/health`)
- [ ] Logs sin errores
- [ ] API docs accesibles (`/docs`)
- [ ] Frontend conectado a la API

---

¡Tu aplicación está lista para producción! 🎉
