# fitness_agent/agent/utils/prompt_utils.py
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("fitness_agent")

def get_formatted_prompt(prompt_type: str, variant: str = "system", **kwargs) -> str:
    """
    Gets a formatted prompt from the prompts directory.
    
    Args:
        prompt_type: Type of prompt (e.g., 'exercise', 'nutrition')
        variant: Variant of the prompt (e.g., 'system', 'user')
        **kwargs: Additional variables to format the prompt with
        
    Returns:
        str: The formatted prompt text
    """
    try:
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the path to the prompts directory (../../prompts relative to this file)
        prompts_dir = os.path.join(current_dir, "..", "prompts")
        
        # Determine the filename - either prompt_type.txt or prompt_type_variant.txt
        filename = f"{prompt_type}.txt" if variant == "system" else f"{prompt_type}_{variant}.txt"
        prompt_path = os.path.join(prompts_dir, filename)
        
        # Check if the file exists
        if not os.path.exists(prompt_path):
            logger.warning(f"Prompt file not found: {prompt_path}")
            
            # Generate fallback prompts based on type
            fallback_prompts = {
                "router": "Eres un router de intención para un asistente virtual de fitness. "
                          "Clasifica el mensaje en una de estas categorías: exercise, nutrition, progress, o general. "
                          "Responde en formato JSON con: intent, confidence (0.0-1.0), y explanation.",
                          
                "exercise": "Eres un entrenador especializado en ejercicios y rutinas de entrenamiento. "
                            "Responde preguntas sobre técnicas, rutinas y consejos de entrenamiento de manera clara y motivadora.",
                            
                "nutrition": "Eres un especialista en nutrición deportiva. "
                             "Ofrece consejos sobre alimentación para optimizar rendimiento y composición corporal.",
                             
                "progress": "Eres un analista de progreso físico y deportivo. "
                            "Ayuda a interpretar datos de entrenamiento y ofrece consejos para mejorar.",
                            
                "general": "Eres un asistente virtual de fitness. "
                           "Proporciona información general sobre bienestar y fitness de manera conversacional."
            }
            
            return fallback_prompts.get(prompt_type, f"DEFAULT PROMPT FOR {prompt_type.upper()} ({variant})")
        
        # Read the prompt file
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()
        
        # Format the prompt with provided variables
        try:
            formatted_prompt = prompt_text.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing key in prompt formatting: {e}")
            formatted_prompt = prompt_text  # Return unformatted if formatting fails
            
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        return f"ERROR LOADING PROMPT FOR {prompt_type.upper()} ({variant})"