from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.services.db_service import Base

class MetricasAnalisis(Base):
    __tablename__ = "metricas_analisis"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    tiempo_analisis = Column(Float, nullable=False)  # Tiempo en segundos
    consumo_energetico_kwh = Column(Float, nullable=False)  # Consumo energético estimado en kWh
    detecciones_correctas = Column(Integer, nullable=True)  # Detecciones correctas (vacío, manual)
    vulnerabilidades_detectadas = Column(Integer, nullable=False, default=0)  # Vulnerabilidades detectadas
    precision = Column(Float, nullable=True)  # Precisión (vacía inicialmente)

    # Relación con el proyecto
    proyecto = relationship("Proyecto", back_populates="metricas_analisis")

    @property
    def total_archivos_analizados(self):
        """Retorna el total de archivos analizados"""
        # Solo contamos las vulnerabilidades detectadas ya que no tenemos los no vulnerables
        return self.vulnerabilidades_detectadas

    @property
    def porcentaje_vulnerabilidades(self):
        """Retorna el porcentaje de vulnerabilidades encontradas"""
        # Este cálculo ahora solo puede basarse en las vulnerabilidades detectadas
        # Se podría calcular diferente si se tiene el total de consultas analizadas
        return 100.0 if self.vulnerabilidades_detectadas > 0 else 0.0

    def calcular_consumo_energetico(self, power_watts: float = 10.0):
        """Calcula el consumo energético estimado basado en el tiempo de análisis
        
        Args:
            power_watts: Potencia estimada en watts (default: 10W)
        """
        # Energía (kWh) = Potencia (W) × Tiempo (h) / 1000
        self.consumo_energetico_kwh = (power_watts * self.tiempo_analisis) / 3600.0
        return self.consumo_energetico_kwh

    def __repr__(self):
        return f"<MetricasAnalisis(proyecto_id={self.proyecto_id}, tiempo={self.tiempo_analisis}s, consumo={self.consumo_energetico_kwh}kWh)>"

# Alias para compatibilidad hacia atrás
MetricasAnalisis = MetricasAnalisis

# Alias en inglés para compatibilidad con importaciones externas
AnalysisMetrics = MetricasAnalisis
