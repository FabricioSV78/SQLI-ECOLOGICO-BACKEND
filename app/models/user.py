from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.services.db_service import Base
from app.models.user_role import UserRole
import datetime

class Usuario(Base):
    """
    Modelo de Usuario del sistema de detección SQLi.
    
    Representa a los usuarios del sistema con diferentes roles:
    - STUDENT: Estudiantes con acceso limitado a sus propios recursos
    - TEACHER: Docentes con acceso a reportes de todos los estudiantes  
    - ADMIN: Administradores con acceso completo
    
    Implementa el requerimiento SRF2 de control de acceso diferenciado.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    contrasena = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    # Campo rol para implementar SRF2 - control de acceso diferenciado
    rol = Column(Enum(UserRole), nullable=False, default=UserRole.ESTUDIANTE)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    proyectos = relationship("Proyecto", back_populates="propietario", cascade="all, delete-orphan")
    # Relación con solicitudes de privacidad (PRF2)
    privacy_requests = relationship("PrivacyRequest", foreign_keys="[PrivacyRequest.usuario_id]", back_populates="usuario")
    
    def tiene_rol(self, rol: UserRole) -> bool:
        """
        Verifica si el usuario tiene un rol específico.
        
        Args:
            rol (UserRole): El rol a verificar
            
        Returns:
            bool: True si el usuario tiene el rol especificado
        """
        return self.rol == rol
    
    def es_privilegiado(self) -> bool:
        """
        Verifica si el usuario tiene privilegios elevados (docente o admin).
        
        Returns:
            bool: True si es docente o administrador
        """
        return self.rol in [UserRole.DOCENTE, UserRole.ADMINISTRADOR]
    
    def puede_acceder_todos_reportes(self) -> bool:
        """
        Verifica si el usuario puede acceder a todos los reportes.
        Implementa la lógica del requerimiento SRF2.
        
        Returns:
            bool: True si puede ver todos los reportes (docente/admin)
        """
        return self.rol in [UserRole.DOCENTE, UserRole.ADMINISTRADOR]
    
    def puede_acceder_proyecto(self, id_propietario_proyecto: int) -> bool:
        """
        Verifica si el usuario puede acceder a un proyecto específico.
        
        Args:
            id_propietario_proyecto (int): ID del propietario del proyecto
            
        Returns:
            bool: True si puede acceder al proyecto
        """
        # Docentes y admins pueden ver todos los proyectos
        if self.es_privilegiado():
            return True
        
        # Estudiantes solo pueden ver sus propios proyectos
        return self.id == id_propietario_proyecto

# Alias para compatibilidad hacia atrás
User = Usuario
