import os
import logging
import matplotlib.pyplot as plt
import networkx as nx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness_chatbot")

def create_and_visualize_graph():
    """Crea y visualiza el grafo de fitness manualmente."""
    # Importar lo mínimo necesario para la visualización
    from fitness_chatbot.schemas.agent_state import AgentState, IntentType
    from fitness_chatbot.schemas.memory_schemas import MemoryState
    
    # Crear grafo NetworkX manualmente
    G = nx.DiGraph()
    
    # Añadir nodos
    nodes = ["START", "classify_intent", "process_exercise", "process_nutrition", 
             "process_progress", "log_activity", "generate_response", "END"]
    for node in nodes:
        G.add_node(node)
    
    # Añadir aristas básicas
    G.add_edge("START", "classify_intent")
    G.add_edge("process_exercise", "generate_response")
    G.add_edge("process_nutrition", "generate_response")
    G.add_edge("process_progress", "generate_response")
    G.add_edge("log_activity", "generate_response")
    G.add_edge("generate_response", "END")
    
    # Añadir aristas condicionales
    G.add_edge("classify_intent", "process_exercise", label="exercise")
    G.add_edge("classify_intent", "process_nutrition", label="nutrition")
    G.add_edge("classify_intent", "process_progress", label="progress")
    G.add_edge("classify_intent", "log_activity", label="log_activity")
    G.add_edge("classify_intent", "generate_response", label="general")
    
    # Visualizar
    plt.figure(figsize=(12, 8))
    
    # Mejorar el layout usando el layout jerárquico
    pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, 
                         node_color=['lightgreen', 'lightblue', 'salmon', 'lightyellow', 'lightpink', 'violet', 'lightgray', 'white'],
                         node_size=2000)
    
    # Dibujar aristas
    nx.draw_networkx_edges(G, pos, arrowsize=20)
    
    # Añadir etiquetas a los nodos
    nx.draw_networkx_labels(G, pos, font_weight='bold')
    
    # Añadir etiquetas a las aristas (opciones)
    edge_labels = {(u, v): d.get('label', '') for u, v, d in G.edges(data=True) if 'label' in d}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    # Ajustar el aspecto
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen
    output_file = os.path.abspath("fitness_graph_manual.png")
    plt.savefig(output_file)
    print(f"Grafo guardado como: {output_file}")
    
    return G

if __name__ == "__main__":
    try:
        import networkx
        if not hasattr(networkx, 'nx_agraph'):
            print("Instala pygraphviz para mejorar el layout: pip install pygraphviz")
    except ImportError:
        print("NetworkX no está instalado. Instalalo con: pip install networkx")
    
    try:
        G = create_and_visualize_graph()
        print("\nArchivos generados:")
        os.system("ls -la fitness_graph*")
    except Exception as e:
        print(f"Error al crear visualización: {e}")