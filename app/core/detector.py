from app.core import grammar, ml_model
import logging
from sqlalchemy.orm import Session
from app.models.project import Proyecto
from app.models.project_file import ArchivoProyecto  
from app.models.vulnerability import Vulnerabilidad
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
        patrones = {"request.", "input", "param", "getParameter", "@RequestParam", "@PathVariable"}
        # use set membership for faster checks when many patterns
        for p in patrones:
            if p in signature:
                resultado["patrones"].append(p)
        # Concatenación directa
        if "+" in signature or "+" in sql:
            resultado["concatenacion"] = True
        # Parámetros del método
        metodo_match = re.search(r'(\w+)\s*\(([^)]*)\)', signature)
        params_set = set(params or [])
        if metodo_match:
            params_firma = metodo_match.group(2)
            param_names = re.findall(r'(\w+)', params_firma)
            for param in param_names:
                if param.lower() in {"username", "user", "input", "param", "name"}:
                    resultado["parametros_inseguros"].append(param)
                # ¿Se usa en la consulta?
                if param in sql or param in params_set:
                    resultado["usados_en_sql"].append(param)
        # Parámetros detectados en la consulta
        for param in params:
            if param.lower() in {"username", "user", "input", "param", "name", "id"}:
                resultado["parametros_inseguros"].append(param)
        # Si hay algún hallazgo, es vulnerable
        resultado["es_vulnerable"] = bool(resultado["patrones"] or resultado["concatenacion"] or resultado["parametros_inseguros"])
        return resultado

    # Solo analizar fuente vulnerable en las consultas clasificadas como vulnerables
    from app.core.flow_graph import build_graph
    grafo_vulnerabilidades = None
    vulnerables = classified_results.get("vulnerable", [])

    # Detectar y consolidar entradas duplicadas (mismo archivo, misma línea y misma consulta)
    logger = logging.getLogger(__name__)
    dedup_map = {}
    duplicates_found = []

    def _norm_sql(s: str) -> str:
        return " ".join((s or "").split())

    for consulta in vulnerables:
        file_path = consulta.get('file', '')
        line_no = int(consulta.get('line', 0) or 0)
        sql_text = consulta.get('sql') or consulta.get('signature') or ""
        key = (file_path, line_no, _norm_sql(sql_text))

        if key not in dedup_map:
            # store original consulta and list of duplicates
            dedup_map[key] = {
                'representative': consulta,
                'variants': [consulta]
            }
        else:
            dedup_map[key]['variants'].append(consulta)

    # Build final vulnerables list and annotate fuente_vulnerable; log duplicates
    consolidated = []
    for key, group in dedup_map.items():
        rep = group['representative']
        variants = group['variants']
        if len(variants) > 1:
            # Log details for investigation: same file/line but multiple detections
            try:
                logger.info(f"[DEDUP] Múltiples detecciones en {key[0]}:{key[1]} -> {len(variants)} entradas")
                for v in variants:
                    logger.debug(f"[DEDUP] variante: pred={v.get('prediccion')} sql={_norm_sql(v.get('sql') or v.get('signature') or '')}")
            except Exception:
                pass
            duplicates_found.append({'file': key[0], 'line': key[1], 'count': len(variants)})

        # Use representative for further analysis
        rep_sql = rep.get('signature') or rep.get('sql', '')
        params = rep.get('params', [])
        rep['fuente_vulnerable'] = is_vulnerable_source(rep.get('signature') or rep.get('sql', ''), rep_sql, params)
        consolidated.append(rep)

    vulnerables = consolidated

    # Si hay vulnerabilidades, genera el grafo de flujo
    if vulnerables:
        grafo_vulnerabilidades = build_graph(vulnerables)
        
        # Guardar vulnerabilidades en BD si se proporciona sesión de BD
        if db and user_id:
            # Buscar el proyecto en la BD
            if project_id.isdigit():
                proyecto = db.query(Proyecto).filter(Proyecto.id == int(project_id), Proyecto.usuario_id == user_id).first()
            else:
                proyecto = db.query(Proyecto).filter(Proyecto.nombre == project_id, Proyecto.usuario_id == user_id).first()
            
            if proyecto:
                # Guardar solo archivos que contienen vulnerabilidades
                archivos_con_vulnerabilidades = set()
                
                for consulta in vulnerables:
                    ruta_archivo = consulta.get('file', '')
                    if ruta_archivo:
                        archivos_con_vulnerabilidades.add(ruta_archivo)

                        # Preparar datos de la vulnerabilidad
                        linea_num = int(consulta.get('line', 0) or 0)
                        consulta_text = consulta.get('sql') or consulta.get('signature', '')

                        # Evitar insertar duplicados en la BD (mismo proyecto, mismo archivo, misma línea y misma consulta)
                        existing_vul = db.query(Vulnerabilidad).filter(
                            Vulnerabilidad.proyecto_id == proyecto.id,
                            Vulnerabilidad.archivo == ruta_archivo,
                            Vulnerabilidad.linea == linea_num,
                            Vulnerabilidad.consulta == consulta_text
                        ).first()

                        if existing_vul:
                            # Ya existe la misma vulnerabilidad registrada; saltar
                            logger = logging.getLogger(__name__)
                            try:
                                logger.debug(f"[DB] Vulnerabilidad existente saltada: {ruta_archivo}:{linea_num} - {consulta_text[:80]}")
                            except Exception:
                                pass
                        else:
                            vulnerability = Vulnerabilidad(
                                proyecto_id=proyecto.id,
                                archivo=ruta_archivo,
                                linea=linea_num,
                                consulta=consulta_text,
                                prediccion='vulnerable'
                            )
                            db.add(vulnerability)
                
                # Guardar archivos que contienen vulnerabilidades (si no existen ya)
                for file_path in archivos_con_vulnerabilidades:
                    existing_file = db.query(ArchivoProyecto).filter(
                        ArchivoProyecto.proyecto_id == proyecto.id,
                        ArchivoProyecto.ruta_archivo == file_path
                    ).first()
                    
                    if not existing_file:
                        nombre_archivo = os.path.basename(file_path)
                        
                        # Leer el contenido del archivo
                        file_content = ""
                        try:
                            if os.path.exists(file_path):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                        except Exception as e:
                            file_content = f"Error al leer el archivo: {str(e)}"
                        
                        project_file = ArchivoProyecto(
                            proyecto_id=proyecto.id,
                            nombre_archivo=nombre_archivo,
                            ruta_archivo=file_path,
                            contenido=file_content
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
