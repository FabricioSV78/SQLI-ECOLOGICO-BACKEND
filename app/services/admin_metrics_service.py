"""
Servicio para calcular métricas administrativas del sistema.
Proporciona estadísticas clave para el panel de administración.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

from app.models.user import Usuario
from app.models.project import Proyecto
from app.models.project_file import ProjectFile
from app.models.analysis_metrics import MetricasAnalisis
from app.models.vulnerability import Vulnerabilidad
from app.models.user_role import UserRole


class AdminMetricsService:
    """Servicio para calcular métricas del sistema para administradores."""
    
    @staticmethod
    def get_active_users_count(db: Session, hours: int = 24) -> int:
        """
        Obtiene el número de usuarios activos en las últimas N horas.
        
        Args:
            db: Sesión de base de datos
            hours: Número de horas para considerar un usuario como activo
            
        Returns:
            int: Cantidad de usuarios activos
        """
        threshold = datetime.utcnow() - timedelta(hours=hours)
        active_users = db.query(Usuario).filter(
            Usuario.ultimo_acceso >= threshold,
            Usuario.activo == True
        ).count()
        return active_users
    
    @staticmethod
    def get_total_users_by_role(db: Session) -> Dict[str, int]:
        """
        Obtiene el total de usuarios por rol.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Diccionario con cantidad por rol
        """
        roles_count = db.query(
            Usuario.rol,
            func.count(Usuario.id).label('count')
        ).group_by(Usuario.rol).all()
        
        return {
            "estudiantes": next((r.count for r in roles_count if r.rol == UserRole.ESTUDIANTE), 0),
            "docentes": next((r.count for r in roles_count if r.rol == UserRole.DOCENTE), 0),
            "administradores": next((r.count for r in roles_count if r.rol == UserRole.ADMINISTRADOR), 0),
            "total": sum(r.count for r in roles_count)
        }
    
    @staticmethod
    def get_projects_statistics(db: Session) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre proyectos en el sistema.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de proyectos
        """
        total_projects = db.query(Proyecto).count()
        
        # Proyectos creados en los últimos 7 días
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_projects = db.query(Proyecto).filter(
            Proyecto.fecha_creacion >= last_week
        ).count()
        
        # Proyectos analizados (con métricas)
        analyzed_projects = db.query(Proyecto).join(
            MetricasAnalisis
        ).distinct().count()
        
        return {
            "total": total_projects,
            "recientes_7_dias": recent_projects,
            "analizados": analyzed_projects,
            "sin_analizar": total_projects - analyzed_projects
        }
    
    @staticmethod
    def get_project_files_size_statistics(db: Session) -> Dict[str, Any]:
        """
        Calcula estadísticas sobre el tamaño de los archivos de proyectos.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de tamaño de archivos
        """
        files = db.query(ProjectFile).all()
        
        if not files:
            return {
                "total_archivos": 0,
                "tamano_total_mb": 0.0,
                "tamano_total_kb": 0.0,
                "tamano_total_bytes": 0,
                "tamano_promedio_kb": 0.0,
                "tamano_promedio_bytes": 0.0,
                "tamano_maximo_mb": 0.0,
                "tamano_maximo_kb": 0.0
            }
        
        # Calcular tamaños
        sizes_bytes = []
        for file in files:
            if file.contenido:
                # Calcular el tamaño del contenido en bytes
                size = len(file.contenido.encode('utf-8'))
                sizes_bytes.append(size)
        
        if not sizes_bytes:
            return {
                "total_archivos": len(files),
                "tamano_total_mb": 0.0,
                "tamano_total_kb": 0.0,
                "tamano_total_bytes": 0,
                "tamano_promedio_kb": 0.0,
                "tamano_promedio_bytes": 0.0,
                "tamano_maximo_mb": 0.0,
                "tamano_maximo_kb": 0.0
            }
        
        total_bytes = sum(sizes_bytes)
        avg_bytes = total_bytes / len(sizes_bytes)
        max_bytes = max(sizes_bytes)
        
        return {
            "total_archivos": len(files),
            "tamano_total_mb": round(total_bytes / (1024 * 1024), 2),
            "tamano_total_kb": round(total_bytes / 1024, 2),
            "tamano_total_bytes": total_bytes,
            "tamano_promedio_kb": round(avg_bytes / 1024, 2),
            "tamano_promedio_bytes": round(avg_bytes, 2),
            "tamano_maximo_mb": round(max_bytes / (1024 * 1024), 2),
            "tamano_maximo_kb": round(max_bytes / 1024, 2)
        }
    
    @staticmethod
    def get_analysis_time_statistics(db: Session) -> Dict[str, Any]:
        """
        Calcula estadísticas sobre tiempos de análisis.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de tiempos de análisis
        """
        metrics = db.query(MetricasAnalisis).all()
        
        if not metrics:
            return {
                "total_analisis": 0,
                "tiempo_promedio_segundos": 0.0,
                "tiempo_promedio_ms": 0.0,
                "tiempo_total_minutos": 0.0,
                "tiempo_total_segundos": 0.0,
                "tiempo_minimo_segundos": 0.0,
                "tiempo_minimo_ms": 0.0,
                "tiempo_maximo_segundos": 0.0,
                "tiempo_maximo_ms": 0.0
            }
        
        times = [m.tiempo_analisis for m in metrics]
        
        return {
            "total_analisis": len(metrics),
            "tiempo_promedio_segundos": round(sum(times) / len(times), 2),
            "tiempo_promedio_ms": round((sum(times) / len(times)) * 1000, 2),
            "tiempo_total_minutos": round(sum(times) / 60, 2),
            "tiempo_total_segundos": round(sum(times), 2),
            "tiempo_minimo_segundos": round(min(times), 2),
            "tiempo_minimo_ms": round(min(times) * 1000, 2),
            "tiempo_maximo_segundos": round(max(times), 2),
            "tiempo_maximo_ms": round(max(times) * 1000, 2)
        }
    
    @staticmethod
    def get_vulnerability_statistics(db: Session) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre vulnerabilidades detectadas.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de vulnerabilidades
        """
        # Total de vulnerabilidades detectadas (prediccion = "vulnerable")
        total_vulnerabilities = db.query(Vulnerabilidad).filter(
            Vulnerabilidad.prediccion == "vulnerable"
        ).count()
        
        # Consultas seguras
        safe_queries = db.query(Vulnerabilidad).filter(
            Vulnerabilidad.prediccion == "safe"
        ).count()
        
        # Proyectos con al menos una vulnerabilidad
        projects_with_vulns = db.query(Vulnerabilidad.proyecto_id).filter(
            Vulnerabilidad.prediccion == "vulnerable"
        ).distinct().count()
        
        # Estadísticas por predicción (simular severidad)
        # Como no hay campo de severidad, usamos la predicción
        severity_counts = {
            "VULNERABLES": total_vulnerabilities,
            "SEGURAS": safe_queries
        }
        
        # Top archivos con más vulnerabilidades
        top_files = db.query(
            Vulnerabilidad.archivo,
            func.count(Vulnerabilidad.id).label('count')
        ).filter(
            Vulnerabilidad.prediccion == "vulnerable"
        ).group_by(
            Vulnerabilidad.archivo
        ).order_by(
            func.count(Vulnerabilidad.id).desc()
        ).limit(5).all()
        
        return {
            "total": total_vulnerabilities,
            "proyectos_con_vulnerabilidades": projects_with_vulns,
            "por_severidad": severity_counts,
            "tipos_mas_comunes": [
                {"tipo": f.archivo.split('/')[-1] if '/' in f.archivo else f.archivo, "cantidad": f.count}
                for f in top_files
            ] if top_files else []
        }
    
    @staticmethod
    def get_energy_statistics(db: Session) -> Dict[str, Any]:
        """
        Calcula estadísticas de consumo energético del sistema.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de consumo energético
        """
        metrics = db.query(MetricasAnalisis).all()
        
        if not metrics:
            return {
                "consumo_total_kwh": 0.0,
                "consumo_promedio_por_analisis_kwh": 0.0
            }
        
        energy_values = [m.consumo_energetico_kwh for m in metrics]
        
        return {
            "consumo_total_kwh": round(sum(energy_values), 8),
            "consumo_promedio_por_analisis_kwh": round(sum(energy_values) / len(energy_values), 8)
        }
    
    @staticmethod
    def get_recent_activity(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene la actividad reciente del sistema.
        
        Args:
            db: Sesión de base de datos
            limit: Número máximo de actividades a retornar
            
        Returns:
            list: Lista de actividades recientes
        """
        recent_projects = db.query(Proyecto).order_by(
            Proyecto.fecha_creacion.desc()
        ).limit(limit).all()
        
        activities = []
        for project in recent_projects:
            # Verificar si tiene análisis
            has_analysis = db.query(MetricasAnalisis).filter(
                MetricasAnalisis.proyecto_id == project.id
            ).first() is not None
            
            activities.append({
                "proyecto_id": project.id,
                "proyecto_nombre": project.nombre,
                "usuario_email": project.propietario.correo if project.propietario else "Desconocido",
                "fecha": project.fecha_creacion.isoformat(),
                "analizado": has_analysis
            })
        
        return activities
    
    @staticmethod
    def get_system_health(db: Session) -> Dict[str, Any]:
        """
        Obtiene métricas de salud del sistema.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            dict: Métricas de salud del sistema
        """
        # Usuarios activos vs inactivos
        total_users = db.query(Usuario).count()
        active_users = db.query(Usuario).filter(Usuario.activo == True).count()
        
        # Tasa de análisis exitosos
        total_metrics = db.query(MetricasAnalisis).count()
        
        # Proyectos activos (creados en el último mes)
        last_month = datetime.utcnow() - timedelta(days=30)
        active_projects = db.query(Proyecto).filter(
            Proyecto.fecha_creacion >= last_month
        ).count()
        
        return {
            "usuarios": {
                "total": total_users,
                "activos": active_users,
                "inactivos": total_users - active_users,
                "porcentaje_activos": round((active_users / total_users * 100) if total_users > 0 else 0, 2)
            },
            "analisis_completados": total_metrics,
            "proyectos_activos_ultimo_mes": active_projects
        }
    
    @staticmethod
    def get_teacher_students(db: Session, teacher_id: int) -> List[int]:
        """
        Obtiene los IDs de los estudiantes creados por un docente específico.
        
        Args:
            db: Sesión de base de datos
            teacher_id: ID del docente
            
        Returns:
            list: Lista de IDs de estudiantes
        """
        students = db.query(Usuario.id).filter(
            Usuario.created_by == teacher_id,
            Usuario.rol == UserRole.ESTUDIANTE
        ).all()
        return [s.id for s in students]
    
    @staticmethod
    def get_teacher_metrics(db: Session, teacher_id: int) -> Dict[str, Any]:
        """
        Obtiene métricas filtradas para un docente específico (solo sus estudiantes).
        
        Args:
            db: Sesión de base de datos
            teacher_id: ID del docente
            
        Returns:
            dict: Métricas filtradas del docente
        """
        # Obtener IDs de estudiantes del docente
        student_ids = AdminMetricsService.get_teacher_students(db, teacher_id)
        
        if not student_ids:
            # Si el docente no tiene estudiantes, retornar métricas vacías
            return {
                "usuarios": {
                    "activos_24h": 0,
                    "por_rol": {
                        "estudiantes": 0,
                        "docentes": 0,
                        "administradores": 0,
                        "total": 0
                    },
                    "registrados_hoy": 0
                },
                "proyectos": {
                    "total": 0,
                    "recientes_7_dias": 0,
                    "analizados": 0,
                    "sin_analizar": 0
                },
                "archivos": {
                    "total_archivos": 0,
                    "tamano_total_mb": 0.0,
                    "tamano_total_kb": 0.0,
                    "tamano_total_bytes": 0,
                    "tamano_promedio_kb": 0.0,
                    "tamano_promedio_bytes": 0.0,
                    "tamano_maximo_mb": 0.0,
                    "tamano_maximo_kb": 0.0
                },
                "analisis": {
                    "total_analisis": 0,
                    "tiempo_promedio_segundos": 0.0,
                    "tiempo_promedio_ms": 0.0,
                    "tiempo_total_minutos": 0.0,
                    "tiempo_total_segundos": 0.0,
                    "tiempo_minimo_segundos": 0.0,
                    "tiempo_minimo_ms": 0.0,
                    "tiempo_maximo_segundos": 0.0,
                    "tiempo_maximo_ms": 0.0
                },
                "vulnerabilidades": {
                    "total": 0,
                    "proyectos_con_vulnerabilidades": 0,
                    "por_severidad": {"VULNERABLES": 0, "SEGURAS": 0},
                    "tipos_mas_comunes": []
                },
                "energia": {
                    "consumo_total_kwh": 0.0,
                    "consumo_promedio_por_analisis_kwh": 0.0
                },
                "salud_sistema": {
                    "usuarios": {
                        "total": 0,
                        "activos": 0,
                        "inactivos": 0,
                        "porcentaje_activos": 0.0
                    },
                    "analisis_completados": 0,
                    "proyectos_activos_ultimo_mes": 0
                },
                "actividad_reciente": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Usuarios activos (solo estudiantes del docente)
        threshold = datetime.utcnow() - timedelta(hours=24)
        activos_24h = db.query(Usuario).filter(
            Usuario.id.in_(student_ids),
            Usuario.ultimo_acceso >= threshold,
            Usuario.activo == True
        ).count()
        
        # Total de estudiantes del docente
        total_students = len(student_ids)
        active_students = db.query(Usuario).filter(
            Usuario.id.in_(student_ids),
            Usuario.activo == True
        ).count()
        
        # Estudiantes registrados hoy
        registrados_hoy = db.query(Usuario).filter(
            Usuario.id.in_(student_ids),
            func.date(Usuario.fecha_creacion) == datetime.utcnow().date()
        ).count()
        
        # Proyectos de los estudiantes
        total_projects = db.query(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).count()
        
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_projects = db.query(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids),
            Proyecto.fecha_creacion >= last_week
        ).count()
        
        # Proyectos analizados (con métricas)
        project_ids = db.query(Proyecto.id).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).subquery()
        
        analyzed_projects = db.query(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).join(MetricasAnalisis).distinct().count()
        
        # Archivos de proyectos de estudiantes
        files = db.query(ProjectFile).join(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).all()
        
        # Calcular tamaños de archivos
        sizes_bytes = []
        for file in files:
            if file.contenido:
                size = len(file.contenido.encode('utf-8'))
                sizes_bytes.append(size)
        
        if sizes_bytes:
            total_bytes = sum(sizes_bytes)
            avg_bytes = total_bytes / len(sizes_bytes)
            max_bytes = max(sizes_bytes)
            archivos_stats = {
                "total_archivos": len(files),
                "tamano_total_mb": round(total_bytes / (1024 * 1024), 2),
                "tamano_total_kb": round(total_bytes / 1024, 2),
                "tamano_total_bytes": total_bytes,
                "tamano_promedio_kb": round(avg_bytes / 1024, 2),
                "tamano_promedio_bytes": round(avg_bytes, 2),
                "tamano_maximo_mb": round(max_bytes / (1024 * 1024), 2),
                "tamano_maximo_kb": round(max_bytes / 1024, 2)
            }
        else:
            archivos_stats = {
                "total_archivos": 0,
                "tamano_total_mb": 0.0,
                "tamano_total_kb": 0.0,
                "tamano_total_bytes": 0,
                "tamano_promedio_kb": 0.0,
                "tamano_promedio_bytes": 0.0,
                "tamano_maximo_mb": 0.0,
                "tamano_maximo_kb": 0.0
            }
        
        # Métricas de análisis
        metrics = db.query(MetricasAnalisis).join(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).all()
        
        if metrics:
            times = [m.tiempo_analisis for m in metrics]
            analisis_stats = {
                "total_analisis": len(metrics),
                "tiempo_promedio_segundos": round(sum(times) / len(times), 2),
                "tiempo_promedio_ms": round((sum(times) / len(times)) * 1000, 2),
                "tiempo_total_minutos": round(sum(times) / 60, 2),
                "tiempo_total_segundos": round(sum(times), 2),
                "tiempo_minimo_segundos": round(min(times), 2),
                "tiempo_minimo_ms": round(min(times) * 1000, 2),
                "tiempo_maximo_segundos": round(max(times), 2),
                "tiempo_maximo_ms": round(max(times) * 1000, 2)
            }
            
            # Consumo energético
            energy_values = [m.consumo_energetico_kwh for m in metrics]
            energia_stats = {
                "consumo_total_kwh": round(sum(energy_values), 8),
                "consumo_promedio_por_analisis_kwh": round(sum(energy_values) / len(energy_values), 8)
            }
        else:
            analisis_stats = {
                "total_analisis": 0,
                "tiempo_promedio_segundos": 0.0,
                "tiempo_promedio_ms": 0.0,
                "tiempo_total_minutos": 0.0,
                "tiempo_total_segundos": 0.0,
                "tiempo_minimo_segundos": 0.0,
                "tiempo_minimo_ms": 0.0,
                "tiempo_maximo_segundos": 0.0,
                "tiempo_maximo_ms": 0.0
            }
            energia_stats = {
                "consumo_total_kwh": 0.0,
                "consumo_promedio_por_analisis_kwh": 0.0
            }
        
        # Vulnerabilidades de proyectos de estudiantes
        student_project_ids = [p.id for p in db.query(Proyecto.id).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).all()]
        
        if student_project_ids:
            total_vulnerabilities = db.query(Vulnerabilidad).filter(
                Vulnerabilidad.proyecto_id.in_(student_project_ids),
                Vulnerabilidad.prediccion == "vulnerable"
            ).count()
            
            safe_queries = db.query(Vulnerabilidad).filter(
                Vulnerabilidad.proyecto_id.in_(student_project_ids),
                Vulnerabilidad.prediccion == "safe"
            ).count()
            
            projects_with_vulns = db.query(Vulnerabilidad.proyecto_id).filter(
                Vulnerabilidad.proyecto_id.in_(student_project_ids),
                Vulnerabilidad.prediccion == "vulnerable"
            ).distinct().count()
            
            top_files = db.query(
                Vulnerabilidad.archivo,
                func.count(Vulnerabilidad.id).label('count')
            ).filter(
                Vulnerabilidad.proyecto_id.in_(student_project_ids),
                Vulnerabilidad.prediccion == "vulnerable"
            ).group_by(
                Vulnerabilidad.archivo
            ).order_by(
                func.count(Vulnerabilidad.id).desc()
            ).limit(5).all()
            
            vulnerabilidades_stats = {
                "total": total_vulnerabilities,
                "proyectos_con_vulnerabilidades": projects_with_vulns,
                "por_severidad": {
                    "VULNERABLES": total_vulnerabilities,
                    "SEGURAS": safe_queries
                },
                "tipos_mas_comunes": [
                    {"tipo": f.archivo.split('/')[-1] if '/' in f.archivo else f.archivo, "cantidad": f.count}
                    for f in top_files
                ] if top_files else []
            }
        else:
            vulnerabilidades_stats = {
                "total": 0,
                "proyectos_con_vulnerabilidades": 0,
                "por_severidad": {"VULNERABLES": 0, "SEGURAS": 0},
                "tipos_mas_comunes": []
            }
        
        # Actividad reciente
        recent_projects_list = db.query(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids)
        ).order_by(Proyecto.fecha_creacion.desc()).limit(5).all()
        
        activities = []
        for project in recent_projects_list:
            has_analysis = db.query(MetricasAnalisis).filter(
                MetricasAnalisis.proyecto_id == project.id
            ).first() is not None
            
            activities.append({
                "proyecto_id": project.id,
                "proyecto_nombre": project.nombre,
                "usuario_email": project.propietario.correo if project.propietario else "Desconocido",
                "fecha": project.fecha_creacion.isoformat(),
                "analizado": has_analysis
            })
        
        # Salud del sistema (solo estudiantes del docente)
        last_month = datetime.utcnow() - timedelta(days=30)
        active_projects_month = db.query(Proyecto).filter(
            Proyecto.usuario_id.in_(student_ids),
            Proyecto.fecha_creacion >= last_month
        ).count()
        
        return {
            "usuarios": {
                "activos_24h": activos_24h,
                "por_rol": {
                    "estudiantes": total_students,
                    "docentes": 0,
                    "administradores": 0,
                    "total": total_students
                },
                "registrados_hoy": registrados_hoy
            },
            "proyectos": {
                "total": total_projects,
                "recientes_7_dias": recent_projects,
                "analizados": analyzed_projects,
                "sin_analizar": total_projects - analyzed_projects
            },
            "archivos": archivos_stats,
            "analisis": analisis_stats,
            "vulnerabilidades": vulnerabilidades_stats,
            "energia": energia_stats,
            "salud_sistema": {
                "usuarios": {
                    "total": total_students,
                    "activos": active_students,
                    "inactivos": total_students - active_students,
                    "porcentaje_activos": round((active_students / total_students * 100) if total_students > 0 else 0, 2)
                },
                "analisis_completados": len(metrics) if metrics else 0,
                "proyectos_activos_ultimo_mes": active_projects_month
            },
            "actividad_reciente": activities,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_complete_dashboard_metrics(db: Session, user_id: int = None, user_role: str = None) -> Dict[str, Any]:
        """
        Obtiene todas las métricas del dashboard en una sola consulta optimizada.
        Si es docente, filtra solo sus estudiantes.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario (para filtrar si es docente)
            user_role: Rol del usuario ('administrador' o 'docente')
            
        Returns:
            dict: Todas las métricas del dashboard
        """
        # Si es docente, retornar solo métricas de sus estudiantes
        if user_role == "docente" and user_id:
            return AdminMetricsService.get_teacher_metrics(db, user_id)
        
        # Si es administrador, retornar todas las métricas
        return {
            "usuarios": {
                "activos_24h": AdminMetricsService.get_active_users_count(db, hours=24),
                "por_rol": AdminMetricsService.get_total_users_by_role(db),
                "registrados_hoy": db.query(Usuario).filter(
                    func.date(Usuario.fecha_creacion) == datetime.utcnow().date()
                ).count()
            },
            "proyectos": AdminMetricsService.get_projects_statistics(db),
            "archivos": AdminMetricsService.get_project_files_size_statistics(db),
            "analisis": AdminMetricsService.get_analysis_time_statistics(db),
            "vulnerabilidades": AdminMetricsService.get_vulnerability_statistics(db),
            "energia": AdminMetricsService.get_energy_statistics(db),
            "salud_sistema": AdminMetricsService.get_system_health(db),
            "actividad_reciente": AdminMetricsService.get_recent_activity(db, limit=5),
            "timestamp": datetime.utcnow().isoformat()
        }
