from app.core import grammar, ml_model
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.vulnerability import Vulnerability
from fastapi import HTTPException
import re
import os

def run_analysis(project_id: str, project_path: str = "uploads/", db: Session = None, user_id: int = None):
    """
    Ejecuta el pipeline de análisis completo:
    1. Parseo del proyecto con ANTLR (grammar.py)
    2. Clasificación de las consultas con ML (ml_model.py)
    """

    # 1. Extraer consultas SQL usando grammar
    parsed_queries = grammar.parse_project(project_id, project_path)

    if not parsed_queries:
        return {
            "project_id": project_id,
            "message": "No se encontraron consultas SQL en el proyecto.",
            "results": []
        }

    # 2. Clasificar consultas con ML
    classified_results = ml_model.analyze_code(parsed_queries)

    # 3. Análisis de flujo de datos básico
    def is_vulnerable_source(signature, sql, params):
        """
        Análisis avanzado de fuente vulnerable:
        - Detecta patrones comunes de entrada insegura en la firma y método.
        - Detecta concatenaciones directas y propagación de variables.
        - Analiza si los parámetros del método/controlador se usan en la consulta.
        - Devuelve detalles de variables inseguras detectadas.
        """
        resultado = {
            "patrones": [],
            "concatenacion": False,
            "parametros_inseguros": [],
            "usados_en_sql": []
        }
        patrones = ["request.", "input", "param", "getParameter", "@RequestParam", "@PathVariable"]
        for p in patrones:
            if p in signature:
                resultado["patrones"].append(p)
        # Concatenación directa
        if "+" in signature or "+" in sql:
            resultado["concatenacion"] = True
        # Parámetros del método
        metodo_match = re.search(r'(\w+)\s*\(([^)]*)\)', signature)
        if metodo_match:
            params_firma = metodo_match.group(2)
            param_names = re.findall(r'(\w+)', params_firma)
            for param in param_names:
                if param.lower() in ["username", "user", "input", "param", "name"]:
                    resultado["parametros_inseguros"].append(param)
                # ¿Se usa en la consulta?
                if param in sql or param in params:
                    resultado["usados_en_sql"].append(param)
        # Parámetros detectados en la consulta
        for param in params:
            if param.lower() in ["username", "user", "input", "param", "name", "id"]:
                resultado["parametros_inseguros"].append(param)
        # Si hay algún hallazgo, es vulnerable
        resultado["es_vulnerable"] = bool(resultado["patrones"] or resultado["concatenacion"] or resultado["parametros_inseguros"])
        return resultado

    # Solo analizar fuente vulnerable en las consultas clasificadas como vulnerables
    from app.core.flow_graph import build_graph
    grafo_vulnerabilidades = None
    vulnerables = classified_results.get("vulnerable", [])
    for consulta in vulnerables:
        signature = consulta.get("signature") or consulta.get("sql", "")
        sql = consulta.get("sql", "")
        params = consulta.get("params", [])
        consulta["fuente_vulnerable"] = is_vulnerable_source(signature, sql, params)

    # Si hay vulnerabilidades, genera el grafo de flujo
    if vulnerables:
        grafo_vulnerabilidades = build_graph(vulnerables)
        
        # Guardar vulnerabilidades en BD si se proporciona sesión de BD
        if db and user_id:
            # Buscar el proyecto en la BD
            if project_id.isdigit():
                project = db.query(Project).filter(Project.id == int(project_id), Project.user_id == user_id).first()
            else:
                project = db.query(Project).filter(Project.name == project_id, Project.user_id == user_id).first()
            
            if project:
                # Guardar solo archivos que contienen vulnerabilidades
                archivos_con_vulnerabilidades = set()
                
                for consulta in vulnerables:
                    file_path = consulta.get('file', '')
                    if file_path:
                        archivos_con_vulnerabilidades.add(file_path)
                        
                        # Guardar la vulnerabilidad
                        vulnerability = Vulnerability(
                            project_id=project.id,
                            file=file_path,
                            line=consulta.get('line', 0),
                            query=consulta.get('sql') or consulta.get('signature', ''),
                            prediction='vulnerable'
                        )
                        db.add(vulnerability)
                
                # Guardar archivos que contienen vulnerabilidades (si no existen ya)
                for file_path in archivos_con_vulnerabilidades:
                    existing_file = db.query(ProjectFile).filter(
                        ProjectFile.project_id == project.id,
                        ProjectFile.filepath == file_path
                    ).first()
                    
                    if not existing_file:
                        filename = os.path.basename(file_path)
                        
                        # Leer el contenido del archivo
                        file_content = ""
                        try:
                            if os.path.exists(file_path):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                        except Exception as e:
                            file_content = f"Error al leer el archivo: {str(e)}"
                        
                        project_file = ProjectFile(
                            project_id=project.id,
                            filename=filename,
                            filepath=file_path,
                            content=file_content
                        )
                        db.add(project_file)
                
                # Commit de todas las operaciones
                db.commit()

    return {
        "project_id": project_id,
        "message": f"Se analizaron {len(classified_results)} consultas SQL.",
        "results": classified_results,
        "flow_graph": grafo_vulnerabilidades
    }
