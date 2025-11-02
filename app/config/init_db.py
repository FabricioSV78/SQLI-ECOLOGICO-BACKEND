from sqlalchemy import create_engine
from app.config.config import settings
from app.services.db_service import Base

# Importar todos los modelos para que se registren en Base.metadata
from app.models.user import User
from app.models.user_role import UserRole  # Incluir el enum de roles
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.vulnerability import Vulnerability
from app.models.analysis_metrics import AnalysisMetrics
from app.models.privacy_request import PrivacyRequest  # Nuevo modelo PRF2
from app.models.data_treatment_registry import DataTreatmentRegistry  # Nuevo modelo PRF4
from app.models.dpa_agreement import DataProcessingAgreement  # Nuevo modelo PRF5


def init_db():
    """
    Inicializa la base de datos creando todas las tablas definidas en los modelos.
    Incluye el nuevo campo 'content' en ProjectFile.
    """
    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base.metadata.drop_all(bind=engine)  # Eliminar tablas existentes
    Base.metadata.create_all(bind=engine)  # Recrear con nueva estructura
    print("Tablas recreadas correctamente con la nueva estructura.")

if __name__ == "__main__":
    init_db()
