from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from app.services import report_service
from app.services.dependencies import get_current_user
from app.services.db_service import get_db
from app.services.role_checker import check_project_access
from app.config.config import settings
import os

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/{project_id}")
def get_report(
    project_id: str, 
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Devuelve el reporte generado para un proyecto.
    
    IMPLEMENTA REQUERIMIENTO SRF2:
    - Docentes y administradores: pueden acceder a todos los reportes
    - Estudiantes: solo pueden acceder a reportes de sus propios proyectos
    
    Args:
        proyecto_id(str): ID o nombre del proyecto
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Reporte del proyecto si el usuario tiene permisos
        
    Raises:
        HTTPException: Si no tiene permisos o el reporte no existe
    """
    
    # Verificar acceso según rol del usuario (SRF2)
    try:
        # check_project_access implementa la lógica de SRF2
        project = check_project_access(current_user, project_id, db)

        # Intentar obtener el reporte (desde disco o BD)
        report = report_service.get_report(project_id, db=db)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte no encontrado para este proyecto"
            )

        # Agregar información de contexto sobre el acceso
        report["access_info"] = {
            "user_role": current_user.rol.value,
            "user_email": current_user.correo,
            "project_owner_id": project.usuario_id,
            "access_type": "full" if current_user.puede_acceder_todos_reportes() else "own_project"
        }

        return report

    except HTTPException as e:
        # Re-lanzar excepciones HTTP específicas
        raise e
    except Exception as e:
        # Manejo de errores inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el reporte: {str(e)}"
        )


@router.get("/")
def list_accessible_reports(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Lista todos los reportes accesibles para el usuario según su rol.
    
    IMPLEMENTA REQUERIMIENTO SRF2:
    - Docentes/Admins: ven reportes de todos los proyectos
    - Estudiantes: solo ven reportes de sus propios proyectos
    
    Returns:
        dict: Lista de reportes accesibles con información de acceso
    """
    
    # Obtener proyectos accesibles según el rol
    if current_user.puede_acceder_todos_reportes():
        # Docentes y administradores ven todos los proyectos
        from app.models.project import Project
        projects = db.query(Project).all()
        access_level = "all_projects"
    else:
        # Estudiantes solo ven sus propios proyectos
        from app.models.project import Project
        projects = db.query(Project).filter(Project.usuario_id == current_user.id).all()
        access_level = "own_projects_only"
    
    # Obtener reportes disponibles para cada proyecto
    available_reports = []
    for project in projects:
        report = report_service.get_report(str(project.id), db=db)
        if report:
            available_reports.append({
                "project_id": project.id,
                "project_name": project.nombre,
                "project_owner_id": project.usuario_id,
                "report_available": True,
                "can_access": current_user.puede_acceder_proyecto(project.usuario_id)
            })
    
    return {
        "user_role": current_user.rol.value,
        "access_level": access_level,
        "total_accessible_reports": len(available_reports),
        "reports": available_reports,
        "message": f"Como {current_user.rol.value}, {'puedes ver todos los reportes' if current_user.puede_acceder_todos_reportes() else 'solo puedes ver tus propios reportes'}"
    }




@router.get("/download/{project_id}")
def download_report(project_id: str, background_tasks: BackgroundTasks, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Descarga el archivo de reporte JSON para el proyecto. Si la configuración
    `REMOVE_REPORTS_AFTER_DOWNLOAD` está activada, el archivo se eliminará
    automáticamente en background tras la transferencia.
    """
    # Verificar acceso
    project = check_project_access(current_user, project_id, db)

    report_path = os.path.join(settings.REPORTS_DIR, f"{project_id}_report.json")

    # Si el archivo existe en disco, servirlo y opcionalmente eliminarlo en background
    if os.path.exists(report_path):
        def _safe_remove(path: str):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        if settings.REMOVE_REPORTS_AFTER_DOWNLOAD:
            background_tasks.add_task(_safe_remove, report_path)

        return FileResponse(report_path, media_type="application/json", filename=f"{project_id}_report.json")

    # Si no hay archivo en disco, intentar armar el reporte desde la BD y devolver JSON
    report = report_service.get_report(project_id, db=db)
    if report:
        return JSONResponse(content=report)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
