from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.services.db_service import Base

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    content = Column(Text, nullable=True)

    # Relaciones
    project = relationship("Project", back_populates="files")