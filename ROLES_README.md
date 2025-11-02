# Sistema de Roles - Requerimiento SRF2

Este documento explica la implementación del sistema de roles para cumplir con el **Requerimiento SRF2**: *Solo docentes y administradores pueden descargar reportes completos; estudiantes solo sus propios reportes.*

## 📋 Roles del Sistema

### 👨‍🎓 STUDENT (Estudiante)
- **Permisos**: Acceso limitado solo a sus propios recursos
- **Reportes**: Solo puede ver reportes de sus propios proyectos
- **Proyectos**: Solo puede acceder a proyectos que haya creado
- **Por defecto**: Todos los nuevos usuarios se registran como estudiantes

### 👨‍🏫 TEACHER (Docente)
- **Permisos**: Acceso completo a reportes de todos los estudiantes
- **Reportes**: Puede ver reportes de cualquier proyecto
- **Proyectos**: Puede acceder a todos los proyectos del sistema
- **Gestión**: No puede cambiar roles de otros usuarios

### 👨‍💼 ADMIN (Administrador)
- **Permisos**: Acceso completo al sistema
- **Reportes**: Puede ver todos los reportes
- **Proyectos**: Puede acceder y gestionar todos los proyectos
- **Gestión**: Puede cambiar roles de otros usuarios

## 🔧 Implementación Técnica

### Archivos Modificados/Creados

1. **`app/models/user_role.py`** - Definición de roles
2. **`app/models/user.py`** - Modelo User actualizado con campo `role`
3. **`app/services/role_checker.py`** - Funciones de acceso a proyectos (SRF2)
4. **`app/services/auth_service.py`** - Autenticación con soporte de roles
5. **`app/services/dependencies.py`** - Dependencias para verificar roles
6. **`app/api/auth.py`** - Endpoints de autenticación actualizados
7. **`app/api/report.py`** - Control de acceso a reportes (SRF2)
8. **`migrate_user_roles.py`** - Script de migración de datos

### Cambios en Base de Datos

```sql
-- Se agrega columna 'role' a la tabla users
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'student' NOT NULL;
```

## 🚀 Uso del Sistema

### 1. Registro de Usuarios

```python
# Registro como estudiante (por defecto)
POST /auth/register
{
    "email": "estudiante@universidad.edu",
    "password": "contraseña123"
}

# Registro con rol específico
POST /auth/register
{
    "email": "docente@universidad.edu", 
    "password": "contraseña123",
    "role": "teacher"
}
```

### 2. Autenticación

```python
# Login - devuelve token con información de rol
POST /auth/login
{
    "username": "usuario@email.com",
    "password": "contraseña"
}

# Respuesta incluye permisos
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "user_info": {
        "email": "docente@universidad.edu",
        "role": "teacher",
        "permissions": {
            "can_view_all_reports": true,
            "is_privileged": true
        }
    }
}
```

### 3. Acceso a Reportes (SRF2)

```python
# Estudiantes: Solo sus propios reportes
GET /report/123  # ✅ Si el proyecto 123 es del estudiante
GET /report/456  # ❌ Error 403 si el proyecto 456 es de otro usuario

# Docentes/Admins: Todos los reportes  
GET /report/123  # ✅ Acceso completo
GET /report/456  # ✅ Acceso completo

# Listar reportes accesibles
GET /report/
```

### 4. Gestión de Roles (Solo Admins)

```python
# Cambiar rol de usuario
POST /auth/change-role
{
    "target_email": "usuario@email.com",
    "new_role": "teacher"
}
```

## 🔄 Migración de Datos

### Ejecutar Migración

```bash
# Migración básica (agrega columna role y asigna STUDENT por defecto)
python migrate_user_roles.py

# Asignar roles específicos
python migrate_user_roles.py --set-teacher docente@universidad.edu
python migrate_user_roles.py --set-admin admin@sistema.com

# Ver usuarios y roles
python migrate_user_roles.py --list-users

# Crear usuarios de prueba
python migrate_user_roles.py --create-test-users
```

### Usuarios de Prueba Creados

- `estudiante@test.com` - Rol: STUDENT - Password: 123456
- `docente@test.com` - Rol: TEACHER - Password: 123456  
- `admin@test.com` - Rol: ADMIN - Password: 123456

## 🛡️ Verificación de Permisos

### En Endpoints (Dependencies)

```python
# Requiere rol específico - usar dependencies.py
@router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
def admin_endpoint():
    pass

# Requiere privilegios elevados - usar dependencies.py
@router.get("/reports-all", dependencies=[Depends(require_privileged_user)])
def all_reports():
    pass
```

### En Funciones (Project Access)

```python
# Verificar acceso a proyecto específico - usar role_checker.py
project = check_project_access(user, project_id, db)

# Verificar acceso booleano - usar role_checker.py
can_access = validate_report_access(user, project_id, db)

# Verificar permisos generales - usar métodos del User
if user.can_access_all_reports():
    # Lógica para docentes/admins
else:
    # Lógica para estudiantes
```

## 🔍 Control de Acceso SRF2

### Lógica Implementada

1. **Docentes y Administradores**:
   - `user.can_access_all_reports()` → `True`
   - Pueden acceder a reportes de cualquier proyecto
   - Ven lista completa de proyectos y reportes

2. **Estudiantes**:
   - `user.can_access_all_reports()` → `False`
   - Solo acceden a reportes de proyectos donde `project.user_id == user.id`
   - Ven solo sus propios proyectos en las listas

### Mensajes de Error

- **403 Forbidden**: "Acceso denegado. Los estudiantes solo pueden acceder a sus propios proyectos."
- **403 Forbidden**: "Solo docentes y administradores pueden acceder a todos los reportes."
- **404 Not Found**: "Proyecto no encontrado" (cuando estudiante intenta acceder a proyecto ajeno)

## ✅ Verificación del Cumplimiento SRF2

### Casos de Prueba

1. **Estudiante accede a su propio reporte** → ✅ Permitido
2. **Estudiante accede a reporte ajeno** → ❌ Error 403
3. **Docente accede a cualquier reporte** → ✅ Permitido
4. **Admin accede a cualquier reporte** → ✅ Permitido
5. **Lista de reportes filtra según rol** → ✅ Implementado

### Funciones Clave

- `check_project_access()` - Verifica acceso a proyecto específico
- `user.can_access_project()` - Método del modelo User
- `user.can_access_all_reports()` - Determina permisos de reporte
- `validate_report_access()` - Validación específica de reportes

## 📝 Notas de Desarrollo

### Consideraciones de Seguridad

- Los roles se validan tanto en el token JWT como en la base de datos
- Tokens incluyen información de rol para evitar consultas adicionales
- Verificación de consistencia entre token y BD al autenticar
- Permisos verificados en cada endpoint que requiere control de acceso

### Extensibilidad

El sistema permite agregar fácilmente:
- Nuevos roles en `UserRole` enum
- Nuevos permisos en `get_role_permissions()`
- Nuevos decoradores de verificación
- Lógica de permisos más granular por proyecto/recurso

---

**✅ REQUERIMIENTO SRF2 CUMPLIDO**: El sistema ahora implementa control de acceso diferenciado donde docentes y administradores pueden ver todos los reportes, mientras que estudiantes solo pueden acceder a reportes de sus propios proyectos.