# back_end/gym/utils/json_utils.py
from fastapi.responses import JSONResponse
import decimal
import datetime
import logging

logger = logging.getLogger(__name__)

class CustomJSONResponse(JSONResponse):
    """Respuesta JSON personalizada que maneja tipos de datos especiales."""
    
    def render(self, content):
        """Renderiza el contenido, convirtiendo tipos de datos especiales."""
        try:
            if content:
                # Si es un diccionario, procesamos sus valores
                if isinstance(content, dict):
                    for key, value in content.items():
                        content[key] = self._process_value(value)
                # Si es una lista, procesamos cada elemento
                elif isinstance(content, list):
                    content = [self._process_value(item) for item in content]
            
            # Añadimos log para depuración
            logger.debug(f"Contenido procesado: {content}")
            
            # Llamar al método render de la clase padre
            return super().render(content)
        except Exception as e:
            logger.error(f"Error al renderizar JSON: {e}")
            # En caso de error, devolvemos un mensaje de error
            error_content = {"success": False, "error": f"Error al procesar la respuesta: {str(e)}"}
            return super().render(error_content)
    
    def _process_value(self, value):
        """Procesa un valor para asegurar que pueda ser serializado a JSON."""
        # Si es None, devolvemos None
        if value is None:
            return None
        
        # Si es un diccionario, procesamos cada valor del diccionario
        if isinstance(value, dict):
            return {k: self._process_value(v) for k, v in value.items()}
        
        # Si es una lista, procesamos cada elemento de la lista
        if isinstance(value, list):
            return [self._process_value(item) for item in value]
        
        # Si es un decimal, lo convertimos a float
        if isinstance(value, decimal.Decimal):
            return float(value)
        
        # Si es una fecha o datetime, lo convertimos a string ISO
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.isoformat()
        
        # Para cualquier otro tipo, lo devolvemos como está
        return value