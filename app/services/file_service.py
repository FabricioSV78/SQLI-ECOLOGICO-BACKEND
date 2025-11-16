import os
import shutil
import zipfile
import logging
import tempfile
from io import BytesIO
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

    # Procesar el ZIP en un directorio temporal (no mantener en UPLOAD_DIR)
    file_content = file.file.read()
    file_size = len(file_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, file.filename)
        # Guardar ZIP temporalmente para permitir el escaneo (SRF3)
        with open(zip_path, 'wb') as f:
            f.write(file_content)

        # 🔍 SRF3: Escaneo de seguridad automático antes del análisis
        if settings.SECURITY_SCAN_ENABLED:
            logger.info(f"🔐 SRF3: Iniciando escaneo de seguridad para {file.filename}")
            is_safe, scan_result = scan_uploaded_zip(zip_path, settings.QUARANTINE_DIR)
            if not is_safe:
                # Archivo rechazado por SRF3 - eliminar proyecto y lanzar error
                db.delete(new_project)
                db.commit()
                # Si el escáner movió el archivo a cuarentena, ya está gestionado
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

        # Extraer ZIP en temporal dentro de un subdirectorio con el id del proyecto
        extract_parent = os.path.join(tmpdir, 'extracted')
        os.makedirs(extract_parent, exist_ok=True)
        project_extract_dir = os.path.join(extract_parent, str(new_project.id))
        os.makedirs(project_extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(project_extract_dir)

        # Ejecutar análisis inmediatamente contra el directorio temporal
        try:
            from app.core import detector
            # detector.run_analysis espera project_id y project_path (project_path debe contener la carpeta <project_id>)
            detector.run_analysis(str(new_project.id), extract_parent, db, user_id)
        except Exception as e:
            # Si el análisis falla, no dejar archivos en disco y reportar
            db.delete(new_project)
            db.commit()
            logger.error(f"Error durante el análisis del proyecto {new_project.id}: {e}")
            raise

    # No se guarda el contenido del proyecto en UPLOAD_DIR; solo se mantiene la info en BD
    return {
        "project_path": None,
        "project": new_project,
        "file_size": file_size
    }


def eliminar_proyecto(project_id: str):
    """
    Elimina carpeta del proyecto.
    """
    project_path = os.path.join(settings.UPLOAD_DIR, project_id)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
