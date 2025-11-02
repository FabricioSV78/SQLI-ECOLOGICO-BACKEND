from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.db_service import get_db
from app.services.dependencies import get_current_user, require_admin
from app.services.data_treatment_service import get_data_treatment_service
from app.models.data_treatment_registry import LegalBasis, DataCategory, RetentionPeriod
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.config.config import settings
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/data-treatment", tags=["data-treatment"])


class TreatmentCreateRequest(BaseModel):
    """Modelo para crear un nuevo registro de tratamiento"""
    treatment_name: str
    treatment_description: str
    data_categories: List[str]
    data_fields: str
    processing_purpose: str
    processing_activities: str
    legal_basis: str  # Será convertido a enum
    retention_period: str  # Será convertido a enum
    legal_basis_details: Optional[str] = None
    retention_criteria: Optional[str] = None
    deletion_procedure: Optional[str] = None
    security_measures: Optional[str] = None
    access_controls: Optional[str] = None
    data_transfers: Optional[str] = None
    transfer_safeguards: Optional[str] = None
    subject_rights_info: Optional[str] = None
    responsible_person: Optional[str] = None


class TreatmentUpdateRequest(BaseModel):
    """Modelo para actualizar un registro de tratamiento"""
    treatment_name: Optional[str] = None
    treatment_description: Optional[str] = None
    data_categories: Optional[List[str]] = None
    data_fields: Optional[str] = None
    processing_purpose: Optional[str] = None
    processing_activities: Optional[str] = None
    legal_basis_details: Optional[str] = None
    retention_criteria: Optional[str] = None
    deletion_procedure: Optional[str] = None
    security_measures: Optional[str] = None
    access_controls: Optional[str] = None
    data_transfers: Optional[str] = None
    transfer_safeguards: Optional[str] = None
    subject_rights_info: Optional[str] = None
    responsible_person: Optional[str] = None


