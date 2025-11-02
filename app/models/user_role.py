"""
Definición de roles de usuario para el sistema de detección SQLi.

Este módulo define los tipos de usuario disponibles en el sistema:
- STUDENT: Estudiantes que solo pueden ver sus propios proyectos y reportes
- TEACHER: Docentes que pueden ver todos los reportes y proyectos
- ADMIN: Administradores con acceso completo al sistema

Requerimiento SRF2: Control de acceso diferenciado para reportes
"""

from enum import Enum


class RolUsuario(str, Enum):
    """
    Enumeración de roles de usuario en el sistema.
    
    Los roles definen los permisos de acceso:
    - ESTUDIANTE: Acceso limitado solo a sus propios recursos
    - DOCENTE: Acceso completo a reportes de todos los estudiantes
    - ADMINISTRADOR: Acceso administrativo completo al sistema
    """
    
    ESTUDIANTE = "estudiante"       # Estudiante - acceso limitado
    DOCENTE = "docente"            # Docente - acceso a todos los reportes
    ADMINISTRADOR = "administrador" # Administrador - acceso completo

# Mantenemos UserRole como alias para compatibilidad hacia atrás
UserRole = RolUsuario


def obtener_permisos_rol(rol: RolUsuario) -> dict:
    """
    Obtiene los permisos asociados a un rol específico.
    
    Args:
        rol (RolUsuario): El rol del usuario
        
    Returns:
        dict: Diccionario con los permisos del rol
    """
    permisos = {
        RolUsuario.ESTUDIANTE: {
            "puede_ver_todos_reportes": False,
            "puede_ver_reportes_propios": True,
            "puede_gestionar_usuarios": False,
            "puede_eliminar_cualquier_proyecto": False,
            "descripcion": "Estudiante con acceso limitado a sus propios recursos"
        },
        RolUsuario.DOCENTE: {
            "puede_ver_todos_reportes": True,
            "puede_ver_reportes_propios": True,
            "puede_gestionar_usuarios": False,
            "puede_eliminar_cualquier_proyecto": False,
            "descripcion": "Docente con acceso a reportes de todos los estudiantes"
        },
        RolUsuario.ADMINISTRADOR: {
            "puede_ver_todos_reportes": True,
            "puede_ver_reportes_propios": True,
            "puede_gestionar_usuarios": True,
            "puede_eliminar_cualquier_proyecto": True,
            "descripcion": "Administrador con acceso completo al sistema"
        }
    }
    
    return permisos.get(rol, permisos[RolUsuario.ESTUDIANTE])

# Mantenemos get_role_permissions como alias para compatibilidad
def get_role_permissions(role: RolUsuario) -> dict:
    return obtener_permisos_rol(role)


def es_usuario_privilegiado(rol: RolUsuario) -> bool:
    """
    Verifica si un usuario tiene privilegios elevados (docente o admin).
    
    Args:
        rol (RolUsuario): El rol del usuario
        
    Returns:
        bool: True si es docente o admin, False si es estudiante
    """
    return rol in [RolUsuario.DOCENTE, RolUsuario.ADMINISTRADOR]


def puede_acceder_todos_reportes(rol: RolUsuario) -> bool:
    """
    Verifica si un usuario puede acceder a todos los reportes.
    
    Args:
        rol (RolUsuario): El rol del usuario
        
    Returns:
        bool: True si puede acceder a todos los reportes
    """
    return obtener_permisos_rol(rol)["puede_ver_todos_reportes"]

# Mantenemos funciones originales como alias para compatibilidad
def is_privileged_user(role: RolUsuario) -> bool:
    return es_usuario_privilegiado(role)

def puede_acceder_todos_reportes(role: RolUsuario) -> bool:
    return puede_acceder_todos_reportes(role)
