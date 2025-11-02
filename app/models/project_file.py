from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.services.db_service import Base


# Primary model name in English for clearer codebase naming
class ProjectFile(Base):
    __tablename__ = "archivos_proyecto"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    nombre_archivo = Column(String, nullable=False)
    ruta_archivo = Column(String, nullable=False)
    contenido = Column(Text, nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="archivos")


# Alias en español para compatibilidad hacia atrás
# Muchas partes del proyecto usan `ArchivoProyecto`; mantenerlo apuntando
# a la misma clase evita romper importaciones existentes.
ArchivoProyecto = ProjectFile
