from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.services.db_service import get_db
from app.services.dependencies import get_current_user, require_admin
from app.services.dpa_management_service import get_dpa_management_service
from app.models.dpa_agreement import DpaStatus, DataLocation, CloudProvider
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.config.config import settings
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
import os


router = APIRouter(prefix="/dpa-admin", tags=["dpa-admin"])


class DpaCreateRequest(BaseModel):
    """Modelo para crear un nuevo DPA"""
    provider_name: str
    cloud_provider: str  # Será convertido a enum
    dpa_title: str
    dpa_description: str
    signed_date: date
    effective_date: date
    expiry_date: date
    data_location: str  # Será convertido a enum
    data_categories_processed: List[str]
    processing_purposes: str
    security_measures: str
    
    # Campos opcionales
    provider_contact: Optional[str] = None
    provider_address: Optional[str] = None
    contract_number: Optional[str] = None
    renewal_date: Optional[date] = None
    data_location_details: Optional[str] = None
    transfer_mechanism: Optional[str] = None
    adequacy_decision: Optional[bool] = False
    data_subjects_categories: Optional[str] = None
    encryption_standards: Optional[str] = None
    access_controls: Optional[str] = None
    subprocessors_allowed: Optional[bool] = False
    subprocessors_list: Optional[str] = None
    subprocessor_notification: Optional[bool] = True
    data_subject_requests: Optional[str] = None
    data_breach_notification: Optional[str] = None
    audit_rights: Optional[str] = None
    auto_renewal: Optional[bool] = False
    termination_notice_days: Optional[int] = 30
    compliance_notes: Optional[str] = None
    risk_assessment: Optional[str] = None


class DpaUpdateRequest(BaseModel):
    """Modelo para actualizar un DPA existente"""
    provider_name: Optional[str] = None
    provider_contact: Optional[str] = None
    provider_address: Optional[str] = None
    dpa_title: Optional[str] = None
    dpa_description: Optional[str] = None
    renewal_date: Optional[date] = None
    data_location_details: Optional[str] = None
    transfer_mechanism: Optional[str] = None
    adequacy_decision: Optional[bool] = None
    processing_purposes: Optional[str] = None
    data_subjects_categories: Optional[str] = None
    security_measures: Optional[str] = None
    encryption_standards: Optional[str] = None
    access_controls: Optional[str] = None
    subprocessors_allowed: Optional[bool] = None
    subprocessors_list: Optional[str] = None
    subprocessor_notification: Optional[bool] = None
    data_subject_requests: Optional[str] = None
    data_breach_notification: Optional[str] = None
    audit_rights: Optional[str] = None
    auto_renewal: Optional[bool] = None
    termination_notice_days: Optional[int] = None
    compliance_notes: Optional[str] = None
    risk_assessment: Optional[str] = None


