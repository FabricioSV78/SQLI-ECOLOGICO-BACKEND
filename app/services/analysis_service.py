from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.vulnerability import Vulnerability
from app.models.project_file import ProjectFile
from fastapi import HTTPException
import os

def obtener_resultados_analisis_proyecto(proyecto_id: str, usuario_id: int, db: Session):
    """
    Obtiene los resultados de análisis de un proyecto desde la base de datos.
    Incluye archivos vulnerables, código del archivo, fragmentos vulnerables y predicciones.
    """
    from app.models.project import Proyecto
    
    # Buscar el proyecto
    if proyecto_id.isdigit():
        proyecto = db.query(Proyecto).filter(Proyecto.id == int(proyecto_id), Proyecto.usuario_id == usuario_id).first()
    else:
        proyecto = db.query(Proyecto).filter(Proyecto.nombre == proyecto_id, Proyecto.usuario_id == usuario_id).first()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado para este usuario.")
    
    # Obtener vulnerabilidades y archivos asociados
    from app.models.vulnerability import Vulnerabilidad
    vulnerabilidades = db.query(Vulnerabilidad).filter(Vulnerabilidad.proyecto_id == proyecto.id).all()
    
    if not vulnerabilidades:
        return {
            "proyecto_id": proyecto_id,
            "nombre_proyecto": proyecto.nombre,
            "mensaje": "No se encontraron vulnerabilidades en este proyecto.",
            "archivos_vulnerables": []
        }
    
    # Agrupar vulnerabilidades por archivo
    datos_archivos = {}
    for vuln in vulnerabilidades:
        ruta_archivo = vuln.archivo
        if ruta_archivo not in datos_archivos:
            datos_archivos[ruta_archivo] = {
                "ruta_archivo": ruta_archivo,
                "nombre_archivo": os.path.basename(ruta_archivo),
                "vulnerabilidades": [],
                "contenido_archivo": None
            }
        
        # Agregar vulnerabilidad
        datos_archivos[ruta_archivo]["vulnerabilidades"].append({
            "id": vuln.id,
            "linea": vuln.linea,
            "fragmento_vulnerable": vuln.consulta,
            "prediccion": vuln.prediccion,
            "fecha_creacion": vuln.fecha_creacion
        })
    
    # Obtener el contenido de cada archivo vulnerable desde la base de datos
    from app.models.project_file import ArchivoProyecto
    for ruta_archivo, datos_archivo in datos_archivos.items():
        # Buscar el archivo en ArchivoProyecto
        archivo_proyecto = db.query(ArchivoProyecto).filter(
            ArchivoProyecto.proyecto_id == proyecto.id,
            ArchivoProyecto.ruta_archivo == ruta_archivo
        ).first()
        
        if archivo_proyecto and archivo_proyecto.contenido:
            datos_archivo["contenido_archivo"] = archivo_proyecto.contenido
        else:
            # Fallback: intentar leer desde el sistema de archivos
            try:
                if os.path.exists(ruta_archivo):
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        datos_archivo["contenido_archivo"] = f.read()
                else:
                    datos_archivo["contenido_archivo"] = "Archivo no encontrado ni en la base de datos ni en el sistema de archivos."
            except Exception as e:
                datos_archivo["contenido_archivo"] = f"Error al leer el archivo: {str(e)}"
    
    return {
        "proyecto_id": proyecto_id,
        "nombre_proyecto": proyecto.nombre,
        "id_bd_proyecto": proyecto.id,
        "total_archivos_vulnerables": len(datos_archivos),
        "total_vulnerabilidades": len(vulnerabilidades),
        "archivos_vulnerables": list(datos_archivos.values())
    }

def obtener_resumen_vulnerabilidades_proyecto(proyecto_id: str, usuario_id: int, db: Session):
    """
    Obtiene un resumen de vulnerabilidades de un proyecto.
    """
    from app.models.project import Proyecto
    from app.models.vulnerability import Vulnerabilidad 
    from app.models.project_file import ArchivoProyecto
    
    # Buscar el proyecto
    if proyecto_id.isdigit():
        proyecto = db.query(Proyecto).filter(Proyecto.id == int(proyecto_id), Proyecto.usuario_id == usuario_id).first()
    else:
        proyecto = db.query(Proyecto).filter(Proyecto.nombre == proyecto_id, Proyecto.usuario_id == usuario_id).first()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado para este usuario.")
    
    # Contar vulnerabilidades
    total_vulnerabilidades = db.query(Vulnerabilidad).filter(Vulnerabilidad.proyecto_id == proyecto.id).count()
    total_archivos = db.query(ArchivoProyecto).filter(ArchivoProyecto.proyecto_id == proyecto.id).count()
    
    return {
        "proyecto_id": proyecto_id,
        "nombre_proyecto": proyecto.nombre,
        "id_bd_proyecto": proyecto.id,
        "total_vulnerabilidades": total_vulnerabilidades,
        "total_archivos_vulnerables": total_archivos,
        "fecha_creacion": proyecto.fecha_creacion
    }

# Funciones de compatibilidad
def get_project_analysis_results(project_id: str, user_id: int, db: Session):
    return obtener_resultados_analisis_proyecto(project_id, user_id, db)

def get_project_vulnerability_summary(project_id: str, user_id: int, db: Session):
    return obtener_resumen_vulnerabilidades_proyecto(project_id, user_id, db)
