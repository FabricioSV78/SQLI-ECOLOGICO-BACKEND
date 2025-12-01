# Migración: Costo → Consumo Energético en Métricas

## 📋 Cambios Realizados

Se ha reemplazado el campo **`costo`** por **`consumo_energetico_kwh`** en la tabla de métricas de análisis.

### Antes:

- Campo: `costo` (Float) - Calculado como `tiempo_analisis * 0.0000066`
- Representaba un costo arbitrario

### Ahora:

- Campo: `consumo_energetico_kwh` (Float) - Calculado en base al consumo energético real
- Fórmula: `(potencia_watts × tiempo_segundos) / 3600`
- Por defecto usa 10W de potencia estimada
- Se mide usando el `EnergyMonitor` que considera CPU y RAM

## 🔧 Archivos Modificados

1. **`app/models/analysis_metrics.py`**

   - Renombrado campo `costo` → `consumo_energetico_kwh`
   - Método `calcular_costo()` → `calcular_consumo_energetico()`

2. **`app/services/analysis_metrics_service.py`**

   - Actualizado `create_metrics()` para aceptar `consumo_energetico_kwh`
   - Se calcula automáticamente si no se proporciona

3. **`app/api/analysis.py`**

   - Todos los endpoints ahora devuelven `consumo_energetico_kwh` en lugar de `costo`
   - Usa `EnergyMonitor` para medir consumo real

4. **`app/services/file_service.py`**
   - Al subir proyecto, usa `EnergyMonitor` para medir y guardar métricas

## 🚀 Instrucciones de Migración

### Opción 1: Si tienes datos importantes en la BD (Recomendado)

```powershell
# Ejecutar script de migración
python -m app.config.migrate_metrics_to_energy
```

Este script:

- ✅ Renombra la columna `costo` → `consumo_energetico_kwh`
- ✅ Recalcula todos los valores existentes
- ✅ Mantiene tus datos históricos

### Opción 2: Si puedes recrear la BD (más simple)

```powershell
# Recrear todas las tablas
python -m app.config.init_db
```

⚠️ **ADVERTENCIA**: Esto eliminará todos los datos existentes.

### Opción 3: Base de datos nueva

Si es una instalación nueva, no necesitas hacer nada. Las tablas se crearán automáticamente con el nuevo esquema.

## 📊 Respuestas de API Actualizadas

### Antes:

```json
{
  "metricas": {
    "tiempo_analisis": 2.5,
    "costo": 0.0000165,
    "vulnerabilidades_detectadas": 5
  }
}
```

### Ahora:

```json
{
  "metricas": {
    "tiempo_analisis": 2.5,
    "consumo_energetico_kwh": 0.00694444,
    "vulnerabilidades_detectadas": 5
  }
}
```

## 🧪 Verificación

Después de migrar, verifica que todo funcione:

```powershell
# Iniciar servidor
cd Taller2-Backend
uvicorn app.main:app --reload

# Subir un proyecto de prueba y verificar las métricas
# El endpoint /analysis/all-metrics debe mostrar consumo_energetico_kwh
```

## ⚡ Beneficios

1. **Métricas más precisas**: Basadas en consumo energético real
2. **Medición detallada**: Considera CPU y RAM usando `EnergyMonitor`
3. **Trazabilidad**: Métricas alineadas con estimaciones de emisiones
4. **Escalabilidad**: Puedes ajustar la potencia estimada vía configuración

## 🔗 Relacionado

- `app/services/energy_monitor.py` - Monitor de consumo energético
- `REPORT_OPTIMIZATIONS.md` - Documentación de optimizaciones
