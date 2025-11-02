# Pipeline CI/CD con SCA/SAST y Escaneo Docker - S-RNF5

Este documento describe la implementación del pipeline CI/CD con análisis de seguridad automático para el proyecto Detector SQLi Backend.

## 🎯 Objetivos del Pipeline

- **SAST (Static Application Security Testing)**: Análisis estático de código para detectar vulnerabilidades
- **SCA (Software Composition Analysis)**: Análisis de dependencias y componentes de terceros
- **Escaneo de Imágenes Docker**: Verificación de vulnerabilidades en contenedores
- **Automatización completa**: Desde commit hasta deploy con validaciones de seguridad

## 🔧 Herramientas Integradas

### Análisis Estático (SAST)
- **Bandit**: Security linter específico para Python
- **Semgrep**: Análisis estático avanzado con reglas de seguridad
- **Safety**: Verificación de vulnerabilidades conocidas en dependencias Python

### Análisis de Composición (SCA)
- **Snyk**: Análisis de vulnerabilidades en dependencias
- **OWASP Dependency Check**: Identificación de CVEs en componentes
- **pip-audit**: Auditoría específica de paquetes Python

### Escaneo de Contenedores
- **Trivy**: Scanner de vulnerabilidades para imágenes Docker
- **Grype**: Análisis de vulnerabilidades en imágenes de contenedor
- **Hadolint**: Linter para Dockerfiles

## 🚀 Flujo del Pipeline

```mermaid
graph TD
    A[Push/PR] --> B[SAST Analysis]
    B --> C[SCA Analysis]
    C --> D[Unit Tests]
    D --> E[Build Docker Image]
    E --> F[Docker Security Scan]
    F --> G[Deploy to Staging]
    G --> H[Integration Tests]
    H --> I[Deploy to Production]
```

### Etapas del Pipeline

1. **SAST Analysis**
   - Escaneo con Bandit, Semgrep y Safety
   - Generación de reportes SARIF
   - Upload automático a GitHub Security tab

2. **SCA Analysis**
   - Verificación con Snyk y OWASP Dependency Check
   - Análisis de licencias y compliance
   - Alertas automáticas por vulnerabilidades críticas

3. **Testing**
   - Tests unitarios con cobertura
   - Tests de integración con base de datos
   - Validación de APIs y endpoints

4. **Docker Build & Scan**
   - Build optimizado con multi-stage
   - Escaneo con Trivy y Grype
   - Validación de Dockerfile con Hadolint

5. **Deployment**
   - Deploy automático en branch main
   - Health checks post-deployment
   - Rollback automático en caso de fallas

## 📋 Configuración de Secrets

Configura los siguientes secrets en GitHub:

```bash
# Secrets requeridos en GitHub Repository Settings > Secrets
SNYK_TOKEN=your_snyk_token_here
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
DEPLOY_SSH_KEY=your_deployment_ssh_key
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your_app_secret_key
```

## 🔒 Estándares de Seguridad

### Niveles de Severidad
- **CRITICAL**: Bloquea el pipeline
- **HIGH**: Genera alerta pero permite continuar
- **MEDIUM**: Se registra para revisión
- **LOW**: Solo se documenta

### Umbrales de Seguridad
```yaml
# Configuración de umbrales
CVSS_THRESHOLD: 7.0
BANDIT_SEVERITY: medium
TRIVY_SEVERITY: HIGH,CRITICAL
SEMGREP_SEVERITY: ERROR
```

## 🛠️ Uso Local

### Configuración inicial
```bash
# Configurar entorno completo
make dev-setup

# Solo herramientas de seguridad
make security-install
```

### Comandos principales
```bash
# Análisis de seguridad completo
make security-check

# Tests con cobertura
make test

# Build y escaneo de imagen Docker
make build && make docker-scan

# Pipeline completo (como CI)
make ci-pipeline
```

### Pre-commit hooks
```bash
# Instalar hooks (se ejecuta automático en commits)
pre-commit install

# Ejecutar manualmente
make pre-commit
```

## 📊 Monitoreo y Reportes

### Dashboards
- **GitHub Security Tab**: Vulnerabilidades y alertas
- **Actions Tab**: Estado de pipelines
- **Codecov**: Cobertura de tests
- **Dependabot**: Actualizaciones de seguridad

### Reportes Generados
- `bandit-report.json`: Resultados de análisis Bandit
- `safety-report.json`: Vulnerabilidades en dependencias
- `trivy-results.sarif`: Escaneo de imagen Docker
- `coverage.xml`: Cobertura de tests
- `semgrep.sarif`: Análisis estático con Semgrep

## 🔧 Personalización

### Agregar nuevas herramientas
1. Modificar `.github/workflows/ci-cd-security.yml`
2. Actualizar `setup_security.py`
3. Añadir configuración en `Makefile`
4. Documentar en este README

### Configurar notificaciones
```yaml
# En el workflow de GitHub Actions
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🚨 Resolución de Problemas

### Errores comunes
1. **Falsos positivos de Bandit**: Configurar `.bandit` para skip específicos
2. **Dependencias desactualizadas**: Usar Dependabot para updates automáticos
3. **Vulnerabilidades en imagen base**: Actualizar FROM en Dockerfile
4. **Tests fallando en CI**: Verificar variables de entorno y servicios

### Debugging
```bash
# Verificar configuración local
make security-check

# Logs detallados del pipeline
# Ver en GitHub Actions > Workflow run > Job logs

# Verificar imagen Docker localmente
docker run --rm -it sqli-detector:latest /bin/bash
```

## 📈 Métricas y KPIs

- **Tiempo promedio de pipeline**: < 10 minutos
- **Cobertura de tests**: > 80%
- **Vulnerabilidades críticas**: 0 permitidas
- **Tiempo de resolución de alertas**: < 24 horas

## 🔄 Mantenimiento

### Actualizaciones regulares
- Herramientas de seguridad: Mensual
- Dependencias: Semanal (Dependabot)
- Imagen base Docker: Cada nueva versión LTS
- Revisión de configuración: Trimestral

### Auditorías
- Revisión de logs de seguridad: Semanal
- Análisis de métricas: Mensual
- Evaluación de efectividad: Trimestral