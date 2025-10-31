from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.services.db_service import Base

class AnalysisMetrics(Base):
    __tablename__ = "metricas_analisis"

    id = Column(Integer, primary_key=True, index=True)
    id_proyecto = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    tiempo_analisis = Column(Float, nullable=False)  # Tiempo en segundos
    costo = Column(Float, nullable=False)  # Costo calculado (tiempo x 5)
    detecciones_correctas = Column(Integer, nullable=True)  # Detecciones correctas (vacío, manual)
    vulnerabilidades_detectadas = Column(Integer, nullable=False, default=0)  # Vulnerabilidades detectadas
    precision = Column(Float, nullable=True)  # Precisión (vacía inicialmente)

    # Relación con el proyecto
    project = relationship("Project", back_populates="analysis_metrics")

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

    def calcular_costo(self):
        """Calcula el costo basado en el tiempo de análisis"""
        self.costo = self.tiempo_analisis * 0.0000066
        return self.costo

    def __repr__(self):
        return f"<MetricasAnalisis(id_proyecto={self.id_proyecto}, tiempo={self.tiempo_analisis}s, costo=${self.costo})>"