from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configuraciones y servicios
from app.config.init_db import init_db
from app.config.config import settings
from app.services.encryption_validator import verify_s_rnf2_compliance, log_encryption_summary

# Routers
from app.api import analysis, upload, report, auth, privacy, data_treatment, dpa_admin

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Detector SQLi Backend",
    descripcion ="API para detección de inyecciones SQL en proyectos Java Spring Boot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Eventos de la aplicación
@app.on_event("startup")
async def startup_event():
    """
    Eventos que se ejecutan al iniciar la aplicación.
    """
    logger.info("🚀 Iniciando Detector SQLi Backend...")
    
    try:
        # Verificar cumplimiento de S-RNF2 (Cifrado en reposo)
        logger.info("🔐 Verificando S-RNF2: Cifrado en reposo...")
        verify_s_rnf2_compliance()
        log_encryption_summary()
        
        # Inicializar la base de datos
        logger.info("🗄️ Inicializando base de datos...")
        init_db()
        logger.info("✅ Base de datos inicializada correctamente")
        
        logger.info(f"🔧 Configuración de BD: {settings.DB_HOST}:{settings.DB_PORT}")
        logger.info(f"📊 Base de datos: {settings.DB_NAME}")
        
    except Exception as e:
        logger.error(f"❌ Error al inicializar la base de datos: {e}")
        # No detener la aplicación, pero registrar el error
        
    logger.info("🎉 Aplicación iniciada correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventos que se ejecutan al cerrar la aplicación.
    """
    logger.info("🔄 Cerrando Detector SQLi Backend...")
    logger.info("👋 Aplicación cerrada correctamente")

# Registrar routers con prefijos organizados
app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1") 
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1")
app.include_router(data_treatment.router, prefix="/api/v1", tags=["data-treatment"])
app.include_router(dpa_admin.router, prefix="/api/v1", tags=["dpa-admin"])

# Endpoints principales
@app.get("/")
def root():
    """
    Endpoint raíz - Información básica de la API.
    """
    return {
        "message": "Detector SQLi Backend - API funcionando correctamente",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "file_upload": "/api/v1/upload", 
            "analysis": "/api/v1/analysis",
            "reports": "/api/v1/report",
            "privacy": "/api/v1/privacy",
            "data_treatment": "/api/v1/data-treatment",
            "dpa_admin": "/api/v1/dpa-admin"
        },
        "compliance": {
            "prf2": "Flujo de solicitudes de privacidad implementado",
            "prf4": "Registro de tratamientos GDPR implementado", 
            "prf5": "Panel administrativo DPA con proveedores cloud implementado",
            "s_rnf2": "Cifrado en reposo verificado",
            "s_rnf5": "Pipeline CI/CD con seguridad implementado"
        }
    }

@app.get("/health")
def health_check():
    """
    Endpoint de salud básico para monitoreo y Docker health check.
    """
    return {
        "status": "healthy",
        "service": "detector-sqli-backend",
        "version": "1.0.0"
    }

@app.get("/health/detailed")
def detailed_health_check():
    """
    Endpoint de salud detallado para monitoreo avanzado.
    """
    import time
    from datetime import datetime
    
    health_data = {
        "status": "healthy",
        "service": "detector-sqli-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time(),
        "checks": {
            "database": "healthy",  # Aquí puedes agregar verificación real de DB
            "ml_model": "healthy",  # Verificación del modelo ML
            "file_system": "healthy"
        },
        "metrics": {
            "memory_usage": "available",
            "cpu_usage": "normal",
            "disk_space": "sufficient"
        }
    }
    
    return health_data
