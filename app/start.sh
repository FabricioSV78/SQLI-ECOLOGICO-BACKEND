#!/bin/bash
# Script de inicio para Railway - Crear directorios necesarios

echo "🚀 Iniciando Detector SQLi Backend..."

# Crear directorios necesarios si no existen
echo "📁 Creando directorios..."
mkdir -p uploads
mkdir -p reports
mkdir -p quarantine
mkdir -p audit_logs
mkdir -p config/quarantine
mkdir -p config/audit_logs

echo "✅ Directorios creados"

# Verificar que DATABASE_URL existe
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️ WARNING: DATABASE_URL no está configurada"
else
    echo "✅ DATABASE_URL detectada"
fi

# Iniciar la aplicación
echo "🎯 Iniciando servidor..."
# Ejecutar uvicorn apuntando al módulo de paquete `app` para que los imports funcionen
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
