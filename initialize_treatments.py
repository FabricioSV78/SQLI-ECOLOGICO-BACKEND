"""
PRF4: Script para inicializar los registros de tratamiento básicos del sistema.

Este script crea los registros obligatorios para cumplir con PRF4 y GDPR,
documentando todos los tratamientos de datos que realiza la aplicación.
"""

from sqlalchemy.orm import Session
from app.services.data_treatment_service import get_data_treatment_service
from app.models.data_treatment_registry import LegalBasis, RetentionPeriod, DataTreatmentRegistry
from app.services.db_service import get_db


def initialize_basic_treatments(db: Session) -> None:
    """
    Inicializa los tratamientos básicos del sistema de análisis SQLi.
    
    Crea registros para:
    1. Gestión de usuarios y autenticación
    2. Procesamiento de proyectos subidos
    3. Análisis de vulnerabilidades y reportes
    4. Logs de auditoría
    5. Solicitudes de privacidad (PRF2)
    """
    
    service = get_data_treatment_service(db)
    
    # Tratamiento 1: Gestión de Usuarios y Autenticación
    treatment_1 = {
        "treatment_name": "Gestión de Usuarios y Autenticación",
        "treatment_description": (
            "Procesamiento de datos personales para crear y gestionar cuentas de usuario, "
            "autenticación, autorización y control de acceso al sistema de análisis SQLi."
        ),
        "data_categories": ["identification", "contact", "authentication"],
        "data_fields": (
            "Email (identificador único), contraseña hash, fecha de registro, "
            "rol del usuario, tokens de sesión, timestamps de último acceso"
        ),
        "processing_purpose": (
            "Permitir el acceso seguro al sistema, identificar usuarios únicamente, "
            "controlar permisos y roles, mantener sesiones activas"
        ),
        "processing_activities": (
            "Registro de usuarios, autenticación mediante email/contraseña, "
            "generación de tokens JWT, validación de sesiones, control de roles"
        ),
        "legal_basis": LegalBasis.CONTRACT,
        "retention_period": RetentionPeriod.THREE_YEARS,
        "legal_basis_details": (
            "Ejecución del contrato de prestación de servicios de análisis de seguridad. "
            "El usuario acepta el procesamiento al registrarse en el sistema."
        ),
        "retention_criteria": (
            "Los datos se conservan mientras la cuenta esté activa más 3 años adicionales "
            "para cumplir obligaciones legales y de seguridad."
        ),
        "deletion_procedure": (
            "Eliminación automática tras período de retención o solicitud expresa del usuario "
            "a través de funcionalidades PRF2. Hash de contraseñas se elimina inmediatamente."
        ),
        "security_measures": (
            "Contraseñas hasheadas con bcrypt, tokens JWT con expiración, "
            "HTTPS obligatorio, validación de sesiones, logs de acceso"
        ),
        "access_controls": (
            "Acceso restringido a administradores del sistema para gestión de usuarios. "
            "Usuarios solo acceden a sus propios datos."
        ),
        "subject_rights_info": (
            "Derecho de acceso, rectificación y eliminación disponible mediante "
            "endpoints PRF2. Portabilidad disponible bajo solicitud."
        ),
        "responsible_person": "Administrador del Sistema"
    }
    
    # Tratamiento 2: Procesamiento de Proyectos y Archivos
    treatment_2 = {
        "treatment_name": "Procesamiento de Proyectos y Archivos de Código",
        "treatment_description": (
            "Almacenamiento y procesamiento de proyectos de código fuente subidos por usuarios "
            "para análisis de vulnerabilidades SQLi, incluyendo metadatos del proyecto."
        ),
        "data_categories": ["content", "technical", "usage"],
        "data_fields": (
            "Archivos de código fuente, nombre del proyecto, descripción, "
            "timestamps de subida, rutas de archivos, contenido de archivos"
        ),
        "processing_purpose": (
            "Analizar código fuente para detectar vulnerabilidades de inyección SQL, "
            "generar reportes de seguridad, almacenar histórico de análisis"
        ),
        "processing_activities": (
            "Recepción de archivos ZIP, descompresión, almacenamiento en filesystem, "
            "indexación en base de datos, análisis con ML/reglas estáticas"
        ),
        "legal_basis": LegalBasis.CONTRACT,
        "retention_period": RetentionPeriod.ONE_YEAR,
        "legal_basis_details": (
            "Prestación del servicio de análisis de seguridad solicitado por el usuario. "
            "Necesario para cumplir con el contrato de servicio."
        ),
        "retention_criteria": (
            "Proyectos se conservan 1 año desde última actividad para permitir "
            "consulta de reportes históricos y comparativas de mejora."
        ),
        "deletion_procedure": (
            "Eliminación automática de archivos del filesystem y registros de BD "
            "tras período de retención. Eliminación inmediata bajo solicitud PRF2."
        ),
        "security_measures": (
            "Escaneo SRF3 pre-almacenamiento, validación de tipos de archivo, "
            "almacenamiento en directorio restringido, acceso controlado por usuario"
        ),
        "access_controls": (
            "Solo el propietario del proyecto y administradores pueden acceder. "
            "Aislamiento por usuario ID en consultas de BD."
        ),
        "subject_rights_info": (
            "Acceso completo a proyectos propios, eliminación disponible, "
            "rectificación de metadatos mediante API"
        ),
        "responsible_person": "Responsable de Datos del Sistema"
    }
    
    # Tratamiento 3: Análisis de Vulnerabilidades y Reportes
    treatment_3 = {
        "treatment_name": "Generación de Reportes de Vulnerabilidades",
        "treatment_description": (
            "Procesamiento y almacenamiento de resultados de análisis de vulnerabilidades SQLi, "
            "incluyendo métricas, detecciones y reportes de seguridad."
        ),
        "data_categories": ["content", "technical", "usage"],
        "data_fields": (
            "Fragmentos de código vulnerable, predicciones ML, métricas de análisis, "
            "timestamps de análisis, archivos afectados, niveles de confianza"
        ),
        "processing_purpose": (
            "Generar reportes detallados de vulnerabilidades detectadas, "
            "proporcionar métricas de calidad, mantener histórico de mejoras"
        ),
        "processing_activities": (
            "Ejecución de modelos ML, aplicación de reglas estáticas, "
            "generación de reportes, cálculo de métricas, almacenamiento de resultados"
        ),
        "legal_basis": LegalBasis.CONTRACT,
        "retention_period": RetentionPeriod.THREE_YEARS,
        "legal_basis_details": (
            "Prestación del servicio principal de análisis de seguridad. "
            "Esencial para cumplir el contrato de detección de vulnerabilidades."
        ),
        "retention_criteria": (
            "Reportes conservados 3 años para análisis de tendencias, "
            "mejora de modelos ML y evidencia de mejoras de seguridad implementadas."
        ),
        "deletion_procedure": (
            "Eliminación automática tras período de retención. "
            "Anonimización de métricas para investigación antes de eliminación completa."
        ),
        "security_measures": (
            "Acceso restringido por usuario, reportes vinculados a proyectos específicos, "
            "no exposición de código sensible en logs"
        ),
        "access_controls": (
            "Solo propietario del proyecto puede acceder a sus reportes. "
            "Administradores acceden solo para soporte técnico."
        ),
        "subject_rights_info": (
            "Acceso completo a reportes propios, eliminación disponible junto con proyecto, "
            "exportación de reportes en formato JSON"
        ),
        "responsible_person": "Equipo de Desarrollo"
    }
    
    # Tratamiento 4: Logs de Auditoría y Seguridad  
    treatment_4 = {
        "treatment_name": "Logs de Auditoría y Monitoreo de Seguridad",
        "treatment_description": (
            "Registro de actividades del sistema, acciones de usuario, eventos de seguridad "
            "y logs de auditoría para cumplimiento normativo y detección de incidentes."
        ),
        "data_categories": ["technical", "usage", "authentication"],
        "data_fields": (
            "ID de usuario, timestamps, acciones realizadas, IPs de acceso, "
            "user agents, resultados de operaciones, eventos de seguridad"
        ),
        "processing_purpose": (
            "Monitoreo de seguridad, detección de incidentes, auditoría de cumplimiento, "
            "trazabilidad de operaciones, investigación de eventos anómalos"
        ),
        "processing_activities": (
            "Registro automático de eventos, almacenamiento de logs, "
            "análisis de patrones de acceso, generación de reportes de auditoría"
        ),
        "legal_basis": LegalBasis.LEGITIMATE_INTERESTS,
        "retention_period": RetentionPeriod.ONE_YEAR,
        "legal_basis_details": (
            "Interés legítimo en mantener la seguridad del sistema, "
            "cumplir obligaciones de auditoría y proteger datos de todos los usuarios."
        ),
        "retention_criteria": (
            "Logs conservados 1 año para investigaciones de seguridad y auditorías. "
            "Eventos críticos pueden conservarse hasta 3 años."
        ),
        "deletion_procedure": (
            "Rotación automática de logs tras período de retención. "
            "Anonimización antes de eliminación para estadísticas de seguridad."
        ),
        "security_measures": (
            "Logs almacenados en archivos protegidos, acceso restringido a administradores, "
            "integridad protegida mediante checksums"
        ),
        "access_controls": (
            "Solo administradores de sistema pueden acceder a logs completos. "
            "Usuarios pueden consultar su propio histórico de actividad."
        ),
        "subject_rights_info": (
            "Acceso a logs propios disponible bajo solicitud. "
            "Eliminación limitada por requisitos de seguridad y auditoría."
        ),
        "responsible_person": "Administrador de Seguridad"
    }
    
    # Tratamiento 5: Gestión de Solicitudes de Privacidad (PRF2)
    treatment_5 = {
        "treatment_name": "Gestión de Solicitudes de Derechos de Privacidad",
        "treatment_description": (
            "Procesamiento de solicitudes de acceso, rectificación y eliminación de datos "
            "personales según derechos GDPR, incluyendo seguimiento y resolución."
        ),
        "data_categories": ["identification", "contact", "usage"],
        "data_fields": (
            "Email del solicitante, tipo de solicitud, fecha de solicitud, "
            "estado de procesamiento, detalles de la solicitud, respuestas generadas"
        ),
        "processing_purpose": (
            "Cumplir con obligaciones GDPR de respuesta a derechos de los interesados, "
            "mantener registro de solicitudes para auditorías de cumplimiento"
        ),
        "processing_activities": (
            "Recepción de solicitudes PRF2, validación de identidad, "
            "procesamiento de solicitudes, generación de respuestas, seguimiento de estado"
        ),
        "legal_basis": LegalBasis.LEGAL_OBLIGATION,
        "retention_period": RetentionPeriod.THREE_YEARS,
        "legal_basis_details": (
            "Obligación legal de cumplir con derechos GDPR de los interesados "
            "según Artículos 15, 16 y 17 del RGPD."
        ),
        "retention_criteria": (
            "Solicitudes conservadas 3 años como evidencia de cumplimiento normativo "
            "y para auditorías de autoridades de protección de datos."
        ),
        "deletion_procedure": (
            "Eliminación automática tras período legal de retención. "
            "Las solicitudes de eliminación se procesan inmediatamente pero se registran."
        ),
        "security_measures": (
            "Validación de identidad antes de procesar solicitudes, "
            "acceso restringido a administradores, logs de todas las operaciones"
        ),
        "access_controls": (
            "Solo administradores de privacidad pueden gestionar solicitudes. "
            "Solicitantes pueden consultar estado de sus propias solicitudes."
        ),
        "subject_rights_info": (
            "Derechos GDPR completos disponibles: acceso, rectificación, eliminación, "
            "portabilidad y oposición según aplicabilidad legal."
        ),
        "responsible_person": "Responsable de Protección de Datos"
    }
    
    # Crear todos los tratamientos
    treatments_data = [treatment_1, treatment_2, treatment_3, treatment_4, treatment_5]
    
    created_count = 0
    for treatment_data in treatments_data:
        try:
            # Verificar si ya existe
            existing = db.consulta(DataTreatmentRegistry).filter(
                DataTreatmentRegistry.treatment_name == treatment_data["treatment_name"],
                DataTreatmentRegistry.is_active == True
            ).first()
            
            if not existing:
                service.create_treatment_registry(
                    usuario_id =1,  # Sistema/Admin
                    **treatment_data
                )
                created_count += 1
                print(f"✅ Creado: {treatment_data['treatment_name']}")
            else:
                print(f"⚠️ Ya existe: {treatment_data['treatment_name']}")
                
        except Exception as e:
            print(f"❌ Error creando {treatment_data['treatment_name']}: {str(e)}")
    
    print(f"\n🎉 Inicialización completada: {created_count} tratamientos creados")
    return created_count


def main():
    """Función principal para ejecutar la inicialización"""
    print("🔄 Inicializando registros de tratamiento PRF4...")
    
    # Obtener sesión de BD
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        created = initialize_basic_treatments(db)
        print(f"\n✅ PRF4 implementado exitosamente: {created} tratamientos registrados")
        print("\n📋 Funcionalidades PRF4 disponibles:")
        print("   • Registro completo de tratamientos según GDPR Art. 30")
        print("   • Bases legales documentadas para cada procesamiento")
        print("   • Períodos de retención definidos y automatizados")
        print("   • APIs para gestión de tratamientos (/data-treatment/*)")
        print("   • Reportes de cumplimiento GDPR")
        print("   • Integración con solicitudes PRF2")
        
    except Exception as e:
        print(f"❌ Error en inicialización: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
