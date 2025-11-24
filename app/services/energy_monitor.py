"""
Módulo para estimar consumo energético por ejecución (análisis)

Metodología simple y configurable:
- Estima energía consumida por CPU a partir de los segundos de CPU usados
- Estima energía consumida por RAM usando un factor por GB
- Convierte energía (kWh) a emisiones (kg CO2e) usando un factor configurable

Parámetros configurables mediante variables de entorno:
- ENERGY_POWER_PER_CPU_CORE_WATTS: potencia aproximada por segundo de CPU usado (W). Default: 10
- ENERGY_MEMORY_POWER_PER_GB_WATTS: potencia por GB de RAM en uso (W). Default: 0.372
- ENERGY_EMISSION_FACTOR_KG_PER_KWH: factor de emisión (kg CO2e / kWh). Default: 0.475

Uso:
with EnergyMonitor() as em:
    run_analysis(...)
metrics = em.get_metrics()

Nota: estimaciones aproximadas. Ver `REPORT_ENERGY.md` para metodología.
"""

import os
import time
import psutil
from typing import Dict


def _get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


class EnergyMonitor:
    """Context manager que mide tiempo, uso de CPU/RAM y estima energía y emisiones."""

    def __init__(
        self,
        power_per_cpu_core_watts: float = None,
        memory_power_per_gb_watts: float = None,
        emission_factor_kg_per_kwh: float = None,
    ):
        # Valores por defecto (configurables via env)
        self.power_per_cpu_core_watts = power_per_cpu_core_watts if power_per_cpu_core_watts is not None else _get_env_float("ENERGY_POWER_PER_CPU_CORE_WATTS", 10.0)
        self.memory_power_per_gb_watts = memory_power_per_gb_watts if memory_power_per_gb_watts is not None else _get_env_float("ENERGY_MEMORY_POWER_PER_GB_WATTS", 0.372)
        self.emission_factor_kg_per_kwh = emission_factor_kg_per_kwh if emission_factor_kg_per_kwh is not None else _get_env_float("ENERGY_EMISSION_FACTOR_KG_PER_KWH", 0.475)

        self._start_time = None
        self._end_time = None
        self._start_cpu_seconds = None
        self._end_cpu_seconds = None
        self._start_rss = None
        self._end_rss = None
        self.metrics: Dict[str, float] = {}

    def __enter__(self):
        self._proc = psutil.Process(os.getpid())
        self._start_time = time.time()
        cpu_times = self._proc.cpu_times()
        # suma de user + system
        self._start_cpu_seconds = float(getattr(cpu_times, 'user', 0.0) + getattr(cpu_times, 'system', 0.0))
        mem = self._proc.memory_info()
        self._start_rss = float(getattr(mem, 'rss', 0))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._end_time = time.time()
        cpu_times = self._proc.cpu_times()
        self._end_cpu_seconds = float(getattr(cpu_times, 'user', 0.0) + getattr(cpu_times, 'system', 0.0))
        mem = self._proc.memory_info()
        self._end_rss = float(getattr(mem, 'rss', 0))

        self._compute_metrics()

    def _compute_metrics(self):
        elapsed = max(0.0, (self._end_time or 0.0) - (self._start_time or 0.0))
        cpu_seconds = max(0.0, (self._end_cpu_seconds or 0.0) - (self._start_cpu_seconds or 0.0))

        # Estimación energía CPU: suponer potencia por segundo de CPU usado
        # energy_cpu_kwh = cpu_seconds * power_watts / 3600
        energy_cpu_kwh = (cpu_seconds * self.power_per_cpu_core_watts) / 3600.0

        # Estimación energía RAM: usar promedio entre inicio y fin
        avg_rss_bytes = ((self._start_rss or 0.0) + (self._end_rss or 0.0)) / 2.0
        avg_rss_gb = avg_rss_bytes / (1024 ** 3)
        # energy_ram_kwh = avg_rss_gb * memory_power_watts_per_gb * elapsed_seconds / 3600
        energy_ram_kwh = (avg_rss_gb * self.memory_power_per_gb_watts * elapsed) / 3600.0

        total_kwh = energy_cpu_kwh + energy_ram_kwh
        emissions_kg = total_kwh * self.emission_factor_kg_per_kwh

        self.metrics = {
            "start_time": self._start_time,
            "end_time": self._end_time,
            "elapsed_seconds": elapsed,
            "cpu_seconds": cpu_seconds,
            "avg_rss_bytes": avg_rss_bytes,
            "avg_rss_gb": avg_rss_gb,
            "power_per_cpu_core_watts": self.power_per_cpu_core_watts,
            "memory_power_per_gb_watts": self.memory_power_per_gb_watts,
            "emission_factor_kg_per_kwh": self.emission_factor_kg_per_kwh,
            "cpu_energy_kwh": energy_cpu_kwh,
            "ram_energy_kwh": energy_ram_kwh,
            "total_kwh": total_kwh,
            "emissions_kg": emissions_kg,
        }

    def get_metrics(self) -> Dict[str, float]:
        return self.metrics or {}


__all__ = ["EnergyMonitor"]
