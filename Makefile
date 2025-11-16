# Makefile para comandos comunes del proyecto
.PHONY: help setup build test security-check clean deploy

# Variables
DOCKER_IMAGE_NAME = sqli-detector
DOCKER_TAG = latest
COMPOSE_FILE = docker-compose.yml

help: ## Mostrar ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configurar entorno de desarrollo
	@echo "🔧 Configurando entorno de desarrollo..."
	python setup_security.py

install: ## Instalar dependencias
	@echo "📦 Instalando dependencias..."
	pip install -r app/requirements.txt
	pip install bandit safety semgrep pre-commit detect-secrets

security-install: ## Instalar herramientas de seguridad
	@echo "🔒 Instalando herramientas de seguridad..."
	pip install bandit safety semgrep detect-secrets
	pre-commit install

build: ## Construir imagen Docker
	@echo "🐳 Construyendo imagen Docker..."
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) .

build-dev: ## Construir imagen para desarrollo
	@echo "🐳 Construyendo entorno de desarrollo..."
	docker-compose build

up: ## Levantar servicios con Docker Compose
	@echo "🚀 Levantando servicios..."
	docker-compose up -d

down: ## Bajar servicios
	@echo "🔽 Bajando servicios..."
	docker-compose down

logs: ## Ver logs de la aplicación
	docker-compose logs -f app

test: ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	cd app && python -m pytest tests/ -v --cov=. --cov-report=html

test-docker: ## Ejecutar tests en Docker
	@echo "🧪 Ejecutando tests en Docker..."
	docker-compose -f $(COMPOSE_FILE) --profile testing up test-db -d
	docker-compose run --rm app python -m pytest tests/ -v
	docker-compose -f $(COMPOSE_FILE) --profile testing down

security-check: ## Ejecutar análisis de seguridad completo
	@echo "🔍 Ejecutando análisis de seguridad..."
	@echo "▶️  Ejecutando Bandit..."
	bandit -r app/ -f txt
	@echo "▶️  Verificando vulnerabilidades con Safety..."
	safety check
	@echo "▶️  Escaneando secretos..."
	detect-secrets scan --baseline .secrets.baseline --update
	@echo "▶️  Análisis con Semgrep..."
	semgrep --config=p/security-audit --config=p/secrets app/

security-baseline: ## Crear baseline para detección de secretos
	@echo "🔐 Creando baseline para detección de secretos..."
	detect-secrets scan --baseline .secrets.baseline

docker-scan: ## Escanear imagen Docker por vulnerabilidades
	@echo "🔍 Escaneando imagen Docker..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD):/tmp -w /tmp \
		aquasec/trivy image $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)

lint: ## Ejecutar linting del código
	@echo "🧹 Ejecutando linting..."
	cd app && python -m flake8 .
	cd app && python -m black --check .
	cd app && python -m isort --check-only .

format: ## Formatear código
	@echo "✨ Formateando código..."
	cd app && python -m black .
	cd app && python -m isort .

pre-commit: ## Ejecutar pre-commit hooks manualmente
	@echo "🔧 Ejecutando pre-commit hooks..."
	pre-commit run --all-files

clean: ## Limpiar archivos temporales y contenedores
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	docker system prune -f
	docker-compose down --remove-orphans

clean-all: clean ## Limpiar todo incluyendo imágenes Docker
	@echo "🧹 Limpieza completa..."
	docker-compose down --volumes --remove-orphans
	docker rmi $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || true

deploy-staging: ## Deploy a staging
	@echo "🚀 Desplegando a staging..."
	@echo "Implementar comandos específicos de tu plataforma"

deploy-prod: ## Deploy a producción
	@echo "🚀 Desplegando a producción..."
	@echo "Implementar comandos específicos de tu plataforma"

monitor: ## Mostrar logs y métricas
	@echo "📊 Monitoreando aplicación..."
	docker-compose logs -f

backup-db: ## Respaldar base de datos
	@echo "💾 Respaldando base de datos..."
	docker-compose exec db pg_dump -U postgres sqli_detector > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restaurar base de datos (especificar BACKUP_FILE=filename.sql)
	@echo "🔄 Restaurando base de datos..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Especifica el archivo: make restore-db BACKUP_FILE=backup.sql"; \
		exit 1; \
	fi
	docker-compose exec -T db psql -U postgres -d sqli_detector < $(BACKUP_FILE)

dev-setup: install security-install build-dev ## Configuración completa para desarrollo
	@echo "✅ Entorno de desarrollo configurado completamente"

ci-pipeline: security-check test docker-scan ## Pipeline completo de CI (como en GitHub Actions)
	@echo "✅ Pipeline de CI ejecutado exitosamente"