import json
import os
import time
import shutil
from typing import List
from app.config.config import settings  #  Importamos configuración centralizada

def generar_reporte(project_id: str, results: dict):
    """
    Genera un archivo JSON con los resultados del análisis.
    """
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(settings.REPORTS_DIR, f"{project_id}_report.json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    return report_path


def get_report(project_id: str, db=None):
    """
    Devuelve el reporte generado.
    """
    report_path = os.path.join(settings.REPORTS_DIR, f"{project_id}_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Si no existe archivo en disco, intentar armar reporte desde la BD
    if db is not None:
        try:
            # Importar modelos localmente para evitar import cycles
            from app.models.project import Proyecto
            from app.models.vulnerability import Vulnerabilidad
            from app.models.project_file import ArchivoProyecto

            # Buscar proyecto por id o nombre
            proyecto = None
            if project_id.isdigit():
                proyecto = db.query(Proyecto).filter(Proyecto.id == int(project_id)).first()
            if not proyecto:
                proyecto = db.query(Proyecto).filter(Proyecto.nombre == project_id).first()

            if not proyecto:
                return None

            # Vulnerabilidades
            vulns = []
            for v in proyecto.vulnerabilidades:
                vulns.append({
                    "id": v.id,
                    "file": v.archivo,
                    "line": v.linea,
                    "query": v.consulta,
                    "prediction": v.prediccion,
                    "created_at": v.fecha_creacion.isoformat() if v.fecha_creacion else None
                })

            # Archivos relevantes (solo los guardados en la BD)
            files = []
            for f in proyecto.archivos:
                files.append({
                    "id": f.id,
                    "filename": f.nombre_archivo,
                    "path": f.ruta_archivo,
                    "content": f.contenido
                })

            report = {
                "project": {
                    "id": proyecto.id,
                    "name": proyecto.nombre,
                    "owner_id": proyecto.usuario_id,
                    "created_at": proyecto.fecha_creacion.isoformat() if proyecto.fecha_creacion else None
                },
                "vulnerabilities": vulns,
                "files": files,
                "generated_from": "database"
            }
            return report
        except Exception:
            return None

    return None


def delete_report(project_id: str) -> bool:
    """
    Elimina el archivo de reporte JSON asociado a `project_id`.
    Devuelve True si se eliminó, False si no existía.
    """
    report_path = os.path.join(settings.REPORTS_DIR, f"{project_id}_report.json")
    if os.path.exists(report_path):
        try:
            os.remove(report_path)
            return True
        except Exception:
            return False
    return False


def cleanup_reports_older_than(days: int = None) -> List[str]:
    """
    Elimina archivos de `settings.REPORTS_DIR` más antiguos que `days`.
    Si days es None, usa settings.REPORT_RETENTION_DAYS.
    Devuelve la lista de rutas eliminadas.
    """
    removed = []
    if days is None:
        days = settings.REPORT_RETENTION_DAYS

    cutoff = time.time() - days * 24 * 60 * 60
    reports_dir = settings.REPORTS_DIR
    if not os.path.isdir(reports_dir):
        return removed

    for fname in os.listdir(reports_dir):
        fpath = os.path.join(reports_dir, fname)
        try:
            # Si es archivo o directorio, comprobar su mtime
            mtime = os.path.getmtime(fpath)
            if mtime < cutoff:
                # Eliminar archivo o directorio
                if os.path.isdir(fpath):
                    shutil.rmtree(fpath)
                else:
                    os.remove(fpath)
                removed.append(fpath)
        except Exception:
            # Ignorar errores individuales y continuar
            continue

    return removed
