from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.vulnerability import Vulnerability
from app.models.project_file import ProjectFile
from fastapi import HTTPException
import os

def get_project_analysis_results(project_id: str, user_id: int, db: Session):
    """
    Obtiene los resultados de análisis de un proyecto desde la base de datos.
    Incluye archivos vulnerables, código del archivo, fragmentos vulnerables y predicciones.
    """
    # Buscar el proyecto
    if project_id.isdigit():
        project = db.query(Project).filter(Project.id == int(project_id), Project.user_id == user_id).first()
    else:
        project = db.query(Project).filter(Project.name == project_id, Project.user_id == user_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado para este usuario.")
    
    # Obtener vulnerabilidades y archivos asociados
    vulnerabilities = db.query(Vulnerability).filter(Vulnerability.project_id == project.id).all()
    
    if not vulnerabilities:
        return {
            "project_id": project_id,
            "project_name": project.name,
            "message": "No se encontraron vulnerabilidades en este proyecto.",
            "vulnerable_files": []
        }
    
    # Agrupar vulnerabilidades por archivo
    files_data = {}
    for vuln in vulnerabilities:
        file_path = vuln.file
        if file_path not in files_data:
            files_data[file_path] = {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "vulnerabilities": [],
                "file_content": None
            }
        
        # Agregar vulnerabilidad
        files_data[file_path]["vulnerabilities"].append({
            "id": vuln.id,
            "line": vuln.line,
            "vulnerable_fragment": vuln.query,
            "prediction": vuln.prediction,
            "created_at": vuln.created_at
        })
    
    # Obtener el contenido de cada archivo vulnerable desde la base de datos
    for file_path, file_data in files_data.items():
        # Buscar el archivo en ProjectFile
        project_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project.id,
            ProjectFile.filepath == file_path
        ).first()
        
        if project_file and project_file.content:
            file_data["file_content"] = project_file.content
        else:
            # Fallback: intentar leer desde el sistema de archivos
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data["file_content"] = f.read()
                else:
                    file_data["file_content"] = "Archivo no encontrado ni en la base de datos ni en el sistema de archivos."
            except Exception as e:
                file_data["file_content"] = f"Error al leer el archivo: {str(e)}"
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_db_id": project.id,
        "total_vulnerable_files": len(files_data),
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerable_files": list(files_data.values())
    }

def get_project_vulnerability_summary(project_id: str, user_id: int, db: Session):
    """
    Obtiene un resumen de vulnerabilidades de un proyecto.
    """
    # Buscar el proyecto
    if project_id.isdigit():
        project = db.query(Project).filter(Project.id == int(project_id), Project.user_id == user_id).first()
    else:
        project = db.query(Project).filter(Project.name == project_id, Project.user_id == user_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado para este usuario.")
    
    # Contar vulnerabilidades
    total_vulnerabilities = db.query(Vulnerability).filter(Vulnerability.project_id == project.id).count()
    total_files = db.query(ProjectFile).filter(ProjectFile.project_id == project.id).count()
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_db_id": project.id,
        "total_vulnerabilities": total_vulnerabilities,
        "total_vulnerable_files": total_files,
        "created_at": project.created_at
    }