"""
Servicio de verificación de acceso a proyectos para el requerimiento SRF2.

Este módulo proporciona funciones específicas para verificar si un usuario
puede acceder a proyectos y reportes según su rol:

- STUDENTS: Solo acceso a sus propios proyectos
- TEACHERS/ADMINS: Acceso a todos los proyectos

Implementa el requerimiento SRF2: Control de acceso diferenciado para reportes.
"""

from fastapi import HTTPException, status
from app.models.user import User
from app.models.project import Project
from sqlalchemy.orm import Session


def check_project_access(user: User, project_id: str, db: Session) -> Project:
    """
    Verifica si un usuario puede acceder a un proyecto específico.
    
    IMPLEMENTA REQUERIMIENTO SRF2:
    - ESTUDIANTES: Solo acceso a proyectos propios (project.usuario_id == user.id)
    - DOCENTES/ADMINS: Acceso completo a todos los proyectos
    
    Args:
        usuario(User): Usuario que solicita acceso
        proyecto_id(str): ID del proyecto (numérico o nombre)
        db (Session): Sesión de base de datos
        
    Returns:
        Project: El proyecto si el usuario tiene acceso
        
    Raises:
        HTTPException 404: Si el proyecto no existe
        HTTPException 403: Si no tiene permisos para acceder
    """
    # Buscar el proyecto por ID numérico o por nombre
    if project_id.isdigit():
        project = db.query(Project).filter(Project.id == int(project_id)).first()
    else:
        project = db.query(Project).filter(Project.nombre == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    # Verificar permisos según rol (lógica SRF2)
    if user.puede_acceder_todos_reportes():
        # Docentes y administradores: acceso completo
        return project
    else:
        # Estudiantes: solo sus propios proyectos
        if project.usuario_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado. Los estudiantes solo pueden acceder a sus propios proyectos."
            )
        return project


def validate_report_access(user: User, project_id: str, db: Session) -> bool:
    """
    Valida si un usuario puede acceder a los reportes de un proyecto.
    
    Función auxiliar que encapsula check_project_access() para devolver
    un booleano en lugar de lanzar excepciones.
    
    Args:
        usuario(User): Usuario que solicita acceso
        proyecto_id(str): ID del proyecto
        db (Session): Sesión de base de datos
        
    Returns:
        bool: True si puede acceder, False si no tiene permisos
    """
    try:
        check_project_access(user, project_id, db)
        return True
    except HTTPException:
        return False
