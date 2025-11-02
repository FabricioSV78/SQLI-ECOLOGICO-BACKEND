"""
Modelo para solicitudes de privacidad de datos (GDPR/LOPD)
Implementa PRF2: Flujo para solicitudes de acceso, rectificación o eliminación
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.services.db_service import Base
from enum import Enum as PyEnum
import datetime

class PrivacyRequestType(PyEnum):
    """Tipos de solicitudes de privacidad según GDPR"""
    ACCESS = "access"           # Derecho de acceso (Art. 15 GDPR)
    RECTIFICATION = "rectification"  # Derecho de rectificación (Art. 16 GDPR)
    ERASURE = "erasure"        # Derecho al olvido (Art. 17 GDPR)
    PORTABILITY = "portability"  # Derecho a la portabilidad (Art. 20 GDPR)

class PrivacyRequestStatus(PyEnum):
    """Estados de las solicitudes de privacidad"""
    PENDING = "pending"         # Pendiente de procesamiento
    IN_PROGRESS = "in_progress"  # En proceso de revisión
    APPROVED = "approved"       # Aprobada y procesada
    REJECTED = "rejected"       # Rechazada (con justificación)
    COMPLETED = "completed"     # Completada exitosamente

class PrivacyRequest(Base):
    """
    Modelo para gestionar solicitudes de privacidad de datos.
    
    Implementa el requerimiento PRF2 proporcionando un flujo estructurado
    para que los titulares (estudiantes) puedan:
    - Solicitar acceso a sus datos personales
    - Solicitar rectificación de datos incorrectos
    - Solicitar eliminación de sus datos personales
    """
    __tablename__ = "privacy_requests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Usuario que solicita (titular de los datos)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Tipo de solicitud
    request_type = Column(Enum(PrivacyRequestType), nullable=False)
    
    # Estado actual de la solicitud
    status = Column(Enum(PrivacyRequestStatus), nullable=False, default=PrivacyRequestStatus.PENDING)
    
    # Descripción de la solicitud
    descripcion = Column(Text, nullable=True)
    
    # Datos específicos para rectificación (JSON string)
    rectification_data = Column(Text, nullable=True)
    
    # Justificación en caso de rechazo
    rejection_reason = Column(Text, nullable=True)
    
    # Fechas importantes
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Usuario administrador que procesa la solicitud
    processed_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Control de notificaciones
    user_notified = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    # Relacionar con el usuario solicitante
    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="privacy_requests")
    processor = relationship("Usuario", foreign_keys=[processed_by])
    
    def is_expired(self, days_limit: int = 30) -> bool:
        """
        Verifica si la solicitud ha excedido el tiempo legal de respuesta.
        GDPR establece 30 días como máximo para responder.
        """
        if not self.fecha_creacion:
            return False
            
        expiration_date = self.fecha_creacion + datetime.timedelta(days=days_limit)
        return datetime.datetime.utcnow() > expiration_date
    
    def can_be_processed_by(self, user_id: int, user_role: str) -> bool:
        """
        Verifica si un usuario puede procesar esta solicitud.
        Solo administradores pueden procesar solicitudes de privacidad.
        """
        from app.models.user_role import UserRole
        return user_role == UserRole.ADMINISTRADOR
    
    def to_dict(self) -> dict:
        """Convierte la solicitud a diccionario para respuestas JSON"""
        return {
            "id": self.id,
            "user_id": self.usuario_id,
            "request_type": self.request_type.value if self.request_type else None,
            "status": self.status.value if self.status else None,
            "description": self.descripcion,
            "created_at": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_expired": self.is_expired(),
            "user_notified": self.user_notified
        }
