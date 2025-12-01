import os
import sys
from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker

# parser ANTLR
from app.core.ANTLR.JavaLexer import JavaLexer
from app.core.ANTLR.JavaParser import JavaParser
from app.core.ANTLR.JavaParserListener import JavaParserListener

import re


class SQLListener(JavaParserListener):
    """
    Listener mejorado para detectar consultas SQL en Java, Spring Boot y MyBatis.
    Extrae cadenas literales y parámetros para análisis de seguridad.
    """
    SQL_METHODS = [
        "createQuery", "createNativeQuery", "prepareStatement", "executeQuery", "executeUpdate"
    ]
    SQL_ANNOTATIONS = ["@Query", "@NamedQuery", "@Select", "@Insert", "@Update", "@Delete"]
    SQL_KEYWORDS = ["select", "insert", "update", "delete"]
    # Precompile frequently-used regex patterns to avoid recompilation on each call
    _KW_ALTERNATION = "|".join(SQL_KEYWORDS)
    _STRING_SQL_RE = re.compile(r'"([^\"]*(' + _KW_ALTERNATION + r')[^\"]*)"', re.IGNORECASE)
    _PARAM_RE = re.compile(r'\+([a-zA-Z0-9_]+)')

    def __init__(self):
        self.queries = []

    def enterExpression(self, ctx: JavaParser.ExpressionContext):
        text = ctx.getText()
        # Detecta métodos relevantes
        for method in self.SQL_METHODS:
            if method in text:
                sql_match = self._STRING_SQL_RE.search(text)
                if sql_match:
                    sql_query = sql_match.group(1)
                    params = self._PARAM_RE.findall(text)
                    self.queries.append({
                        "type": "method",
                        "method": method,
                        "sql": sql_query,
                        "params": params,
                        "line": ctx.start.line
                    })

    def enterAnnotation(self, ctx: JavaParser.AnnotationContext):
        text = ctx.getText()
        for annotation in self.SQL_ANNOTATIONS:
            if annotation in text:
                # Extrae la consulta SQL dentro de la anotación
                sql_match = self._STRING_SQL_RE.search(text)
                if sql_match:
                    sql_query = sql_match.group(1)
                    # Detecta si la consulta usa parámetros seguros (#{param}) en MyBatis
                    safe_params = re.findall(r'\#\{[a-zA-Z0-9_]+\}', sql_query)
                    unsafe_params = re.findall(r'\$\{[a-zA-Z0-9_]+\}', sql_query)
                    self.queries.append({
                        "type": "annotation",
                        "annotation": annotation,
                        "sql": sql_query,
                        "safe_params": safe_params,
                        "unsafe_params": unsafe_params,
                        "line": ctx.start.line
                    })

def parse_xml_mybatis(file_path):
    """
    Parsea archivos XML de MyBatis y detecta consultas SQL y parámetros inseguros.
    """
    results = []
    try:
        with open(file_path, encoding="utf-8") as f:
            contenido = f.read()
            # Busca etiquetas <select>, <insert>, <update>, <delete>
            for tag in ["select", "insert", "update", "delete"]:
                for match in re.finditer(rf'<{tag}[^>]*>([\s\S]*?)</{tag}>', contenido, re.IGNORECASE):
                    sql_query = match.group(1).strip()
                    safe_params = re.findall(r'\#\{[a-zA-Z0-9_]+\}', sql_query)
                    unsafe_params = re.findall(r'\$\{[a-zA-Z0-9_]+\}', sql_query)
                    results.append({
                        "type": "xml",
                        "tag": tag,
                        "sql": sql_query,
                        "safe_params": safe_params,
                        "unsafe_params": unsafe_params
                    })
    except Exception as e:
        print(f"[ERROR] No se pudo parsear XML MyBatis {file_path}: {e}", archivo =sys.stderr)
    return results


