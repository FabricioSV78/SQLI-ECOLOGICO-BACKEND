# Multi-stage build para optimizar la imagen
FROM python:3.11-slim AS builder

# Variables de entorno para evitar caches innecesarios
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar herramientas de build solo en la etapa builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc6-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Copiar requirements-prod e instalar en un prefijo /install para copiar solo los paquetes necesarios
COPY app/requirements-prod.txt ./
RUN pip install --prefix=/install -r requirements-prod.txt

########################################
## Runtime stage (imagen final pequeña)
########################################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar solo certificados necesarios (no build tools) y curl para descargar modelo si es necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar los paquetes instalados desde builder
COPY --from=builder /install /usr/local

# Crear usuario no privilegiado
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copiar el código de la aplicación (los modelos grandes deberían estar en .dockerignore)
COPY app/ .

# Hacer ejecutable el script de inicio y ajustar permisos
RUN chmod +x start.sh && chown -R appuser:appuser /app

USER appuser

# Exponer puerto (Render/Heroku usa la variable PORT)
EXPOSE 8000

# Health check (usa requests instalado en los paquetes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando por defecto - Usar el script de inicio
CMD ["./start.sh"]