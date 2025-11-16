from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.services.db_service import Base
import datetime

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    propietario = relationship("Usuario", back_populates="proyectos")
    archivos = relationship("ProjectFile", back_populates="proyecto", cascade="all, delete-orphan")
    vulnerabilidades = relationship("Vulnerabilidad", back_populates="proyecto", cascade="all, delete-orphan")
    metricas_analisis = relationship("MetricasAnalisis", back_populates="proyecto", cascade="all, delete-orphan")

# Alias para compatibilidad hacia atrás
Project = Proyecto
