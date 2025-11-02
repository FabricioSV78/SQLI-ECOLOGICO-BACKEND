import json
import os
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


def get_report(project_id: str):
    """
    Devuelve el reporte generado.
    """
    report_path = os.path.join(settings.REPORTS_DIR, f"{project_id}_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
