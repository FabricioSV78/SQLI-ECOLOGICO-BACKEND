from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, Date
from sqlalchemy.sql import func
from app.services.db_service import Base
import enum
from datetime import datetime, date


class DpaStatus(enum.Enum):
    """
    Estados de los Data Processing Agreements
    """
    DRAFT = "draft"  # Borrador
    ACTIVE = "active"  # Activo y vigente
    EXPIRED = "expired"  # Vencido
    TERMINATED = "terminated"  # Terminado anticipadamente
    SUSPENDED = "suspended"  # Suspendido temporalmente


class DataLocation(enum.Enum):
    """
    Ubicaciones geográficas donde se almacenan los datos
    """
    EU = "eu"  # Unión Europea
    US = "us"  # Estados Unidos
    LATAM = "latam"  # Latinoamérica
    ASIA = "asia"  # Asia-Pacífico
    GLOBAL = "global"  # Múltiples regiones
    ON_PREMISE = "on_premise"  # En las instalaciones


class CloudProvider(enum.Enum):
    """
    Proveedores de servicios cloud principales
    """
    AWS = "aws"  # Amazon Web Services
    AZURE = "azure"  # Microsoft Azure
    GCP = "gcp"  # Google Cloud Platform
    DIGITALOCEAN = "digitalocean"  # DigitalOcean
    HEROKU = "heroku"  # Heroku
    VERCEL = "vercel"  # Vercel
    OTHER = "other"  # Otro proveedor


