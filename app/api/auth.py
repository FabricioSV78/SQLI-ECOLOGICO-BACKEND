from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.services import auth_service, db_service
from app.services.dependencies import get_current_user, get_optional_user
from app.services.audit_logger import log_user_action, AuditAction, AuditResult
from app.config.config import settings
from app.models.user_role import UserRole
from app.models.user import Usuario
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])


class RegistroUsuario(BaseModel):
    """
    Modelo para registro de usuario con soporte de roles.
    Actualizado para implementar el requerimiento SRF2.
    """
    correo: str
    contrasena: str
    rol: Optional[UserRole] = UserRole.ESTUDIANTE
    nombre_completo: Optional[str] = None

class UserRegister(BaseModel):
    """
    Modelo compatible con frontend para registro de usuario.
    """
    email: str
    password: str
    role: Optional[str] = "estudiante"
    full_name: Optional[str] = None
    username: Optional[str] = None  # Para compatibilidad, se ignora

class CambioRol(BaseModel):
    """
    Modelo para cambio de rol de usuario.
    """
    target_email: str
    new_role: UserRole

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

@router.post("/registrar")
def registrar(usuario: RegistroUsuario, db: Session = Depends(db_service.get_db), current_user: Usuario = Depends(get_optional_user)):
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
    # Si el usuario actual es docente y está creando un estudiante, pasar su ID como created_by
    created_by = None
    if current_user is not None and usuario.rol == UserRole.ESTUDIANTE and current_user.rol == UserRole.DOCENTE:
        created_by = current_user.id

    # Registrar usuario con rol especificado
    nuevo_usuario = auth_service.registrar_usuario(
        db,
        usuario.correo,
        usuario.contrasena,
        usuario.rol,
        usuario.nombre_completo,
        created_by=created_by
    )
    
    return RespuestaRegistro(
        estado="ok",
        usuario=nuevo_usuario.correo,
        rol=nuevo_usuario.rol.value,
        mensaje=f"Usuario registrado como {nuevo_usuario.rol.value}"
    )

# Endpoint de compatibilidad
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(db_service.get_db), current_user: Usuario = Depends(get_optional_user)):
    """
    Endpoint de registro compatible con frontend (campos en inglés).
    
    Args:
        user: Datos del usuario en formato inglés
        db: Sesión de base de datos
        
    Returns:
        dict: Información del usuario registrado
    """
    # Convertir rol de string a enum
    try:
        rol_enum = UserRole(user.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido: {user.role}. Roles válidos: administrador, docente, estudiante"
        )
    
    # Crear objeto en formato español
    usuario_es = RegistroUsuario(
        correo=user.email,
        contrasena=user.password,
        rol=rol_enum,
        nombre_completo=user.full_name
    )
    
    # Asignar created_by si el request proviene de un docente autenticado
    created_by = None
    if current_user is not None and rol_enum == UserRole.ESTUDIANTE and current_user.rol == UserRole.DOCENTE:
        created_by = current_user.id

    nuevo_usuario = auth_service.registrar_usuario(
        db,
        usuario_es.correo,
        usuario_es.contrasena,
        usuario_es.rol,
        usuario_es.nombre_completo,
        created_by=created_by
    )

    return RespuestaRegistro(
        estado="ok",
        usuario=nuevo_usuario.correo,
        rol=nuevo_usuario.rol.value,
        mensaje=f"Usuario registrado como {nuevo_usuario.rol.value}"
    )


