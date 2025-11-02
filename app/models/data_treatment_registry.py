from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from app.services.db_service import Base
import enum


class LegalBasis(enum.Enum):
    """
    Bases legales para el tratamiento de datos según GDPR
    """
    CONSENT = "consent"  # Consentimiento del interesado
    CONTRACT = "contract"  # Ejecución de un contrato
    LEGAL_OBLIGATION = "legal_obligation"  # Cumplimiento de una obligación legal
    VITAL_INTERESTS = "vital_interests"  # Protección de intereses vitales
    PUBLIC_TASK = "public_task"  # Misión de interés público
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Intereses legítimos


class DataCategory(enum.Enum):
    """
    Categorías de datos personales procesados
    """
    IDENTIFICATION = "identification"  # Datos identificativos (email, nombre)
    CONTACT = "contact"  # Datos de contacto
    ACADEMIC = "academic"  # Datos académicos/profesionales
    TECHNICAL = "technical"  # Datos técnicos (IP, logs)
    USAGE = "usage"  # Datos de uso del sistema
    CONTENT = "content"  # Contenido subido por usuarios
    AUTHENTICATION = "authentication"  # Datos de autenticación


class RetentionPeriod(enum.Enum):
    """
    Períodos de retención predefinidos
    """
    SESSION_ONLY = "session_only"  # Solo durante la sesión
    THIRTY_DAYS = "30_days"  # 30 días
    ONE_YEAR = "1_year"  # 1 año
    THREE_YEARS = "3_years"  # 3 años (período académico)
    FIVE_YEARS = "5_years"  # 5 años (requisitos legales)
    UNTIL_DELETION_REQUEST = "until_deletion"  # Hasta solicitud de eliminación


class DataTreatmentRegistry(Base):
    """
    PRF4: Registro de tratamientos de datos personales
    
    Registra qué datos procesamos, con qué finalidad, base legal y período de retención
    para cumplir con los requisitos GDPR de transparencia y accountability.
    """
    __tablename__ = "data_treatment_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación del tratamiento
    treatment_name = Column(String(200), nullable=False, index=True)
    treatment_description = Column(Text, nullable=False)
    
    # Qué datos procesamos
    data_categories = Column(String(500), nullable=False)  # JSON array de categorías
    data_fields = Column(Text, nullable=False)  # Descripción específica de campos
    
    # Para qué procesamos (finalidad)
    processing_purpose = Column(Text, nullable=False)
    processing_activities = Column(Text, nullable=False)
    
    # Base legal
    legal_basis = Column(Enum(LegalBasis), nullable=False)
    legal_basis_details = Column(Text)  # Detalles específicos de la base legal
    
    # Período de retención
    retention_period = Column(Enum(RetentionPeriod), nullable=False)
    retention_criteria = Column(Text)  # Criterios específicos de retención
    deletion_procedure = Column(Text)  # Procedimiento de eliminación
    
    # Seguridad y protección
    security_measures = Column(Text)  # Medidas de seguridad aplicadas
    access_controls = Column(Text)  # Controles de acceso
    
    # Transferencias (si aplica)
    data_transfers = Column(Text)  # Transferencias a terceros
    transfer_safeguards = Column(Text)  # Salvaguardas para transferencias
    
    # Derechos del interesado
    subject_rights_info = Column(Text)  # Información sobre derechos
    
    # Metadatos
    responsible_person = Column(String(200))  # Responsable del tratamiento
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Auditoría
    last_reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    def __repr__(self):
        return f"<DataTreatment(nombre ={self.treatment_name}, purpose={self.processing_purpose[:50]})>"
    
    def to_dict(self):
        """Convierte el registro a diccionario para respuestas API"""
        return {
            "id": self.id,
            "treatment_name": self.treatment_name,
            "treatment_description": self.treatment_description,
            "data_categories": self.data_categories,
            "data_fields": self.data_fields,
            "processing_purpose": self.processing_purpose,
            "processing_activities": self.processing_activities,
            "legal_basis": self.legal_basis.value if self.legal_basis else None,
            "legal_basis_details": self.legal_basis_details,
            "retention_period": self.retention_period.value if self.retention_period else None,
            "retention_criteria": self.retention_criteria,
            "deletion_procedure": self.deletion_procedure,
            "security_measures": self.security_measures,
            "access_controls": self.access_controls,
            "data_transfers": self.data_transfers,
            "transfer_safeguards": self.transfer_safeguards,
            "subject_rights_info": self.subject_rights_info,
            "responsible_person": self.responsible_person,
            "created_at": self.fecha_creacion,
            "updated_at": self.fecha_actualizacion,
            "is_active": self.is_active,
            "last_reviewed_at": self.last_reviewed_at,
            "review_notes": self.review_notes
        }
