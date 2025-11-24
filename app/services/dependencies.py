from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.models.user import Usuario, User
from app.models.user_role import UserRole
from app.services.db_service import get_db
from app.config.config import settings  # Ahora importamos desde config.py

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/iniciar-sesion", auto_error=False)


def get_optional_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[Usuario]:
    """
    Devuelve el usuario autenticado si el token es válido, o None si no hay token.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(Usuario).filter(Usuario.correo == email).first()
        return user
    except Exception:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Obtiene el usuario actual desde el token JWT.
    Actualizado para soportar roles y requerimiento SRF2.
    
    Args:
        token (str): Token JWT del usuario
        db (Session): Sesión de base de datos
        
    Returns:
        User: Usuario autenticado con información de rol
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    import logging
    logger = logging.getLogger(__name__)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Si no viene token (auto_error=False devuelve None), rechazamos
    if not token or token in ("null", "undefined", ""):
        logger.error("❌ No se proporcionó token")
        raise credentials_exception

    try:
        logger.info(f"🔍 Validando token: {str(token)[:50]}...")

        # Decodificar token JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.info(f"📋 Payload decodificado: {payload}")
        
        email: str = payload.get("sub")
        user_id: int = payload.get("usuario_id")  # Corregido: usar "usuario_id"
        role_str: str = payload.get("rol")  # Corregido: usar "rol"
        
        logger.info(f"📧 Email extraído: {email}")
        logger.info(f"🆔 User ID extraído: {user_id}")
        logger.info(f"👤 Rol extraído: {role_str}")
        
        if email is None:
            logger.error("❌ No se encontró email en el token")
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"❌ Error JWT: {e}")
        raise credentials_exception
    
    # Buscar usuario en base de datos
    logger.info(f"🔍 Buscando usuario con email: {email}")
    user = db.query(Usuario).filter(Usuario.correo == email).first()
    if user is None:
        logger.error(f"❌ Usuario no encontrado en BD: {email}")
        raise credentials_exception
    
    logger.info(f"✅ Usuario encontrado: {user.correo}, rol: {user.rol.value}")
    
    # Verificar consistencia del rol entre token y base de datos
    if role_str and user.rol.value != role_str:
        logger.error(f"❌ Rol inconsistente - Token: {role_str}, BD: {user.rol.value}")
        # El rol en el token no coincide con la base de datos
        # Esto podría indicar que el rol cambió después de generar el token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Información de rol desactualizada. Vuelve a iniciar sesión."
        )
    
    logger.info(f"✅ Validación completa exitosa para: {user.correo}")
    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependencia que requiere que el usuario tenga uno de los roles especificados.
    Función de conveniencia para usar como dependencia de FastAPI.
    
    Args:
        *allowed_roles: Roles permitidos
        
    Returns:
        function: Función dependencia para FastAPI
        
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMINISTRADOR))])
        def admin_endpoint():
            pass
    """
    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Requiere uno de estos roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_dependency


def require_privileged_user(current_user: User = Depends(get_current_user)):
    """
    Dependencia que requiere privilegios elevados (TEACHER o ADMIN).
    Implementa parte del requerimiento SRF2.
    
    Args:
        current_user (User): Usuario autenticado
        
    Returns:
        User: Usuario si tiene privilegios elevados
        
    Raises:
        HTTPException: Si no tiene privilegios suficientes
    """
    if not hasattr(current_user, 'es_privilegiado') or not current_user.es_privilegiado():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo docentes y administradores pueden acceder."
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)):
    """
    Dependencia que requiere rol de administrador.
    
    Args:
        current_user (User): Usuario autenticado
        
    Returns:
        User: Usuario si es administrador
        
    Raises:
        HTTPException: Si no es administrador
    """
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo administradores pueden acceder."
        )
    return current_user


def require_teacher_or_admin(current_user: User = Depends(get_current_user)):
    """
    Dependencia que requiere rol de docente o administrador.
    Específica para el requerimiento SRF2.
    
    Args:
        current_user (User): Usuario autenticado
        
    Returns:
        User: Usuario si es docente o administrador
        
    Raises:
        HTTPException: Si no es docente ni administrador
    """
    if current_user.rol not in [UserRole.DOCENTE, UserRole.ADMINISTRADOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo docentes y administradores pueden acceder a todos los reportes."
        )
    return current_user
