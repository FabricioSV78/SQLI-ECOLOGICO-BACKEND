#!/usr/bin/env python3
"""
Script para gestionar la base de datos.
Ejecuta: python manage_db.py
"""

import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from app.config.config import settings
from app.services.db_service import Base

# Importar todos los modelos para que se registren en Base.metadata
from app.models.user import User
from app.models.user_role import UserRole
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.vulnerability import Vulnerability
from app.models.analysis_metrics import AnalysisMetrics

def test_connection():
    """Prueba la conexión a la base de datos."""
    try:
        print("🔗 Probando conexión a la base de datos...")
        print(f"   URL: {settings.DATABASE_URL}")
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            print("✅ Conexión exitosa a la base de datos")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def show_current_tables():
    """Muestra las tablas actuales en la base de datos."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"📋 Tablas existentes ({len(tables)}):")
            for table in tables:
                columns = inspector.get_columns(table)
                print(f"   📊 {table}:")
                for col in columns:
                    print(f"      - {col['name']}: {col['type']}")
        else:
            print("📋 No hay tablas en la base de datos")
        
        return tables
    except Exception as e:
        print(f"❌ Error al obtener tablas: {e}")
        return []

def create_tables():
    """Crea todas las tablas necesarias."""
    try:
        print("🔨 Creando tablas...")
        engine = create_engine(settings.DATABASE_URL, echo=True)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente!")
        
        # Mostrar resultado
        show_current_tables()
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

def recreate_tables():
    """Elimina y recrea todas las tablas. ⚠️ BORRA TODOS LOS DATOS."""
    try:
        print("⚠️ ADVERTENCIA: Esto eliminará TODOS los datos existentes.")
        confirm = input("¿Estás seguro? Escribe 'CONFIRMAR' para continuar: ")
        
        if confirm != "CONFIRMAR":
            print("❌ Operación cancelada")
            return False
            
        engine = create_engine(settings.DATABASE_URL, echo=True)
        
        print("🗑️ Eliminando tablas existentes...")
        Base.metadata.drop_all(bind=engine)
        
        print("🔨 Creando nuevas tablas...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas recreadas exitosamente!")
        show_current_tables()
        return True
        
    except Exception as e:
        print(f"❌ Error al recrear tablas: {e}")
        return False

def main():
    """Función principal con menú interactivo."""
    print("🏗️ Gestor de Base de Datos - Detector SQLi")
    print("=" * 50)
    
    # Mostrar configuración
    print("🔧 Configuración actual:")
    print(f"   Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"   Usuario: {settings.DB_USER}")
    print(f"   Base de datos: {settings.DB_NAME}")
    print()
    
    # Probar conexión
    if not test_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    while True:
        print("\n🎯 Opciones disponibles:")
        print("1. Mostrar tablas actuales")
        print("2. Crear tablas (mantiene datos existentes)")
        print("3. Recrear tablas (⚠️ BORRA todos los datos)")
        print("4. Probar conexión")
        print("5. Salir")
        
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        if choice == "1":
            show_current_tables()
        elif choice == "2":
            create_tables()
        elif choice == "3":
            recreate_tables()
        elif choice == "4":
            test_connection()
        elif choice == "5":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()
