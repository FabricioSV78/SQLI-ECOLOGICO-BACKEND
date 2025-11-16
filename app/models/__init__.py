from app.models.user import Usuario, User
from app.models.user_role import RolUsuario, UserRole
from app.models.project import Proyecto, Project
from app.models.project_file import ArchivoProyecto, ProjectFile
from app.models.vulnerability import Vulnerabilidad, Vulnerability
from app.models.analysis_metrics import MetricasAnalisis, AnalysisMetrics

__all__ = [
    # Nombres en español (principales)
    "Usuario", "RolUsuario", "Proyecto", "ArchivoProyecto", "Vulnerabilidad", "MetricasAnalisis",
    # Nombres en inglés (compatibilidad)
    "User", "UserRole", "Project", "ProjectFile", "Vulnerability", "AnalysisMetrics"
]
