# fitness_chatbot/chains/edit_routine_chain.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.utils.api_utils import make_api_request

logger = logging.getLogger("fitness_chatbot")

class EditRoutineChain:
    """
    Cadena para procesar solicitudes de edición de rutinas de entrenamiento.
    """
    
    @staticmethod
    async def process_query(user_id: str, query: str, auth_token: Optional[str] = None) -> str:
        """
        Procesa una solicitud para editar una rutina y devuelve una respuesta formateada.
        
        Args:
            user_id: ID del usuario
            query: Consulta en lenguaje natural
            auth_token: Token de autenticación (opcional)
            
        Returns:
            Respuesta formateada para el usuario
        """
        logger.info(f"EditRoutineChain procesando: '{query}' para usuario {user_id}")
        
        try:
            # Analizar la consulta para entender qué cambios quiere hacer el usuario
            edit_instructions = await EditRoutineChain._analyze_edit_request(query)
            
            # Comprobar si tenemos instrucciones claras
            if not edit_instructions:
                return "Lo siento, no entendí qué cambios quieres hacer en tu rutina. ¿Podrías ser más específico? Por ejemplo: 'cambia mi rutina de lunes para incluir más ejercicios de pecho'."
            
            # Intentar obtener la rutina actual a través de la API
            endpoint = "rutina_completa"
            
            response_data = make_api_request(
                endpoint=endpoint, 
                method="GET", 
                params={"user_id": user_id}, 
                auth_token=auth_token,
                timeout=10,
                retries=1
            )
            
            # Si la API responde correctamente
            if response_data.get("success", False) and "rutina" in response_data:
                # Enviar cambios a la API
                update_response = EditRoutineChain._update_routine(
                    user_id, 
                    response_data["rutina"],
                    edit_instructions,
                    auth_token
                )
                
                if update_response.get("success", False):
                    return f"✅ He actualizado tu rutina según tus indicaciones.\n\n{edit_instructions.get('confirmation_message', 'Los cambios han sido aplicados.')}"
                else:
                    return f"No pude actualizar tu rutina. {update_response.get('detail', 'Por favor, intenta de nuevo más tarde.')}"
            else:
                logger.warning("No se pudo obtener la rutina actual (backend no disponible)")
                # Respuesta de fallback
                return await EditRoutineChain._generate_fallback_response(query, edit_instructions)
        
        except Exception as e:
            logger.exception(f"Error en EditRoutineChain: {str(e)}")
            return "Lo siento, hubo un problema al procesar tu solicitud para modificar la rutina. Por favor, intenta de nuevo más tarde."
    
    @staticmethod
    async def _analyze_edit_request(query: str) -> Dict[str, Any]:
        """
        Usa el LLM para analizar la solicitud de edición y extraer información estructurada.
        
        Args:
            query: Consulta original del usuario
            
        Returns:
            Diccionario con información estructurada sobre los cambios solicitados
        """
        try:
            # Obtener LLM
            llm = get_llm()
            
            if not llm:
                logger.error("LLM no disponible para analizar solicitud de edición")
                return {
                    "day": "desconocido",
                    "change_type": "general",
                    "details": "No se pudo analizar la solicitud",
                    "confirmation_message": "He registrado tu solicitud de cambio en la rutina."
                }
            
            # Crear un prompt para extraer información estructurada
            system_prompt = """Eres un analizador de solicitudes de modificación de rutinas de ejercicio.
            Tu trabajo es extraer información estructurada de la solicitud del usuario.
            
            Debes identificar:
            1. Qué día(s) de la semana quiere modificar el usuario
            2. Qué tipo de cambio quiere hacer (añadir ejercicios, eliminar ejercicios, modificar series/repeticiones, etc.)
            3. Detalles específicos del cambio
            
            Devuelve la información en formato JSON con los siguientes campos:
            - day: día o días de la semana (lunes, martes, etc. o "todos" si aplica a toda la semana)
            - change_type: tipo de cambio (add, remove, modify, replace)
            - details: detalles específicos del cambio
            - confirmation_message: un mensaje de confirmación personalizado para el usuario
            
            Ejemplo de respuesta:
            {
              "day": "lunes",
              "change_type": "add",
              "details": "Añadir 3 series de 12 repeticiones de press de pecho",
              "confirmation_message": "He añadido press de pecho (3x12) a tu rutina de lunes."
            }"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            # Invocar LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Intentar extraer JSON
            try:
                # Buscar patrón JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    edit_data = json.loads(json_str)
                    
                    # Verificar campos requeridos
                    required_fields = ["day", "change_type", "details", "confirmation_message"]
                    if all(field in edit_data for field in required_fields):
                        return edit_data
            except Exception as e:
                logger.error(f"Error extrayendo JSON de respuesta LLM: {str(e)}")
            
            # Si no se pudo extraer JSON válido, devolver información básica
            return {
                "day": "desconocido",
                "change_type": "general",
                "details": content,
                "confirmation_message": "He registrado tu solicitud de cambio en la rutina."
            }
            
        except Exception as e:
            logger.error(f"Error analizando solicitud de edición: {str(e)}")
            return {
                "day": "desconocido",
                "change_type": "general",
                "details": "No se pudo analizar la solicitud",
                "confirmation_message": "He registrado tu solicitud de cambio en la rutina."
            }
    
    @staticmethod
    def _update_routine(user_id: str, current_routine: Dict[str, Any], edit_instructions: Dict[str, Any], auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía los cambios a la API para actualizar la rutina.
        
        Args:
            user_id: ID del usuario
            current_routine: Rutina actual
            edit_instructions: Instrucciones de edición
            auth_token: Token de autenticación
            
        Returns:
            Respuesta de la API
        """
        try:
            # En una implementación real, aquí modificaríamos la rutina según las instrucciones
            # y luego llamaríamos a la API para actualizarla
            
            # Por ahora, simular una respuesta exitosa
            return {
                "success": True,
                "detail": "Rutina actualizada exitosamente"
            }
        except Exception as e:
            logger.error(f"Error actualizando rutina: {str(e)}")
            return {
                "success": False,
                "detail": f"Error al actualizar la rutina: {str(e)}"
            }
    
    @staticmethod
    async def _generate_fallback_response(query: str, edit_instructions: Dict[str, Any]) -> str:
        """
        Genera una respuesta de fallback cuando no se puede acceder a la API.
        
        Args:
            query: Consulta original
            edit_instructions: Instrucciones de edición extraídas
            
        Returns:
            Respuesta de fallback
        """
        try:
            # Obtener LLM
            llm = get_llm()
            
            if not llm:
                return "No pude acceder al sistema para modificar tu rutina. Por favor, intenta de nuevo más tarde."
            
            # Crear un prompt para generar una respuesta
            system_prompt = """Eres un asistente de fitness que ayuda a los usuarios con sus rutinas de entrenamiento.
            El usuario ha solicitado modificar su rutina, pero no puedes acceder al sistema para hacerlo.
            
            Debes:
            1. Explicar amablemente que has entendido su solicitud pero que no puedes modificar su rutina en este momento
            2. Confirmar que has registrado su solicitud y que se procesará más tarde
            3. Ofrecer alternativas o sugerencias relacionadas con su solicitud
            
            Mantén un tono amigable y servicial."""
            
            # Preparar un mensaje con la información extraída
            day = edit_instructions.get("day", "desconocido")
            change_type = edit_instructions.get("change_type", "general")
            details = edit_instructions.get("details", "cambios en la rutina")
            
            user_message = f"Quiero {change_type} mi rutina de {day} para {details}, pero no puedes acceder al sistema para hacerlo ahora."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Invocar LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            return content
        
        except Exception as e:
            logger.error(f"Error generando respuesta fallback: {str(e)}")
            return "He recibido tu solicitud para modificar la rutina, pero no puedo acceder al sistema en este momento. Lo intentaré más tarde."