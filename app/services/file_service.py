import os
import shutil
import zipfile
import logging
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.config.config import settings
from app.models.project import Proyecto
from app.services.security_scanner import scan_uploaded_zip

logger = logging.getLogger(__name__)

def save_project_file(project_id: str, file: UploadFile, user_id: int, db: Session):
    """
    Guarda un proyecto subido como ZIP, lo descomprime y lo registra en la base de datos.
    """
    # Verificar si ya existe un proyecto con ese nombre para el usuario
    """ existing = db.query(Proyecto).filter(Proyecto.nombre == project_id, Proyecto.usuario_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un proyecto con ese nombre para este usuario.") """

    # Registrar en la base de datos
    new_project = Proyecto(nombre =project_id, usuario_id =user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Crear directorio base de uploads si no existe
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Guardar archivos en carpeta del proyecto
    project_path = os.path.join(settings.UPLOAD_DIR, str(new_project.id))
    os.makedirs(project_path, exist_ok=True)

    zip_path = os.path.join(project_path, file.filename)
    
    # Leer el contenido del archivo correctamente
    file_content = file.file.read()
    file_size = len(file_content)
    with open(zip_path, "wb") as f:
        f.write(file_content)
    
    # Resetear el puntero del archivo para uso posterior si es necesario
    file.file.seek(0)
    
    logger.info(f"📁 Archivo guardado: {zip_path} ({file_size} bytes)")

    # 🔍 SRF3: Escaneo de seguridad automático antes del análisis
    if settings.SECURITY_SCAN_ENABLED:
        logger.info(f"🔐 SRF3: Iniciando escaneo de seguridad para {file.filename}")
        
        is_safe, scan_result = scan_uploaded_zip(zip_path, settings.QUARANTINE_DIR)
        
        if not is_safe:
            # Archivo rechazado por SRF3 - eliminar proyecto y lanzar error
            db.delete(new_project)
            db.commit()
            
            # Limpiar directorio del proyecto
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
            
            # Error detallado con información de amenazas
            threats_summary = []
            for threat in scan_result.get('threats_found', [])[:3]:
                threats_summary.append(f"• {threat['file']}: {threat['reason']}")
            
            error_msg = (
                f"SRF3: Archivo rechazado por contener binarios o contenido peligroso. "
                f"Amenazas detectadas: {len(scan_result.get('threats_found', []))}. "
                f"Detalles: {'; '.join(threats_summary)}"
            )
            
            logger.warning(f"❌ SRF3: {error_msg}")
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "SRF3_SECURITY_VIOLATION",
                    "message": "Archivo rechazado por escaneo de seguridad",
                    "details": error_msg,
                    "scan_result": scan_result
                }
            )
        else:
            logger.info(f"✅ SRF3: Archivo {file.filename} aprobado para procesamiento")

    # Extraer ZIP (solo si pasó el escaneo de seguridad)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(project_path)

    # Eliminar ZIP luego de descomprimir
    os.remove(zip_path)


    return {
        "project_path": project_path, 
        "project": new_project,
        "file_size": file_size if 'file_size' in locals() else 0
    }


def eliminar_proyecto(project_id: str):
    """
    Elimina carpeta del proyecto.
    """
    project_path = os.path.join(settings.UPLOAD_DIR, project_id)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
