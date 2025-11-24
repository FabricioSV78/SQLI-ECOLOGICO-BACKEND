"""
Servicio de monitoreo de recursos del sistema (CPU y RAM)
Implementa métricas Prometheus para monitoreo energético
"""

from prometheus_client import Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import psutil
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# === MÉTRICAS PROMETHEUS ===

# Métricas de CPU
cpu_usage = Gauge(
    "cpu_usage_percent", 
    "Uso de CPU en porcentaje"
)

cpu_cores = Gauge(
    "cpu_cores_total",
    "Número total de núcleos de CPU"
)

# Métricas de RAM
ram_usage = Gauge(
    "ram_usage_percent", 
    "Uso de RAM en porcentaje"
)

ram_total = Gauge(
    "ram_total_bytes",
    "Memoria RAM total en bytes"
)

ram_available = Gauge(
    "ram_available_bytes",
    "Memoria RAM disponible en bytes"
)

ram_used = Gauge(
    "ram_used_bytes",
    "Memoria RAM utilizada en bytes"
)

# Métricas de Disco
disk_usage = Gauge(
    "disk_usage_percent",
    "Uso de disco en porcentaje"
)

disk_total = Gauge(
    "disk_total_bytes",
    "Espacio total de disco en bytes"
)

disk_free = Gauge(
    "disk_free_bytes",
    "Espacio libre de disco en bytes"
)

# Métricas de red
network_bytes_sent = Counter(
    "network_bytes_sent_total",
    "Total de bytes enviados por red"
)

network_bytes_recv = Counter(
    "network_bytes_recv_total",
    "Total de bytes recibidos por red"
)

# Métricas de la aplicación
request_count = Counter(
    "api_requests_total",
    "Total de peticiones HTTP",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "api_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos",
    ["method", "endpoint"]
)

# === FUNCIONES DE ACTUALIZACIÓN ===

def update_cpu_metrics():
    """Actualiza las métricas de CPU"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_usage.set(cpu_percent)
        
        # CPU cores
        cores = psutil.cpu_count()
        cpu_cores.set(cores)
        
        logger.debug(f"CPU Metrics: {cpu_percent}% ({cores} cores)")
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de CPU: {e}")


def update_ram_metrics():
    """Actualiza las métricas de RAM"""
    try:
        memory = psutil.virtual_memory()
        
        ram_usage.set(memory.percent)
        ram_total.set(memory.total)
        ram_available.set(memory.available)
        ram_used.set(memory.used)
        
        logger.debug(f"RAM Metrics: {memory.percent}% ({memory.used}/{memory.total} bytes)")
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de RAM: {e}")


def update_disk_metrics():
    """Actualiza las métricas de disco"""
    try:
        disk = psutil.disk_usage('/')
        
        disk_usage.set(disk.percent)
        disk_total.set(disk.total)
        disk_free.set(disk.free)
        
        logger.debug(f"Disk Metrics: {disk.percent}% ({disk.free}/{disk.total} bytes free)")
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de disco: {e}")


def update_network_metrics():
    """Actualiza las métricas de red"""
    try:
        net_io = psutil.net_io_counters()
        
        # Nota: Counter solo aumenta, no se puede decrementar
        # Aquí solo actualizamos con los valores totales
        network_bytes_sent._value.set(net_io.bytes_sent)
        network_bytes_recv._value.set(net_io.bytes_recv)
        
        logger.debug(f"Network Metrics: Sent {net_io.bytes_sent} bytes, Recv {net_io.bytes_recv} bytes")
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de red: {e}")


def update_all_metrics():
    """Actualiza todas las métricas del sistema"""
    update_cpu_metrics()
    update_ram_metrics()
    update_disk_metrics()
    update_network_metrics()


# === FUNCIONES DE UTILIDAD ===

def get_system_info() -> Dict[str, Any]:
    """
    Obtiene información completa del sistema en formato JSON
    Útil para debugging y monitoreo manual
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None
            },
            "memory": {
                "usage_percent": memory.percent,
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2)
            },
            "disk": {
                "usage_percent": disk.percent,
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "used_bytes": disk.used,
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2)
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "mb_sent": round(net_io.bytes_sent / (1024**2), 2),
                "mb_recv": round(net_io.bytes_recv / (1024**2), 2)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo información del sistema: {e}")
        return {"error": str(e)}


def generate_prometheus_metrics() -> Response:
    """
    Genera y devuelve las métricas en formato Prometheus
    """
    try:
        # Actualizar todas las métricas antes de generar el reporte
        update_all_metrics()
        
        # Generar el reporte Prometheus
        metrics_output = generate_latest()
        
        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generando métricas Prometheus: {e}")
        return Response(
            content=f"Error: {str(e)}",
            status_code=500
        )
