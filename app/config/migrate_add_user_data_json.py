"""
Script de migración para agregar la columna user_data_json a la tabla privacy_requests
Esta columna almacenará los datos del usuario en formato JSON cuando se apruebe una solicitud de acceso
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from app.services.db_service import get_db, engine

def migrate_add_user_data_json():
    """
    Agrega la columna user_data_json a la tabla privacy_requests si no existe
    """
    print("🔄 Iniciando migración: Agregar columna user_data_json a privacy_requests")
    
    try:
        # Verificar si la columna ya existe
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('privacy_requests')]
        
        if 'user_data_json' in columns:
            print("✅ La columna 'user_data_json' ya existe en la tabla privacy_requests")
            return True
        
        # Agregar la columna
        with engine.connect() as conn:
            # Para SQLite
            conn.execute(text("""
                ALTER TABLE privacy_requests 
                ADD COLUMN user_data_json TEXT NULL
            """))
            conn.commit()
            print("✅ Columna 'user_data_json' agregada exitosamente a privacy_requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("MIGRACIÓN: Agregar columna user_data_json")
    print("=" * 70)
    
    success = migrate_add_user_data_json()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print("\nAhora cuando un administrador apruebe una solicitud de acceso:")
        print("  1. Los datos del usuario se guardarán en formato JSON")
        print("  2. El usuario podrá ver sus datos en el historial de solicitudes")
        print("  3. Podrá descargar sus datos en formato JSON")
    else:
        print("\n" + "=" * 70)
        print("❌ LA MIGRACIÓN FALLÓ")
        print("=" * 70)
        sys.exit(1)
