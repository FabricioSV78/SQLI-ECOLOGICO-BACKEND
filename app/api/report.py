from fastapi import APIRouter, Depends
from app.services import report_service
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/{project_id}")
def get_report(project_id: str, current_user: dict = Depends(get_current_user)):
    """
    Devuelve el reporte generado para un proyecto.
    """
    report = report_service.get_report(project_id)
    if not report:
        return {"status": "error", "message": "Reporte no encontrado"}
    return report
