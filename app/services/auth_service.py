from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.user_role import UserRole, RolUsuario
from app.services.db_service import get_db
from app.config.config import settings  # ahora usamos config.py

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def obtener_hash_contrasena(contrasena: str):
    """
    Genera el hash de una contraseña usando bcrypt.
    
    Args:
        contrasena (str): Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(contrasena)


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str):
    """
    Verifica si una contraseña coincide con su hash.
    
    Args:
        contrasena_plana (str): Contraseña en texto plano
        contrasena_hash (str): Hash almacenado
        
    Returns:
        bool: True si la contraseña es correcta
    """
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def crear_token_acceso(datos: dict, delta_expiracion: timedelta = None):
    """
    Crea un token JWT con información del usuario incluyendo rol.
    Actualizado para soportar el requerimiento SRF2.
    
    Args:
        datos (dict): Datos a incluir en el token (debe incluir rol)
        delta_expiracion (timedelta, optional): Tiempo de expiración personalizado
        
    Returns:
        str: Token JWT generado
    """
    datos_codificar = datos.copy()
    expiracion = datetime.utcnow() + (
        delta_expiracion or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    datos_codificar.update({"exp": expiracion})
    return jwt.encode(datos_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Funciones de compatibilidad en inglés
def hash_password(password: str):
    return obtener_hash_contrasena(password)

def verify_password(plain_password: str, hashed_password: str):
    return verificar_contrasena(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    return crear_token_acceso(data, expires_delta)


def autenticar_usuario(db: Session, correo: str, contrasena: str):
    """
    Autentica un usuario verificando email y contraseña.
    
    Args:
        db (Session): Sesión de base de datos
        correo (str): Email del usuario
        contrasena (str): Contraseña en texto plano
        
    Returns:
        Usuario | None: Usuario autenticado o None si fallan las credenciales
    """
    from app.models.user import Usuario
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario or not verificar_contrasena(contrasena, usuario.contrasena):
        return None
    return usuario

# Función de compatibilidad con diferente nombre
def authenticate_user(db: Session, email: str, password: str):
    from app.models.user import Usuario
    usuario = db.query(Usuario).filter(Usuario.correo == email).first()
    if not usuario or not verificar_contrasena(password, usuario.contrasena):
        return None
    return usuario


def crear_token_usuario(usuario) -> str:
    """
    Crea un token JWT para un usuario incluyendo información de rol.
    Función específica para incluir datos de rol en el token.
    
    Args:
        usuario: Usuario autenticado
        
    Returns:
        str: Token JWT con información de rol
    """
    # Incluir rol en el token para verificación posterior
    datos_token = {
        "sub": usuario.correo,
        "usuario_id": usuario.id,
        "rol": usuario.rol.value  # Incluir rol para control de acceso
    }
    return crear_token_acceso(datos_token)

# Función de compatibilidad
def create_user_token(user) -> str:
    return crear_token_usuario(user)


def registrar_usuario(db: Session, correo: str, contrasena: str, rol: RolUsuario = UserRole.ESTUDIANTE):
    """
    Registra un nuevo usuario en el sistema con rol especificado.
    Implementa el requerimiento SRF2 de control de acceso basado en roles.
    
    Args:
        db (Session): Sesión de base de datos
        correo (str): Email del usuario
        contrasena (str): Contraseña en texto plano
        rol (UserRole): Rol del usuario (STUDENT por defecto)
        
    Returns:
        Usuario: Usuario creado
        
    Raises:
        HTTPException: Si el usuario ya existe
    """
    from app.models.user import Usuario
    
    # Verificar si el usuario ya existe
    usuario_existente = db.query(Usuario).filter(Usuario.correo == correo).first()
    if usuario_existente:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El usuario ya está registrado")
    
    # Crear hash de la contraseña
    contrasena_hash = obtener_hash_contrasena(contrasena)
    
    # Crear nuevo usuario con rol
    nuevo_usuario = Usuario(
        correo=correo,
        contrasena=contrasena_hash,
        rol=rol
    )
    
    # Guardar en base de datos
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario

# Función de compatibilidad en inglés que llama a la función principal en español
def register_user(db: Session, email: str, password: str, role: RolUsuario = UserRole.ESTUDIANTE):
    # Llamar a la función principal con parámetros en español
    return registrar_usuario(db, email, password, role)


def obtener_rol_usuario_desde_token(token: str) -> UserRole:
    """
    Extrae el rol del usuario de un token JWT.
    
    Args:
        token (str): Token JWT
        
    Returns:
        UserRole: Rol del usuario extraído del token
        
    Raises:
        JWTError: Si el token es inválido
    """
    try:
        carga = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        rol_str = carga.get("rol") or carga.get("role")  # Soporte para ambos formato
        if rol_str:
            return RolUsuario(rol_str)
        return UserRole.ESTUDIANTE  # Valor por defecto
    except JWTError:
        raise JWTError("Token inválido")

# Función de compatibilidad
def get_user_role_from_token(token: str) -> UserRole:
    return obtener_rol_usuario_desde_token(token)