class DataProcessingAgreement(Base):
    """
    PRF5: Modelo para gestionar Data Processing Agreements (DPA) con proveedores cloud.
    
    Registra acuerdos de procesamiento de datos con terceros proveedores,
    incluyendo ubicación de datos, fechas de vigencia y términos específicos
    para cumplir con requisitos GDPR de transferencias internacionales.
    """
    __tablename__ = "data_processing_agreements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información del proveedor
    provider_name = Column(String(200), nullable=False, index=True)
    cloud_provider = Column(Enum(CloudProvider), nullable=False)
    provider_contact = Column(String(300))  # Email de contacto del proveedor
    provider_address = Column(Text)  # Dirección legal del proveedor
    
    # Información del acuerdo
    dpa_title = Column(String(300), nullable=False)
    dpa_description = Column(Text, nullable=False)
    contract_number = Column(String(100), unique=True, index=True)  # Número de contrato único
    
    # Fechas de vigencia
    signed_date = Column(Date, nullable=False)  # Fecha de firma
    effective_date = Column(Date, nullable=False)  # Fecha de entrada en vigor
    expiry_date = Column(Date, nullable=False)  # Fecha de vencimiento
    renewal_date = Column(Date)  # Fecha de próxima renovación (opcional)
    
    # Ubicación y transferencia de datos
    data_location = Column(Enum(DataLocation), nullable=False)
    data_location_details = Column(Text)  # Detalles específicos de ubicación
    transfer_mechanism = Column(String(200))  # Mecanismo de transferencia (SCCs, Adequacy, etc.)
    adequacy_decision = Column(Boolean, default=False)  # Si hay decisión de adecuación
    
    # Tipos de datos procesados
    data_categories_processed = Column(Text, nullable=False)  # JSON array de categorías
    processing_purposes = Column(Text, nullable=False)  # Finalidades del procesamiento
    data_subjects_categories = Column(Text)  # Categorías de interesados
    
    # Medidas de seguridad
    security_measures = Column(Text, nullable=False)  # Medidas técnicas y organizativas
    encryption_standards = Column(String(200))  # Estándares de cifrado
    access_controls = Column(Text)  # Controles de acceso
    
    # Subprocesadores
    subprocessors_allowed = Column(Boolean, default=False)  # Si se permiten subprocesadores
    subprocessors_list = Column(Text)  # Lista de subprocesadores aprobados
    subprocessor_notification = Column(Boolean, default=True)  # Notificación de cambios
    
    # Derechos del responsable
    data_subject_requests = Column(Text)  # Procedimiento para solicitudes de interesados
    data_breach_notification = Column(Text)  # Procedimiento para notificación de brechas
    audit_rights = Column(Text)  # Derechos de auditoría
    
    # Estado y gestión
    status = Column(Enum(DpaStatus), nullable=False, default=DpaStatus.DRAFT)
    auto_renewal = Column(Boolean, default=False)  # Renovación automática
    termination_notice_days = Column(Integer, default=30)  # Días de aviso para terminación
    
    # Archivos y documentación
    contract_file_path = Column(String(500))  # Ruta al archivo del contrato
    amendments_count = Column(Integer, default=0)  # Número de enmiendas
    
    # Metadatos
    created_by = Column(Integer)  # ID del usuario que creó el registro
    approved_by = Column(Integer)  # ID del usuario que aprobó
    last_reviewed_by = Column(Integer)  # ID del último revisor
    
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    approved_at = Column(DateTime)  # Fecha de aprobación
    last_reviewed_at = Column(DateTime)  # Fecha de última revisión
    
    # Campos de auditoría
    is_active = Column(Boolean, default=True)
    compliance_notes = Column(Text)  # Notas de cumplimiento
    risk_assessment = Column(Text)  # Evaluación de riesgo
    
    def __repr__(self):
        return f"<DPA(provider={self.provider_name}, contract={self.contract_number}, status={self.status.value})>"
    
    @property
    def is_expired(self) -> bool:
        """Verifica si el DPA está vencido"""
        return date.today() > self.expiry_date
    
    @property
    def days_until_expiry(self) -> int:
        """Días hasta el vencimiento"""
        return (self.expiry_date - date.today()).days
    
    @property
    def is_expiring_soon(self, days_threshold: int = 30) -> bool:
        """Verifica si el DPA vence pronto"""
        return 0 <= self.days_until_expiry <= days_threshold
    
    def to_dict(self):
        """Convierte el DPA a diccionario para respuestas API"""
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "cloud_provider": self.cloud_provider.value if self.cloud_provider else None,
            "provider_contact": self.provider_contact,
            "provider_address": self.provider_address,
            "dpa_title": self.dpa_title,
            "dpa_description": self.dpa_description,
            "contract_number": self.contract_number,
            "signed_date": self.signed_date.isoformat() if self.signed_date else None,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "renewal_date": self.renewal_date.isoformat() if self.renewal_date else None,
            "data_location": self.data_location.value if self.data_location else None,
            "data_location_details": self.data_location_details,
            "transfer_mechanism": self.transfer_mechanism,
            "adequacy_decision": self.adequacy_decision,
            "data_categories_processed": self.data_categories_processed,
            "processing_purposes": self.processing_purposes,
            "data_subjects_categories": self.data_subjects_categories,
            "security_measures": self.security_measures,
            "encryption_standards": self.encryption_standards,
            "access_controls": self.access_controls,
            "subprocessors_allowed": self.subprocessors_allowed,
            "subprocessors_list": self.subprocessors_list,
            "subprocessor_notification": self.subprocessor_notification,
            "data_subject_requests": self.data_subject_requests,
            "data_breach_notification": self.data_breach_notification,
            "audit_rights": self.audit_rights,
            "status": self.status.value if self.status else None,
            "auto_renewal": self.auto_renewal,
            "termination_notice_days": self.termination_notice_days,
            "contract_file_path": self.contract_file_path,
            "amendments_count": self.amendments_count,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "last_reviewed_by": self.last_reviewed_by,
            "created_at": self.fecha_creacion,
            "updated_at": self.fecha_actualizacion,
            "approved_at": self.approved_at,
            "last_reviewed_at": self.last_reviewed_at,
            "is_active": self.is_active,
            "compliance_notes": self.compliance_notes,
            "risk_assessment": self.risk_assessment,
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "is_expiring_soon": self.is_expiring_soon()
        }
