from fastapi import APIRouter, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core import detector
from app.config.config import settings
from app.services.dependencies import get_current_user
from app.services.db_service import get_db
from app.services.visualizar_grafo_service import visualizar_grafo
from app.services.analysis_service import get_project_analysis_results, get_project_vulnerability_summary
from app.services.analysis_metrics_service import AnalysisMetricsService, AnalysisTimer
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.models.vulnerability import Vulnerability
from app.models.project import Proyecto
import os
import shutil
from app.services.energy_monitor import EnergyMonitor
from app.services.profiler import Profiler

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/all-metrics")
def get_all_metrics(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtiene todas las métricas de análisis de todos los proyectos del usuario.
    """
    metrics_service = AnalysisMetricsService(db)
    all_metrics = metrics_service.get_all_metrics()
    
    return {
        "total_metricas": len(all_metrics),
        "metricas": [
            {
                "id": m.id,
                "id_proyecto": m.proyecto_id,
                "tiempo_analisis": m.tiempo_analisis,
                "consumo_energetico_kwh": m.consumo_energetico_kwh,
                "detecciones_correctas": m.detecciones_correctas,
                "vulnerabilidades_detectadas": m.vulnerabilidades_detectadas,
                "total_archivos_analizados": m.total_archivos_analizados,
                "porcentaje_vulnerabilidades": m.porcentaje_vulnerabilidades,
                "precision": m.precision
            }
            for m in all_metrics
        ]
    }

@router.get("/{project_id}")
def analizar_proyecto(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db), profile: int = Query(0, description="Set 1 to enable profiling for this request")):
    """
    Ejecuta el análisis de un proyecto y guarda vulnerabilidades en BD.
    También registra las métricas de análisis automáticamente.
    Los docentes pueden analizar proyectos de sus estudiantes.
    """
    try:
        # Inicializar servicios
        metrics_service = AnalysisMetricsService(db)

        # Si el proyecto ya fue analizado y tenemos vulnerabilidades en la BD,
        # devolver los resultados desde la base de datos en lugar de volver a
        # ejecutar el análisis (evita fallos cuando los archivos temporales
        # ya no están disponibles tras el procesamiento en save_project_file).
        try:
            from app.models.vulnerability import Vulnerabilidad
            # Determinar proyecto en BD
            proyecto_obj = None
            if project_id.isdigit():
                proyecto_obj = db.query(Proyecto).filter(Proyecto.id == int(project_id)).first()
            else:
                proyecto_obj = db.query(Proyecto).filter(Proyecto.nombre == project_id).first()

            if proyecto_obj:
                # Verificar permisos
                es_dueno = proyecto_obj.usuario_id == current_user.id
                es_docente_del_estudiante = False
                
                if current_user.rol == 'docente':
                    from app.models.user import Usuario
                    estudiante = db.query(Usuario).filter(Usuario.id == proyecto_obj.usuario_id).first()
                    if estudiante and estudiante.created_by == current_user.id:
                        es_docente_del_estudiante = True
                
                if not es_dueno and not es_docente_del_estudiante:
                    raise HTTPException(status_code=403, detail="No tienes permisos para analizar este proyecto.")
                
                vuln_count = db.query(Vulnerabilidad).filter(Vulnerabilidad.proyecto_id == proyecto_obj.id).count()
                if vuln_count > 0:
                    # Ya existen vulnerabilidades registradas; devolver resultados desde la BD
                    cached_results = get_project_analysis_results(project_id, current_user.id, db)
                    cached_results["cached_from_db"] = True
                    return cached_results
        except HTTPException:
            raise
        except Exception:
            # Si algo falla al consultar la BD para el atajo, continuar con el análisis normal
            pass

        # Medir tiempo de análisis y estimar consumo energético
        upload_dir = settings.UPLOAD_DIR
        enable_profiling = bool(profile) or os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        profiler_summary = None
        profiler_files = {}
        with AnalysisTimer() as timer:
            with EnergyMonitor() as em:
                # Usar siempre la ruta absoluta de uploads
                if enable_profiling:
                    with Profiler(enabled=True, output_dir=settings.REPORTS_DIR) as pr:
                        results = detector.run_analysis(project_id, upload_dir, db, current_user.id)
                    profiler_summary = pr.get_text_summary()
                    profiler_files["prof_file"] = pr.get_stats_file()
                    profiler_files["txt_file"] = pr.get_text_file()
                else:
                    results = detector.run_analysis(project_id, upload_dir, db, current_user.id)
        # Calcular métricas después del análisis
        analysis_time = timer.get_elapsed_time()
        # Obtener métricas energéticas estimadas por el análisis
        energy_metrics = em.get_metrics()
        
        # Contar vulnerabilidades detectadas
        vulnerable_count = db.query(Vulnerability).filter(
            Vulnerability.proyecto_id == int(project_id),
            Vulnerability.prediccion == 'vulnerable'
        ).count()
        
        # 📝 SRF5: Log de análisis exitoso
        """ if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.ANALYSIS,
                result=AuditResult.SUCCESS,
                details={
                    "project_id": project_id,
                    "analysis_time_seconds": round(analysis_time, 2),
                    "vulnerabilities_found": vulnerable_count,
                    "files_analyzed": len(results.get('files', [])),
                    "total_lines_analyzed": sum(f.get('lines_count', 0) for f in results.get('files', []))
                },
                audit_dir=settings.AUDIT_DIR
            ) """
        
        # Guardar métricas en la base de datos
        try:
            # Obtener consumo energético del monitor
            consumo_kwh = energy_metrics.get('total_kwh', 0.0)
            
            metrics = metrics_service.create_metrics(
                id_proyecto=int(project_id),
                tiempo_analisis=analysis_time,
                vulnerabilidades_detectadas=vulnerable_count,
                consumo_energetico_kwh=consumo_kwh
            )
            
            # Agregar información de métricas a la respuesta
            results["metricas_analisis"] = {
                "id": metrics.id,
                "tiempo_analisis": metrics.tiempo_analisis,
                "consumo_energetico_kwh": metrics.consumo_energetico_kwh,
                "detecciones_correctas": metrics.detecciones_correctas,
                "vulnerabilidades_detectadas": metrics.vulnerabilidades_detectadas,
                "total_archivos_analizados": metrics.total_archivos_analizados,
                "porcentaje_vulnerabilidades": metrics.porcentaje_vulnerabilidades,
                "precision": metrics.precision
            }
            # Añadir métricas energéticas estimadas (no persistidas en BD)
            try:
                results["metricas_analisis"]["energia_kwh"] = round(energy_metrics.get("total_kwh", 0.0), 8)
                results["metricas_analisis"]["emisiones_kg_co2e"] = round(energy_metrics.get("emissions_kg", energy_metrics.get("emissions_kg", energy_metrics.get("emissions_kg", 0.0))), 6) if energy_metrics else 0.0
                results["metricas_analisis"]["energia_detalle"] = energy_metrics
                # Añadir resumen y archivos de profiling si existen
                if profiler_summary:
                    results["metricas_analisis"]["profiling_summary"] = profiler_summary
                    results["metricas_analisis"]["profiling_files"] = profiler_files
            except Exception:
                # Si algo falla incluyendo métricas energéticas, no interrumpir el flujo
                pass
            
        except Exception as e:
            # Si hay error guardando métricas, no fallar el análisis
            results["error_metricas"] = f"Error guardando métricas: {str(e)}"
        # Eliminar archivos subidos del proyecto si la configuración lo indica
        try:
            from app.config.config import settings
            if settings.REMOVE_UPLOADS_AFTER_ANALYSIS:
                upload_project_dir = os.path.join(settings.UPLOAD_DIR, str(project_id))
                if os.path.isdir(upload_project_dir):
                    try:
                        shutil.rmtree(upload_project_dir)
                    except Exception:
                        # Si no se puede eliminar, simplemente ignorar para evitar fallos de análisis
                        pass
        except Exception:
            pass
        
        return results
        
    except Exception as e:
        # 📝 SRF5: Log de análisis fallido
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.ANALYSIS,
                result=AuditResult.ERROR,
                details={
                    "project_id": project_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                audit_dir=settings.AUDIT_DIR
            )
        raise e

@router.get("/{project_id}/graph")
def get_graph(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Devuelve la imagen del grafo de vulnerabilidad para el proyecto analizado.
    """
    upload_dir = settings.UPLOAD_DIR
    results = detector.run_analysis(project_id, upload_dir, db, current_user.id)
    flow_graph = results.get('flow_graph')
    if flow_graph:
        image_path = f"/tmp/{project_id}_graph.png"
        visualizar_grafo(flow_graph, save_path=image_path)
        if os.path.exists(image_path):
            # 📝 SRF5: Log de descarga exitosa del grafo
            if settings.AUDIT_ENABLED:
                log_user_action(
                    user_id=current_user.id,
                    username=current_user.correo,
                    action=AuditAction.DOWNLOAD,
                    result=AuditResult.SUCCESS,
                    details={
                        "project_id": project_id,
                        "download_type": "vulnerability_graph",
                        "file_format": "png",
                        "file_path": image_path
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            # Entregar el archivo y programar su eliminación en background para evitar almacenamiento redundante
            from fastapi import BackgroundTasks
            bg = BackgroundTasks()
            # Añadir tarea en background para eliminar el archivo después de servirlo
            def _safe_remove(path: str):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

            bg.add_task(_safe_remove, image_path)
            return FileResponse(image_path, media_type="image/png", background=bg)
        else:
            # 📝 SRF5: Log de error en descarga
            if settings.AUDIT_ENABLED:
                log_user_action(
                    user_id=current_user.id,
                    username=current_user.correo,
                    action=AuditAction.DOWNLOAD,
                    result=AuditResult.ERROR,
                    details={
                        "project_id": project_id,
                        "download_type": "vulnerability_graph",
                        "error": "No se pudo generar la imagen del grafo"
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            return {"status": "error", "message": "No se pudo generar la imagen del grafo."}
    
    # 📝 SRF5: Log de descarga fallida (no hay grafo)
    if settings.AUDIT_ENABLED:
        log_user_action(
            user_id=current_user.id,
            username=current_user.correo,
            action=AuditAction.DOWNLOAD,
            result=AuditResult.FAILURE,
            details={
                "project_id": project_id,
                "download_type": "vulnerability_graph",
                "error": "No hay grafo para este proyecto"
            },
            audit_dir=settings.AUDIT_DIR
        )
    return {"status": "error", "message": "No hay grafo para este proyecto."}

@router.get("/{project_id}/results")
def obtener_resultados_analisis(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtiene los resultados detallados del análisis de un proyecto desde la base de datos.
    Incluye archivos vulnerables, código completo, fragmentos vulnerables y predicciones.
    """
    return get_project_analysis_results(project_id, current_user.id, db)

@router.get("/{project_id}/summary")
def get_analysis_summary(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtiene un resumen de vulnerabilidades del proyecto analizado.
    """
    return get_project_vulnerability_summary(project_id, current_user.id, db)

@router.get("/{project_id}/metrics")
def get_project_metrics(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtiene todas las métricas de análisis de un proyecto específico.
    """
    metrics_service = AnalysisMetricsService(db)
    metrics_list = metrics_service.get_metrics_by_project(int(project_id))
    
    return {
        "id_proyecto": project_id,
        "cantidad_metricas": len(metrics_list),
        "metricas": [
            {
                "id": m.id,
                "tiempo_analisis": m.tiempo_analisis,
                "consumo_energetico_kwh": m.consumo_energetico_kwh,
                "detecciones_correctas": m.detecciones_correctas,
                "vulnerabilidades_detectadas": m.vulnerabilidades_detectadas,
                "total_archivos_analizados": m.total_archivos_analizados,
                "porcentaje_vulnerabilidades": m.porcentaje_vulnerabilidades,
                "precision": m.precision
            }
            for m in metrics_list
        ]
    }

@router.get("/{project_id}/metrics/latest")
def get_latest_project_metrics(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtiene las métricas más recientes de un proyecto.
    """
    metrics_service = AnalysisMetricsService(db)
    latest_metrics = metrics_service.get_latest_metrics(int(project_id))
    
    if not latest_metrics:
        return {"mensaje": "No se encontraron métricas para este proyecto"}
    
    return {
        "id_proyecto": project_id,
        "metricas": {
            "id": latest_metrics.id,
            "tiempo_analisis": latest_metrics.tiempo_analisis,
            "consumo_energetico_kwh": latest_metrics.consumo_energetico_kwh,
            "detecciones_correctas": latest_metrics.detecciones_correctas,
            "vulnerabilidades_detectadas": latest_metrics.vulnerabilidades_detectadas,
            "total_archivos_analizados": latest_metrics.total_archivos_analizados,
            "porcentaje_vulnerabilidades": latest_metrics.porcentaje_vulnerabilidades,
            "precision": latest_metrics.precision
        }
    }

@router.put("/metrics/{metrics_id}/precision")
def update_metrics_precision(
    metrics_id: int, 
    precision: float,
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Actualiza la precisión de una entrada de métricas específica.
    """
    metrics_service = AnalysisMetricsService(db)
    updated_metrics = metrics_service.update_precision(metrics_id, precision)
    
    if not updated_metrics:
        return {"error": "Métricas no encontradas"}
    
    return {
        "mensaje": "Precisión actualizada correctamente",
        "metricas": {
            "id": updated_metrics.id,
            "precision": updated_metrics.precision
        }
    }

@router.put("/metrics/{metrics_id}/detecciones-correctas")
def update_metrics_detecciones_correctas(
    metrics_id: int, 
    detecciones_correctas: int,
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Actualiza las detecciones correctas de una entrada de métricas específica.
    """
    metrics_service = AnalysisMetricsService(db)
    updated_metrics = metrics_service.update_detecciones_correctas(metrics_id, detecciones_correctas)
    
    if not updated_metrics:
        return {"error": "Métricas no encontradas"}
    
    return {
        "mensaje": "Detecciones correctas actualizadas correctamente",
        "metricas": {
            "id": updated_metrics.id,
            "detecciones_correctas": updated_metrics.detecciones_correctas
        }
    }
