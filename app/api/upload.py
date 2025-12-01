from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.services import file_service
from app.services.dependencies import get_current_user
from app.services.db_service import get_db
from app.models.project import Proyecto
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.config.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/{nombre_proyecto}")
def upload_project(
    nombre_proyecto: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sube un proyecto (ZIP), lo escanea con SRF3, lo descomprime y lo registra.
    
    SRF3: Realiza escaneo automático de seguridad antes del análisis.
    Rechaza archivos ZIP que contengan binarios o contenido peligroso.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📁 Iniciando upload - Proyecto: {nombre_proyecto}")
    logger.info(f"📁 Usuario: {current_user.correo}")
    logger.info(f"📁 Archivo recibido: {file}")
    if file:
        logger.info(f"📁 Filename: {file.filename}")
        logger.info(f"📁 Content type: {getattr(file, 'content_type', 'unknown')}")
    
    # Validaciones básicas
    if not file or not file.filename:
        return {
            "error": "NO_FILE",
            "message": "No se proporcionó ningún archivo",
            "status": "rejected"
        }
    
    if not file.filename.endswith('.zip'):
        # 📝 SRF5: Log de subida rechazada por tipo de archivo
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.UPLOAD,
                result=AuditResult.REJECTED,
                details={
                    "project_name": nombre_proyecto,
                    "filename": file.filename,
                    "error": "INVALID_FILE_TYPE",
                    "reason": "No es archivo ZIP"
                },
                audit_dir=settings.AUDIT_DIR
            )
        
        return {
            "error": "INVALID_FILE_TYPE",
            "message": "Solo se permiten archivos ZIP",
            "status": "rejected"
        }
    
    try:
        # SRF3: El escaneo se realiza automáticamente en save_project_file
        result = file_service.save_project_file(nombre_proyecto, file, current_user.id, db)
        
        # 📝 SRF5: Log de subida exitosa
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.UPLOAD,
                result=AuditResult.SUCCESS,
                details={
                    "project_name": nombre_proyecto,
                    "filename": file.filename,
                    "project_id": result["project"].id,
                    "file_size": result.get("file_size", 0),
                    "security_scan": "✅ SRF3: Passed - No threats detected"
                },
                audit_dir=settings.AUDIT_DIR
            )
        
        return {
            "nombre_proyecto": nombre_proyecto,
            "path": result["project_path"],
            "status": "uploaded",
            "db_id": result["project"].id,
            "security_scan": "✅ SRF3: Passed - No threats detected"
        }
        
    except Exception as e:
        # Si es un error de SRF3, devolver información detallada
        if hasattr(e, 'detail') and isinstance(e.detail, dict) and e.detail.get('error') == 'SRF3_SECURITY_VIOLATION':
            # 📝 SRF5: Log de subida rechazada por SRF3
            if settings.AUDIT_ENABLED:
                log_user_action(
                    user_id=current_user.id,
                    username=current_user.correo,
                    action=AuditAction.UPLOAD,
                    result=AuditResult.REJECTED,
                    details={
                        "project_name": nombre_proyecto,
                        "filename": file.filename,
                        "error": "SRF3_SECURITY_VIOLATION",
                        "reason": "Binarios detectados en escaneo",
                        "threats": e.detail.get('scan_result', {}).get('threats_found', [])[:3]  # Primeras 3 amenazas
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            
            # Extraer las amenazas encontradas
            threats_found = e.detail.get('scan_result', {}).get('threats_found', [])
            
            return {
                "error": "SRF3_SECURITY_VIOLATION", 
                "message": "Archivo rechazado por escaneo de seguridad",
                "details": threats_found,  # Enviar array de amenazas directamente
                "threats_count": len(threats_found),
                "status": "quarantined",
                "security_scan": "❌ SRF3: Failed - Threats detected"
            }
        else:
            # 📝 SRF5: Log de error en subida
            if settings.AUDIT_ENABLED:
                log_user_action(
                    user_id=current_user.id,
                    username=current_user.correo,
                    action=AuditAction.UPLOAD,
                    result=AuditResult.ERROR,
                    details={
                        "project_name": nombre_proyecto,
                        "filename": file.filename,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            # Otros errores
            raise e

@router.get("/projects")
def list_user_projects(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista todos los proyectos subidos por el usuario autenticado desde la base de datos.
    """
    projects = db.query(Proyecto).filter(Proyecto.usuario_id == current_user.id).all()
    return {
        "user": current_user.correo,
        "projects": [
            {"id": p.id, "name": p.nombre, "description": p.descripcion, "created_at": p.fecha_creacion}
            for p in projects
        ]
    }

@router.get("/projects/user/{user_id}")
def list_user_projects_by_id(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los proyectos de un usuario específico.
    Solo accesible para docentes y administradores.
    """
    from app.models.user_role import UserRole
    
    # Verificar permisos: solo docentes y administradores
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMINISTRADOR]:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver proyectos de otros usuarios"
        )
    
    # Obtener información del usuario objetivo
    from app.models.user import User
    target_user = db.query(User).filter(User.id == user_id).first()
    
    if not target_user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Obtener proyectos del usuario
    projects = db.query(Proyecto).filter(Proyecto.usuario_id == user_id).all()
    
    return {
        "user_id": user_id,
        "user_email": target_user.correo,
        "user_full_name": getattr(target_user, 'nombre_completo', target_user.correo),
        "projects": [
            {
                "id": p.id,
                "name": p.nombre,
                "description": p.descripcion,
                "created_at": p.fecha_creacion
            }
            for p in projects
        ]
    }

@router.get("/projects/{project_id}")
def get_project_info(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de un proyecto específico.
    Los usuarios pueden ver sus propios proyectos.
    Los docentes pueden ver proyectos de sus estudiantes.
    """
    from app.models.user import Usuario
    from fastapi import HTTPException, status
    
    # Buscar el proyecto
    proyecto = db.query(Proyecto).filter(Proyecto.id == project_id).first()
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    # Verificar permisos
    es_dueno = proyecto.usuario_id == current_user.id
    es_docente_del_estudiante = False
    
    if current_user.rol == 'docente':
        # Verificar si el estudiante fue creado por este docente
        estudiante = db.query(Usuario).filter(Usuario.id == proyecto.usuario_id).first()
        if estudiante and estudiante.created_by == current_user.id:
            es_docente_del_estudiante = True
    
    if not es_dueno and not es_docente_del_estudiante:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este proyecto"
        )
    
    # Obtener información del dueño del proyecto
    dueno = db.query(Usuario).filter(Usuario.id == proyecto.usuario_id).first()
    
    return {
        "id": proyecto.id,
        "name": proyecto.nombre,
        "description": proyecto.descripcion,
        "created_at": proyecto.fecha_creacion,
        "usuario_id": proyecto.usuario_id,
        "usuario_email": dueno.correo if dueno else None
    }
