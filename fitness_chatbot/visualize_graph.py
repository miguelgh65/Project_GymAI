# fitness_chatbot/visualize_graph.py
import os
import logging
import matplotlib.pyplot as plt
import networkx as nx
import inspect
import re
from typing import Dict, Any, List, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness_chatbot")

def create_and_visualize_graph():
    """Crea y visualiza el grafo de fitness con patrones de fan-in/fan-out."""
    # Importar el grafo real
    try:
        from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
        from fitness_chatbot.schemas.agent_state import IntentType
        
        # Crear grafo NetworkX
        G = nx.DiGraph()
        
        # Obtener el código fuente de la función
        fitness_graph_source = inspect.getsource(create_fitness_graph)
        logger.info("Código de fitness_graph.py cargado correctamente")
        
        # Extraer nodos del código fuente
        nodes = extract_nodes_from_source(fitness_graph_source)
        nodes.extend(["START", "END"])  # Añadir nodos adicionales para la visualización
        nodes = sorted(set(nodes))  # Eliminar duplicados y ordenar
        
        # Colores para nodos
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
            color = node_colors.get(node, "white")
            G.add_node(node, color=color)
        
        # Extraer aristas directas
        direct_edges = extract_direct_edges(fitness_graph_source)
        
        # Extraer aristas condicionales
        conditional_edges = extract_conditional_edges(fitness_graph_source)
        
        # Añadir la arista inicial
        G.add_edge("START", "classify_intent")
        
        # Añadir aristas directas
        for source, target in direct_edges:
            G.add_edge(source, target)
        
        # Añadir aristas condicionales con estilos
        for source, target, condition in conditional_edges:
            if "process_history" in source and "process_progress" in target and "is_progress" in condition:
                # Historia a progreso (vía fitbit) cuando es progress
                G.add_edge(source, "process_fitbit", style="dashed", color="red", label="if progress")
            elif "process_fitbit" in source and "process_progress" in target and "is_progress" in condition:
                # Fitbit a progreso cuando es progress
                G.add_edge(source, target, style="dashed", color="red", label="if progress")
            elif "classify_intent" in source and "process_history" in target and "progress" in condition.lower():
                # Classify intent a history cuando es progress
                G.add_edge(source, target, style="dashed", color="red", label="if progress")
            elif "process_history" in source and "generate_response" in target and "not" in condition:
                # Historia a generate cuando no es progress
                G.add_edge(source, target, style="dotted", label="if not progress")
            elif "process_fitbit" in source and "generate_response" in target and "not" in condition:
                # Fitbit a generate cuando no es progress 
                G.add_edge(source, target, style="dotted", label="if not progress")
            else:
                # Otras conexiones condicionales
                G.add_edge(source, target, style="solid", label=condition)
        
        # Visualizar el grafo
        visualize_graph(G, "Grafo de Fitness Chatbot con Fan-in/Fan-out para Progress")
        
        return G
        
    except ImportError as e:
        logger.error(f"Error importando el grafo: {e}")
        print(f"Error: No se pudo importar el grafo. Verifica que la ruta es correcta.")
        return None
    except Exception as e:
        logger.error(f"Error analizando el grafo: {e}")
        print(f"Error al analizar el grafo: {e}")
        return None

def extract_nodes_from_source(source_code: str) -> List[str]:
    """Extrae los nombres de los nodos del código fuente."""
    nodes = []
    # Buscar líneas donde se añaden nodos
    for line in source_code.split('\n'):
        if 'graph.add_node(' in line:
            # Extraer nombre del nodo
            node_match = line.split('graph.add_node(')[1].split(',')[0].strip('"\'')
            nodes.append(node_match)
    return nodes

def extract_direct_edges(source_code: str) -> List[Tuple[str, str]]:
    """Extrae las aristas directas (graph.add_edge) del código fuente."""
    edges = []
    # Buscar líneas donde se añaden aristas directas
    for line in source_code.split('\n'):
        if 'graph.add_edge(' in line:
            parts = line.split('graph.add_edge(')[1].split(')')[0].split(',')
            if len(parts) >= 2:
                source = parts[0].strip('"\'')
                target = parts[1].strip('"\'')
                edges.append((source, target))
    return edges

