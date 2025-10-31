from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.services import file_service
from app.services.dependencies import get_current_user
from app.services.db_service import get_db
from app.models.project import Project
import os

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/{nombre_proyecto}")
def upload_project(
    nombre_proyecto: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sube un proyecto (ZIP), lo descomprime y lo registra en la base de datos.
    """
    result = file_service.save_project_file(nombre_proyecto, file, current_user.id, db)
    return {
        "nombre_proyecto": nombre_proyecto,
        "path": result["project_path"],
        "status": "uploaded",
        "db_id": result["project"].id
    }

@router.get("/projects")
def list_user_projects(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista todos los proyectos subidos por el usuario autenticado desde la base de datos.
    """
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return {
        "user": current_user.email,
        "projects": [
            {"id": p.id, "name": p.name, "description": p.description, "created_at": p.created_at}
            for p in projects
        ]
    }