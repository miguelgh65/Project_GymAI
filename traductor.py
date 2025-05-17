import pandas as pd
from deep_translator import GoogleTranslator
import time

def translate_text(text, source='en', target='es'):
    """Traduce un texto de un idioma a otro."""
    if not isinstance(text, str) or text.strip() == '':
        return text
    
    try:
        translator = GoogleTranslator(source=source, target=target)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Error al traducir '{text}': {str(e)}")
        return text

def translate_csv(input_file, output_file, columns_to_translate, batch_size=100):
    """
    Traduce los valores de las columnas especificadas en un archivo CSV.
    
    Args:
        input_file: Ruta al archivo CSV de entrada.
        output_file: Ruta donde guardar el archivo CSV traducido.
        columns_to_translate: Lista de nombres de columnas a traducir.
        batch_size: Número de filas a procesar antes de mostrar progreso.
    """
    print(f"Leyendo archivo: {input_file}")
    df = pd.read_csv(input_file)
    total_rows = len(df)
    
    for column in columns_to_translate:
        if column not in df.columns:
            print(f"¡Advertencia! La columna '{column}' no existe en el archivo.")
            continue
        
        print(f"Traduciendo columna: {column}")
        for i, value in enumerate(df[column]):
            if i % batch_size == 0:
                print(f"Progreso: {i}/{total_rows} filas ({i/total_rows*100:.1f}%)")
            
            # Traducir el valor y almacenarlo de nuevo en el DataFrame
            df.at[i, column] = translate_text(value)
            
            # Pequeña pausa para evitar bloqueos por límite de uso de la API
            time.sleep(0.2)
    
    print(f"Guardando archivo traducido: {output_file}")
    df.to_csv(output_file, index=False)
    print(f"¡Traducción completada! Archivo guardado como: {output_file}")

def main():
    # Traducir el archivo de ingredientes
    ingredients_file = "ingredients_macros.csv"
    ingredients_output = "ingredients_macros_es.csv"
    translate_csv(ingredients_file, ingredients_output, ["Ingredient"])
    
    # Traducir el archivo de comidas
    meals_file = "list_meals.csv"
    meals_output = "list_meals_es.csv"
    translate_csv(meals_file, meals_output, ["Meal", "Recipe", "Ingredients"])
    
    print("¡Todos los archivos han sido traducidos correctamente!")
    print("Archivos generados:")
    print(f"- {ingredients_output}")
    print(f"- {meals_output}")

if __name__ == "__main__":
    main()