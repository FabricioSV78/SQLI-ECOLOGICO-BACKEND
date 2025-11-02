#!/usr/bin/env python3
"""
Script de configuración para el entorno de desarrollo con seguridad
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Salida del error: {e.stderr}")
        return None

def setup_security_tools():
    """Instala y configura herramientas de seguridad"""
    
    print("🔒 Configurando herramientas de seguridad para desarrollo...")
    
    # Instalar herramientas de seguridad
    security_tools = [
        "bandit",
        "safety", 
        "semgrep",
        "pre-commit",
        "detect-secrets"
    ]
    
    for tool in security_tools:
        run_command(f"pip install {tool}", f"Instalando {tool}")
    
    # Configurar pre-commit
    run_command("pre-commit install", "Configurando pre-commit hooks")
    
    # Crear baseline para detect-secrets
    if not os.path.exists(".secrets.baseline"):
        run_command("detect-secrets scan --baseline .secrets.baseline", 
                   "Creando baseline para detección de secretos")
    
    # Ejecutar análisis inicial
    print("\n🔍 Ejecutando análisis de seguridad inicial...")
    
    # Bandit scan
    run_command("bandit -r app/ -f txt", "Escaneando código con Bandit")
    
    # Safety check
    run_command("safety check", "Verificando vulnerabilidades en dependencias")
    
    # Detect secrets
    run_command("detect-secrets scan --baseline .secrets.baseline --update", 
               "Actualizando baseline de secretos")
    
    print("\n✅ Configuración de seguridad completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecuta 'docker-compose up --build' para iniciar el entorno de desarrollo")
    print("2. Los pre-commit hooks se ejecutarán automáticamente en cada commit")
    print("3. Revisa los reportes de seguridad generados")

def setup_docker_environment():
    """Configura el entorno Docker"""
    print("\n🐳 Configurando entorno Docker...")
    
    # Build de la imagen
    run_command("docker-compose build", "Construyendo imagen Docker")
    
    # Verificar que todo esté correcto
    run_command("docker-compose config", "Validando configuración de Docker Compose")
    
    print("✅ Entorno Docker configurado correctamente!")

def main():
    print("🚀 Iniciando configuración del entorno de desarrollo seguro...")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app/requirements.txt"):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Instalar dependencias del proyecto
    run_command("pip install -r app/requirements.txt", "Instalando dependencias del proyecto")
    
    # Configurar herramientas de seguridad
    setup_security_tools()
    
    # Configurar Docker
    setup_docker_environment()
    
    print("\n🎉 ¡Configuración completada exitosamente!")
    print("\nPuedes empezar a desarrollar de forma segura.")

if __name__ == "__main__":
    main()
