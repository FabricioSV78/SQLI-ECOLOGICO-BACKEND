from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.services.db_service import Base
import datetime

class Feedback(Base):
    """
    Modelo de Retroalimentación del sistema.
    
    Registra la satisfacción de los usuarios con respecto al análisis realizado.
    Permite recopilar datos para mejora continua del sistema.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True)
    
    # Tipo de feedback: 'analysis_speed' (rapidez del análisis), 'accuracy' (precisión), 'usability' (usabilidad)
    tipo_feedback = Column(String(50), nullable=False)
    
    # Calificación de 1 a 5 estrellas
    calificacion = Column(Integer, nullable=False)
    
    # Comentario opcional del usuario
    comentario = Column(Text, nullable=True)
    
    # Metadata adicional (puede incluir tiempo de análisis, número de vulnerabilidades, etc.)
    extra_data = Column(Text, nullable=True)
    
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", backref="feedbacks")
    proyecto = relationship("Proyecto", backref="feedbacks")

    def __repr__(self):
        return f"<Feedback(id={self.id}, tipo={self.tipo_feedback}, calificacion={self.calificacion}, usuario_id={self.usuario_id})>"
