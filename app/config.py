import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del archivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    # --- Base de Datos ---
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASS: str = os.getenv("DB_PASS", "postgres")
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

    # --- Rutas del sistema ---
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))


# Instancia global de configuración
settings = Settings()
