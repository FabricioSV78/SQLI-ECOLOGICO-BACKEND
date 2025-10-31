from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.services.db_service import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
