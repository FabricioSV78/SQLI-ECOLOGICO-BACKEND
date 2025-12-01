"""
API endpoints para solicitudes de privacidad de datos (PRF2)
Implementa los derechos GDPR: acceso, rectificación y eliminación
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.db_service import get_db
from app.services.privacy_service import PrivacyService
from app.services.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/privacy", tags=["privacy"])

# === ESQUEMAS PYDANTIC ===

class AccessRequestCreate(BaseModel):
    """Esquema para crear solicitud de acceso a datos personales"""
    description: str = "Solicito acceso a todos mis datos personales almacenados en el sistema"

class RectificationRequestCreate(BaseModel):
    """Esquema para crear solicitud de rectificación"""
    description: str = "Solicito rectificación de mis datos personales"
    rectification_data: Dict[str, Any]  # Campos a modificar
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Solicito cambiar mi email por uno correcto",
                "rectification_data": {
                    "email": "nuevo_email@ejemplo.com"
                }
            }
        }

class ErasureRequestCreate(BaseModel):
    """Esquema para crear solicitud de eliminación"""
    description: str = "Solicito la eliminación completa de todos mis datos personales"
    confirmation: bool  # El usuario debe confirmar que entiende que es irreversible
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Quiero que todos mis datos sean eliminados permanentemente",
                "confirmation": True
            }
        }

class PrivacyRequestResponse(BaseModel):
    """Respuesta de solicitud de privacidad"""
    id: int
    request_type: str
    status: str
    description: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_expired: bool
    user_notified: bool

class ProcessRequestUpdate(BaseModel):
    """Esquema para procesar solicitudes (solo admins)"""
    approve: bool
    reason: Optional[str] = None  # Requerido si approve=False

# === ENDPOINTS PARA USUARIOS (CREAR SOLICITUDES) ===

@router.post("/request/access", response_model=PrivacyRequestResponse)
def create_access_request(
    request_data: AccessRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear solicitud de acceso a datos personales (Art. 15 GDPR).
    
    El usuario puede solicitar:
    - Una copia de todos sus datos personales
    - Información sobre cómo se procesan sus datos
    - Con quién se comparten sus datos
    """
    privacy_service = PrivacyService(db)
    
    try:
        request = privacy_service.create_access_request(
            usuario_id=current_user.id,
            descripcion=request_data.description
        )
        return PrivacyRequestResponse(
            id=request.id,
            request_type=request.request_type.value,
            status=request.status.value,
            description=request.descripcion,
            created_at=request.fecha_creacion,
            processed_at=request.processed_at,
            completed_at=request.completed_at,
            is_expired=request.is_expired(),
            user_notified=request.user_notified
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear solicitud de acceso: {str(e)}"
        )

@router.post("/request/rectification", response_model=PrivacyRequestResponse)
def create_rectification_request(
    request_data: RectificationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear solicitud de rectificación de datos personales (Art. 16 GDPR).
    
    El usuario puede solicitar la corrección de:
    - Datos personales inexactos
    - Datos incompletos
    - Información desactualizada
    """
    privacy_service = PrivacyService(db)
    
    try:
        # Validar que los campos a rectificar sean permitidos
        allowed_fields = ["email"]  # Agregar más campos según sea necesario
        for field in request_data.rectification_data.keys():
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo '{field}' no puede ser modificado mediante este proceso"
                )
        
        request = privacy_service.create_rectification_request(
            usuario_id=current_user.id,
            rectification_data=request_data.rectification_data,
            descripcion=request_data.description
        )
        
        return PrivacyRequestResponse(
            id=request.id,
            request_type=request.request_type.value,
            status=request.status.value,
            description=request.descripcion,
            created_at=request.fecha_creacion,
            processed_at=request.processed_at,
            completed_at=request.completed_at,
            is_expired=request.is_expired(),
            user_notified=request.user_notified
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear solicitud de rectificación: {str(e)}"
        )

@router.post("/request/erasure", response_model=PrivacyRequestResponse)
def create_erasure_request(
    request_data: ErasureRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear solicitud de eliminación/olvido (Art. 17 GDPR).
    
    ⚠️ ATENCIÓN: Esta solicitud es irreversible.
    Se eliminarán TODOS los datos del usuario:
    - Datos personales
    - Proyectos y archivos subidos
    - Historial de análisis
    - Reportes generados
    """
    if not request_data.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe confirmar que entiende que la eliminación es irreversible"
        )
    
    privacy_service = PrivacyService(db)
    
    try:
        request = privacy_service.create_erasure_request(
            usuario_id=current_user.id,
            descripcion=request_data.description
        )
        
        return PrivacyRequestResponse(
            id=request.id,
            request_type=request.request_type.value,
            status=request.status.value,
            description=request.descripcion,
            created_at=request.fecha_creacion,
            processed_at=request.processed_at,
            completed_at=request.completed_at,
            is_expired=request.is_expired(),
            user_notified=request.user_notified
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear solicitud de eliminación: {str(e)}"
        )

# === ENDPOINTS PARA CONSULTAR SOLICITUDES ===

