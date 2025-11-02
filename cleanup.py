#!/usr/bin/env python3
"""
Script de limpieza y mantenimiento del proyecto.
Ejecuta: python cleanup.py
"""

import os
import shutil
from pathlib import Path

def clean_pycache():
    """Elimina todos los directorios __pycache__."""
    print("🧹 Limpiando archivos cache de Python...")
    
    project_root = Path(__file__).parent
    cache_dirs = list(project_root.rglob("__pycache__"))
    
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"   ✅ Eliminado: {cache_dir}")
        except Exception as e:
            print(f"   ❌ Error eliminando {cache_dir}: {e}")
    
    print(f"🎉 Eliminados {len(cache_dirs)} directorios cache")

def clean_pyc_files():
    """Elimina archivos .pyc individuales."""
    print("🧹 Limpiando archivos .pyc...")
    
    project_root = Path(__file__).parent
    pyc_files = list(project_root.rglob("*.pyc"))
    
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            print(f"   ✅ Eliminado: {pyc_file}")
        except Exception as e:
            print(f"   ❌ Error eliminando {pyc_file}: {e}")
    
    print(f"🎉 Eliminados {len(pyc_files)} archivos .pyc")

def clean_temp_files():
    """Elimina archivos temporales."""
    print("🧹 Limpiando archivos temporales...")
    
    project_root = Path(__file__).parent
    temp_patterns = ["*.tmp", "*.temp", "*~", "*.bak"]
    
    total_cleaned = 0
    for pattern in temp_patterns:
        temp_files = list(project_root.rglob(pattern))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                print(f"   ✅ Eliminado: {temp_file}")
                total_cleaned += 1
            except Exception as e:
                print(f"   ❌ Error eliminando {temp_file}: {e}")
    
    print(f"🎉 Eliminados {total_cleaned} archivos temporales")

def show_project_structure():
    """Muestra la estructura limpia del proyecto."""
    print("📋 Estructura actual del proyecto:")
    
    project_root = Path(__file__).parent
    
    # Directorios principales
    main_dirs = [d for d in project_root.iterdir() if d.is_dir() and not d.nombre.startswith('.')]
    
    for main_dir in sorted(main_dirs):
        print(f"📁 {main_dir.nombre}/")
        
        # Subdirectorios
        if main_dir.nombre == "app":
            for sub_dir in sorted(main_dir.iterdir()):
                if sub_dir.is_dir() and not sub_dir.nombre.startswith('__'):
                    print(f"   📁 {sub_dir.nombre}/")
                    
                    # Archivos Python en subdirectorio
                    py_files = list(sub_dir.glob("*.py"))
                    for py_file in sorted(py_files):
                        print(f"      📄 {py_file.nombre}")
    
    # Archivos en la raíz
    root_files = [f for f in project_root.iterdir() if f.is_file() and f.suffix in ['.py', '.md', '.txt']]
    if root_files:
        print("📄 Archivos en la raíz:")
        for root_file in sorted(root_files):
            print(f"   📄 {root_file.nombre}")

def validate_imports():
    """Valida que no haya imports rotos después de la limpieza."""
    print("🔍 Validando imports...")
    
    try:
        # Imports principales
        from app.config.config import settings
        print("   ✅ app.config.config importado correctamente")

        from app.services.db_service import Base
        print("   ✅ app.services.db_service importado correctamente")

        from app.models.user import User
        print("   ✅ app.models.user importado correctamente")

        from app.models.user_role import UserRole
        print("   ✅ app.models.user_role importado correctamente")

        from app.api.auth import router
        print("   ✅ app.api.auth importado correctamente")

        print("🎉 Todos los imports principales funcionan correctamente")

    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False
    
    return True

def main():
    """Función principal de limpieza."""
    print("🏗️ Script de Limpieza del Proyecto")
    print("=" * 50)
    
    # Ejecutar limpiezas
    clean_pycache()
    clean_pyc_files()
    clean_temp_files()
    
    print("\n" + "=" * 50)
    
    # Validar que todo sigue funcionando
    if validate_imports():
        print("\n✅ Proyecto limpio y funcional")
        show_project_structure()
    else:
        print("\n❌ Se encontraron problemas después de la limpieza")
        print("   Revisa los imports manualmente")

if __name__ == "__main__":
    main()
