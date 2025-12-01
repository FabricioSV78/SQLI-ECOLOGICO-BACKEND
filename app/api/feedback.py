from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

from app.services.db_service import get_db
from app.services.dependencies import get_current_user
from app.services.feedback_service import FeedbackService
from app.models.user import Usuario
from app.models.user_role import UserRole

router = APIRouter()

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class FeedbackCreate(BaseModel):
    """Modelo para crear un nuevo feedback"""
    tipo_feedback: str = Field(..., description="Tipo de feedback: analysis_speed, accuracy, usability, general")
    calificacion: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5 estrellas")
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto relacionado")
    comentario: Optional[str] = Field(None, max_length=1000, description="Comentario opcional")
    extra_data: Optional[Dict] = Field(None, description="Datos adicionales")
    
    @validator('tipo_feedback')
    def validar_tipo(cls, v):
        tipos_validos = ['analysis_speed', 'accuracy', 'usability', 'general']
        if v not in tipos_validos:
            raise ValueError(f'tipo_feedback debe ser uno de: {", ".join(tipos_validos)}')
        return v

class FeedbackResponse(BaseModel):
    """Modelo de respuesta de feedback"""
    id: int
    usuario_id: int
    proyecto_id: Optional[int]
    tipo_feedback: str
    calificacion: int
    comentario: Optional[str]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class EstadisticasFeedback(BaseModel):
    """Modelo para estadísticas de feedback"""
    total_respuestas: int
    calificacion_promedio: float
    distribucion: Dict[str, int]
    comentarios_count: int

class PromediosPorTipo(BaseModel):
    """Modelo para promedios por tipo de feedback"""
    analysis_speed: float
    accuracy: float
    usability: float
    general: float

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo feedback",
    description="Permite a los usuarios enviar retroalimentación sobre el análisis realizado"
)
async def crear_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear un nuevo registro de feedback.
    
    **Parámetros:**
    - **tipo_feedback**: Tipo de retroalimentación (analysis_speed, accuracy, usability, general)
    - **calificacion**: Calificación de 1 a 5 estrellas
    - **proyecto_id**: (Opcional) ID del proyecto relacionado
    - **comentario**: (Opcional) Comentario adicional del usuario
    - **extra_data**: (Opcional) Información adicional en formato JSON
    
    **Roles permitidos:** Todos los usuarios autenticados
    """
    try:
        feedback = FeedbackService.crear_feedback(
            db=db,
            usuario_id=current_user.id,
            tipo_feedback=feedback_data.tipo_feedback,
            calificacion=feedback_data.calificacion,
            proyecto_id=feedback_data.proyecto_id,
            comentario=feedback_data.comentario,
            extra_data=feedback_data.extra_data
        )
        
        return feedback
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear feedback: {str(e)}"
        )

@router.get(
    "/feedback/mis-feedbacks",
    response_model=List[FeedbackResponse],
    summary="Obtener mis feedbacks",
    description="Obtiene los feedbacks enviados por el usuario actual"
)
async def obtener_mis_feedbacks(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener el historial de feedback del usuario actual.
    
    **Roles permitidos:** Todos los usuarios autenticados
    """
    feedbacks = FeedbackService.obtener_feedback_por_usuario(
        db=db,
        usuario_id=current_user.id,
        limit=limit
    )
    
    return feedbacks

@router.get(
    "/feedback/estadisticas",
    response_model=EstadisticasFeedback,
    summary="Obtener estadísticas de feedback",
    description="Obtiene estadísticas agregadas de todos los feedbacks (solo para docentes y admins)"
)
async def obtener_estadisticas(
    tipo_feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas agregadas de feedback.
    
    **Parámetros:**
    - **tipo_feedback**: (Opcional) Filtrar por tipo específico
    
    **Roles permitidos:** DOCENTE, ADMIN
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estadísticas de feedback"
        )
    
    estadisticas = FeedbackService.obtener_estadisticas_feedback(
        db=db,
        tipo_feedback=tipo_feedback
    )
    
    return estadisticas

@router.get(
    "/feedback/promedios-por-tipo",
    response_model=PromediosPorTipo,
    summary="Obtener promedios por tipo de feedback",
    description="Obtiene el promedio de calificación para cada tipo de feedback (solo para docentes y admins)"
)
async def obtener_promedios_por_tipo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener el promedio de calificación por cada tipo de feedback.
    
    **Roles permitidos:** DOCENTE, ADMIN
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estadísticas de feedback"
        )
    
    promedios = FeedbackService.obtener_promedio_por_tipo(db=db)
    
    return promedios

@router.get(
    "/feedback/recientes",
    response_model=List[FeedbackResponse],
    summary="Obtener feedbacks recientes",
    description="Obtiene los feedbacks más recientes del sistema (solo para docentes y admins)"
)
async def obtener_feedbacks_recientes(
    limit: int = 20,
    tipo_feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los feedbacks más recientes.
    
    **Parámetros:**
    - **limit**: Número máximo de resultados (default: 20)
    - **tipo_feedback**: (Opcional) Filtrar por tipo específico
    
    **Roles permitidos:** DOCENTE, ADMIN
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver feedbacks de otros usuarios"
        )
    
    feedbacks = FeedbackService.obtener_feedback_reciente(
        db=db,
        limit=limit,
        tipo_feedback=tipo_feedback
    )
    
    return feedbacks

@router.get(
    "/feedback/proyecto/{proyecto_id}",
    response_model=List[FeedbackResponse],
    summary="Obtener feedback de un proyecto",
    description="Obtiene todos los feedbacks relacionados con un proyecto específico"
)
async def obtener_feedback_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener feedback de un proyecto específico.
    
    **Roles permitidos:** DOCENTE, ADMIN o el propietario del proyecto
    """
    feedbacks = FeedbackService.obtener_feedback_por_proyecto(
        db=db,
        proyecto_id=proyecto_id
    )
    
    # Si es estudiante, solo puede ver sus propios feedbacks
    if current_user.rol == UserRole.ESTUDIANTE:
        feedbacks = [f for f in feedbacks if f.usuario_id == current_user.id]
    
    return feedbacks
