import re

def build_graph(parsed_data):
    """
    Construye un grafo simple de flujo para vulnerabilidades detectadas.
    Nodos: variables, métodos, consultas.
    Edges: flujo entre origen y consulta.
    """
    nodes = []
    edges = []
    for consulta in parsed_data:
        # Nodo para la consulta vulnerable
        consulta_id = f"consulta_{consulta.get('line', '')}_{consulta.get('file', '')}"
        nodes.append({"id": consulta_id, "label": consulta.get("signature", consulta.get("sql", "")), "type": "consulta"})

        # Nodo para el método/firma (si se puede extraer)
        firma = consulta.get("signature", "")
        # Extrae el nombre del método de la firma (ejemplo: List<User> findUserInsecure(String username);)
        metodo_match = re.search(r'(\w+)\s*\(', firma)
        if metodo_match:
            metodo_nombre = metodo_match.group(1)
            metodo_id = f"metodo_{metodo_nombre}_{consulta.get('line', '')}"
            nodes.append({"id": metodo_id, "label": metodo_nombre, "type": "metodo"})
            # Conecta método/firma con la consulta
            edges.append({"from": metodo_id, "to": consulta_id, "label": "llama"})
        else:
            metodo_id = None

        # Nodos para variables inseguras detectadas
        params = consulta.get("params", [])
        if not params:
            signature = consulta.get("signature", "")
            params += re.findall(r':([a-zA-Z0-9_]+)', signature)
            params += re.findall(r'\?([0-9]+)', signature)
            params += re.findall(r'\#\{([a-zA-Z0-9_]+)\}', signature)
            params += re.findall(r'\$\{([a-zA-Z0-9_]+)\}', signature)
        for var in params:
            var_id = f"var_{var}_{consulta.get('line', '')}"
            nodes.append({"id": var_id, "label": var, "type": "variable"})
            # Conecta variable -> método/firma -> consulta
            if metodo_id:
                edges.append({"from": var_id, "to": metodo_id, "label": "flujo"})
                edges.append({"from": metodo_id, "to": consulta_id, "label": "llama"})
            else:
                edges.append({"from": var_id, "to": consulta_id, "label": "flujo"})
    return {"nodes": nodes, "edges": edges}
