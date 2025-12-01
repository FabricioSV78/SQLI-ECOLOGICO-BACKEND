from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.feedback import Feedback
from app.models.user import Usuario
from app.models.project import Proyecto
from typing import List, Optional, Dict
import json
import datetime

class FeedbackService:
    """
    Servicio para gestionar la retroalimentación de los usuarios.
    """
    
    @staticmethod
    def crear_feedback(
        db: Session,
        usuario_id: int,
        tipo_feedback: str,
        calificacion: int,
        proyecto_id: Optional[int] = None,
        comentario: Optional[str] = None,
        extra_data: Optional[Dict] = None
    ) -> Feedback:
        """
        Crear un nuevo registro de feedback.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario que proporciona feedback
            tipo_feedback: Tipo de feedback ('analysis_speed', 'accuracy', 'usability')
            calificacion: Calificación de 1 a 5
            proyecto_id: ID del proyecto relacionado (opcional)
            comentario: Comentario adicional del usuario (opcional)
            extra_data: Datos adicionales en formato JSON (opcional)
            
        Returns:
            Feedback: Objeto de feedback creado
            
        Raises:
            ValueError: Si la calificación no está entre 1 y 5
        """
        # Validar calificación
        if not 1 <= calificacion <= 5:
            raise ValueError("La calificación debe estar entre 1 y 5")
        
        # Validar tipo de feedback
        tipos_validos = ['analysis_speed', 'accuracy', 'usability', 'general']
        if tipo_feedback not in tipos_validos:
            raise ValueError(f"Tipo de feedback debe ser uno de: {', '.join(tipos_validos)}")
        
        # Convertir extra_data a JSON string si existe
        extra_data_str = json.dumps(extra_data) if extra_data else None
        
        # Crear el feedback
        nuevo_feedback = Feedback(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id,
            tipo_feedback=tipo_feedback,
            calificacion=calificacion,
            comentario=comentario,
            extra_data=extra_data_str
        )
        
        db.add(nuevo_feedback)
        db.commit()
        db.refresh(nuevo_feedback)
        
        return nuevo_feedback
    
    @staticmethod
    def obtener_feedback_por_usuario(
        db: Session,
        usuario_id: int,
        limit: int = 50
    ) -> List[Feedback]:
        """
        Obtener el feedback de un usuario específico.
        """
        return db.query(Feedback)\
            .filter(Feedback.usuario_id == usuario_id)\
            .order_by(Feedback.fecha_creacion.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def obtener_feedback_por_proyecto(
        db: Session,
        proyecto_id: int
    ) -> List[Feedback]:
        """
        Obtener todo el feedback relacionado con un proyecto.
        """
        return db.query(Feedback)\
            .filter(Feedback.proyecto_id == proyecto_id)\
            .order_by(Feedback.fecha_creacion.desc())\
            .all()
    
    @staticmethod
    def obtener_estadisticas_feedback(
        db: Session,
        tipo_feedback: Optional[str] = None,
        fecha_desde: Optional[datetime.datetime] = None,
        fecha_hasta: Optional[datetime.datetime] = None
    ) -> Dict:
        """
        Obtener estadísticas agregadas de feedback.
        
        Returns:
            Dict con estadísticas: promedio, total de respuestas, distribución por calificación
        """
        query = db.query(Feedback)
        
        # Aplicar filtros
        if tipo_feedback:
            query = query.filter(Feedback.tipo_feedback == tipo_feedback)
        if fecha_desde:
            query = query.filter(Feedback.fecha_creacion >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Feedback.fecha_creacion <= fecha_hasta)
        
        # Calcular estadísticas
        total_respuestas = query.count()
        
        if total_respuestas == 0:
            return {
                "total_respuestas": 0,
                "calificacion_promedio": 0,
                "distribucion": {},
                "comentarios_count": 0
            }
        
        # Promedio de calificación
        promedio = db.query(func.avg(Feedback.calificacion))\
            .filter(Feedback.id.in_([f.id for f in query.all()]))\
            .scalar()
        
        # Distribución por calificación
        distribucion = {}
        for i in range(1, 6):
            count = query.filter(Feedback.calificacion == i).count()
            distribucion[str(i)] = count
        
        # Contar comentarios
        comentarios_count = query.filter(Feedback.comentario.isnot(None)).count()
        
        return {
            "total_respuestas": total_respuestas,
            "calificacion_promedio": round(float(promedio), 2) if promedio else 0,
            "distribucion": distribucion,
            "comentarios_count": comentarios_count
        }
    
    @staticmethod
    def obtener_feedback_reciente(
        db: Session,
        limit: int = 20,
        tipo_feedback: Optional[str] = None
    ) -> List[Feedback]:
        """
        Obtener el feedback más reciente del sistema.
        """
        query = db.query(Feedback)
        
        if tipo_feedback:
            query = query.filter(Feedback.tipo_feedback == tipo_feedback)
        
        return query.order_by(Feedback.fecha_creacion.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def obtener_feedback_con_comentarios(
        db: Session,
        limit: int = 50
    ) -> List[Feedback]:
        """
        Obtener feedback que incluye comentarios de los usuarios.
        """
        return db.query(Feedback)\
            .filter(Feedback.comentario.isnot(None))\
            .order_by(Feedback.fecha_creacion.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def obtener_promedio_por_tipo(
        db: Session
    ) -> Dict[str, float]:
        """
        Obtener el promedio de calificación por cada tipo de feedback.
        """
        tipos = ['analysis_speed', 'accuracy', 'usability', 'general']
        resultados = {}
        
        for tipo in tipos:
            promedio = db.query(func.avg(Feedback.calificacion))\
                .filter(Feedback.tipo_feedback == tipo)\
                .scalar()
            resultados[tipo] = round(float(promedio), 2) if promedio else 0
        
        return resultados
