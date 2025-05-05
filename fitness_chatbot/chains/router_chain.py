# fitness_chatbot/chains/router_chain.py

import logging
import json
import re
from typing import Dict, Any, Optional, List

from fitness_chatbot.schemas.agent_state import IntentType
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

class RouterChain:
    """
    Cadena de clasificación de intenciones para el chatbot de fitness.
    Utiliza exclusivamente LLM para determinar la intención del usuario.
    """
    
    @staticmethod
    async def classify_intent(query: str) -> Dict[str, Any]:
        """
        Clasifica la intención del usuario utilizando exclusivamente un LLM.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Dict con la intención detectada y explicación
        """
        logger.info(f"🔍 RouterChain procesando consulta: '{query}'")
        
        # Obtener prompts específicos para el router
        messages = PromptManager.get_prompt_messages("router", query=query)
        
        # Obtener el LLM configurado
        llm = get_llm()
        
        if not llm:
            logger.error("❌ RouterChain: No se pudo obtener el LLM para clasificación")
            return {
                "intent": IntentType.GENERAL,
                "explanation": "Error: LLM no disponible para clasificación"
            }
        
        try:
            # Configurar LLM para clasificación precisa
            if hasattr(llm, 'with_temperature'):
                llm = llm.with_temperature(0.1)  # Temperatura muy baja para clasificaciones deterministas
            
            # Invocar el LLM con el prompt del router
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            logger.debug(f"📊 RouterChain: Respuesta cruda del LLM:\n{content[:300]}...")
            
            # Extraer el JSON con la clasificación
            intent_data = RouterChain._extract_intent_from_response(content)
            
            if intent_data and "intent" in intent_data:
                # Normalizar la intención al formato estándar
                normalized_intent = RouterChain._normalize_intent(intent_data["intent"])
                intent_data["intent"] = normalized_intent
                
                logger.info(f"🎯 RouterChain: Intención detectada: {normalized_intent}")
                return intent_data
            else:
                logger.warning("⚠️ RouterChain: No se pudo extraer intención del LLM")
                return {
                    "intent": IntentType.GENERAL,
                    "explanation": "No se pudo determinar la intención con suficiente confianza"
                }
        
        except Exception as e:
            logger.error(f"❌ RouterChain: Error en clasificación: {str(e)}")
            return {
                "intent": IntentType.GENERAL,
                "explanation": f"Error durante la clasificación: {str(e)}"
            }
    
    @staticmethod
    def _extract_intent_from_response(content: str) -> Optional[Dict[str, Any]]:
        """
        Extrae la intención y explicación de la respuesta del LLM.
        
        Args:
            content: Respuesta completa del LLM
            
        Returns:
            Dict con intent y explanation, o None si no se pudo extraer
        """
        try:
            # Primero intentar extraer un objeto JSON completo
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                intent_data = json.loads(json_str)
                
                # Verificar que tenga los campos necesarios
                if "intent" in intent_data:
                    return intent_data
            
            # Si no se encontró un JSON válido, intentar extraer con regex
            intent_match = re.search(r'intent["\']?\s*:\s*["\']?(\w+)["\']?', content)
            if intent_match:
                intent = intent_match.group(1).lower()
                
                # Intentar extraer explicación si está disponible
                explanation_match = re.search(r'explanation["\']?\s*:\s*["\']?(.*?)["\']?[,}]', content)
                explanation = explanation_match.group(1) if explanation_match else "Sin explicación disponible"
                
                return {
                    "intent": intent,
                    "explanation": explanation
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error extrayendo intención: {str(e)}")
            return None
    
    @staticmethod
    def _normalize_intent(intent: str) -> str:
        """
        Normaliza la intención a uno de los tipos estándar definidos en IntentType.
        
        Args:
            intent: Intención detectada por el LLM
            
        Returns:
            Intención normalizada
        """
        intent_lower = intent.lower().strip()
        
        # Mapeo de variantes comunes a los tipos estándar
        intent_map = {
            IntentType.EXERCISE: ["exercise", "ejercicio", "entrenamiento", "ejercitar"],
            IntentType.NUTRITION: ["nutrition", "nutricion", "nutrición", "dieta", "alimentacion", "alimentación"],
            IntentType.PROGRESS: ["progress", "progreso", "evolución", "evolucion", "estadística", "estadistica", "histórico", "historico"],
            IntentType.LOG_ACTIVITY: ["log_activity", "log", "registrar", "anotar", "registro", "actividad"],
            IntentType.FITBIT: ["fitbit", "datos", "personal", "salud", "health", "métrica", "metrica", "medición", "medicion"],
            IntentType.GENERAL: ["general", "otro", "other", "desconocido", "unknown"]
        }
        
        # Buscar coincidencias en el mapeo
        for standard_intent, variants in intent_map.items():
            if any(variant == intent_lower for variant in variants) or any(variant in intent_lower for variant in variants):
                return standard_intent
        
        # Si no hay coincidencias, usar general como fallback
        return IntentType.GENERAL