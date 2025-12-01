import re

def build_graph(parsed_data):
    """
    Construye un grafo simple de flujo para vulnerabilidades detectadas.
    Nodos: variables, métodos, consultas.
    Edges: flujo entre origen y consulta.
    """
    # Use dicts/sets to avoid duplicate nodes/edges and O(n) membership checks
    nodes_by_id = {}
    edges_set = set()

    def add_node(node_id, label, ntype):
        if node_id not in nodes_by_id:
            nodes_by_id[node_id] = {"id": node_id, "label": label, "type": ntype}

    def add_edge(frm, to, label):
        key = (frm, to, label)
        if key not in edges_set:
            edges_set.add(key)

    for consulta in parsed_data:
        consulta_id = f"consulta_{consulta.get('line', '')}_{consulta.get('file', '')}"
        add_node(consulta_id, consulta.get("signature", consulta.get("sql", "")), "consulta")

        firma = consulta.get("signature", "")
        metodo_match = re.search(r'(\w+)\s*\(', firma)
        metodo_id = None
        if metodo_match:
            metodo_nombre = metodo_match.group(1)
            metodo_id = f"metodo_{metodo_nombre}_{consulta.get('line', '')}"
            add_node(metodo_id, metodo_nombre, "metodo")
            add_edge(metodo_id, consulta_id, "llama")

        # Params: prefer existing parsed params, otherwise extract from signature
        params = list(consulta.get("params", []) or [])
        if not params:
            signature = consulta.get("signature", "")
            # Collect fragments using list comprehensions
            params = (
                re.findall(r':([a-zA-Z0-9_]+)', signature)
                + re.findall(r'\?([0-9]+)', signature)
                + re.findall(r'\#\{([a-zA-Z0-9_]+)\}', signature)
                + re.findall(r'\$\{([a-zA-Z0-9_]+)\}', signature)
            )

        for var in params:
            var_id = f"var_{var}_{consulta.get('line', '')}"
            add_node(var_id, var, "variable")
            # Conecta variable -> método/firma -> consulta
            if metodo_id:
                add_edge(var_id, metodo_id, "flujo")
                add_edge(metodo_id, consulta_id, "llama")
            else:
                add_edge(var_id, consulta_id, "flujo")

    return {"nodes": list(nodes_by_id.values()), "edges": [{"from": f, "to": t, "label": l} for (f, t, l) in edges_set]}
