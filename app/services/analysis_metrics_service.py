from sqlalchemy.orm import Session
from app.models.analysis_metrics import AnalysisMetrics
from typing import Optional, List
import time

class AnalysisMetricsService:
    """Servicio para manejar las métricas de análisis de proyectos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_metrics(
        self, 
        id_proyecto: int, 
        tiempo_analisis: float, 
        vulnerabilidades_detectadas: int = 0,
        detecciones_correctas: Optional[int] = None,
        precision: Optional[float] = None,
        consumo_energetico_kwh: Optional[float] = None
    ) -> AnalysisMetrics:
        """
        Crea una nueva entrada de métricas para un proyecto
        
        Args:
            id_proyecto: ID del proyecto
            tiempo_analisis: Tiempo de análisis en segundos
            vulnerabilidades_detectadas: Cantidad de vulnerabilidades detectadas
            detecciones_correctas: Cantidad de detecciones correctas (opcional, manual)
            precision: Precisión del análisis (opcional)
            consumo_energetico_kwh: Consumo energético en kWh (opcional, se calcula si no se proporciona)
        
        Returns:
            AnalysisMetrics: La entrada de métricas creada
        """
        metrics = AnalysisMetrics(
            proyecto_id=id_proyecto,  # Usar proyecto_id en lugar de id_proyecto
            tiempo_analisis=tiempo_analisis,
            vulnerabilidades_detectadas=vulnerabilidades_detectadas,
            detecciones_correctas=detecciones_correctas,
            precision=precision,
            consumo_energetico_kwh=consumo_energetico_kwh or 0.0
        )
        
        # Calcular el consumo energético automáticamente si no se proporcionó
        if consumo_energetico_kwh is None:
            metrics.calcular_consumo_energetico()
        
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics
    
    def get_metrics_by_project(self, id_proyecto: int) -> List[AnalysisMetrics]:
        """
        Obtiene todas las métricas de un proyecto específico
        
        Args:
            id_proyecto: ID del proyecto
            
        Returns:
            List[AnalysisMetrics]: Lista de métricas del proyecto
        """
        return self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.proyecto_id == id_proyecto  # Usar proyecto_id
        ).all()
    
    def get_latest_metrics(self, id_proyecto: int) -> Optional[AnalysisMetrics]:
        """
        Obtiene las métricas más recientes de un proyecto
        
        Args:
            id_proyecto: ID del proyecto
            
        Returns:
            Optional[AnalysisMetrics]: Las métricas más recientes o None
        """
        return self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.proyecto_id == id_proyecto  # Usar proyecto_id
        ).order_by(AnalysisMetrics.id.desc()).first()
    
    def update_precision(self, metrics_id: int, precision: float) -> Optional[AnalysisMetrics]:
        """
        Actualiza la precisión de una entrada de métricas
        
        Args:
            metrics_id: ID de las métricas
            precision: Nuevo valor de precisión
            
        Returns:
            Optional[AnalysisMetrics]: Las métricas actualizadas o None
        """
        metrics = self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.id == metrics_id
        ).first()
        
        if metrics:
            metrics.precision = precision
            self.db.commit()
            self.db.refresh(metrics)
        
        return metrics
    
    def get_all_metrics(self) -> List[AnalysisMetrics]:
        """
        Obtiene todas las métricas de todos los proyectos
        
        Returns:
            List[AnalysisMetrics]: Lista de todas las métricas
        """
        return self.db.query(AnalysisMetrics).order_by(
            AnalysisMetrics.id.desc()
        ).all()
    
    def update_detecciones_correctas(self, metrics_id: int, detecciones_correctas: int) -> Optional[AnalysisMetrics]:
        """
        Actualiza las detecciones correctas de una entrada de métricas
        
        Args:
            metrics_id: ID de las métricas
            detecciones_correctas: Nuevo valor de detecciones correctas
            
        Returns:
            Optional[AnalysisMetrics]: Las métricas actualizadas o None
        """
        metrics = self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.id == metrics_id
        ).first()
        
        if metrics:
            metrics.detecciones_correctas = detecciones_correctas
            self.db.commit()
            self.db.refresh(metrics)
        
        return metrics
    
    def delete_metrics(self, metrics_id: int) -> bool:
        """
        Elimina una entrada de métricas
        
        Args:
            metrics_id: ID de las métricas a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no se encontró
        """
        metrics = self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.id == metrics_id
        ).first()
        
        if metrics:
            self.db.delete(metrics)
            self.db.commit()
            return True
        
        return False

class AnalysisTimer:
    """Clase helper para medir el tiempo de análisis"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Inicia el cronómetro"""
        self.start_time = time.time()
    
    def stop(self):
        """Detiene el cronómetro y retorna el tiempo transcurrido"""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.time()
        return self.get_elapsed_time()
    
    def get_elapsed_time(self) -> float:
        """Retorna el tiempo transcurrido en segundos"""
        if self.start_time is None or self.end_time is None:
            raise ValueError("Timer not properly initialized")
        
        return self.end_time - self.start_time
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
