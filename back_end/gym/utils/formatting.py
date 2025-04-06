import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re


def clean_input(text: str) -> str:
    """
    Limpia el texto de entrada eliminando timestamps y nombres de usuario.
    
    Args:
        text (str): Texto de entrada con posibles timestamps y nombres de usuario.
        
    Returns:
        str: Texto limpio.
    """
    return re.sub(r'\[\d+/\d+, \d+:\d+\] .*?: ', '', text).strip()