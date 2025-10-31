from app.config.init_db import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Routers
from app.api import analysis, upload, report, auth

app = FastAPI(
    title="Detector SQLi Backend",
    description="API para detección de inyecciones SQL en proyectos Java Spring Boot",
    version="1.0.0",
)

# Configuración de CORS (ajústalo según tu frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción reemplaza con el dominio de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(report.router)

@app.get("/")
def root():
    return {"message": "API Detector SQLi funcionando correctamente"}
