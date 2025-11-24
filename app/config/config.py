import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del archivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    # --- Base de Datos ---
    # Railway proporciona DATABASE_URL automáticamente
    # Formato: postgresql://user:password@host:port/database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Si no existe DATABASE_URL (desarrollo local), construir desde variables individuales
    if not DATABASE_URL:
        DB_USER: str = os.getenv("DB_USER", "postgres")
        DB_PASS: str = os.getenv("DB_PASS", "Joseallain27")
        DB_HOST: str = os.getenv("DB_HOST", "localhost")
        DB_PORT: str = os.getenv("DB_PORT", "5432")
        DB_NAME: str = os.getenv("DB_NAME", "detector_sqli")
        
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Railway usa postgres:// pero SQLAlchemy necesita postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # --- Seguridad ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    # --- S-RNF2: Cifrado en reposo (delegado a Railway PaaS) ---
    # Railway maneja automáticamente el cifrado en reposo para:
    # - Base de datos PostgreSQL (AES-256)
    # - Volúmenes persistentes 
    # - Backups automáticos
    RAILWAY_ENVIRONMENT: bool = os.getenv("RAILWAY_ENVIRONMENT_NAME") is not None
    ENCRYPTION_AT_REST_PROVIDER: str = "Railway PaaS"  # Delegado al proveedor

    # --- Rutas del sistema ---
    # En Railway, usar rutas relativas al directorio de trabajo
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))
    
    # --- Puerto para Railway ---
    PORT: int = int(os.getenv("PORT", 8000))
    # --- Retención / eliminación automática de reportes ---
    # Si se desea eliminar los reportes automáticamente después de descargarse,
    # establecer REMOVE_REPORTS_AFTER_DOWNLOAD=true en .env
    REMOVE_REPORTS_AFTER_DOWNLOAD: bool = os.getenv("REMOVE_REPORTS_AFTER_DOWNLOAD", "false").lower() == "true"
    # Días por defecto para retener reportes antes de limpieza automática mediante cron/script
    REPORT_RETENTION_DAYS: int = int(os.getenv("REPORT_RETENTION_DAYS", 1))
    # --- Eliminación automática de archivos subidos después del análisis ---
    REMOVE_UPLOADS_AFTER_ANALYSIS: bool = os.getenv("REMOVE_UPLOADS_AFTER_ANALYSIS", "true").lower() == "true"
    
    # --- SRF3: Escaneo de seguridad automático ---
    # Directorio para archivos en cuarentena (binarios detectados)
    QUARANTINE_DIR: str = os.getenv("QUARANTINE_DIR", str(BASE_DIR / "quarantine"))
    SECURITY_SCAN_ENABLED: bool = os.getenv("SECURITY_SCAN_ENABLED", "true").lower() == "true"
    
    # --- SRF5: Logs inmutables para auditoría ---
    # Directorio para logs de auditoría (usuario, timestamp, acción, resultado)
    AUDIT_DIR: str = os.getenv("AUDIT_DIR", str(BASE_DIR / "audit_logs"))
    AUDIT_ENABLED: bool = os.getenv("AUDIT_ENABLED", "true").lower() == "true"


# Instancia global de configuración
settings = Settings()
