#!/bin/sh
# Script de inicio para Render/Heroku - Crear directorios necesarios y descargar modelo si es necesario

echo "🚀 Iniciando Detector SQLi Backend..."

# Crear directorios necesarios si no existen
echo "📁 Creando directorios..."
mkdir -p uploads
mkdir -p reports
mkdir -p quarantine
mkdir -p audit_logs
mkdir -p config/quarantine
mkdir -p config/audit_logs
mkdir -p core/MODELO_ML

echo "✅ Directorios creados"

# Verificar que DATABASE_URL existe
if [ -z "$DATABASE_URL" ]; then
        echo "⚠️ WARNING: DATABASE_URL no está configurada"
else
        echo "✅ DATABASE_URL detectada"
fi

# Descargar modelo en runtime si no existe (opcional) - configurar MODEL_URL en Render
## If package `app` is copied to /app/app in the container, model directory is inside that package
MODEL_DIR="./app/core/MODELO_ML"
MODEL_FILE="${MODEL_FILE:-model.safetensors}"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

if [ -n "$MODEL_URL" ] && [ ! -f "$MODEL_PATH" ]; then
    echo "⬇️  Modelo no encontrado en $MODEL_PATH, descargando desde MODEL_URL..."
    mkdir -p "$MODEL_DIR"
    # Descargar con Python (usa requests instalado en la imagen)
    python - <<'PY'
import os,sys
import requests

url = os.environ.get('MODEL_URL')
path = os.environ.get('MODEL_PATH', './core/MODELO_ML/model.safetensors')
if not url:
        print('MODEL_URL no definida', file=sys.stderr)
        sys.exit(2)
os.makedirs(os.path.dirname(path), exist_ok=True)
resp = requests.get(url, stream=True)
resp.raise_for_status()
with open(path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                        f.write(chunk)
print('✅ Modelo descargado en', path)
PY
    PY_EXIT=$?
    if [ $PY_EXIT -ne 0 ]; then
        echo "❌ Error descargando el modelo (exit $PY_EXIT)"
        rm -f "$MODEL_PATH"
    fi
else
    if [ -f "$MODEL_PATH" ]; then
        echo "✅ Modelo encontrado en $MODEL_PATH"
    else
        echo "ℹ️ MODEL_URL no configurada y modelo no presente; asegúrate de montar el modelo como volumen o configurar MODEL_URL"
    fi
fi

# Iniciar la aplicación
echo "🎯 Iniciando servidor..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
