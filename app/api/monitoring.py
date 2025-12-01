"""
API endpoints para monitoreo de recursos del sistema
Expone métricas de CPU, RAM, disco y red en formato Prometheus
"""

from fastapi import APIRouter
from app.services.monitoring import generate_prometheus_metrics, get_system_info

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
def metrics_endpoint():
    """
    Endpoint para exportar métricas en formato Prometheus.
    
    Este endpoint expone métricas del sistema que pueden ser consumidas por:
    - Prometheus (para recolección de métricas)
    - Grafana (para visualización)
    - Cualquier herramienta compatible con formato Prometheus
    
    Métricas expuestas:
    - cpu_usage_percent: Uso de CPU en porcentaje
    - cpu_cores_total: Número total de núcleos de CPU
    - ram_usage_percent: Uso de RAM en porcentaje
    - ram_total_bytes: Memoria RAM total en bytes
    - ram_available_bytes: Memoria RAM disponible en bytes
    - ram_used_bytes: Memoria RAM utilizada en bytes
    - disk_usage_percent: Uso de disco en porcentaje
    - disk_total_bytes: Espacio total de disco en bytes
    - disk_free_bytes: Espacio libre de disco en bytes
    - network_bytes_sent_total: Total de bytes enviados por red
    - network_bytes_recv_total: Total de bytes recibidos por red
    
    Returns:
        Response con métricas en formato Prometheus
    """
    return generate_prometheus_metrics()


@router.get("/system-info")
def system_info_endpoint():
    """
    Endpoint para obtener información del sistema en formato JSON.
    
    Útil para:
    - Debugging
    - Monitoreo manual
    - Dashboards personalizados
    - Verificación rápida del estado del sistema
    
    Returns:
        Dict con información detallada del sistema (CPU, RAM, disco, red)
    """
    return get_system_info()


@router.get("/health/resources")
def resource_health_check():
    """
    Health check específico para recursos del sistema.
    
    Devuelve el estado de salud basado en umbrales:
    - CPU > 90% = warning
    - RAM > 90% = warning
    - Disco > 90% = warning
    
    Returns:
        Dict con estado de salud y alertas si existen
    """
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    status = "healthy"
    warnings = []
    
    # Verificar umbrales
    if cpu_percent > 90:
        status = "warning"
        warnings.append(f"CPU usage high: {cpu_percent}%")
    
    if memory.percent > 90:
        status = "warning"
        warnings.append(f"RAM usage high: {memory.percent}%")
    
    if disk.percent > 90:
        status = "warning"
        warnings.append(f"Disk usage high: {disk.percent}%")
    
    return {
        "status": status,
        "resources": {
            "cpu_percent": cpu_percent,
            "ram_percent": memory.percent,
            "disk_percent": disk.percent
        },
        "warnings": warnings if warnings else None
    }
