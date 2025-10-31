# Sistema de Métricas de Análisis

## Descripción

El sistema de métricas de análisis registra automáticamente información detallada sobre cada análisis de proyecto realizado, incluyendo tiempo de ejecución, costo calculado, y estadísticas de vulnerabilidades.

## Tabla: metricas_analisis

La nueva tabla `metricas_analisis` contiene los siguientes campos:

| Campo                   | Tipo    | Descripción                                                 |
| ----------------------- | ------- | ----------------------------------------------------------- |
| `id`                    | Integer | ID único de la métrica                                      |
| `id_proyecto`           | Integer | ID del proyecto analizado (FK a projects)                   |
| `tiempo_analisis`       | Float   | Tiempo de análisis en segundos                              |
| `costo`                 | Float   | Costo calculado (tiempo × 5)                                |
| `detecciones_correctas` | Integer | Cantidad de detecciones correctas (para llenar manualmente) |
| `codigos_vulnerables`   | Integer | Cantidad de códigos vulnerables                             |
| `precision`             | Float   | Precisión del análisis (inicialmente NULL)                  |

## Funcionalidades Automáticas

### 1. Registro Automático de Métricas

Cuando ejecutas un análisis usando el endpoint `/analysis/{project_id}`, el sistema automáticamente:

- Mide el tiempo de análisis
- Cuenta códigos vulnerables
- Calcula el costo (tiempo × 5)
- Guarda todo en la base de datos
- Deja el campo `detecciones_correctas` vacío para que lo llenes manualmente

### 2. Propiedades Calculadas

El modelo incluye propiedades útiles:

- `total_archivos_analizados`: Total de archivos analizados (basado en códigos vulnerables)
- `porcentaje_vulnerabilidades`: Porcentaje de vulnerabilidades encontradas

## Endpoints de API

### 1. Análisis con Métricas Automáticas

```
GET /analysis/{project_id}
```

Ejecuta el análisis y registra métricas automáticamente.

**Respuesta incluye:**

```json
{
  "id_proyecto": "1",
  "message": "Se analizaron 15 consultas SQL.",
  "results": [...],
  "metricas_analisis": {
    "id": 1,
    "tiempo_analisis": 2.5,
    "costo": 12.5,
    "detecciones_correctas": null,
    "codigos_vulnerables": 5,
    "total_archivos_analizados": 5,
    "porcentaje_vulnerabilidades": 100.0,
    "precision": null
  }
}
```

### 2. Obtener Métricas de un Proyecto

```
GET /analysis/{project_id}/metrics
```

Retorna todas las métricas históricas de un proyecto.

### 3. Obtener Métricas Más Recientes

```
GET /analysis/{project_id}/metrics/latest
```

Retorna solo las métricas del análisis más reciente.

### 4. Actualizar Precisión

```
PUT /analysis/metrics/{metrics_id}/precision
```

Permite actualizar el campo `precision`.

**Body:**

```json
{
  "precision": 0.85
}
```

### 5. Actualizar Detecciones Correctas

```
PUT /analysis/metrics/{metrics_id}/detecciones-correctas
```

Permite actualizar el campo `detecciones_correctas` manualmente.

**Body:**

```json
{
  "detecciones_correctas": 8
}
```

### 6. Obtener Todas las Métricas

```
GET /analysis/metrics/all
```

Retorna métricas de todos los proyectos.

## Ejemplo de Uso

### 1. Ejecutar Análisis

```bash
curl -X GET "http://localhost:8000/analysis/1" \
  -H "Authorization: Bearer tu_token"
```

### 2. Ver Métricas del Proyecto

```bash
curl -X GET "http://localhost:8000/analysis/1/metrics" \
  -H "Authorization: Bearer tu_token"
```

### 3. Actualizar Detecciones Correctas

```bash
curl -X PUT "http://localhost:8000/analysis/metrics/1/detecciones-correctas" \
  -H "Authorization: Bearer tu_token" \
  -H "Content-Type: application/json" \
  -d '{"detecciones_correctas": 8}'
```

### 4. Actualizar Precisión

```bash
curl -X PUT "http://localhost:8000/analysis/metrics/1/precision" \
  -H "Authorization: Bearer tu_token" \
  -H "Content-Type: application/json" \
  -d '{"precision": 0.92}'
```

## Beneficios del Sistema

1. **Tracking Automático**: Todas las métricas se registran automáticamente
2. **Análisis de Costos**: Cálculo automático basado en tiempo de procesamiento
3. **Estadísticas de Calidad**: Conteo de vulnerabilidades por análisis
4. **Historial Completo**: Mantiene registro de todos los análisis realizados
5. **Flexibilidad**: Campos de precisión y detecciones correctas actualizables posteriormente
6. **Nombres en Español**: Toda la estructura usa terminología en español

## Estructura de Base de Datos

```sql
CREATE TABLE metricas_analisis (
    id SERIAL PRIMARY KEY,
    id_proyecto INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tiempo_analisis FLOAT NOT NULL,
    costo FLOAT NOT NULL,
    detecciones_correctas INTEGER NULL,
    codigos_vulnerables INTEGER NOT NULL DEFAULT 0,
    precision FLOAT NULL
);
```

## Servicios Disponibles

### AnalysisMetricsService

- `create_metrics()`: Crear nueva entrada de métricas
- `get_metrics_by_project()`: Obtener métricas por proyecto
- `get_latest_metrics()`: Obtener métricas más recientes
- `update_precision()`: Actualizar precisión
- `update_detecciones_correctas()`: Actualizar detecciones correctas
- `get_all_metrics()`: Obtener todas las métricas

### AnalysisTimer

- Context manager para medir tiempo de análisis
- Uso: `with AnalysisTimer() as timer:`

## Cambios Realizados

### ✅ Eliminado:

- ❌ `non_vulnerable_count` (códigos no vulnerables)
- ❌ `created_at` (fecha de creación)
- ❌ Nombres de campos en inglés

### ✅ Agregado:

- ✅ `detecciones_correctas` (campo vacío para llenar manualmente)
- ✅ Todos los nombres de campos en español
- ✅ Endpoint para actualizar detecciones correctas
- ✅ Estructura optimizada sin dependencias de tiempo
