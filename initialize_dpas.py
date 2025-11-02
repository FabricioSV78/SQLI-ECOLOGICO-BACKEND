"""
PRF5: Script para inicializar DPA básicos de ejemplo con proveedores cloud comunes.

Este script crea registros de ejemplo para demostrar el panel administrativo
de gestión de Data Processing Agreements según PRF5.
"""

from sqlalchemy.orm import Session
from app.services.dpa_management_service import get_dpa_management_service
from app.models.dpa_agreement import DataProcessingAgreement, CloudProvider, DataLocation, DpaStatus
from app.services.db_service import get_db
from datetime import date, timedelta


def initialize_sample_dpas(db: Session) -> None:
    """
    Inicializa DPA de ejemplo con proveedores cloud típicos.
    
    Crea registros para:
    1. AWS para hosting de aplicación (EU)
    2. PostgreSQL en DigitalOcean (EU)
    3. GitHub para repositorios (US con SCCs)
    4. Vercel para despliegue frontend (Global)
    5. Azure para respaldos (US)
    """
    
    service = get_dpa_management_service(db)
    
    # DPA 1: AWS para hosting principal
    dpa_aws = {
        "provider_name": "Amazon Web Services (AWS)",
        "cloud_provider": CloudProvider.AWS,
        "dpa_title": "AWS Data Processing Agreement - Hosting Aplicación SQLi Detector",
        "dpa_description": (
            "Acuerdo para procesamiento de datos en servicios AWS para hosting "
            "de la aplicación de detección SQLi, incluyendo EC2, RDS y S3."
        ),
        "signed_date": date(2024, 1, 15),
        "effective_date": date(2024, 2, 1),
        "expiry_date": date(2025, 2, 1),
        "renewal_date": date(2025, 1, 15),
        "data_location": DataLocation.EU,
        "data_categories_processed": ["user_accounts", "project_files", "analysis_results", "logs"],
        "processing_purposes": (
            "Hosting de aplicación web, almacenamiento de base de datos, "
            "respaldos automáticos, logs de aplicación"
        ),
        "security_measures": (
            "Cifrado AES-256 en reposo y en tránsito, VPC con subnets privadas, "
            "WAF habilitado, CloudTrail para auditoría, MFA obligatorio"
        ),
        "provider_contact": "privacy@amazon.com",
        "provider_address": "Amazon Web Services EMEA SARL, 38 avenue John F. Kennedy, L-1855, Luxembourg",
        "contract_number": "AWS-EDU-2024-001",
        "data_location_details": "Región eu-west-1 (Irlanda), data centers certificados ISO 27001",
        "transfer_mechanism": "Adequacy Decision (EU Commission Decision 2023/2854)",
        "adequacy_decision": True,
        "data_subjects_categories": "Usuarios de la aplicación (estudiantes, docentes, administradores)",
        "encryption_standards": "AES-256-GCM, TLS 1.3",
        "access_controls": "IAM con MFA, least privilege, VPC endpoints",
        "subprocessors_allowed": True,
        "subprocessors_list": "Según lista actualizada en: https://aws.amazon.com/compliance/sub-processors/",
        "subprocessor_notification": True,
        "data_subject_requests": "Facilitar acceso, rectificación y eliminación mediante APIs y herramientas AWS",
        "data_breach_notification": "Notificación en 24 horas según AWS Incident Response",
        "audit_rights": "Acceso a reportes SOC, auditorías independientes disponibles",
        "auto_renewal": True,
        "termination_notice_days": 60,
        "compliance_notes": "Certificado ISO 27001, SOC 2 Type II, PCI DSS",
        "risk_assessment": "Riesgo BAJO - Proveedor tier 1 con certificaciones completas"
    }
    
    # DPA 2: DigitalOcean para base de datos
    dpa_digitalocean = {
        "provider_name": "DigitalOcean LLC",
        "cloud_provider": CloudProvider.DIGITALOCEAN,
        "dpa_title": "DigitalOcean Managed Database - PostgreSQL",
        "dpa_description": (
            "Acuerdo para base de datos PostgreSQL gestionada en DigitalOcean "
            "para almacenamiento de datos de la aplicación."
        ),
        "signed_date": date(2024, 3, 10),
        "effective_date": date(2024, 3, 15),
        "expiry_date": date(2025, 3, 15),
        "data_location": DataLocation.EU,
        "data_categories_processed": ["user_data", "project_metadata", "vulnerabilities", "metrics"],
        "processing_purposes": "Almacenamiento y gestión de base de datos principal de la aplicación",
        "security_measures": (
            "Cifrado en reposo con AES-256, backups cifrados, "
            "acceso restringido por IP, SSL/TLS obligatorio"
        ),
        "provider_contact": "security@digitalocean.com",
        "provider_address": "DigitalOcean LLC, 101 Avenue of the Americas, New York, NY 10013, USA",
        "contract_number": "DO-DB-2024-002",
        "data_location_details": "Datacenter AMS3 (Amsterdam), región Europa",
        "transfer_mechanism": "Standard Contractual Clauses (SCCs 2021)",
        "adequacy_decision": False,
        "encryption_standards": "AES-256, TLS 1.2+",
        "access_controls": "Database firewall, connection pooling, read replicas",
        "subprocessors_allowed": False,
        "subprocessor_notification": True,
        "data_breach_notification": "Notificación inmediata según términos de servicio",
        "audit_rights": "Reportes de seguridad disponibles trimestralmente",
        "auto_renewal": False,
        "termination_notice_days": 30,
        "compliance_notes": "SOC 2 Type II, GDPR compliant",
        "risk_assessment": "Riesgo MEDIO - Requiere SCCs por ser proveedor US"
    }
    
    # DPA 3: GitHub para repositorios
    dpa_github = {
        "provider_name": "GitHub Inc. (Microsoft)",
        "cloud_provider": CloudProvider.OTHER,
        "dpa_title": "GitHub Repository Hosting and CI/CD",
        "dpa_description": (
            "Acuerdo para almacenamiento de código fuente, control de versiones "
            "y pipeline CI/CD con GitHub Actions."
        ),
        "signed_date": date(2024, 1, 20),
        "effective_date": date(2024, 1, 25),
        "expiry_date": date(2025, 1, 25),
        "data_location": DataLocation.US,
        "data_categories_processed": ["source_code", "ci_cd_logs", "commit_history"],
        "processing_purposes": "Control de versiones, CI/CD, colaboración en desarrollo",
        "security_measures": (
            "2FA obligatorio, branch protection, secret scanning, "
            "dependency vulnerability alerts"
        ),
        "provider_contact": "privacy@github.com",
        "contract_number": "GH-EDU-2024-003",
        "data_location_details": "Múltiples regiones US (este y oeste), replicación global",
        "transfer_mechanism": "Standard Contractual Clauses (Microsoft)",
        "adequacy_decision": False,
        "encryption_standards": "TLS 1.2+, Git over HTTPS/SSH",
        "access_controls": "RBAC, branch protection rules, required reviews",
        "subprocessors_allowed": True,
        "subprocessors_list": "Microsoft Azure (infraestructura)",
        "auto_renewal": True,
        "termination_notice_days": 30,
        "compliance_notes": "SOC 2, ISO 27001, parte del Microsoft DPA",
        "risk_assessment": "Riesgo BAJO - Proveedor confiable con SCCs robustas"
    }
    
    # DPA 4: Vercel para frontend
    dpa_vercel = {
        "provider_name": "Vercel Inc.",
        "cloud_provider": CloudProvider.VERCEL,
        "dpa_title": "Vercel Edge Network - Frontend Deployment",
        "dpa_description": (
            "Acuerdo para despliegue y distribución del frontend de la aplicación "
            "a través de la red edge de Vercel."
        ),
        "signed_date": date(2024, 2, 5),
        "effective_date": date(2024, 2, 10),
        "expiry_date": date(2025, 2, 10),
        "data_location": DataLocation.GLOBAL,
        "data_categories_processed": ["frontend_assets", "analytics", "performance_metrics"],
        "processing_purposes": "Distribución de contenido estático, analytics de rendimiento",
        "security_measures": "HTTPS automático, DDoS protection, edge caching seguro",
        "provider_contact": "security@vercel.com",
        "contract_number": "VERCEL-2024-004",
        "data_location_details": "Red global de edge locations (primariamente US/EU)",
        "transfer_mechanism": "Privacy Shield successor framework",
        "adequacy_decision": False,
        "auto_renewal": True,
        "termination_notice_days": 15,
        "compliance_notes": "GDPR compliant, Privacy Shield certified",
        "risk_assessment": "Riesgo BAJO - Solo contenido estático, sin datos sensibles"
    }
    
    # DPA 5: Azure para respaldos
    dpa_azure = {
        "provider_name": "Microsoft Azure",
        "cloud_provider": CloudProvider.AZURE,
        "dpa_title": "Azure Backup Services - Disaster Recovery",
        "dpa_description": "Acuerdo para servicios de respaldo y recuperación ante desastres.",
        "signed_date": date(2024, 4, 1),
        "effective_date": date(2024, 4, 15),
        "expiry_date": date(2025, 4, 15),
        "data_location": DataLocation.US,
        "data_categories_processed": ["database_backups", "file_backups", "system_images"],
        "processing_purposes": "Respaldos automatizados, recuperación ante desastres",
        "security_measures": (
            "Cifrado AES-256, geo-replicación, access controls estrictos, "
            "retención configurable"
        ),
        "provider_contact": "privacy@microsoft.com",
        "contract_number": "AZURE-BACKUP-2024-005",
        "data_location_details": "US East 2 (Virginia) con replicación a US West 2",
        "transfer_mechanism": "Microsoft Standard Contractual Clauses",
        "adequacy_decision": False,
        "encryption_standards": "AES-256, customer-managed keys disponibles",
        "access_controls": "Azure AD, RBAC, conditional access policies",
        "subprocessors_allowed": True,
        "auto_renewal": False,
        "termination_notice_days": 45,
        "compliance_notes": "ISO 27001, SOC 1/2/3, FedRAMP High",
        "risk_assessment": "Riesgo MEDIO - Datos en US requieren SCCs apropiadas"
    }
    
    # Crear todos los DPA
    dpas_data = [dpa_aws, dpa_digitalocean, dpa_github, dpa_vercel, dpa_azure]
    
    created_count = 0
    for dpa_data in dpas_data:
        try:
            # Verificar si ya existe
            existing = db.consulta(DataProcessingAgreement).filter(
                DataProcessingAgreement.contract_number == dpa_data.get("contract_number"),
                DataProcessingAgreement.is_active == True
            ).first()
            
            if not existing:
                service.create_dpa(
                    usuario_id =1,  # Usuario admin
                    **dpa_data
                )
                created_count += 1
                print(f"✅ Creado DPA: {dpa_data['provider_name']}")
            else:
                print(f"⚠️ Ya existe DPA: {dpa_data['provider_name']}")
                
        except Exception as e:
            print(f"❌ Error creando DPA {dpa_data['provider_name']}: {str(e)}")
    
    print(f"\n🎉 Inicialización DPA completada: {created_count} acuerdos creados")
    return created_count


def main():
    """Función principal para ejecutar la inicialización de DPA"""
    print("🔄 Inicializando DPA de ejemplo para PRF5...")
    
    # Obtener sesión de BD
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        created = initialize_sample_dpas(db)
        print(f"\n✅ PRF5 implementado exitosamente: {created} DPA registrados")
        print("\n📋 Panel administrativo PRF5 disponible:")
        print("   • Gestión completa de Data Processing Agreements")
        print("   • Registro de ubicación de datos por proveedor")
        print("   • Control de fechas de vigencia y renovaciones")
        print("   • Dashboard con alertas de vencimiento")
        print("   • APIs para panel administrativo (/api/v1/dpa-admin/*)")
        print("   • Reportes de ubicaciones y transferencias GDPR")
        print("   • Auditoría completa de cambios en DPA")
        
        print(f"\n🌍 Ubicaciones de datos registradas:")
        print("   • EU (Adequacy Decision): AWS, DigitalOcean")
        print("   • US (SCCs requeridas): GitHub, Azure")
        print("   • Global (Edge Network): Vercel")
        
    except Exception as e:
        print(f"❌ Error en inicialización: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
