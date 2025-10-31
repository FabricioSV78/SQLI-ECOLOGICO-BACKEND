#!/usr/bin/env python3
"""
Script de prueba para los reportes del modelo ML
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_modelo_reportes():
    """Prueba los reportes del modelo ML"""
    print("🔬 Iniciando prueba de reportes del modelo ML...")
    
    try:
        # Importar el módulo ML (esto activará la carga del modelo)
        from app.core import ml_model
        
        print("\n✅ Modelo cargado exitosamente!")
        
        # Pruebas con diferentes tipos de consultas
        consultas_prueba = [
            "SELECT * FROM users WHERE username = ?",
            "SELECT * FROM users WHERE username = '" + "admin" + "'",
            "String query = 'SELECT * FROM products WHERE id = ' + productId",
            "PreparedStatement ps = connection.prepareStatement('SELECT * FROM orders WHERE user_id = ?')",
            "em.createQuery('SELECT u FROM User u WHERE u.name = :name')"
        ]
        
        print(f"\n🧪 Probando {len(consultas_prueba)} consultas...")
        
        resultados = []
        for i, consulta in enumerate(consultas_prueba, 1):
            print(f"\n--- Prueba {i}/{len(consultas_prueba)} ---")
            resultado = ml_model.classify_query(consulta)
            resultados.append({
                'consulta': consulta,
                'resultado': resultado
            })
        
        # Resumen final
        print("\n" + "="*80)
        print("📋 RESUMEN DE RESULTADOS")
        print("="*80)
        for i, res in enumerate(resultados, 1):
            print(f"{i}. {res['resultado']}: {res['consulta'][:60]}...")
        
        print(f"\n🎯 Total consultadas: {len(resultados)}")
        vulnerables = sum(1 for r in resultados if "SQLi" in r['resultado'])
        seguras = len(resultados) - vulnerables
        print(f"✅ Consultas seguras: {seguras}")
        print(f"⚠️  Consultas vulnerables: {vulnerables}")
        
        print("\n✨ Prueba completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_modelo_reportes()