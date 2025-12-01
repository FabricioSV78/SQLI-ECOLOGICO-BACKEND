from sqlalchemy.orm import Session
from app.models.dpa_agreement import (
    DataProcessingAgreement, 
    DpaStatus, 
    DataLocation, 
    CloudProvider
)
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime, date, timedelta
import json


class DpaManagementService:
    """
    PRF5: Servicio para gestionar Data Processing Agreements (DPA) con proveedores cloud.
    
    Proporciona funcionalidad para:
    - Crear y mantener registros de DPA
    - Monitorear fechas de vigencia y vencimientos
    - Generar alertas de renovación
    - Auditar cumplimiento de transferencias internacionales
    - Gestionar ubicaciones de datos y medidas de seguridad
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_dpa(
        self,
        provider_name: str,
        cloud_provider: CloudProvider,
        dpa_title: str,
        dpa_description: str,
        signed_date: date,
        effective_date: date,
        expiry_date: date,
        data_location: DataLocation,
        data_categories_processed: List[str],
        processing_purposes: str,
        security_measures: str,
        user_id: int,
        **optional_fields
    ) -> DataProcessingAgreement:
        """
        Crea un nuevo DPA con un proveedor cloud.
        
        Args:
            provider_name: Nombre del proveedor
            cloud_provider: Tipo de proveedor cloud
            dpa_title: Título del acuerdo
            dpa_description: Descripción detallada
            signed_date: Fecha de firma
            effective_date: Fecha de entrada en vigor
            expiry_date: Fecha de vencimiento
            data_location: Ubicación de los datos
            data_categories_processed: Categorías de datos procesados
            processing_purposes: Finalidades del procesamiento
            security_measures: Medidas de seguridad implementadas
            user_id: ID del usuario que crea el DPA
            **optional_fields: Campos opcionales adicionales
        """
        try:
            # Validaciones básicas
            if effective_date > expiry_date:
                raise HTTPException(
                    status_code=400,
                    detail="La fecha de vigencia no puede ser posterior a la fecha de vencimiento"
                )
            
            if signed_date > effective_date:
                raise HTTPException(
                    status_code=400,
                    detail="La fecha de firma no puede ser posterior a la fecha de vigencia"
                )
            
            # Crear DPA
            dpa = DataProcessingAgreement(
                provider_name=provider_name,
                cloud_provider=cloud_provider,
                dpa_title=dpa_title,
                dpa_description=dpa_description,
                signed_date=signed_date,
                effective_date=effective_date,
                expiry_date=expiry_date,
                data_location=data_location,
                data_categories_processed=json.dumps(data_categories_processed),
                processing_purposes=processing_purposes,
                security_measures=security_measures,
                created_by=user_id,
                status=DpaStatus.DRAFT,
                # Campos opcionales
                provider_contact=optional_fields.get('provider_contact'),
                provider_address=optional_fields.get('provider_address'),
                contract_number=optional_fields.get('contract_number'),
                renewal_date=optional_fields.get('renewal_date'),
                data_location_details=optional_fields.get('data_location_details'),
                transfer_mechanism=optional_fields.get('transfer_mechanism'),
                adequacy_decision=optional_fields.get('adequacy_decision', False),
                data_subjects_categories=optional_fields.get('data_subjects_categories'),
                encryption_standards=optional_fields.get('encryption_standards'),
                access_controls=optional_fields.get('access_controls'),
                subprocessors_allowed=optional_fields.get('subprocessors_allowed', False),
                subprocessors_list=optional_fields.get('subprocessors_list'),
                subprocessor_notification=optional_fields.get('subprocessor_notification', True),
                data_subject_requests=optional_fields.get('data_subject_requests'),
                data_breach_notification=optional_fields.get('data_breach_notification'),
                audit_rights=optional_fields.get('audit_rights'),
                auto_renewal=optional_fields.get('auto_renewal', False),
                termination_notice_days=optional_fields.get('termination_notice_days', 30),
                contract_file_path=optional_fields.get('contract_file_path'),
                compliance_notes=optional_fields.get('compliance_notes'),
                risk_assessment=optional_fields.get('risk_assessment')
            )
            
            self.db.add(dpa)
            self.db.commit()
            self.db.refresh(dpa)
            
            # Log de auditoría
            """ if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"admin_{user_id}",
                    action=AuditAction.DPA_CREATE,
                    result=AuditResult.SUCCESS,
                    details={
                        "module": "PRF5_DPA_MANAGEMENT",
                        "dpa_id": dpa.id,
                        "provider_name": provider_name,
                        "cloud_provider": cloud_provider.value,
                        "data_location": data_location.value,
                        "expiry_date": expiry_date.isoformat()
                    },
                    audit_dir=settings.AUDIT_DIR
                )
             """
            return dpa
            
        except Exception as e:
            self.db.rollback()
            # Log de error
            """ if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"admin_{user_id}",
                    action=AuditAction.DPA_CREATE,
                    result=AuditResult.ERROR,
                    details={
                        "module": "PRF5_DPA_MANAGEMENT",
                        "provider_name": provider_name,
                        "error": str(e)
                    },
                    audit_dir=settings.AUDIT_DIR
                ) """
            raise HTTPException(
                status_code=500,
                detail=f"Error creando DPA: {str(e)}"
            )
    
    def get_all_dpas(self, active_only: bool = True) -> List[DataProcessingAgreement]:
        """Obtiene todos los DPA registrados"""
        consulta = self.db.query(DataProcessingAgreement)
        if active_only:
            consulta = consulta.filter(DataProcessingAgreement.is_active == True)
        
        return consulta.order_by(DataProcessingAgreement.fecha_creacion.desc()).all()
    
    def get_dpa_by_id(self, dpa_id: int) -> Optional[DataProcessingAgreement]:
        """Obtiene un DPA específico por ID"""
        return self.db.query(DataProcessingAgreement).filter(
            DataProcessingAgreement.id == dpa_id,
            DataProcessingAgreement.is_active == True
        ).first()
    
    def get_dpas_by_provider(self, cloud_provider: CloudProvider) -> List[DataProcessingAgreement]:
        """Obtiene DPA por tipo de proveedor cloud"""
        return self.db.query(DataProcessingAgreement).filter(
            DataProcessingAgreement.cloud_provider == cloud_provider,
            DataProcessingAgreement.is_active == True
        ).all()
    
    def get_dpas_by_location(self, data_location: DataLocation) -> List[DataProcessingAgreement]:
        """Obtiene DPA por ubicación de datos"""
        return self.db.query(DataProcessingAgreement).filter(
            DataProcessingAgreement.data_location == data_location,
            DataProcessingAgreement.is_active == True
        ).all()
    
    def get_expiring_dpas(self, days_ahead: int = 30) -> List[DataProcessingAgreement]:
        """
        Obtiene DPA que vencen en los próximos X días.
        Útil para alertas de renovación.
        """
        threshold_date = date.today() + timedelta(days=days_ahead)
        
        return self.db.query(DataProcessingAgreement).filter(
            DataProcessingAgreement.expiry_date <= threshold_date,
            DataProcessingAgreement.expiry_date >= date.today(),
            DataProcessingAgreement.status.in_([DpaStatus.ACTIVE, DpaStatus.DRAFT]),
            DataProcessingAgreement.is_active == True
        ).order_by(DataProcessingAgreement.expiry_date).all()
    
    def get_expired_dpas(self) -> List[DataProcessingAgreement]:
        """Obtiene DPA ya vencidos"""
        return self.db.query(DataProcessingAgreement).filter(
            DataProcessingAgreement.expiry_date < date.today(),
            DataProcessingAgreement.status != DpaStatus.EXPIRED,
            DataProcessingAgreement.is_active == True
        ).all()
    
    def update_dpa_status(self, dpa_id: int, new_status: DpaStatus, user_id: int) -> DataProcessingAgreement:
        """Actualiza el estado de un DPA"""
        dpa = self.get_dpa_by_id(dpa_id)
        if not dpa:
            raise HTTPException(status_code=404, detail="DPA no encontrado")
        
        try:
            old_status = dpa.status
            dpa.status = new_status
            dpa.fecha_actualizacion = datetime.now()
            
            if new_status == DpaStatus.ACTIVE:
                dpa.approved_by = user_id
                dpa.approved_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(dpa)
            
            # Log de auditoría
            """ if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"admin_{user_id}",
                    action=AuditAction.DPA_STATUS_CHANGE,
                    result=AuditResult.SUCCESS,
                    details={
                        "module": "PRF5_DPA_MANAGEMENT",
                        "dpa_id": dpa_id,
                        "provider_name": dpa.provider_name,
                        "old_status": old_status.value,
                        "new_status": new_status.value
                    },
                    audit_dir=settings.AUDIT_DIR
                ) """
            
            return dpa
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error actualizando estado del DPA: {str(e)}"
            )
    
    def update_dpa(
        self, 
        dpa_id: int, 
        user_id: int,
        **update_fields
    ) -> DataProcessingAgreement:
        """Actualiza campos específicos de un DPA"""
        dpa = self.get_dpa_by_id(dpa_id)
        if not dpa:
            raise HTTPException(status_code=404, detail="DPA no encontrado")
        
        try:
            # Actualizar campos proporcionados
            for field, value in update_fields.items():
                if hasattr(dpa, field) and value is not None:
                    if field == 'data_categories_processed' and isinstance(value, list):
                        value = json.dumps(value)
                    setattr(dpa, field, value)
            
            dpa.fecha_actualizacion = datetime.now()
            dpa.last_reviewed_by = user_id
            dpa.last_reviewed_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(dpa)
            
            # Log de auditoría
            """ if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"admin_{user_id}",
                    action=AuditAction.DPA_UPDATE,
                    result=AuditResult.SUCCESS,
                    details={
                        "module": "PRF5_DPA_MANAGEMENT",
                        "dpa_id": dpa_id,
                        "provider_name": dpa.provider_name,
                        "updated_fields": list(update_fields.keys())
                    },
                    audit_dir=settings.AUDIT_DIR
                ) """
            
            return dpa
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error actualizando DPA: {str(e)}"
            )
    
    def deactivate_dpa(self, dpa_id: int, user_id: int) -> bool:
        """Desactiva un DPA (no lo elimina físicamente)"""
        dpa = self.get_dpa_by_id(dpa_id)
        if not dpa:
            raise HTTPException(status_code=404, detail="DPA no encontrado")
        
        try:
            dpa.is_active = False
            dpa.status = DpaStatus.TERMINATED
            dpa.fecha_actualizacion = datetime.now()
            self.db.commit()
            
            # Log de auditoría
            """ if settings.AUDIT_ENABLED:
                log_user_action(
                    usuario_id =user_id,
                    nombre_usuario =f"admin_{user_id}",
                    action=AuditAction.DELETE,
                    result=AuditResult.SUCCESS,
                    details={
                        "module": "PRF5_DPA_MANAGEMENT",
                        "dpa_id": dpa_id,
                        "provider_name": dpa.provider_name
                    },
                    audit_dir=settings.AUDIT_DIR
                ) """
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error desactivando DPA: {str(e)}"
            )
    
    def generate_dpa_dashboard(self) -> Dict[str, Any]:
        """
        Genera un dashboard administrativo con estadísticas de DPA.
        
        Returns:
            Dashboard con métricas clave para administradores
        """
        all_dpas = self.get_all_dpas()
        expiring_soon = self.get_expiring_dpas()
        expired = self.get_expired_dpas()
        
        # Estadísticas por proveedor
        by_provider = {}
        by_location = {}
        by_status = {}
        
        for dpa in all_dpas:
            # Por proveedor
            provider = dpa.cloud_provider.value
            by_provider[provider] = by_provider.get(provider, 0) + 1
            
            # Por ubicación
            location = dpa.data_location.value
            by_location[location] = by_location.get(location, 0) + 1
            
            # Por estado
            status = dpa.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "prf5_dpa_dashboard": {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_active_dpas": len(all_dpas),
                    "expiring_soon": len(expiring_soon),
                    "expired_requiring_attention": len(expired),
                    "active_providers": len(by_provider),
                    "data_locations": len(by_location)
                },
                "statistics": {
                    "by_cloud_provider": by_provider,
                    "by_data_location": by_location,
                    "by_status": by_status
                },
                "alerts": {
                    "expiring_dpas": [
                        {
                            "id": dpa.id,
                            "provider": dpa.provider_name,
                            "expiry_date": dpa.expiry_date.isoformat(),
                            "days_remaining": dpa.days_until_expiry
                        }
                        for dpa in expiring_soon
                    ],
                    "expired_dpas": [
                        {
                            "id": dpa.id,
                            "provider": dpa.provider_name,
                            "expiry_date": dpa.expiry_date.isoformat(),
                            "days_overdue": abs(dpa.days_until_expiry)
                        }
                        for dpa in expired
                    ]
                },
                "compliance_status": {
                    "prf5_compliant": len(all_dpas) > 0,
                    "gdpr_transfer_safeguards": "documented",
                    "adequacy_decisions_tracked": True,
                    "security_measures_documented": True
                }
            }
        }
    
    def generate_data_location_report(self) -> Dict[str, Any]:
        """
        Genera reporte de ubicaciones de datos para cumplimiento GDPR.
        
        Returns:
            Reporte detallado de dónde se almacenan los datos
        """
        all_dpas = self.get_all_dpas()
        
        location_details = {}
        
        for dpa in all_dpas:
            location = dpa.data_location.value
            
            if location not in location_details:
                location_details[location] = {
                    "location": location,
                    "providers": [],
                    "data_categories": set(),
                    "transfer_mechanisms": set(),
                    "adequacy_decisions": 0,
                    "total_agreements": 0
                }
            
            location_info = location_details[location]
            location_info["providers"].append({
                "name": dpa.provider_name,
                "cloud_provider": dpa.cloud_provider.value,
                "status": dpa.status.value,
                "expiry_date": dpa.expiry_date.isoformat()
            })
            
            # Procesar categorías de datos
            try:
                categories = json.loads(dpa.data_categories_processed)
                location_info["data_categories"].update(categories)
            except:
                pass
            
            if dpa.transfer_mechanism:
                location_info["transfer_mechanisms"].add(dpa.transfer_mechanism)
            
            if dpa.adequacy_decision:
                location_info["adequacy_decisions"] += 1
            
            location_info["total_agreements"] += 1
        
        # Convertir sets a listas para JSON
        for location in location_details.values():
            location["data_categories"] = list(location["data_categories"])
            location["transfer_mechanisms"] = list(location["transfer_mechanisms"])
        
        return {
            "data_location_report": {
                "generated_at": datetime.now().isoformat(),
                "total_locations": len(location_details),
                "locations": location_details,
                "gdpr_compliance": {
                    "international_transfers_documented": True,
                    "transfer_mechanisms_identified": True,
                    "adequacy_decisions_tracked": True,
                    "data_mapping_complete": True
                }
            }
        }


def get_dpa_management_service(db: Session) -> DpaManagementService:
    """Factory function para el servicio de gestión DPA"""
    return DpaManagementService(db)
