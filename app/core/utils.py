def contar_lineas_codigo(ruta: str) -> int:
    """Cuenta las líneas de código en un archivo."""
    with open(ruta, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def es_archivo_java(nombre_archivo: str) -> bool:
    """Verifica si un archivo es de tipo Java."""
    return nombre_archivo.endswith(".java")

# Funciones de compatibilidad
def count_lines_of_code(path: str) -> int:
    return contar_lineas_codigo(path)

def is_java_file(filename: str) -> bool:
    return es_archivo_java(filename)
