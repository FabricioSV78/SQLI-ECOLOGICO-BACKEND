from sqlalchemy.orm import Session
from app.models.data_treatment_registry import (
    DataTreatmentRegistry, 
    LegalBasis, 
    DataCategory, 
    RetentionPeriod
)
from app.services.audit_logger import AuditAction, AuditResult
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime
import json


class DataTreatmentService:
    """
    PRF4: Servicio para gestionar el registro de tratamientos de datos personales.
    
    Proporciona funcionalidad para:
    - Crear y mantener registros de tratamiento
    - Consultar tratamientos activos
    - Generar reportes de cumplimiento
    - Gestionar períodos de retención
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_treatment_registry(
        self,
        treatment_name: str,
        treatment_description: str,
        data_categories: List[str],
        data_fields: str,
        processing_purpose: str,
        processing_activities: str,
        legal_basis: LegalBasis,
        retention_period: RetentionPeriod,
        user_id: int,
        **optional_fields
    ) -> DataTreatmentRegistry:
        """
        Crea un nuevo registro de tratamiento de datos.
        
        Args:
            treatment_name: Nombre identificativo del tratamiento
            treatment_description: Descripción detallada
            data_categories: Lista de categorías de datos
            data_fields: Campos específicos procesados
            processing_purpose: Finalidad del procesamiento
            processing_activities: Actividades de procesamiento
            legal_basis: Base legal para el tratamiento
            retention_period: Período de retención
            user_id: ID del usuario que crea el registro
            **optional_fields: Campos opcionales adicionales
        """
        try:
            # Crear registro
            treatment = DataTreatmentRegistry(
                treatment_name=treatment_name,
                treatment_description=treatment_description,
                data_categories=json.dumps(data_categories),
                data_fields=data_fields,
                processing_purpose=processing_purpose,
                processing_activities=processing_activities,
                legal_basis=legal_basis,
                retention_period=retention_period,
                legal_basis_details=optional_fields.get('legal_basis_details'),
                retention_criteria=optional_fields.get('retention_criteria'),
                deletion_procedure=optional_fields.get('deletion_procedure'),
                security_measures=optional_fields.get('security_measures'),
                access_controls=optional_fields.get('access_controls'),
                data_transfers=optional_fields.get('data_transfers'),
                transfer_safeguards=optional_fields.get('transfer_safeguards'),
                subject_rights_info=optional_fields.get('subject_rights_info'),
                responsible_person=optional_fields.get('responsible_person', f"user_{user_id}")
            )
            
            self.db.add(treatment)
            self.db.commit()
            self.db.refresh(treatment)
            
            # Log de auditoría usando la función directa
            from app.services.audit_logger import log_user_action
            from app.config.config import settings
            if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"user_{user_id}",
                    action=AuditAction.TREATMENT_CREATE,
                    result=AuditResult.SUCCESS,
                    details={
                        "treatment_registry_id": treatment.id,
                        "treatment_name": treatment_name,
                        "legal_basis": legal_basis.value,
                        "retention_period": retention_period.value,
                        "data_categories": data_categories
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            
            return treatment
            
        except Exception as e:
            self.db.rollback()
            # Log de error usando la función directa
            from app.services.audit_logger import log_user_action
            from app.config.config import settings
            if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"user_{user_id}",
                    action=AuditAction.TREATMENT_CREATE,
                    result=AuditResult.ERROR,
                    details={
                        "treatment_name": treatment_name,
                        "error": str(e)
                    },
                    audit_dir=settings.AUDIT_DIR
                )
            raise HTTPException(
                status_code=500,
                detail=f"Error creando registro de tratamiento: {str(e)}"
            )
    
    def get_all_treatments(self, active_only: bool = True) -> List[DataTreatmentRegistry]:
        """Obtiene todos los registros de tratamiento"""
        consulta = self.db.query(DataTreatmentRegistry)
        if active_only:
            consulta = query.filter(DataTreatmentRegistry.is_active == True)
        
        return query.order_by(DataTreatmentRegistry.fecha_creacion.desc()).all()
    
    def get_treatment_by_id(self, treatment_id: int) -> Optional[DataTreatmentRegistry]:
        """Obtiene un tratamiento específico por ID"""
        return self.db.query(DataTreatmentRegistry).filter(
            DataTreatmentRegistry.id == treatment_id,
            DataTreatmentRegistry.is_active == True
        ).first()
    
    def get_treatments_by_category(self, category: DataCategory) -> List[DataTreatmentRegistry]:
        """Obtiene tratamientos que procesan una categoría específica de datos"""
        return self.db.query(DataTreatmentRegistry).filter(
            DataTreatmentRegistry.data_categories.contains(category.value),
            DataTreatmentRegistry.is_active == True
        ).all()
    
    def get_treatments_by_legal_basis(self, legal_basis: LegalBasis) -> List[DataTreatmentRegistry]:
        """Obtiene tratamientos basados en una base legal específica"""
        return self.db.query(DataTreatmentRegistry).filter(
            DataTreatmentRegistry.legal_basis == legal_basis,
            DataTreatmentRegistry.is_active == True
        ).all()
    
    def update_treatment(
        self, 
        treatment_id: int, 
        user_id: int,
        **update_fields
    ) -> DataTreatmentRegistry:
        """Actualiza un registro de tratamiento existente"""
        treatment = self.get_treatment_by_id(treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Registro de tratamiento no encontrado")
        
        try:
            # Actualizar campos proporcionados
            for field, value in update_fields.items():
                if hasattr(treatment, field) and value is not None:
                    if field == 'data_categories' and isinstance(value, list):
                        value = json.dumps(value)
                    setattr(treatment, field, value)
            
            treatment.fecha_actualizacion = datetime.now()
            self.db.commit()
            self.db.refresh(treatment)
            
            # Log de auditoría
            self.audit_logger.log_audit_event(
                usuario_id =user_id,
                nombre_usuario =f"user_{user_id}",
                action=AuditAction.TREATMENT_UPDATE,
                result=AuditResult.SUCCESS,
                details={
                    "treatment_registry_id": treatment_id,
                    "updated_fields": list(update_fields.keys())
                }
            )
            
            return treatment
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error actualizando registro: {str(e)}"
            )
    
    def deactivate_treatment(self, treatment_id: int, user_id: int) -> bool:
        """Desactiva un registro de tratamiento"""
        treatment = self.get_treatment_by_id(treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        
        try:
            treatment.is_active = False
            treatment.fecha_actualizacion = datetime.now()
            self.db.commit()
            
            # Log de auditoría
            self.audit_logger.log_audit_event(
                usuario_id =user_id,
                nombre_usuario =f"user_{user_id}",
                action=AuditAction.TREATMENT_DELETE,
                result=AuditResult.SUCCESS,
                details={
                    "treatment_registry_id": treatment_id,
                    "treatment_name": treatment.treatment_name
                }
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error desactivando registro: {str(e)}"
            )
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        Genera un reporte de cumplimiento PRF4 con todos los tratamientos registrados
        """
        treatments = self.get_all_treatments()
        
        # Estadísticas generales
        total_treatments = len(treatments)
        by_legal_basis = {}
        by_retention_period = {}
        by_category = {}
        
        for treatment in treatments:
            # Contar por base legal
            basis = treatment.legal_basis.value
            by_legal_basis[basis] = by_legal_basis.get(basis, 0) + 1
            
            # Contar por período de retención
            retention = treatment.retention_period.value
            by_retention_period[retention] = by_retention_period.get(retention, 0) + 1
            
            # Contar por categorías de datos
            try:
                categories = json.loads(treatment.data_categories)
                for category in categories:
                    by_category[category] = by_category.get(category, 0) + 1
            except:
                pass
        
        return {
            "prf4_compliance_report": {
                "generated_at": datetime.now().isoformat(),
                "total_active_treatments": total_treatments,
                "summary": {
                    "legal_bases_distribution": by_legal_basis,
                    "retention_periods_distribution": by_retention_period,
                    "data_categories_distribution": by_category
                },
                "treatments": [t.to_dict() for t in treatments],
                "compliance_status": {
                    "prf4_compliant": total_treatments > 0,
                    "gdpr_article_30_compliant": True,
                    "records_complete": all(
                        t.legal_basis and t.retention_period and t.processing_purpose 
                        for t in treatments
                    )
                }
            }
        }
    
    def get_treatments_for_data_subject(self, subject_email: str) -> List[Dict[str, Any]]:
        """
        Obtiene tratamientos que pueden afectar a un interesado específico.
        Usado para responder solicitudes de acceso (PRF2).
        """
        treatments = self.get_all_treatments()
        
        # Filtrar tratamientos relevantes (todos los que procesan datos de usuarios)
        relevant_treatments = []
        for treatment in treatments:
            try:
                categories = json.loads(treatment.data_categories)
                # Si procesa datos identificativos, de contacto o de contenido
                if any(cat in ['identification', 'contact', 'content', 'authentication'] 
                       for cat in categories):
                    relevant_treatments.append({
                        "treatment_name": treatment.treatment_name,
                        "purpose": treatment.processing_purpose,
                        "legal_basis": treatment.legal_basis.value,
                        "retention_period": treatment.retention_period.value,
                        "data_categories": categories,
                        "subject_rights": treatment.subject_rights_info
                    })
            except:
                continue
        
        return relevant_treatments


def get_data_treatment_service(db: Session) -> DataTreatmentService:
    """Factory function para el servicio de tratamiento de datos"""
    return DataTreatmentService(db)
