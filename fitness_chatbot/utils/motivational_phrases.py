# fitness_chatbot/utils/motivational_phrases.py
import random
from typing import List, Optional

def get_ronnie_phrase(exercise_name: str = None) -> str:
    """
    Devuelve una frase motivacional al estilo Ronnie Coleman.
    
    Args:
        exercise_name: Nombre del ejercicio (opcional)
        
    Returns:
        Frase motivacional
    """
    exercise_text = exercise_name.upper() if exercise_name else "EJERCICIO"
    
    # Emojis relacionados con fuerza y entrenamiento
    emojis = ["💪", "🔥", "💯", "⚡", "🏋️", "🦍", "🦁", "💥", "🚀", "🏆", "👊", "😤", "🥇"]
    
    # Seleccionar 2-3 emojis aleatorios para la frase
    selected_emojis = random.sample(emojis, k=min(3, len(emojis)))
    emoji_prefix = "".join(selected_emojis)
    emoji_suffix = "".join(random.sample(emojis, k=min(2, len(emojis))))
    
    # Posibles frases según el tipo de ejercicio
    base_phrases = [
        f"# {emoji_prefix} ¡BOOM! ¡{exercise_text} REGISTRADO! {emoji_suffix}\n\n¡LIGHTWEIGHT BABY! ¡YEAAAAAH BUDDY!",
        f"# {emoji_prefix} ¡AIN'T NOTHIN' BUT A PEANUT! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡EVERYBODY WANNA BE A BODYBUILDER!",
        f"# {emoji_prefix} ¡{exercise_text} COMPLETADO! {emoji_suffix}\n\n¡LIGHTWEIGHT BABY! ¿Qué más vas a destrozar hoy?",
        f"# {emoji_prefix} ¡BOOOOM! ¡{exercise_text}! {emoji_suffix}\n\n¡SIGAMOS CRECIENDO! ¡NO PAIN NO GAIN!",
        f"# {emoji_prefix} ¡REGISTRASTE {exercise_text}! {emoji_suffix}\n\n¡HOY VAMOS A HACER LO QUE OTROS NO HARÁN, PARA TENER LO QUE OTROS NO TIENEN!",
        f"# {emoji_prefix} ¡{exercise_text} COMPLETADO! {emoji_suffix}\n\n¡SIGUE ASÍ! ¡CADA REPETICIÓN TE ACERCA A TU META!",
        f"# {emoji_prefix} ¡{exercise_text} REGISTRADO! {emoji_suffix}\n\n¡SIGUEEEEE! ¡YEAAAAAH BUDDY!",
        f"# {emoji_prefix} ¡TODOS QUIEREN SER CULTURISTAS! {emoji_suffix}\n\n¡PERO NADIE QUIERE LEVANTAR ESTE PESO PESADO! ¡{exercise_text} REGISTRADO!",
        f"# {emoji_prefix} ¡WOOOOO! ¡{exercise_text}! {emoji_suffix}\n\n¡SIGUE ROMPIENDO BARRERAS!",
        f"# {emoji_prefix} ¡YEAH BUDDY! ¡{exercise_text}! {emoji_suffix}\n\n¡AHORA A POR EL SIGUIENTE!",
        f"# {emoji_prefix} ¡{exercise_text} HECHO! {emoji_suffix}\n\n¡RONNIE ESTÁ ORGULLOSO DE TI!",
        f"# {emoji_prefix} ¡MENOS HABLAR, MÁS LEVANTAR! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡YEAAAAAH!",
        f"# {emoji_prefix} ¡EL TIEMPO EN EL GYM ES UNA INVERSIÓN! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO Y LISTO PARA LOS GAINS!",
        f"# {emoji_prefix} ¡ESO ES! ¡{exercise_text}! {emoji_suffix}\n\n¡SIGUE HACIENDO QUE PASE! ¡TODO EL MUNDO QUIERE SER UN CULTURISTA, PERO NADIE QUIERE LEVANTAR ESTE MALDITO PESO!"
    ]
    
    # Frases específicas según el tipo de ejercicio
    exercise_specific_phrases = []
    
    # Para press banca
    if exercise_name and ("press" in exercise_name.lower() and "banca" in exercise_name.lower()):
        exercise_specific_phrases = [
            f"# {emoji_prefix} ¡PECHO DE ACERO! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡SIGUEEEEE EMPUJANDO ESOS KILOS, BABY!",
            f"# {emoji_prefix} ¡BOOM! ¡PRESS BANCA! {emoji_suffix}\n\n¡TUS FIBRAS MUSCULARES ESTÁN GRITANDO DE ALEGRÍA! ¡YEAAAH BUDDY!",
            f"# {emoji_prefix} ¡PECTORAL EN FUEGO! {emoji_suffix}\n\n¡PRESS BANCA REGISTRADO! ¡LIGHTWEIGHT BABY!"
        ]
    
    # Para sentadillas
    elif exercise_name and ("sentadilla" in exercise_name.lower() or "squat" in exercise_name.lower()):
        exercise_specific_phrases = [
            f"# {emoji_prefix} ¡REY DE LAS SENTADILLAS! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡LIGHTWEIGHT BABY!",
            f"# {emoji_prefix} ¡QUADS DE PODER! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡LAS SENTADILLAS SON EL DESAYUNO DE LOS CAMPEONES!",
            f"# {emoji_prefix} ¡SENTADILLAS PARA LA GLORIA! {emoji_suffix}\n\n¡REGISTRADO! ¡ASÍ SE HACE, BABY!"
        ]
    
    # Para peso muerto
    elif exercise_name and ("peso muerto" in exercise_name.lower() or "deadlift" in exercise_name.lower()):
        exercise_specific_phrases = [
            f"# {emoji_prefix} ¡LEVANTAR Y CONQUISTAR! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡ERES UNA BESTIA!",
            f"# {emoji_prefix} ¡BEAST MODE: ACTIVADO! {emoji_suffix}\n\n¡{exercise_text} REGISTRADO! ¡EVERYBODY WANNA BE A BODYBUILDER!",
            f"# {emoji_prefix} ¡PESO MUERTO = REY DE LOS EJERCICIOS! {emoji_suffix}\n\n¡REGISTRADO! ¡SIGUE LEVANTANDO, BABY!"
        ]
    
    # Si hay frases específicas, úsalas, si no, usa las generales
    phrases = exercise_specific_phrases if exercise_specific_phrases else base_phrases
    
    # Seleccionar una frase aleatoria
    return random.choice(phrases)

