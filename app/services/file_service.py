import os
import shutil
import zipfile
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.config.config import settings
from app.models.project import Project

def save_project_file(project_id: str, file: UploadFile, user_id: int, db: Session):
    """
    Guarda un proyecto subido como ZIP, lo descomprime y lo registra en la base de datos.
    """
    # Verificar si ya existe un proyecto con ese nombre para el usuario
    """ existing = db.query(Project).filter(Project.name == project_id, Project.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un proyecto con ese nombre para este usuario.") """

    # Registrar en la base de datos
    new_project = Project(name=project_id, user_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Guardar archivos en carpeta
    project_path = os.path.join(settings.UPLOAD_DIR, str(new_project.id))
    os.makedirs(project_path, exist_ok=True)

    zip_path = os.path.join(project_path, file.filename)
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extraer ZIP
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(project_path)

    # Eliminar ZIP luego de descomprimir
    os.remove(zip_path)


    return {"project_path": project_path, "project": new_project}


def delete_project(project_id: str):
    """
    Elimina carpeta del proyecto.
    """
    project_path = os.path.join(settings.UPLOAD_DIR, project_id)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)