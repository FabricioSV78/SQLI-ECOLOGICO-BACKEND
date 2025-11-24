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
            import time
            from app.core import detector
            from app.services.analysis_metrics_service import AnalysisMetricsService
            from app.services.energy_monitor import EnergyMonitor
            from app.models.vulnerability import Vulnerabilidad
            
            # Medir tiempo de análisis y consumo energético
            with EnergyMonitor() as em:
                # detector.run_analysis espera project_id y project_path (project_path debe contener la carpeta <project_id>)
                results = detector.run_analysis(str(new_project.id), extract_parent, db, user_id)
            
            # Obtener métricas energéticas y tiempo
            energy_metrics = em.get_metrics()
            analysis_time = energy_metrics.get('elapsed_seconds', 0.0)
            consumo_kwh = energy_metrics.get('total_kwh', 0.0)
            
            # Contar vulnerabilidades detectadas
            vulnerable_count = db.query(Vulnerabilidad).filter(
                Vulnerabilidad.proyecto_id == new_project.id,
                Vulnerabilidad.prediccion == 'vulnerable'
            ).count()
            
            # Guardar métricas en la base de datos
            try:
                metrics_service = AnalysisMetricsService(db)
                metrics_service.create_metrics(
                    id_proyecto=new_project.id,
                    tiempo_analisis=analysis_time,
                    vulnerabilidades_detectadas=vulnerable_count,
                    consumo_energetico_kwh=consumo_kwh
                )
                logger.info(f"📊 Métricas guardadas para proyecto {new_project.id}: {analysis_time:.2f}s, {consumo_kwh:.8f} kWh, {vulnerable_count} vulnerabilidades")
            except Exception as metrics_error:
                # Si hay error guardando métricas, no fallar el análisis
                logger.warning(f"⚠️ Error guardando métricas para proyecto {new_project.id}: {str(metrics_error)}")
            
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