@router.get("/requests", response_model=List[PrivacyRequestResponse])
def get_my_privacy_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las solicitudes de privacidad del usuario actual.
    """
    privacy_service = PrivacyService(db)
    requests = privacy_service.get_user_requests(current_user.id)
    
    return [
        PrivacyRequestResponse(
            id=req.id,
            request_type=req.request_type.value,
            status=req.status.value,
            description=req.descripcion,
            created_at=req.fecha_creacion,
            processed_at=req.processed_at,
            completed_at=req.completed_at,
            is_expired=req.is_expired(),
            user_notified=req.user_notified
        )
        for req in requests
    ]

@router.get("/request/{request_id}", response_model=PrivacyRequestResponse)
def get_privacy_request_detail(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles de una solicitud específica (solo del usuario actual).
    """
    privacy_service = PrivacyService(db)
    request = privacy_service.get_request_by_id(request_id, current_user.id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    return PrivacyRequestResponse(
        id=request.id,
        request_type=request.request_type.value,
        status=request.status.value,
        description=request.descripcion,
        created_at=request.fecha_creacion,
        processed_at=request.processed_at,
        completed_at=request.completed_at,
        is_expired=request.is_expired(),
        user_notified=request.user_notified
    )

@router.get("/request/{request_id}/data")
def get_privacy_request_data(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener los datos del usuario (JSON) de una solicitud de acceso completada.
    Solo el usuario propietario de la solicitud puede acceder a sus datos.
    """
    privacy_service = PrivacyService(db)
    request = privacy_service.get_request_by_id(request_id, current_user.id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    # Verificar que sea una solicitud de acceso
    if request.request_type.value != "access":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo las solicitudes de acceso contienen datos del usuario"
        )
    
    # Verificar que la solicitud esté completada
    if request.status.value != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La solicitud aún no ha sido procesada"
        )
    
    # Devolver los datos en formato JSON
    if request.user_data_json:
        import json
        return {
            "request_id": request.id,
            "status": request.status.value,
            "processed_at": request.processed_at,
            "completed_at": request.completed_at,
            "user_data": json.loads(request.user_data_json)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos disponibles para esta solicitud"
        )

# === ENDPOINTS PARA ADMINISTRADORES ===

@router.get("/admin/requests/pending", response_model=List[PrivacyRequestResponse])
def get_pending_privacy_requests(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las solicitudes de privacidad pendientes (solo admins).
    """
    privacy_service = PrivacyService(db)
    requests = privacy_service.get_pending_requests()
    
    return [
        PrivacyRequestResponse(
            id=req.id,
            request_type=req.request_type.value,
            status=req.status.value,
            description=req.descripcion,
            created_at=req.fecha_creacion,
            processed_at=req.processed_at,
            completed_at=req.completed_at,
            is_expired=req.is_expired(),
            user_notified=req.user_notified
        )
        for req in requests
    ]

@router.post("/admin/request/{request_id}/process/access")
def process_access_request_admin(
    request_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Procesar solicitud de acceso y generar reporte con datos del usuario.
    """
    privacy_service = PrivacyService(db)
    
    try:
        user_data = privacy_service.process_access_request(request_id, current_user.id)
        return {
            "message": "Solicitud de acceso procesada exitosamente",
            "data": user_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar solicitud de acceso: {str(e)}"
        )

@router.post("/admin/request/{request_id}/process/rectification")
def process_rectification_request_admin(
    request_id: int,
    process_data: ProcessRequestUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Procesar solicitud de rectificación (aprobar o rechazar).
    """
    privacy_service = PrivacyService(db)
    
    try:
        success = privacy_service.process_rectification_request(
            request_id=request_id,
            processor_id=current_user.id,
            approve=process_data.approve,
            reason=process_data.reason
        )
        
        action = "aprobada" if success else "rechazada"
        return {"message": f"Solicitud de rectificación {action} exitosamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar solicitud de rectificación: {str(e)}"
        )

@router.post("/admin/request/{request_id}/process/erasure")
def process_erasure_request_admin(
    request_id: int,
    process_data: ProcessRequestUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Procesar solicitud de eliminación (aprobar o rechazar).
    ⚠️ CUIDADO: Si se aprueba, los datos se eliminan PERMANENTEMENTE.
    """
    privacy_service = PrivacyService(db)
    
    try:
        success = privacy_service.process_erasure_request(
            request_id=request_id,
            processor_id=current_user.id,
            approve=process_data.approve,
            reason=process_data.reason
        )
        
        if success:
            return {"message": "Datos del usuario eliminados permanentemente"}
        else:
            return {"message": "Solicitud de eliminación rechazada"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar solicitud de eliminación: {str(e)}"
        )

# === ENDPOINT DE INFORMACIÓN SOBRE DERECHOS ===

@router.get("/rights")
def get_privacy_rights_info():
    """
    Información sobre los derechos de privacidad disponibles.
    """
    return {
        "message": "Derechos de Privacidad según GDPR/LOPD",
        "rights": {
            "access": {
                "title": "Derecho de Acceso (Art. 15 GDPR)",
                "description": "Puedes solicitar una copia de todos tus datos personales almacenados",
                "endpoint": "/privacy/request/access"
            },
            "rectification": {
                "title": "Derecho de Rectificación (Art. 16 GDPR)",
                "description": "Puedes solicitar la corrección de datos inexactos o incompletos",
                "endpoint": "/privacy/request/rectification"
            },
            "erasure": {
                "title": "Derecho al Olvido (Art. 17 GDPR)",
                "description": "Puedes solicitar la eliminación completa de todos tus datos",
                "endpoint": "/privacy/request/erasure",
                "warning": "Esta acción es irreversible"
            }
        },
        "contact": "Para dudas sobre privacidad, contacta al DPO (Data Protection Officer)",
        "response_time": "Las solicitudes se procesan en máximo 30 días según GDPR"
    }
