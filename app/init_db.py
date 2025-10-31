from sqlalchemy import create_engine
from app.config import settings
from app.services.db_service import Base

import app.models  # con esto se registran todas las clases


def init_db():
    """
    Inicializa la base de datos creando todas las tablas definidas en los modelos.
    """
    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente en la base de datos.")

if __name__ == "__main__":
    init_db()
