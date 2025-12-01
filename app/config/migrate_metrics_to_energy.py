"""
Script de migración para actualizar la tabla metricas_analisis:
- Renombra la columna 'costo' a 'consumo_energetico_kwh'
- Recalcula los valores basándose en el tiempo de análisis

Ejecutar este script ANTES de reiniciar el servidor con los nuevos cambios.

Uso:
    python -m app.config.migrate_metrics_to_energy
"""

from sqlalchemy import create_engine, text
from app.config.config import settings
import sys


def migrate_metrics_table():
    """
    Migra la tabla metricas_analisis de 'costo' a 'consumo_energetico_kwh'
    """
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    try:
        with engine.connect() as conn:
            # Verificar si la columna 'costo' existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='metricas_analisis' AND column_name='costo'
            """))
            
            if result.fetchone():
                print("✅ Columna 'costo' encontrada. Iniciando migración...")
                
                # PostgreSQL/SQLite: Renombrar columna y recalcular valores
                try:
                    # Intentar renombrar (funciona en PostgreSQL y SQLite 3.25+)
                    conn.execute(text("""
                        ALTER TABLE metricas_analisis 
                        RENAME COLUMN costo TO consumo_energetico_kwh
                    """))
                    conn.commit()
                    print("✅ Columna renombrada exitosamente")
                    
                    # Recalcular valores: convertir costo a consumo energético
                    # Fórmula anterior: costo = tiempo * 0.0000066
                    # Nueva fórmula: consumo_kwh = (10W * tiempo_segundos) / 3600
                    # Relación: consumo_kwh = costo * (10/3600) / 0.0000066
                    
                    conn.execute(text("""
                        UPDATE metricas_analisis 
                        SET consumo_energetico_kwh = (tiempo_analisis * 10.0) / 3600.0
                        WHERE consumo_energetico_kwh IS NOT NULL
                    """))
                    conn.commit()
                    print("✅ Valores recalculados exitosamente")
                    
                except Exception as e:
                    print(f"⚠️ No se pudo renombrar la columna: {e}")
                    print("Intentando método alternativo (crear nueva columna)...")
                    
                    # Método alternativo: crear nueva columna, copiar datos, eliminar antigua
                    conn.execute(text("""
                        ALTER TABLE metricas_analisis 
                        ADD COLUMN consumo_energetico_kwh FLOAT
                    """))
                    conn.commit()
                    
                    conn.execute(text("""
                        UPDATE metricas_analisis 
                        SET consumo_energetico_kwh = (tiempo_analisis * 10.0) / 3600.0
                    """))
                    conn.commit()
                    
                    conn.execute(text("""
                        ALTER TABLE metricas_analisis 
                        DROP COLUMN costo
                    """))
                    conn.commit()
                    print("✅ Migración completada usando método alternativo")
                    
            else:
                # Verificar si ya existe la nueva columna
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='metricas_analisis' AND column_name='consumo_energetico_kwh'
                """))
                
                if result.fetchone():
                    print("✅ La columna 'consumo_energetico_kwh' ya existe. No se requiere migración.")
                else:
                    print("❌ No se encontró ninguna de las columnas esperadas.")
                    print("⚠️ Es posible que necesites ejecutar init_db.py para recrear las tablas.")
                    return False
                    
        print("\n✅ Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        print("\nSi la tabla no existe o está vacía, puedes:")
        print("1. Ejecutar: python -m app.config.init_db")
        print("2. O simplemente iniciar el servidor (las nuevas métricas usarán el nuevo campo)")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: metricas_analisis (costo → consumo_energetico_kwh)")
    print("=" * 60)
    print()
    
    success = migrate_metrics_table()
    
    if success:
        print("\n🎉 ¡Migración exitosa!")
        print("Ya puedes reiniciar el servidor con los nuevos cambios.")
        sys.exit(0)
    else:
        print("\n⚠️ Migración no completada.")
        print("Revisa los mensajes anteriores para más detalles.")
        sys.exit(1)
