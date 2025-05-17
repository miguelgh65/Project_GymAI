# fitness_chatbot/utils/db_adapter.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("fitness_chatbot")

class ExerciseDBAdapter:
    """
    Adaptador para convertir los datos del chatbot al formato esperado por la base de datos.
    """
    
    @staticmethod
    def format_for_db(exercise_name: str, sets: List[Dict[str, Any]], rir: Optional[int] = None, comentarios: Optional[str] = None) -> Dict[str, Any]:
        """
        Convierte los datos de ejercicio al formato esperado por la tabla 'ejercicios'.
        
        Args:
            exercise_name: Nombre del ejercicio
            sets: Lista de series con repeticiones y pesos
            rir: Valor RIR global (opcional)
            comentarios: Comentarios adicionales (opcional)
            
        Returns:
            Dict con el formato correcto para la BD
        """
        # Asegurarse de que todos los conjuntos tienen el formato esperado
        formatted_sets = []
        for s in sets:
            # Convertir del formato LLM al formato BD
            formatted_sets.append({
                "repeticiones": int(s.get("reps", 0)),
                "peso": float(s.get("weight", 0)),
                "rir": s.get("rir", None)  # Opcional, puede ser None
            })
        
        # Calcular total de repeticiones
        total_reps = sum(s["repeticiones"] for s in formatted_sets)
        
        # Crear el formato esperado por la tabla ejercicios (formato nuevo)
        result = {
            "ejercicio": exercise_name,
            "series_json": formatted_sets,  # NUEVO: Usar series_json en lugar de repeticiones
            "repeticiones": total_reps,     # NUEVO: Campo repeticiones ahora guarda el total
            "fecha": datetime.now().isoformat()
        }
        
        # Añadir campos opcionales si están presentes
        if rir is not None:
            result["rir"] = rir
        
        if comentarios:
            result["comentarios"] = comentarios
            
        return result
    
    @staticmethod
    def adapt_sets_from_llm(sets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adapta el formato de conjuntos (sets) del LLM al formato esperado por la BD.
        
        Args:
            sets_data: Lista de conjuntos en formato LLM
            
        Returns:
            Lista de conjuntos en formato BD
        """
        adapted_sets = []
        for s in sets_data:
            try:
                # Asegurar que tenemos valores numéricos válidos
                reps = int(s.get("reps", 0))
                weight = float(s.get("weight", 0))
                rir = s.get("rir", None)  # Nuevo: Extraer RIR si está presente
                
                # Convertir al formato esperado por la BD
                set_data = {
                    "repeticiones": reps,
                    "peso": weight
                }
                
                # Añadir RIR si está presente
                if rir is not None:
                    set_data["rir"] = rir
                
                adapted_sets.append(set_data)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error adaptando conjunto: {e}. Datos: {s}")
                # Usar valores por defecto en caso de error
                adapted_sets.append({
                    "repeticiones": 0,
                    "peso": 0
                })
        
        return adapted_sets
    
    @staticmethod
    def extract_exercise_details(text: str) -> Optional[Dict[str, Any]]:
        """
        Extrae detalles de ejercicio de texto plano usando reglas simples.
        Función alternativa a format_for_postgres.
        
        Args:
            text: Texto con descripción del ejercicio
            
        Returns:
            Dict con ejercicio y repeticiones formateados para BD
        """
        try:
            # Importar funciones de log_activity_node para evitar importaciones circulares
            from fitness_chatbot.nodes.log_activity_node import extract_exercise_name, extract_rir, extract_comentarios
            
            # Extraer información básica
            exercise_name = extract_exercise_name(text)
            rir_value = extract_rir(text)
            comentarios = extract_comentarios(text)
            
            if not exercise_name:
                logger.warning(f"No se pudo extraer nombre de ejercicio de: {text}")
                return None
            
            # Extraer series y repeticiones usando regex
            import re
            series_patterns = [
                # 3x10x60kg
                r'(\d+)\s*[xX]\s*(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos?)',
                # 3 series de 10 repeticiones con 60kg
                r'(\d+)\s*series\s*(?:de)?\s*(\d+)\s*(?:reps|repeticiones)?\s*(?:con)?\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos?)',
                # 10 repeticiones con 60kg, 3 series
                r'(\d+)\s*(?:reps|repeticiones)\s*(?:con)?\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos?).*?(\d+)\s*series'
            ]
            
            formatted_sets = []
            for pattern in series_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        # Dependiendo del patrón, la posición de las repeticiones/series/pesos puede variar
                        # Intentar inferir cuál es cuál
                        if len(match) >= 3:
                            try:
                                # Si es el primer patrón (3x10x60kg)
                                series = int(match[0])
                                reps = int(match[1])
                                weight = float(match[2])
                                
                                # Crear las series
                                for _ in range(series):
                                    formatted_sets.append({
                                        "repeticiones": reps,
                                        "peso": weight
                                    })
                            except (ValueError, IndexError):
                                continue
            
            # Si no se encontraron series, usar valores por defecto
            if not formatted_sets:
                logger.warning(f"No se pudieron extraer series del ejercicio: {text}")
                formatted_sets = [{"repeticiones": 10, "peso": 0}]
            
            # Calcular total de repeticiones
            total_reps = sum(s["repeticiones"] for s in formatted_sets)
            
            # Crear estructura final con el nuevo formato
            result = {
                "ejercicio": exercise_name,
                "series_json": formatted_sets,  # Nuevo formato
                "repeticiones": total_reps,     # Total de repeticiones
                "fecha": datetime.now().isoformat()
            }
            
            # Añadir campos opcionales si están presentes
            if rir_value is not None:
                result["rir"] = rir_value
            
            if comentarios:
                result["comentarios"] = comentarios
            
            return result
        
        except Exception as e:
            logger.error(f"Error extrayendo detalles del ejercicio: {e}")
            return None
    
    @staticmethod
    def normalize_exercise_name(name: str) -> str:
        """
        Normaliza el nombre del ejercicio para consistencia en la BD.
        
        Args:
            name: Nombre del ejercicio
            
        Returns:
            Nombre normalizado
        """
        if not name:
            return "desconocido"
        
        # Mapa de normalización - añade aquí más términos según necesites
        normalization_map = {
            "press de banca": "press banca",
            "press banco": "press banca",
            "bench press": "press banca",
            "sentadilla": "sentadillas",
            "squad": "sentadillas",
            "squat": "sentadillas",
            "peso muerto": "peso muerto",
            "deadlift": "peso muerto",
            "dominada": "dominadas",
            "chin up": "dominadas",
            "pull up": "dominadas",
            "press militar": "press militar",
            "military press": "press militar",
            "curl biceps": "curl de bíceps",
            "bicep curl": "curl de bíceps",
            "curl de biceps": "curl de bíceps",
            "extensiones de triceps": "extensiones de tríceps",
            "tricep extension": "extensiones de tríceps",
            "fondos": "fondos",
            "dips": "fondos",
            "elevaciones laterales": "elevaciones laterales",
            "lateral raise": "elevaciones laterales"
        }
        
        # Buscar coincidencias exactas primero
        if name.lower() in normalization_map:
            return normalization_map[name.lower()]
        
        # Buscar coincidencias parciales
        for key, normalized in normalization_map.items():
            if key in name.lower():
                return normalized
        
        # Si no hay coincidencias, devolver el nombre original
        return name.lower()