def get_arnold_phrase(exercise_name: str = None) -> str:
    """
    Devuelve una frase motivacional al estilo Arnold Schwarzenegger.
    
    Args:
        exercise_name: Nombre del ejercicio (opcional)
        
    Returns:
        Frase motivacional
    """
    exercise_text = exercise_name.upper() if exercise_name else "EJERCICIO"
    
    # Emojis relacionados con fuerza y entrenamiento
    emojis = ["💪", "🔥", "💯", "⚡", "🏋️", "🧠", "🦾", "💎", "🏆", "👑", "🥇"]
    
    # Seleccionar 1-2 emojis aleatorios para la frase
    emoji_prefix = "".join(random.sample(emojis, k=min(2, len(emojis))))
    emoji_suffix = "".join(random.sample(emojis, k=min(1, len(emojis))))
    
    phrases = [
        f"# {emoji_prefix} ¡Hasta la vista, baby! {emoji_suffix}\n\n{exercise_text} registrado. Volverás.",
        f"# {emoji_prefix} El {exercise_text} ha sido registrado. {emoji_suffix}\n\nRecuerda: \"Sin dolor, no hay crecimiento.\"",
        f"# {emoji_prefix} Tu {exercise_text} está ahora en la base de datos. {emoji_suffix}\n\nEl culturismo es como cualquier otro deporte. Para tener éxito, debes dedicarte al 100%.",
        f"# {emoji_prefix} ¡{exercise_text} registrado! {emoji_suffix}\n\nNo te preocupes por los fracasos, preocúpate por las oportunidades que pierdes cuando ni siquiera lo intentas.",
        f"# {emoji_prefix} Has dominado el {exercise_text}. {emoji_suffix}\n\nLa mente es la clave para el entrenamiento y la competición; estés donde estés, tu mente está ahí también.",
        f"# {emoji_prefix} Tu {exercise_text} ha sido terminado... {emoji_suffix}\n\n¡Pero tu entrenamiento nunca termina!",
        f"# {emoji_prefix} ¡{exercise_text} completado! {emoji_suffix}\n\nLa última repetición, la más dolorosa, es la que hace crecer el músculo.",
        f"# {emoji_prefix} He registrado tu {exercise_text}. {emoji_suffix}\n\nEl secreto es trabajar duro. Por cada ejercicio registrado estás un paso más cerca de tu meta.",
        f"# {emoji_prefix} ¡{exercise_text} registrado! {emoji_suffix}\n\nTu cuerpo es un reflejo de tu estilo de vida. ¡Sigue así!",
        f"# {emoji_prefix} El {exercise_text} ya está en el sistema. {emoji_suffix}\n\nRecuerda: el éxito no llegará por sí solo, tienes que trabajar por él."
    ]
    
    return random.choice(phrases)

def get_random_motivation(exercise_name: str = None, style: str = "ronnie") -> str:
    """
    Devuelve una frase motivacional aleatoria según el estilo solicitado.
    
    Args:
        exercise_name: Nombre del ejercicio (opcional)
        style: Estilo de la frase ("ronnie", "arnold", "random")
        
    Returns:
        Frase motivacional
    """
    if style.lower() == "arnold":
        return get_arnold_phrase(exercise_name)
    elif style.lower() == "random":
        return random.choice([get_ronnie_phrase(exercise_name), get_arnold_phrase(exercise_name)])
    else:  # Default es Ronnie
        return get_ronnie_phrase(exercise_name)