from app.core.detector import run_analysis
from app.services.visualizar_grafo_service import visualizar_grafo
import json

# Ejecuta el pipeline completo sobre el proyecto de prueba
resultado = run_analysis('springboot-sqli-jpa', 'pro/')
flow_graph = resultado.get('flow_graph')
if flow_graph:
    visualizar_grafo(flow_graph)
# Imprime el resultado sin la clave 'flow_graph'
resultado_sin_grafo = dict(resultado)
resultado_sin_grafo.pop('flow_graph', None)
print(json.dumps(resultado_sin_grafo, indent=4, ensure_ascii=False))