# fitness_chatbot/utils/prompt_manager.py
import os
import logging
import re
from typing import Dict, List

logger = logging.getLogger("fitness_chatbot")

class PromptManager:
    """Gestor centralizado de prompts para el chatbot de fitness."""
    
    @staticmethod
    def load_prompt(category: str, prompt_type: str) -> str:
        """
        Carga un prompt desde un archivo.
        
        Args:
            category: Categoría del prompt (router, exercise, nutrition, progress)
            prompt_type: Tipo de prompt (system, human)
            
        Returns:
            Contenido del prompt o un texto por defecto si no se encuentra
        """
        # Calcular la ruta al prompt
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", category, f"{prompt_type}.txt")
        
        try:
            # Verificar si el archivo existe
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            else:
                logger.warning(f"Archivo de prompt no encontrado: {prompt_path}")
                # Devolver un prompt genérico por defecto
                return PromptManager._get_default_prompt(category, prompt_type)
                
        except Exception as e:
            logger.error(f"Error cargando prompt '{category}/{prompt_type}': {str(e)}")
            return PromptManager._get_default_prompt(category, prompt_type)
    
    @staticmethod
    def format_prompt(template: str, **kwargs) -> str:
        """
        Formatea un template de prompt con las variables proporcionadas.
        
        Args:
            template: Template del prompt
            **kwargs: Variables para formatear el template
            
        Returns:
            Prompt formateado
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Falta la clave {e} para formatear el prompt")
            return template
        except Exception as e:
            logger.error(f"Error formateando prompt: {e}")
            return template
    
    @staticmethod
    def get_prompt_messages(category: str, **kwargs) -> List[Dict[str, str]]:
        """
        Prepara mensajes para el LLM basados en el prompt estructurado.
        
        Args:
            category: Categoría del prompt
            **kwargs: Variables para formatear el prompt
            
        Returns:
            Lista de mensajes con roles para el LLM
        """
        # Cargar prompts
        system_content = PromptManager.load_prompt(category, "system")
        human_template = PromptManager.load_prompt(category, "human")
        
        # Formatear el prompt del usuario
        human_content = PromptManager.format_prompt(human_template, **kwargs)
        
        # Extraer el contenido de las etiquetas <system>
        system_match = re.search(r'<s>(.*?)</s>', system_content, re.DOTALL)
        if system_match:
            system_content = system_match.group(1).strip()
        else:
            # Si no encuentra <s>, buscar otras etiquetas comunes
            system_match = re.search(r'<system>(.*?)</system>', system_content, re.DOTALL)
            if system_match:
                system_content = system_match.group(1).strip()
        
        # Extraer el contenido de las etiquetas <human>
        human_match = re.search(r'<human>(.*?)</human>', human_content, re.DOTALL)
        human_content = human_match.group(1).strip() if human_match else human_content
        
        # Crear mensajes
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": human_content}
        ]
        
        return messages
    
    @staticmethod
    def _get_default_prompt(category: str, prompt_type: str) -> str:
        """
        Devuelve un prompt por defecto para una categoría y tipo.
        
        Args:
            category: Categoría del prompt
            prompt_type: Tipo de prompt
            
        Returns:
            Prompt por defecto con formato de etiquetas
        """
        if category == "router":
            if prompt_type == "system":
                return "<s>Clasifica el mensaje en una categoría: exercise, nutrition, progress, log_activity, general.</s>"
            else:  # human
                return "<human>Analiza el siguiente mensaje y clasifícalo según su intención:\n\n{query}</human>"
        
        elif category == "exercise":
            if prompt_type == "system":
                return "<s>Eres un entrenador personal especializado en ejercicios y rutinas de entrenamiento.</s>"
            else:  # human
                return "<context>{user_context}</context>\n\n<human>{query}</human>"
        
        elif category == "nutrition":
            if prompt_type == "system":
                return "<s>Eres un nutricionista especializado en nutrición deportiva.</s>"
            else:  # human
                return "<context>{user_context}</context>\n\n<human>{query}</human>"
        
        elif category == "progress":
            if prompt_type == "system":
                return "<s>Eres un analista de progreso físico.</s>"
            else:  # human
                return "<context>{user_context}</context>\n\n<human>{query}</human>"
        
        elif category == "log_activity":
            if prompt_type == "system":
                return "<s>Extrae datos estructurados de actividades para registrar en la base de datos.</s>"
            else:  # human
                return "<human>Extrae los datos para registrar esta actividad:\n\n{query}</human>"
        
        else:
            return f"<s>Prompt por defecto para {category}/{prompt_type}.</s>"