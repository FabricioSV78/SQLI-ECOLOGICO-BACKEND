from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core import detector
from app.config.config import settings
from app.services.dependencies import get_current_user
from app.services.db_service import get_db
from app.services.visualizar_grafo_service import visualizar_grafo
from app.services.analysis_service import get_project_analysis_results, get_project_vulnerability_summary
from app.services.analysis_metrics_service import AnalysisMetricsService, AnalysisTimer
from app.models.vulnerability import Vulnerability
import os

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/{project_id}")
def analyze_project(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Ejecuta el análisis de un proyecto y guarda vulnerabilidades en BD.
    También registra las métricas de análisis automáticamente.
    """
    # Inicializar servicios
    metrics_service = AnalysisMetricsService(db)
    
    # Medir tiempo de análisis
    with AnalysisTimer() as timer:
        # Usar siempre la ruta absoluta de uploads
        upload_dir = settings.UPLOAD_DIR
        results = detector.run_analysis(project_id, upload_dir, db, current_user.id)
    
    # Calcular métricas después del análisis
    analysis_time = timer.get_elapsed_time()
    
    # Contar vulnerabilidades detectadas
    vulnerable_count = db.query(Vulnerability).filter(
        Vulnerability.project_id == int(project_id),
        Vulnerability.prediction == 'vulnerable'
    ).count()
    
    # Guardar métricas en la base de datos
    try:
        metrics = metrics_service.create_metrics(
            id_proyecto=int(project_id),
            tiempo_analisis=analysis_time,
            vulnerabilidades_detectadas=vulnerable_count
        )
        
        # Agregar información de métricas a la respuesta
        results["metricas_analisis"] = {
            "id": metrics.id,
            "tiempo_analisis": metrics.tiempo_analisis,
            "costo": metrics.costo,
            "detecciones_correctas": metrics.detecciones_correctas,
            "vulnerabilidades_detectadas": metrics.vulnerabilidades_detectadas,
            "total_archivos_analizados": metrics.total_archivos_analizados,
            "porcentaje_vulnerabilidades": metrics.porcentaje_vulnerabilidades,
            "precision": metrics.precision
        }
        
    except Exception as e:
        # Si hay error guardando métricas, no fallar el análisis
        results["error_metricas"] = f"Error guardando métricas: {str(e)}"
    
    return results

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
            return FileResponse(image_path, media_type="image/png")
        else:
            return {"status": "error", "message": "No se pudo generar la imagen del grafo."}
    return {"status": "error", "message": "No hay grafo para este proyecto."}

@router.get("/{project_id}/results")
def get_analysis_results(project_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
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
                "costo": m.costo,
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
            "costo": latest_metrics.costo,
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

@router.get("/metrics/all")
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
                "id_proyecto": m.id_proyecto,
                "tiempo_analisis": m.tiempo_analisis,
                "costo": m.costo,
                "detecciones_correctas": m.detecciones_correctas,
                "vulnerabilidades_detectadas": m.vulnerabilidades_detectadas,
                "total_archivos_analizados": m.total_archivos_analizados,
                "porcentaje_vulnerabilidades": m.porcentaje_vulnerabilidades,
                "precision": m.precision
            }
            for m in all_metrics
        ]
    }