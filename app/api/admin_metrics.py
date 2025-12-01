"""
API endpoints para métricas administrativas.
Proporciona estadísticas del sistema para el panel de administración.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.services.db_service import get_db
from app.services.dependencies import require_teacher_or_admin
from app.services.admin_metrics_service import AdminMetricsService
from app.models.user import Usuario

router = APIRouter(prefix="/admin", tags=["admin-metrics"])


@router.get("/metrics")
def get_admin_metrics(
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas completas del sistema para el panel de administración.
    
    Accesible para usuarios con rol de administrador o docente.
    Los docentes solo ven métricas de sus estudiantes.
    
    Métricas incluidas:
    - Usuarios conectados actualmente (últimas 24h)
    - Distribución de usuarios por rol
    - Estadísticas de proyectos (total, recientes, analizados)
    - Tamaño de archivos y proyectos subidos
    - Tiempo promedio de análisis
    - Estadísticas de vulnerabilidades detectadas
    - Consumo energético del sistema
    - Salud general del sistema
    - Actividad reciente
    
    Args:
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas completas del sistema (filtradas por rol)
    """
    try:
        # Pasar el ID y rol del usuario para filtrar métricas si es docente
        metrics = AdminMetricsService.get_complete_dashboard_metrics(
            db, 
            user_id=current_user.id, 
            user_role=current_user.rol.value
        )
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas: {str(e)}"
        )


@router.get("/metrics/users")
def get_user_metrics(
    hours: Optional[int] = Query(24, ge=1, le=168, description="Horas para considerar usuarios activos"),
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas específicas de usuarios.
    
    Args:
        hours: Número de horas para considerar un usuario como activo (1-168)
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas de usuarios
    """
    try:
        active_users = AdminMetricsService.get_active_users_count(db, hours)
        users_by_role = AdminMetricsService.get_total_users_by_role(db)
        
        return {
            "status": "success",
            "data": {
                "usuarios_activos": {
                    "cantidad": active_users,
                    "periodo_horas": hours
                },
                "distribucion_por_rol": users_by_role
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas de usuarios: {str(e)}"
        )


@router.get("/metrics/projects")
def get_project_metrics(
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas específicas de proyectos.
    
    Args:
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas de proyectos
    """
    try:
        project_stats = AdminMetricsService.get_projects_statistics(db)
        file_stats = AdminMetricsService.get_project_files_size_statistics(db)
        
        return {
            "status": "success",
            "data": {
                "proyectos": project_stats,
                "archivos": file_stats
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas de proyectos: {str(e)}"
        )


@router.get("/metrics/analysis")
def get_analysis_metrics(
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas específicas de análisis realizados.
    
    Args:
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas de análisis
    """
    try:
        analysis_stats = AdminMetricsService.get_analysis_time_statistics(db)
        cost_stats = AdminMetricsService.get_cost_statistics(db)
        
        return {
            "status": "success",
            "data": {
                "tiempos": analysis_stats,
                "costos": cost_stats
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas de análisis: {str(e)}"
        )


@router.get("/metrics/vulnerabilities")
def get_vulnerability_metrics(
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas específicas de vulnerabilidades detectadas.
    
    Args:
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas de vulnerabilidades
    """
    try:
        vuln_stats = AdminMetricsService.get_vulnerability_statistics(db)
        
        return {
            "status": "success",
            "data": vuln_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas de vulnerabilidades: {str(e)}"
        )


@router.get("/metrics/health")
def get_system_health(
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas de salud del sistema.
    
    Args:
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Métricas de salud del sistema
    """
    try:
        health_stats = AdminMetricsService.get_system_health(db)
        
        return {
            "status": "success",
            "data": health_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas de salud: {str(e)}"
        )


@router.get("/metrics/activity")
def get_recent_activity(
    limit: Optional[int] = Query(10, ge=1, le=50, description="Número de actividades a mostrar"),
    current_user: Usuario = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene la actividad reciente del sistema.
    
    Args:
        limit: Número máximo de actividades a retornar (1-50)
        current_user: Usuario administrador o docente autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Lista de actividades recientes
    """
    try:
        activities = AdminMetricsService.get_recent_activity(db, limit)
        
        return {
            "status": "success",
            "data": {
                "actividades": activities,
                "total": len(activities)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener actividad reciente: {str(e)}"
        )
