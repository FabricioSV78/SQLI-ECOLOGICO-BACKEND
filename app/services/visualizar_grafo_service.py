import networkx as nx
import matplotlib.pyplot as plt

def visualizar_grafo(flow_graph):
    """
    Visualiza el grafo de flujo de vulnerabilidad usando networkx y matplotlib.
    Recibe un diccionario con 'nodes' y 'edges'.
    """
    nodes = flow_graph.get('nodes', [])
    edges = flow_graph.get('edges', [])

    G = nx.DiGraph()

    # Agrega nodos
    for node in nodes:
        G.add_node(node['id'], label=node['label'], type=node['type'])

    # Agrega aristas
    for edge in edges:
        G.add_edge(edge['from'], edge['to'], label=edge.get('label', ''))

    pos = nx.spring_layout(G, seed=42)
    labels = nx.get_node_attributes(G, 'label')
    node_types = nx.get_node_attributes(G, 'type')
    node_colors = []
    for n in G.nodes:
        if node_types[n] == 'variable':
            node_colors.append('orange')
        elif node_types[n] == 'metodo' or node_types[n] == 'firma':
            node_colors.append('lightblue')
        elif node_types[n] == 'consulta':
            node_colors.append('red')
        else:
            node_colors.append('gray')

    plt.figure(figsize=(14, 9))
    nx.draw(G, pos, labels=labels, with_labels=True, node_color=node_colors, node_size=1800, font_size=11, font_weight='bold', arrows=True, edge_color='gray')

    # Dibujar etiquetas de aristas
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='green', font_size=10)

    # Crear leyenda
    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color='orange', label='Variable de entrada'),
        mpatches.Patch(color='lightblue', label='Método/Firma'),
        mpatches.Patch(color='red', label='Consulta Vulnerable'),
        mpatches.Patch(color='gray', label='Otro')
    ]
    plt.legend(handles=legend_handles, loc='upper left', fontsize=12)
    plt.title('Grafo de Flujo de Vulnerabilidad\nCada nodo representa el origen, método/firma y consulta vulnerable', fontsize=15)
    plt.xlabel('Flujo: Variable → Método/Firma → Consulta Vulnerable', fontsize=12)
    plt.tight_layout()
    plt.show()
