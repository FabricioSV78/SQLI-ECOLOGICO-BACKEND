import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del archivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    # --- Base de Datos ---
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASS: str = os.getenv("DB_PASS", "admin")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "detector_sqli")

    DATABASE_URL: str = (
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

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
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))
    
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