def parse_file(file_path: str):
    """
    Parsea un archivo Java con ANTLR y búsqueda por texto plano para anotaciones.
    Devuelve las consultas encontradas.
    """
    # ANTLR analysis
    input_stream = FileStream(file_path, encoding="utf-8")
    lexer = JavaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = JavaParser(stream)

    tree = parser.compilationUnit()
    walker = ParseTreeWalker()

    listener = SQLListener()
    walker.walk(listener, tree)

    queries = listener.queries.copy()

    # Plain text analysis for annotations (detecta value=..., @Query("..."), y concatenaciones)
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
            # Precompiled patterns for annotation/plain-text extraction (reuse SQLListener keyword alternation)
            pattern_value = re.compile(r'@(Query|NamedQuery|Select|Insert|Update|Delete)\s*\(\s*value\s*=\s*"([^\"]*(' + SQLListener._KW_ALTERNATION + r')[^\"]*)"', re.IGNORECASE)
            pattern_direct = re.compile(r'@(Query|NamedQuery|Select|Insert|Update|Delete)\s*\(\s*"([^\"]*(' + SQLListener._KW_ALTERNATION + r')[^\"]*)"', re.IGNORECASE)
            pattern_concat = re.compile(r'@(Query|NamedQuery|Select|Insert|Update|Delete)\s*\((.*)', re.IGNORECASE)
            # Detecta @Query(value = "...") y @Query("...")
            for idx, line in enumerate(lines):
                # value="..."
                for match in pattern_value.finditer(line):
                    annotation = f"@{match.group(1)}"
                    sql_query = match.group(2)
                    signature = line.rstrip()
                    if idx + 1 < len(lines):
                        signature += "\n" + lines[idx + 1].rstrip()
                    safe_params = re.findall(r'\#\{[a-zA-Z0-9_]+\}', sql_query)
                    unsafe_params = re.findall(r'\$\{[a-zA-Z0-9_]+\}', sql_query)
                    queries.append({
                        "type": "annotation",
                        "annotation": annotation,
                        "signature": signature,
                        "sql": sql_query,
                        "safe_params": safe_params,
                        "unsafe_params": unsafe_params,
                        "line": idx + 1
                    })
                # @Query("...")
                for match in pattern_direct.finditer(line):
                    annotation = f"@{match.group(1)}"
                    sql_query = match.group(2)
                    signature = line.rstrip()
                    if idx + 1 < len(lines):
                        signature += "\n" + lines[idx + 1].rstrip()
                    safe_params = re.findall(r'\#\{[a-zA-Z0-9_]+\}', sql_query)
                    unsafe_params = re.findall(r'\$\{[a-zA-Z0-9_]+\}', sql_query)
                    queries.append({
                        "type": "annotation",
                        "annotation": annotation,
                        "signature": signature,
                        "sql": sql_query,
                        "safe_params": safe_params,
                        "unsafe_params": unsafe_params,
                        "line": idx + 1
                    })
                # @Query con concatenación de strings
                if pattern_concat.match(line):
                    # Busca la línea siguiente para la firma completa
                    signature = line.rstrip()
                    if idx + 1 < len(lines):
                        signature += "\n" + lines[idx + 1].rstrip()
                    # Extrae todo el contenido entre paréntesis
                    concat_content = pattern_concat.match(line).group(2)
                    # Busca todos los fragmentos de string
                    sql_fragments = re.findall(r'"([^"]*)"', concat_content)
                    sql_query = "".join(sql_fragments)
                    # Si la consulta contiene palabras clave SQL, la agregamos
                    if any(kw in sql_query.lower() for kw in SQLListener.SQL_KEYWORDS):
                        safe_params = re.findall(r'\#\{[a-zA-Z0-9_]+\}', sql_query)
                        unsafe_params = re.findall(r'\$\{[a-zA-Z0-9_]+\}', sql_query)
                        queries.append({
                            "type": "annotation",
                            "annotation": "@Query",
                            "signature": signature,
                            "sql": sql_query,
                            "safe_params": safe_params,
                            "unsafe_params": unsafe_params,
                            "line": idx + 1
                        })
    except Exception as e:
        print(f"[ERROR] No se pudo analizar por texto plano {file_path}: {e}", archivo =sys.stderr)

    return queries



def parse_project(project_id: str, project_path: str = "uploads/"):
    """
    Recorre todos los archivos Java y XML de un proyecto
    y retorna las consultas encontradas, incluyendo el nombre del proyecto en cada resultado.
    """
    project_dir = os.path.join(project_path, project_id)
    results = []

    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".java"):
                java_file = os.path.join(root, file)
                print(f"[DEBUG] Procesando archivo Java: {java_file}")
                try:
                    queries = parse_file(java_file)
                    print(f"[DEBUG] Consultas encontradas: {queries}")
                    # Agregar información del archivo a cada consulta
                    for query in queries:
                        query["file"] = java_file
                    if queries:
                        results.append({
                            "project": project_id,
                            "file": java_file,
                            "queries": queries
                        })
                except Exception as e:
                    print(f"[ERROR] No se pudo parsear {java_file}: {e}", archivo =sys.stderr)
            elif file.endswith(".xml"):
                xml_file = os.path.join(root, file)
                print(f"[DEBUG] Procesando archivo XML: {xml_file}")
                xml_queries = parse_xml_mybatis(xml_file)
                print(f"[DEBUG] Consultas XML encontradas: {xml_queries}")
                # Agregar información del archivo a cada consulta XML
                for query in xml_queries:
                    query["file"] = xml_file
                if xml_queries:
                    results.append({
                        "project": project_id,
                        "file": xml_file,
                        "queries": xml_queries
                    })

    return results