@router.post("/dpa")
def create_dpa(
    request: DpaCreateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Crea un nuevo Data Processing Agreement (DPA) con un proveedor cloud.
    
    Permite registrar acuerdos de procesamiento de datos con proveedores externos,
    incluyendo ubicación de datos, fechas de vigencia y medidas de seguridad.
    
    Requiere rol de administrador.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        
        # Validar y convertir enums
        try:
            cloud_provider = CloudProvider(request.cloud_provider)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Proveedor cloud inválido: {request.cloud_provider}"
            )
        
        try:
            data_location = DataLocation(request.data_location)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Ubicación de datos inválida: {request.data_location}"
            )
        
        # Crear DPA
        dpa = service.create_dpa(
            provider_name=request.provider_name,
            cloud_provider=cloud_provider,
            dpa_title=request.dpa_title,
            dpa_description=request.dpa_description,
            signed_date=request.signed_date,
            effective_date=request.effective_date,
            expiry_date=request.expiry_date,
            data_location=data_location,
            data_categories_processed=request.data_categories_processed,
            processing_purposes=request.processing_purposes,
            security_measures=request.security_measures,
            usuario_id =current_user.id,
            # Campos opcionales
            provider_contact=request.provider_contact,
            provider_address=request.provider_address,
            contract_number=request.contract_number,
            renewal_date=request.renewal_date,
            data_location_details=request.data_location_details,
            transfer_mechanism=request.transfer_mechanism,
            adequacy_decision=request.adequacy_decision,
            data_subjects_categories=request.data_subjects_categories,
            encryption_standards=request.encryption_standards,
            access_controls=request.access_controls,
            subprocessors_allowed=request.subprocessors_allowed,
            subprocessors_list=request.subprocessors_list,
            subprocessor_notification=request.subprocessor_notification,
            data_subject_requests=request.data_subject_requests,
            data_breach_notification=request.data_breach_notification,
            audit_rights=request.audit_rights,
            auto_renewal=request.auto_renewal,
            termination_notice_days=request.termination_notice_days,
            compliance_notes=request.compliance_notes,
            risk_assessment=request.risk_assessment
        )
        
        return {
            "status": "success",
            "message": "DPA creado exitosamente",
            "dpa_id": dpa.id,
            "dpa": dpa.to_dict(),
            "compliance": {
                "prf5_compliant": True,
                "gdpr_transfer_safeguards": "documented",
                "data_location_registered": dpa.data_location.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando DPA: {str(e)}"
        )


@router.get("/dpa")
def list_dpas(
    active_only: bool = Query(True, descripcion ="Solo DPA activos"),
    provider: Optional[str] = Query(None, descripcion ="Filtrar por proveedor cloud"),
    location: Optional[str] = Query(None, descripcion ="Filtrar por ubicación de datos"),
    expiring_soon: Optional[bool] = Query(False, descripcion ="Solo los que vencen pronto"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Lista todos los Data Processing Agreements registrados.
    
    Proporciona panel administrativo para visualizar todos los DPA,
    con opciones de filtrado por proveedor, ubicación y estado de vencimiento.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        
        if expiring_soon:
            dpas = service.get_expiring_dpas()
        elif provider:
            try:
                cloud_provider = CloudProvider(provider)
                dpas = service.get_dpas_by_provider(cloud_provider)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Proveedor inválido: {provider}")
        elif location:
            try:
                data_location = DataLocation(location)
                dpas = service.get_dpas_by_location(data_location)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Ubicación inválida: {location}")
        else:
            dpas = service.get_all_dpas(active_only=active_only)
        
        return {
            "total_dpas": len(dpas),
            "filters_applied": {
                "active_only": active_only,
                "provider": provider,
                "location": location,
                "expiring_soon": expiring_soon
            },
            "dpas": [dpa.to_dict() for dpa in dpas],
            "compliance_status": {
                "prf5_compliant": len(dpas) > 0,
                "gdpr_transfer_documentation": "available"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo DPA: {str(e)}"
        )


@router.get("/dpa/{dpa_id}")
def get_dpa_details(
    dpa_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """PRF5: Obtiene detalles completos de un DPA específico"""
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        dpa = service.get_dpa_by_id(dpa_id)
        
        if not dpa:
            raise HTTPException(status_code=404, detail="DPA no encontrado")
        
        return {
            "dpa": dpa.to_dict(),
            "compliance_analysis": {
                "days_until_expiry": dpa.days_until_expiry,
                "is_expiring_soon": dpa.is_expiring_soon(),
                "is_expired": dpa.is_expired,
                "adequacy_decision": dpa.adequacy_decision,
                "transfer_mechanism_required": dpa.data_location not in [DataLocation.EU, DataLocation.ON_PREMISE]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo DPA: {str(e)}"
        )


@router.put("/dpa/{dpa_id}")
def update_dpa(
    dpa_id: int,
    request: DpaUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Actualiza un DPA existente.
    
    Permite modificar campos específicos del acuerdo manteniendo
    trazabilidad de cambios para auditorías.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        
        # Preparar campos para actualización
        update_fields = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[field] = value
        
        dpa = service.update_dpa(dpa_id, current_user.id, **update_fields)
        
        return {
            "status": "success",
            "message": "DPA actualizado exitosamente",
            "dpa": dpa.to_dict(),
            "updated_fields": list(update_fields.keys()),
            "last_reviewed": dpa.last_reviewed_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando DPA: {str(e)}"
        )


@router.patch("/dpa/{dpa_id}/status")
def change_dpa_status(
    dpa_id: int,
    new_status: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Cambia el estado de un DPA (draft, active, expired, terminated, suspended).
    
    Permite gestionar el ciclo de vida de los acuerdos con los proveedores.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        # Validar estado
        try:
            status_enum = DpaStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {new_status}")
        
        service = get_dpa_management_service(db)
        dpa = service.update_dpa_status(dpa_id, status_enum, current_user.id)
        
        return {
            "status": "success",
            "message": f"Estado del DPA cambiado a: {new_status}",
            "dpa_id": dpa_id,
            "new_status": new_status,
            "approved_by": current_user.id if new_status == "active" else None,
            "approved_at": dpa.approved_at.isoformat() if dpa.approved_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cambiando estado del DPA: {str(e)}"
        )


@router.delete("/dpa/{dpa_id}")
def deactivate_dpa(
    dpa_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Desactiva un DPA (no elimina físicamente).
    
    Mantiene el registro para trazabilidad pero lo marca como inactivo.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        success = service.deactivate_dpa(dpa_id, current_user.id)
        
        return {
            "status": "success",
            "message": "DPA desactivado exitosamente",
            "dpa_id": dpa_id,
            "deactivated": success,
            "deactivated_by": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error desactivando DPA: {str(e)}"
        )


@router.get("/dashboard")
def get_dpa_dashboard(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Panel administrativo principal con estadísticas y alertas de DPA.
    
    Proporciona vista general del estado de todos los acuerdos:
    - Estadísticas por proveedor y ubicación
    - Alertas de vencimiento
    - Métricas de cumplimiento
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        dashboard = service.generate_dpa_dashboard()
        
        # Log de acceso al dashboard
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=current_user.id,
                username=current_user.correo,
                action=AuditAction.VIEW,
                result=AuditResult.SUCCESS,
                details={
                    "module": "PRF5_DPA_DASHBOARD",
                    "dashboard_type": "admin_panel",
                    "total_dpas": dashboard["prf5_dpa_dashboard"]["summary"]["total_active_dpas"]
                },
                audit_dir=settings.AUDIT_DIR
            )
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando dashboard: {str(e)}"
        )


@router.get("/data-locations")
def get_data_location_report(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Reporte detallado de ubicaciones de datos y transferencias.
    
    Genera mapeo completo de dónde se almacenan los datos según
    los DPA registrados, útil para cumplimiento GDPR de transferencias.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        report = service.generate_data_location_report()
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte de ubicaciones: {str(e)}"
        )


@router.get("/alerts")
def get_dpa_alerts(
    days_ahead: int = Query(30, descripcion ="Días para alertas de vencimiento"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRF5: Obtiene alertas de DPA que requieren atención.
    
    Identifica DPA que vencen pronto o ya vencidos para
    facilitar renovaciones oportunas.
    """
    # Verificar rol de administrador
    require_admin(current_user)
    
    try:
        service = get_dpa_management_service(db)
        
        expiring = service.get_expiring_dpas(days_ahead)
        expired = service.get_expired_dpas()
        
        return {
            "alert_summary": {
                "expiring_soon": len(expiring),
                "expired": len(expired),
                "days_threshold": days_ahead,
                "generated_at": datetime.now().isoformat()
            },
            "expiring_dpas": [
                {
                    "id": dpa.id,
                    "provider": dpa.provider_name,
                    "cloud_provider": dpa.cloud_provider.value,
                    "expiry_date": dpa.expiry_date.isoformat(),
                    "days_remaining": dpa.days_until_expiry,
                    "auto_renewal": dpa.auto_renewal,
                    "priority": "high" if dpa.days_until_expiry <= 7 else "medium"
                }
                for dpa in expiring
            ],
            "expired_dpas": [
                {
                    "id": dpa.id,
                    "provider": dpa.provider_name,
                    "cloud_provider": dpa.cloud_provider.value,
                    "expiry_date": dpa.expiry_date.isoformat(),
                    "days_overdue": abs(dpa.days_until_expiry),
                    "status": dpa.status.value,
                    "priority": "critical"
                }
                for dpa in expired
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo alertas: {str(e)}"
        )


@router.get("/enums")
def get_dpa_enums():
    """
    PRF5: Obtiene los valores disponibles para enums de DPA.
    
    Útil para formularios del panel administrativo.
    """
    return {
        "cloud_providers": [
            {"value": provider.value, "name": provider.nombre} 
            for provider in CloudProvider
        ],
        "data_locations": [
            {"value": location.value, "name": location.nombre}
            for location in DataLocation
        ],
        "dpa_statuses": [
            {"value": status.value, "name": status.nombre}
            for status in DpaStatus
        ],
        "transfer_mechanisms": [
            "Standard Contractual Clauses (SCCs)",
            "Adequacy Decision",
            "Binding Corporate Rules (BCRs)",
            "Certification",
            "Code of Conduct",
            "Other"
        ]
    }