def extract_conditional_edges(source_code: str) -> List[Tuple[str, str, str]]:
    """Extrae las aristas condicionales del código fuente."""
    conditional_edges = []
    
    # Buscar bloques de add_conditional_edges
    conditional_blocks = re.findall(r'graph.add_conditional_edges\([^)]+\)[\s\S]+?{([^}]+)}', source_code)
    
    # Analizar cada bloque
    for block in conditional_blocks:
        # Extraer el nodo origen de la función add_conditional_edges más cercana
        source_match = re.search(r'graph.add_conditional_edges\(\s*["\']([^"\']+)["\']', source_code)
        if source_match:
            source_node = source_match.group(1)
            
            # Analizar el diccionario de destinos
            for line in block.split('\n'):
                if ":" in line and not line.strip().startswith('#'):
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        condition = parts[0].strip().strip('"\'{}')
                        target = parts[1].strip().strip(',"\'{}')
                        
                        # Añadir la conexión condicional
                        conditional_edges.append((source_node, target, condition))
    
    # Buscar también en la lógica de las funciones de decisión
    # (Esto es simplificado y puede no capturar toda la lógica, especialmente en funciones complejas)
    decision_functions = re.findall(r'def ([^(]+)\(states\):[^:]+return\s+([^#\n]+)', source_code, re.DOTALL)
    for func_name, return_value in decision_functions:
        # Buscar dónde se usa esta función
        usage_match = re.search(r'graph.add_conditional_edges\(\s*["\']([^"\']+)["\'],\s*' + re.escape(func_name), source_code)
        if usage_match:
            source_node = usage_match.group(1)
            return_lines = return_value.strip().split('\n')
            for line in return_lines:
                # Simplificar y extraer las condiciones/destinos
                if 'return' in line and '"' in line:
                    condition = "based on " + func_name  # Simplificado
                    target_match = re.search(r'return\s+["\']([^"\']+)["\']', line)
                    if target_match:
                        target = target_match.group(1)
                        conditional_edges.append((source_node, target, condition))
    
    return conditional_edges

def visualize_graph(G, title):
    """Visualiza el grafo con estilos específicos."""
    plt.figure(figsize=(16, 12))
    
    # Mejorar el layout usando dot (requiere pygraphviz)
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except:
        # Fallback a un layout básico
        pos = nx.spring_layout(G, seed=42)
    
    # Dibujar nodos con colores personalizados
    node_colors = [G.nodes[node].get("color", "white") for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2500, alpha=0.8)
    
    # Dibujar diferentes tipos de aristas
    normal_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style', 'solid') == 'solid']
    dashed_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dashed']
    dotted_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dotted']
    
    # Dibujar aristas según su estilo
    nx.draw_networkx_edges(G, pos, edgelist=normal_edges, arrowsize=20)
    nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, arrowsize=20, 
                          style='dashed', edge_color='red', width=2)
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
    plt.title(title, fontsize=16)
    
    # Añadir leyenda
    plt.figtext(0.01, 0.01, "Líneas sólidas: Flujo normal\nLíneas punteadas rojas: Fan-out/Fan-in para Progress\nLíneas punteadas: Rutas condicionales", fontsize=12)
    
    # Ajustar el aspecto
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen
    output_file = os.path.abspath("fitness_graph_fanin_fanout.png")
    plt.savefig(output_file)
    print(f"Grafo guardado como: {output_file}")

if __name__ == "__main__":
    try:
        import networkx
        if not hasattr(networkx, 'nx_agraph'):
            print("Instala pygraphviz para mejorar el layout: pip install pygraphviz")
    except ImportError:
        print("NetworkX no está instalado. Instalalo con: pip install networkx")
    
    try:
        G = create_and_visualize_graph()
        if G:
            print("\nArchivos generados:")
            os.system("ls -la fitness_graph*")
    except Exception as e:
        print(f"Error al crear visualización: {e}")