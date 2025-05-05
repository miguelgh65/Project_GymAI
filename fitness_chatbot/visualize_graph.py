# fitness_chatbot/visualize_graph.py
import os
import logging
import matplotlib.pyplot as plt
import networkx as nx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness_chatbot")

def create_and_visualize_graph():
    """Crea y visualiza el grafo de fitness con patrones de fan-in/fan-out."""
    # Importar lo mínimo necesario para la visualización
    from fitness_chatbot.schemas.agent_state import IntentType
    
    # Crear grafo NetworkX manualmente
    G = nx.DiGraph()
    
    # Añadir nodos
    nodes = [
        "START", 
        "classify_intent", 
        "process_exercise", 
        "process_nutrition",
        "process_history", 
        "process_fitbit", 
        "process_today_routine",
        "process_progress", 
        "log_activity", 
        "generate_response", 
        "END"
    ]
    
    # Colores para nodos para mejor visualización
    node_colors = {
        "START": "lightgreen",
        "classify_intent": "lightskyblue",
        "process_exercise": "lightcoral",
        "process_nutrition": "khaki",
        "process_history": "thistle",
        "process_fitbit": "lightsteelblue",
        "process_today_routine": "peachpuff",
        "process_progress": "orchid",
        "log_activity": "palegreen",
        "generate_response": "lightgrey",
        "END": "white"
    }
    
    # Añadir nodos al grafo
    for node in nodes:
        G.add_node(node)
    
    # Añadir aristas básicas
    G.add_edge("START", "classify_intent")
    
    # Conexiones normales - nodos que van directamente a generate_response
    direct_to_response = [
        "process_exercise", 
        "process_nutrition",
        "process_today_routine",
        "log_activity"
    ]
    
    for node in direct_to_response:
        G.add_edge(node, "generate_response")
    
    # Agregar la conexión de progress a generate_response
    G.add_edge("process_progress", "generate_response")
    
    # Agregar conexión final
    G.add_edge("generate_response", "END")
    
    # Añadir aristas condicionales desde classify_intent para intents normales
    normal_intents = {
        "process_exercise": "exercise",
        "process_nutrition": "nutrition",
        "process_today_routine": "today_routine",
        "log_activity": "log_activity",
        "process_history": "history",
        "process_fitbit": "fitbit",
        "generate_response": "general"
    }
    
    for node, intent in normal_intents.items():
        G.add_edge("classify_intent", node, label=intent, style="solid")
    
    # Agregar aristas especiales para el patrón fan-out en PROGRESS
    # Estas son aristas punteadas para mostrar que son condicionales
    G.add_edge("classify_intent", "process_history", label="progress", style="dashed", color="red")
    G.add_edge("classify_intent", "process_fitbit", label="progress", style="dashed", color="red")
    
    # Agregar aristas condicionales para el patrón fan-in
    # Desde history y fitbit al nodo de progress (cuando intent es progress)
    G.add_edge("process_history", "process_progress", label="si intent=progress", style="dashed", color="red")
    G.add_edge("process_fitbit", "process_progress", label="si intent=progress", style="dashed", color="red")
    
    # También agregar las conexiones directas a generate_response (cuando intent no es progress)
    G.add_edge("process_history", "generate_response", label="si intent≠progress", style="dotted")
    G.add_edge("process_fitbit", "generate_response", label="si intent≠progress", style="dotted")
    
    # Visualizar
    plt.figure(figsize=(16, 12))
    
    # Mejorar el layout usando dot (require pygraphviz)
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except:
        # Fallback a un layout básico
        pos = nx.spring_layout(G, seed=42)
    
    # Dibujar nodos con colores personalizados
    color_list = [node_colors[node] for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=color_list, node_size=2500, alpha=0.8)
    
    # Dibujar aristas normales
    normal_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style', 'solid') == 'solid']
    nx.draw_networkx_edges(G, pos, edgelist=normal_edges, arrowsize=20)
    
    # Dibujar aristas punteadas (fan-out para progress)
    dashed_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dashed']
    nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, arrowsize=20, 
                          style='dashed', edge_color='red', width=2)
    
    # Dibujar aristas punteadas (fan-in condicional)
    dotted_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dotted']
    nx.draw_networkx_edges(G, pos, edgelist=dotted_edges, arrowsize=20, 
                          style='dotted', width=1.5)
    
    # Añadir etiquetas a los nodos
    nx.draw_networkx_labels(G, pos, font_weight='bold', font_size=12)
    
    # Añadir etiquetas a las aristas
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if 'label' in d:
            edge_labels[(u, v)] = d['label']
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)
    
    # Añadir título
    plt.title("Grafo de Fitness Chatbot con Fan-in/Fan-out para Progress", fontsize=16)
    
    # Añadir leyenda
    plt.figtext(0.01, 0.01, "Líneas sólidas: Flujo normal\nLíneas punteadas rojas: Fan-out/Fan-in para Progress\nLíneas punteadas: Rutas condicionales", fontsize=12)
    
    # Ajustar el aspecto
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen
    output_file = os.path.abspath("fitness_graph_fanin_fanout.png")
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