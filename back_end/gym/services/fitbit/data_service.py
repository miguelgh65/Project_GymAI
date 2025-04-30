# Archivo: back_end/gym/services/fitbit/data_service.py
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

class FitbitDataService:
    """Servicio para procesar y transformar datos de Fitbit."""
    
    @staticmethod
    def process_data(data_type, data):
        """
        Procesa y transforma datos de Fitbit según el tipo.
        
        Args:
            data_type (str): Tipo de datos (profile, activity_summary, etc.)
            data (dict): Datos crudos de la API de Fitbit
            
        Returns:
            dict: Datos procesados
        """
        # Por ahora, simplemente devolver los datos sin procesar
        # En el futuro, se puede agregar lógica para transformar o enriquecer datos
        return data
    
    @staticmethod
    def calculate_activity_metrics(activity_data):
        """
        Calcula métricas adicionales a partir de datos de actividad.
        
        Args:
            activity_data (dict): Datos de actividad de Fitbit
            
        Returns:
            dict: Métricas calculadas
        """
        # Ejemplo: calcular porcentaje de objetivo de pasos
        try:
            if 'summary' in activity_data and 'goals' in activity_data:
                steps = activity_data['summary'].get('steps', 0)
                steps_goal = activity_data['goals'].get('steps', 0)
                
                if steps_goal > 0:
                    steps_percentage = (steps / steps_goal) * 100
                else:
                    steps_percentage = 0
                    
                return {
                    "steps_percentage": round(steps_percentage, 2),
                    "steps": steps,
                    "steps_goal": steps_goal
                }
            return {}
        except Exception as e:
            logger.exception(f"Error al calcular métricas de actividad: {str(e)}")
            return {}
    
    @staticmethod
    def extract_sleep_metrics(sleep_data):
        """
        Extrae métricas relevantes de los datos de sueño.
        
        Args:
            sleep_data (dict): Datos de sueño de Fitbit
            
        Returns:
            dict: Métricas de sueño
        """
        try:
            metrics = {
                "total_time_minutes": 0,
                "efficiency": 0,
                "deep_sleep_minutes": 0,
                "light_sleep_minutes": 0,
                "rem_sleep_minutes": 0,
                "awake_minutes": 0
            }
            
            if 'sleep' in sleep_data and sleep_data['sleep']:
                main_sleep = None
                
                # Buscar el sueño principal
                for sleep in sleep_data['sleep']:
                    if sleep.get('isMainSleep', False):
                        main_sleep = sleep
                        break
                
                # Si no hay sueño principal, usar el primero
                if not main_sleep and sleep_data['sleep']:
                    main_sleep = sleep_data['sleep'][0]
                
                if main_sleep:
                    metrics['total_time_minutes'] = main_sleep.get('minutesAsleep', 0)
                    metrics['efficiency'] = main_sleep.get('efficiency', 0)
                    
                    # Extraer fases de sueño
                    for stage in main_sleep.get('levels', {}).get('summary', {}):
                        if stage in ['deep', 'light', 'rem', 'wake']:
                            key = f"{stage}_sleep_minutes"
                            if stage == 'wake':
                                key = "awake_minutes"
                            metrics[key] = main_sleep['levels']['summary'][stage].get('minutes', 0)
            
            return metrics
        except Exception as e:
            logger.exception(f"Error al extraer métricas de sueño: {str(e)}")
            return {}