@router.post("/registry")
def create_treatment_registry(
    request: TreatmentCreateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Crea un nuevo registro de tratamiento de datos personales.
    
    Permite registrar qué datos procesamos, con qué finalidad, base legal
    y período de retención según los requisitos GDPR.
    
    Requiere rol de administrador.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_data_treatment_service(db)
        
        # Validar y convertir enums
        try:
            legal_basis = LegalBasis(request.legal_basis)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Base legal inválida: {request.legal_basis}"
            )
        
        try:
            retention_period = RetentionPeriod(request.retention_period)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Período de retención inválido: {request.retention_period}"
            )
        
        # Crear registro
        treatment = service.create_treatment_registry(
            treatment_name=request.treatment_name,
            treatment_description=request.treatment_description,
            data_categories=request.data_categories,
            data_fields=request.data_fields,
            processing_purpose=request.processing_purpose,
            processing_activities=request.processing_activities,
            legal_basis=legal_basis,
            retention_period=retention_period,
            usuario_id =current_user.id,
            legal_basis_details=request.legal_basis_details,
            retention_criteria=request.retention_criteria,
            deletion_procedure=request.deletion_procedure,
            security_measures=request.security_measures,
            access_controls=request.access_controls,
            data_transfers=request.data_transfers,
            transfer_safeguards=request.transfer_safeguards,
            subject_rights_info=request.subject_rights_info,
            responsible_person=request.responsible_person
        )
        
        # Log de auditoría
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.CREATE,
                result=AuditResult.SUCCESS,
                details={
                    "module": "PRF4_DATA_TREATMENT_REGISTRY",
                    "treatment_id": treatment.id,
                    "treatment_name": request.treatment_name,
                    "legal_basis": legal_basis.value,
                    "retention_period": retention_period.value
                },
                audit_dir=settings.AUDIT_DIR
            )
        
        return {
            "status": "success",
            "message": "Registro de tratamiento creado exitosamente",
            "treatment_id": treatment.id,
            "treatment": treatment.to_dict(),
            "compliance": {
                "prf4_compliant": True,
                "gdpr_article_30": "registered",
                "created_at": treatment.fecha_creacion
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando registro de tratamiento: {str(e)}"
        )


@router.get("/registry")
def list_treatment_registries(
    active_only: bool = Query(True, descripcion ="Solo registros activos"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Lista todos los registros de tratamiento de datos.
    
    Proporciona visibilidad completa de qué datos procesamos y cómo,
    cumpliendo con los requisitos de transparencia GDPR.
    """
    try:
        service = get_data_treatment_service(db)
        treatments = service.get_all_treatments(active_only=active_only)
        
        return {
            "total_treatments": len(treatments),
            "active_only": active_only,
            "treatments": [treatment.to_dict() for treatment in treatments],
            "compliance_status": {
                "prf4_compliant": len(treatments) > 0,
                "gdpr_article_30_records": "available"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo registros: {str(e)}"
        )


@router.get("/registry/{treatment_id}")
def get_treatment_registry(
    treatment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """PRF4: Obtiene un registro específico de tratamiento por ID"""
    try:
        service = get_data_treatment_service(db)
        treatment = service.get_treatment_by_id(treatment_id)
        
        if not treatment:
            raise HTTPException(status_code=404, detail="Registro de tratamiento no encontrado")
        
        return {
            "treatment": treatment.to_dict(),
            "compliance_info": {
                "prf4_status": "compliant",
                "last_updated": treatment.fecha_actualizacion
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo registro: {str(e)}"
        )


@router.put("/registry/{treatment_id}")
def update_treatment_registry(
    treatment_id: int,
    request: TreatmentUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Actualiza un registro existente de tratamiento de datos.
    
    Requiere rol de administrador.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_data_treatment_service(db)
        
        # Preparar campos para actualización
        update_fields = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[field] = value
        
        treatment = service.update_treatment(treatment_id, current_user.id, **update_fields)
        
        return {
            "status": "success",
            "message": "Registro actualizado exitosamente",
            "treatment": treatment.to_dict(),
            "updated_fields": list(update_fields.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando registro: {str(e)}"
        )


@router.delete("/registry/{treatment_id}")
def deactivate_treatment_registry(
    treatment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Desactiva un registro de tratamiento.
    
    No elimina físicamente el registro para mantener trazabilidad.
    Requiere rol de administrador.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_data_treatment_service(db)
        success = service.deactivate_treatment(treatment_id, current_user.id)
        
        return {
            "status": "success",
            "message": "Registro desactivado exitosamente",
            "treatment_id": treatment_id,
            "deactivated": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error desactivando registro: {str(e)}"
        )


@router.get("/compliance-report")
def generate_compliance_report(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Genera un reporte completo de cumplimiento GDPR.
    
    Incluye todos los tratamientos registrados, estadísticas y 
    estado de cumplimiento según Artículo 30 GDPR.
    """
    try:
        service = get_data_treatment_service(db)
        report = service.generate_compliance_report()
        
        # Log del reporte generado
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.VIEW,
                result=AuditResult.SUCCESS,
                details={
                    "module": "PRF4_COMPLIANCE_REPORT",
                    "report_type": "gdpr_article_30",
                    "treatments_included": report["prf4_compliance_report"]["total_active_treatments"]
                },
                audit_dir=settings.AUDIT_DIR
            )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte: {str(e)}"
        )


@router.get("/enums")
def get_available_enums():
    """
    PRF4: Obtiene los valores disponibles para enums (bases legales, 
    categorías de datos, períodos de retención).
    
    Útil para formularios y validaciones del frontend.
    """
    return {
        "legal_bases": [
            {"value": basis.value, "name": basis.nombre} 
            for basis in LegalBasis
        ],
        "data_categories": [
            {"value": category.value, "name": category.nombre}
            for category in DataCategory
        ],
        "retention_periods": [
            {"value": period.value, "name": period.nombre}
            for period in RetentionPeriod
        ]
    }


@router.get("/subject-treatments/{subject_email}")
def get_treatments_for_subject(
    subject_email: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF4: Obtiene tratamientos que afectan a un interesado específico.
    
    Usado para responder solicitudes de acceso de datos (integración con PRF2).
    Requiere rol de administrador o que sea el propio usuario.
    """
    # Verificar permisos (admin o el propio usuario)
    if current_user.correo != subject_email and current_user.rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="No autorizado para consultar tratamientos de otro usuario"
        )
    
    try:
        service = get_data_treatment_service(db)
        treatments = service.get_treatments_for_data_subject(subject_email)
        
        return {
            "subject_email": subject_email,
            "applicable_treatments": treatments,
            "total_treatments": len(treatments),
            "data_subject_rights": {
                "access": "Available via PRF2 endpoints",
                "rectification": "Available via PRF2 endpoints", 
                "erasure": "Available via PRF2 endpoints",
                "portability": "Contact administrator",
                "objection": "Contact administrator"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo tratamientos para interesado: {str(e)}"
        )
