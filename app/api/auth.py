from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.services import auth_service, db_service
from app.services.dependencies import get_current_user
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.config.config import settings
from app.models.user_role import UserRole
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])


class RegistroUsuario(BaseModel):
    """
    Modelo para registro de usuario con soporte de roles.
    Actualizado para implementar el requerimiento SRF2.
    """
    correo: str
    contrasena: str
    rol: Optional[UserRole] = UserRole.ESTUDIANTE

class RespuestaAutenticacion(BaseModel):
    token_acceso: str
    tipo_token: str = "bearer"
    info_usuario: dict

class RespuestaRegistro(BaseModel):
    estado: str
    usuario: str
    rol: str
    mensaje: str

class RespuestaError(BaseModel):
    error: str
    mensaje: str

# Alias para compatibilidad
UserRegister = RegistroUsuario

@router.post("/registrar")
def registrar(usuario: RegistroUsuario, db: Session = Depends(db_service.get_db)):
    """
    Registrar nuevo usuario con rol especificado.
    
    Por defecto se asigna rol STUDENT (estudiante).
    Solo administradores pueden crear usuarios con otros roles.
    
    Args:
        usuario: Datos del usuario a registrar
        db: Sesión de base de datos
        
    Returns:
        dict: Información del usuario registrado
    """
    # Registrar usuario con rol especificado
    nuevo_usuario = auth_service.registrar_usuario(
        db, 
        usuario.correo, 
        usuario.contrasena, 
        usuario.rol
    )
    
    return RespuestaRegistro(
        estado="ok",
        usuario=nuevo_usuario.correo,
        rol=nuevo_usuario.rol.value,
        mensaje=f"Usuario registrado como {nuevo_usuario.rol.value}"
    )

# Endpoint de compatibilidad
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(db_service.get_db)):
    return registrar(user, db)

@router.post("/iniciar-sesion")
def iniciar_sesion(datos_formulario: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_service.get_db)):
    """
    Autenticar usuario y devolver JWT con información de rol.
    
    El token incluye información del rol para implementar 
    el control de acceso del requerimiento SRF2.
    
    Args:
        datos_formulario: Credenciales del usuario
        db: Sesión de base de datos
        
    Returns:
        dict: Token de acceso con información de rol
    """
    usuario = auth_service.autenticar_usuario(db, datos_formulario.username, datos_formulario.password)
    
    if not usuario:
        if settings.AUDIT_ENABLED:
            log_user_action(
                user_id=0,
                username=datos_formulario.username,
                action=AuditAction.LOGIN,
                result=AuditResult.FAILURE,
                details={
                    "reason": "Credenciales incorrectas",
                    "username_attempted": datos_formulario.username
                },
                audit_dir=settings.AUDIT_DIR
            )
        return RespuestaError(error="credenciales_incorrectas", mensaje="Credenciales incorrectas")
    
    # Crear token con información de rol para SRF2
    token = auth_service.crear_token_usuario(usuario)
    
    # 📝 SRF5: Log de login exitoso
    if settings.AUDIT_ENABLED:
        log_user_action(
            user_id=usuario.id,
            username=usuario.correo,
            action=AuditAction.LOGIN,
            result=AuditResult.SUCCESS,
            details={
                "role": usuario.rol.value,
                "permissions": {
                    "puede_ver_todos_reportes": usuario.puede_acceder_todos_reportes(),
                    "es_privilegiado": usuario.es_privilegiado()
                }
            },
            audit_dir=settings.AUDIT_DIR
        )
    
    return RespuestaAutenticacion(
        token_acceso=token,
        tipo_token="bearer",
        info_usuario={
            "correo": usuario.correo,
            "rol": usuario.rol.value,
            "permisos": {
                "puede_ver_todos_reportes": usuario.puede_acceder_todos_reportes(),
                "es_privilegiado": usuario.es_privilegiado()
            }
        }
    )

# 🔄 Endpoint de compatibilidad en inglés
@router.post("/login", summary="Iniciar Sesión (English Compatibility)", 
            description="Endpoint de compatibilidad para clientes que usan '/login'. Redirige a iniciar_sesion().")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_service.get_db)):
    """Endpoint de compatibilidad en inglés que redirige al principal en español."""
    return iniciar_sesion(form_data, db)

@router.get("/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Obtiene información del usuario actual incluyendo permisos según su rol.
    
    Args:
        current_user: Usuario autenticado obtenido del token JWT
        
    Returns:
        dict: Información completa del usuario y sus permisos
    """
    return {
        "id": current_user.id,
        "email": current_user.correo,
        "role": current_user.rol.value,
        "created_at": current_user.fecha_creacion,
        "permissions": {
            "can_view_all_reports": current_user.puede_acceder_todos_reportes(),
            "is_privileged": current_user.es_privilegiado(),
            "role_description": {
                UserRole.ESTUDIANTE: "Estudiante - Acceso limitado a proyectos propios",
                UserRole.DOCENTE: "Docente - Acceso a reportes de todos los estudiantes", 
                UserRole.ADMINISTRADOR: "Administrador - Acceso completo al sistema"
            }[current_user.rol]
        }
    }

@router.post("/change-role")
def change_user_role(
    target_email: str,
    new_role: UserRole,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Cambiar el rol de un usuario (solo administradores).
    
    Args:
        target_email: Email del usuario objetivo
        new_role: Nuevo rol a asignar
        current_user: Usuario autenticado (debe ser admin)
        db: Sesión de base de datos
        
    Returns:
        dict: Confirmación del cambio de rol
    """
    # Solo administradores pueden cambiar roles
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=403, 
            detail="Solo administradores pueden cambiar roles de usuario"
        )
    
    # Buscar usuario objetivo
    from app.models.user import User
    target_user = db.query(User).filter(User.correo == target_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    old_role = target_user.rol
    target_user.rol = new_role
    db.commit()
    
    return {
        "status": "ok",
        "message": f"Rol de {target_email} cambiado de {old_role.value} a {new_role.value}",
        "user": target_email,
        "old_role": old_role.value,
        "new_role": new_role.value
    }