@router.get("/students/by-creator")
def students_by_creator(current_user: Usuario = Depends(get_current_user), db: Session = Depends(db_service.get_db)):
    """
    Devuelve la lista de estudiantes creados por el docente autenticado.
    """
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMINISTRADOR]:
        # Solo docentes o administradores pueden consultar este endpoint
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo docentes o administradores pueden ver estudiantes creados.")

    # Si no es docente (por ejemplo administrador) permitimos ver todos los estudiantes si se desea,
    # pero el caso principal es filtrar por created_by
    estudiantes = db.query(Usuario).filter(Usuario.rol == UserRole.ESTUDIANTE, Usuario.created_by == current_user.id).all()

    return [
        {
            "id": e.id,
            "correo": e.correo,
            "nombre_completo": e.nombre_completo,
            "fecha_creacion": e.fecha_creacion.isoformat() if e.fecha_creacion else None
        }
        for e in estudiantes
    ]

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
    
    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.utcnow()
    db.commit()
    
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
    cambio_rol: CambioRol,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Cambiar el rol de un usuario (solo administradores).
    
    Args:
        cambio_rol: Datos del cambio de rol
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
    target_user = db.query(User).filter(User.correo == cambio_rol.target_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    old_role = target_user.rol
    target_user.rol = cambio_rol.new_role
    db.commit()
    
    return {
        "status": "ok",
        "message": f"Rol de {cambio_rol.target_email} cambiado de {old_role.value} a {cambio_rol.new_role.value}",
        "user": cambio_rol.target_email,
        "old_role": old_role.value,
        "new_role": cambio_rol.new_role.value
    }


# ===== ENDPOINTS DE GESTIÓN DE USUARIOS =====

@router.get("/users")
def get_all_users(
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Obtener lista de todos los usuarios (SOLO para administradores).
    Los docentes ya no pueden ver la lista completa de usuarios.
    
    Args:
        current_user: Usuario autenticado (debe ser administrador)
        db: Sesión de base de datos
        
    Returns:
        list: Lista de usuarios con información básica
    """
    # SOLO administradores pueden ver la lista completa
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=403, 
            detail="Solo los administradores pueden ver la lista completa de usuarios"
        )
    
    from app.models.user import User
    users = db.query(User).all()
    
    return [
        {
            "id": user.id,
            "email": user.correo,
            "username": user.correo.split('@')[0],  # Extraer username del email
            "full_name": user.nombre_completo,
            "role": user.rol.value,
            "is_active": user.activo,
            "last_login": user.ultimo_acceso,
            "created_at": user.fecha_creacion
        }
        for user in users
    ]

@router.get("/users/role/{role}")
def get_users_by_role(
    role: UserRole,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Obtener usuarios por rol específico (SOLO para administradores).
    Los docentes ya no pueden ver listas de usuarios.
    
    Args:
        role: Rol de usuario a filtrar
        current_user: Usuario autenticado (debe ser administrador)
        db: Sesión de base de datos
        
    Returns:
        list: Lista de usuarios del rol especificado
    """
    # SOLO administradores pueden ver listas de usuarios
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=403, 
            detail="Solo los administradores pueden ver listas de usuarios"
        )
    
    from app.models.user import User
    users = db.query(User).filter(User.rol == role).all()
    
    return [
        {
            "id": user.id,
            "email": user.correo,
            "username": user.correo.split('@')[0],
            "full_name": user.nombre_completo,
            "role": user.rol.value,
            "is_active": user.activo,
            "created_at": user.fecha_creacion
        }
        for user in users
    ]

@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Activar un usuario.
    
    Args:
        user_id: ID del usuario a activar
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Confirmación de activación
    """
    # Verificar permisos según jerarquía
    from app.models.user import User
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.rol == UserRole.DOCENTE:
        # Los docentes solo pueden activar estudiantes
        if target_user.rol != UserRole.ESTUDIANTE:
            raise HTTPException(
                status_code=403, 
                detail="Los docentes solo pueden activar estudiantes"
            )
    elif current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="Sin permisos suficientes")
    
    # Activar usuario
    target_user.activo = True
    db.commit()
    
    return {
        "status": "ok", 
        "message": f"Usuario {target_user.correo} activado exitosamente",
        "user_id": user_id,
        "user_email": target_user.correo
    }

@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Desactivar un usuario.
    
    Args:
        user_id: ID del usuario a desactivar
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Confirmación de desactivación
    """
    # Verificar permisos según jerarquía
    from app.models.user import User
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir desactivar al propio usuario
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="No puedes desactivarte a ti mismo"
        )
    
    if current_user.rol == UserRole.DOCENTE:
        # Los docentes solo pueden desactivar estudiantes
        if target_user.rol != UserRole.ESTUDIANTE:
            raise HTTPException(
                status_code=403, 
                detail="Los docentes solo pueden desactivar estudiantes"
            )
    elif current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="Sin permisos suficientes")
    
    # Desactivar usuario
    target_user.activo = False
    db.commit()
    
    return {
        "status": "ok", 
        "message": f"Usuario {target_user.correo} desactivado exitosamente",
        "user_id": user_id,
        "user_email": target_user.correo
    }

@router.get("/users/{user_id}")
def get_user_by_id(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Obtener información detallada de un usuario específico.
    
    Args:
        user_id: ID del usuario
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Información detallada del usuario
    """
    if not current_user.es_privilegiado():
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": user.id,
        "email": user.correo,
        "username": user.correo.split('@')[0],
        "full_name": user.nombre_completo,
        "role": user.rol.value,
        "is_active": user.activo,
        "last_login": user.ultimo_acceso,
        "created_at": user.fecha_creacion,
        "permissions": {
            "can_view_all_reports": user.puede_acceder_todos_reportes(),
            "is_privileged": user.es_privilegiado()
        }
    }

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(db_service.get_db)
):
    """
    Actualizar información de un usuario.
    
    Args:
        user_id: ID del usuario
        full_name: Nuevo nombre completo (opcional)
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        dict: Confirmación de actualización
    """
    from app.models.user import User
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Los usuarios pueden editar su propia información
    # Los admins pueden editar cualquier usuario
    # Los docentes pueden editar estudiantes
    can_edit = (
        target_user.id == current_user.id or  # Editar a sí mismo
        current_user.rol == UserRole.ADMINISTRADOR or  # Admin puede editar a todos
        (current_user.rol == UserRole.DOCENTE and target_user.rol == UserRole.ESTUDIANTE)  # Docente puede editar estudiantes
    )
    
    if not can_edit:
        raise HTTPException(status_code=403, detail="Sin permisos para editar este usuario")
    
    # Actualizar campos proporcionados
    if full_name is not None:
        target_user.nombre_completo = full_name
    
    db.commit()
    
    return {
        "status": "ok",
        "message": f"Usuario {target_user.correo} actualizado exitosamente",
        "user_id": user_id,
        "user_email": target_user.correo
    }

