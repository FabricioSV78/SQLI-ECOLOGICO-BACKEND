#!/bin/bash
# Script de inicio para Railway - Crear directorios necesarios

echo "🚀 Iniciando Detector SQLi Backend..."

# Crear directorios necesarios si no existen
echo "📁 Creando directorios..."
mkdir -p /workspace/app/uploads
mkdir -p /workspace/app/reports
mkdir -p /workspace/app/quarantine
mkdir -p /workspace/app/audit_logs
mkdir -p /workspace/app/config/quarantine
mkdir -p /workspace/app/config/audit_logs

echo "✅ Directorios creados"

# Verificar que DATABASE_URL existe
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️ WARNING: DATABASE_URL no está configurada"
else
    echo "✅ DATABASE_URL detectada"
fi

# Iniciar la aplicación
echo "🎯 Iniciando servidor..."
cd /workspace/app
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
