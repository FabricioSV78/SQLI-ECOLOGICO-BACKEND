"""
Script de prueba para el sistema de métricas de análisis
Este script demuestra cómo usar el nuevo sistema de métricas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.services.db_service import get_db, engine
from app.services.analysis_metrics_service import AnalysisMetricsService, AnalysisTimer
from app.models.analysis_metrics import AnalysisMetrics
import time

def test_metrics_system():
    """Prueba el sistema completo de métricas"""
    print("🧪 Probando el sistema de métricas de análisis...")
    
    # Obtener sesión de base de datos
    db: Session = next(get_db())
    metrics_service = AnalysisMetricsService(db)
    
    # Crear un proyecto y usuario de prueba
    from app.models.user import User
    from app.models.project import Project
    
    print("\n0. Creando datos de prueba...")
    
    # Crear usuario de prueba
    test_user = User(
        email="test@test.com",
        password="hashed_password"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Crear proyecto de prueba
    test_project = Project(
        name="Proyecto de Prueba",
        description="Proyecto para probar métricas",
        user_id=test_user.id
    )
    db.add(test_project)
    db.commit()
    db.refresh(test_project)
    
    print(f"   ✅ Usuario creado con ID: {test_user.id}")
    print(f"   ✅ Proyecto creado con ID: {test_project.id}")
    
    print("\n1. Simulando análisis con timer...")
    
    # Simular un análisis con el timer
    with AnalysisTimer() as timer:
        # Simular trabajo de análisis
        time.sleep(2)  # Simula 2 segundos de análisis
        print("   ⏳ Analizando código...")
        time.sleep(1)  # Un segundo más
    
    analysis_time = timer.get_elapsed_time()
    print(f"   ✅ Análisis completado en {analysis_time:.2f} segundos")
    
    print("\n2. Guardando métricas en la base de datos...")
    
    # Crear métricas para el proyecto de prueba
    try:
        metrics = metrics_service.create_metrics(
            id_proyecto=test_project.id,
            tiempo_analisis=analysis_time,
            vulnerabilidades_detectadas=3
        )
        
        print(f"   ✅ Métricas guardadas con ID: {metrics.id}")
        print(f"   📊 Tiempo: {metrics.tiempo_analisis:.2f}s")
        print(f"   💰 Costo: ${metrics.costo:.2f}")
        print(f"   🔍 Archivos analizados: {metrics.total_archivos_analizados}")
        print(f"   ⚠️  Porcentaje vulnerabilidades: {metrics.porcentaje_vulnerabilidades:.1f}%")
        print(f"   ✨ Detecciones correctas: {metrics.detecciones_correctas}")
        
    except Exception as e:
        print(f"   ❌ Error guardando métricas: {str(e)}")
        # Limpiar datos de prueba en caso de error
        db.delete(test_project)
        db.delete(test_user)
        db.commit()
        return
    
    print("\n3. Probando consultas de métricas...")
    
    # Obtener métricas más recientes
    latest = metrics_service.get_latest_metrics(test_project.id)
    if latest:
        print(f"   ✅ Métricas más recientes encontradas (ID: {latest.id})")
    else:
        print("   ❌ No se encontraron métricas")
    
    # Obtener todas las métricas del proyecto
    all_metrics = metrics_service.get_metrics_by_project(test_project.id)
    print(f"   📋 Total de métricas para proyecto {test_project.id}: {len(all_metrics)}")
    
    print("\n4. Probando actualización de detecciones correctas...")
    
    # Actualizar detecciones correctas
    updated = metrics_service.update_detecciones_correctas(metrics.id, 5)
    if updated:
        print(f"   ✅ Detecciones correctas actualizadas a: {updated.detecciones_correctas}")
    else:
        print("   ❌ Error actualizando detecciones correctas")
    
    # También probar actualización de precisión
    updated_precision = metrics_service.update_precision(metrics.id, 0.87)
    if updated_precision:
        print(f"   ✅ Precisión actualizada a: {updated_precision.precision}")
    else:
        print("   ❌ Error actualizando precisión")
    
    print("\n5. Limpiando datos de prueba...")
    
    # Limpiar datos de prueba (el CASCADE eliminará las métricas automáticamente)
    db.delete(test_project)
    db.delete(test_user)
    db.commit()
    print("   ✅ Datos de prueba eliminados correctamente")
    
    db.close()
    print("\n🎉 ¡Prueba del sistema de métricas completada exitosamente!")

def test_timer_standalone():
    """Prueba el timer de forma independiente"""
    print("\n🔧 Probando AnalysisTimer...")
    
    # Prueba básica del timer
    timer = AnalysisTimer()
    timer.start()
    time.sleep(1)
    elapsed = timer.stop()
    print(f"   ✅ Timer básico: {elapsed:.2f} segundos")
    
    # Prueba con context manager
    with AnalysisTimer() as ctx_timer:
        time.sleep(0.5)
    
    elapsed = ctx_timer.get_elapsed_time()
    print(f"   ✅ Timer con context manager: {elapsed:.2f} segundos")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema de métricas...")
    
    try:
        test_timer_standalone()
        test_metrics_system()
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Pruebas finalizadas.")