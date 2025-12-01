**Profiling e optimizaciones**

- Se integró un wrapper de profiling usando `cProfile` y `pstats` en `app/services/profiler.py`.
- El endpoint de análisis (`/api/v1/analysis/{project_id}`) permite activar profiling por petición con `?profile=1` o habilitarlo globalmente con la variable de entorno `ENABLE_PROFILING=true`.
- El profiler genera dos archivos en el directorio de reportes (`REPORTS_DIR`): un `.prof` binario y un `.txt` con el resumen de las funciones más costosas.
- Actualmente no se aplicaron cambios de código para optimizar internals del detector; el siguiente paso es ejecutar el profiler sobre casos reales, identificar hotspots, aplicar optimizaciones y registrar las mejoras de tiempo en este documento.

Recomendación de flujo para optimizar:
1. Ejecutar análisis representativo con `?profile=1`.
2. Revisar `REPORTS_DIR/profiler_*.txt` para identificar funciones con mayor `cumtime`.
3. Aplicar optimizaciones locales (evitar recalcular, usar estructuras más eficientes, vectorizar, etc.).
4. Re-ejecutar profiling y registrar tiempos antes/después en este documento para auditar la mejora.
